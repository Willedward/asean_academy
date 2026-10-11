"""Durable tutor sessions and atomic usage accounting."""

from __future__ import annotations

import json
import threading
from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import Error as BinasciiError
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .tutor_contracts import AnswerLockState, TutorMode
from .tutor_routing import TutorRouteDecision, TutorRoutePlan


class TutorError(RuntimeError):
    def __init__(self, code: str, message: str, status: int, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details


@dataclass(frozen=True, slots=True)
class TutorLimits:
    daily_messages: int
    daily_tokens: int
    monthly_cost_micros_sgd: int
    academy_monthly_cost_micros_sgd: int
    max_input_tokens: int
    max_output_tokens: int
    max_turn_cost_micros_sgd: int

    @property
    def max_turn_tokens(self) -> int:
        return self.max_input_tokens + self.max_output_tokens


@dataclass(frozen=True, slots=True)
class TutorGrounding:
    session_id: str
    question_title: str
    question_difficulty: int
    question_blocks: tuple[dict, ...]
    unlocked_hint_blocks: tuple[dict, ...]
    lesson_sections: tuple[dict, ...]
    unlocked_solution_blocks: tuple[dict, ...]
    latest_attempt: dict | None
    recent_messages: tuple[dict, ...]
    answer_lock_state: AnswerLockState
    incorrect_attempts: int
    premium_turns_this_session: int
    leakage_answers: tuple[str, ...]
    grounding_revision_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UsageReservation:
    reservation_id: str
    session_id: str
    learner_id: str
    usage_date: date
    usage_month: date
    route_decision_id: str | None = None


@dataclass(frozen=True, slots=True)
class UsageReservationQuote:
    max_input_tokens: int
    max_output_tokens: int
    max_cost_micros_sgd: int

    @property
    def max_tokens(self) -> int:
        return self.max_input_tokens + self.max_output_tokens


@dataclass(frozen=True, slots=True)
class UsageActual:
    input_tokens: int
    output_tokens: int
    cost_micros_sgd: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True, slots=True)
class QuotaSnapshot:
    daily_messages_remaining: int
    daily_tokens_remaining: int
    monthly_cost_remaining_micros_sgd: int
    resets_at: datetime


@dataclass(frozen=True, slots=True)
class TutorRouteDecisionCursor:
    created_at: datetime
    decision_id: str


def encode_tutor_route_cursor(created_at: datetime, decision_id: str) -> str:
    payload = json.dumps(
        [created_at.astimezone(UTC).isoformat(), str(UUID(decision_id))],
        separators=(",", ":"),
    ).encode()
    return urlsafe_b64encode(payload).decode().rstrip("=")


def decode_tutor_route_cursor(cursor: str) -> TutorRouteDecisionCursor:
    try:
        padding = "=" * (-len(cursor) % 4)
        payload = json.loads(urlsafe_b64decode(cursor + padding))
        if not isinstance(payload, list) or len(payload) != 2:
            raise ValueError
        created_at = datetime.fromisoformat(str(payload[0]))
        if created_at.tzinfo is None:
            raise ValueError
        decision_id = str(UUID(str(payload[1])))
    except (BinasciiError, UnicodeDecodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise TutorError(
            "invalid_tutor_routing_cursor",
            "The tutor routing cursor is invalid or expired.",
            422,
        ) from exc
    return TutorRouteDecisionCursor(created_at.astimezone(UTC), decision_id)


class TutorRepository(Protocol):
    def create_session(
        self,
        learner_id: str,
        *,
        practice_session_id: str,
        question_key: str,
        question_revision: int,
        model_policy_version: str,
    ) -> dict: ...

    def get_session(self, learner_id: str, session_id: str) -> dict: ...
    def close_session(self, learner_id: str, session_id: str) -> dict: ...
    def grounding(self, learner_id: str, session_id: str) -> TutorGrounding: ...

    def append_message(
        self,
        session_id: str,
        *,
        role: str,
        mode: TutorMode | None,
        content: dict,
        grounding_revision_ids: tuple[str, ...] = (),
        model_name: str | None = None,
        prompt_version: str | None = None,
        safety_outcome: str = "accepted",
        latency_ms: int | None = None,
        token_usage: dict | None = None,
        provider_name: str | None = None,
        model_tier: str | None = None,
        route_decision_id: str | None = None,
    ) -> dict: ...

    def reserve(
        self,
        learner_id: str,
        session_id: str,
        limits: TutorLimits,
        *,
        request_id: str,
        quote: UsageReservationQuote | None = None,
        routing: TutorRoutePlan | None = None,
    ) -> UsageReservation: ...

    def reconcile(
        self,
        reservation: UsageReservation,
        actual: UsageActual,
        limits: TutorLimits,
        *,
        request_id: str,
    ) -> QuotaSnapshot: ...

    def release(
        self,
        reservation: UsageReservation,
        *,
        request_id: str,
        reason: str,
    ) -> None: ...

    def admin_usage(self, usage_month: date) -> dict: ...

    def admin_route_decisions(
        self,
        usage_month: date,
        *,
        cursor: str | None = None,
        limit: int = 50,
        routing_mode: str | None = None,
        recommended_tier: str | None = None,
        executed_tier: str | None = None,
        tutor_mode: str | None = None,
        question_difficulty: int | None = None,
        reason_code: str | None = None,
        reservation_status: str | None = None,
    ) -> dict: ...


def _next_utc_day(day: date) -> datetime:
    return datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=UTC)


def _priced_tokens(tokens: int, per_million_micros_sgd: int) -> int:
    if tokens == 0 or per_million_micros_sgd == 0:
        return 0
    return (tokens * per_million_micros_sgd + 999_999) // 1_000_000


def _safe_attempt_evidence(row: dict | None) -> dict | None:
    if row is None:
        return None
    answers = row["answers"] if isinstance(row["answers"], dict) else {}
    result = row["result"] if isinstance(row["result"], dict) else {}
    parts = []
    for item in result.get("parts", []):
        if not isinstance(item, dict):
            continue
        parts.append(
            {
                "position": item.get("position"),
                "correct": item.get("correct"),
                "error": str(item["error"])[:500] if item.get("error") else None,
                "marks_awarded": item.get("marks_awarded"),
                "marks_available": item.get("marks_available"),
            }
        )
    return {
        "attempt_number": row["attempt_number"],
        "submitted_answers": {
            str(position): str(answer)[:500] for position, answer in answers.items()
        },
        "correct": row["is_correct"],
        "parts": parts,
        "marks_awarded": row["marks_awarded"],
        "marks_available": result.get("marks_available"),
    }


def _session_record(row: dict, messages: list[dict]) -> dict:
    return {
        "session_id": str(row["id"]),
        "practice_session_id": str(row["practice_session_id"]),
        "question_key": row["question_key"],
        "question_revision": row["question_revision"],
        "status": row["status"],
        "answer_lock_state": row["answer_lock_state"],
        "model_policy_version": row["model_policy_version"],
        "messages": messages,
        "created_at": row["created_at"],
        "closed_at": row["closed_at"],
    }


def _message_record(row: dict) -> dict:
    content = row["content"]
    return {
        "id": str(row["id"]),
        "role": row["role"],
        "mode": row["mode"],
        "blocks": content.get("blocks", []),
        "safety_outcome": row["safety_outcome"],
        "created_at": row["created_at"],
    }


class PostgresTutorRepository:
    def __init__(self, database_url: str, *, allow_draft_grounding: bool = False):
        self.database_url = database_url
        self.allow_draft_grounding = allow_draft_grounding

    def _connect(self):
        return psycopg.connect(
            self.database_url,
            prepare_threshold=None,
            row_factory=dict_row,
        )

    def create_session(
        self,
        learner_id: str,
        *,
        practice_session_id: str,
        question_key: str,
        question_revision: int,
        model_policy_version: str,
    ) -> dict:
        with self._connect() as connection:
            source = connection.execute(
                """
                select assigned.id as session_question_id,
                       assigned.status::text as question_status,
                       versions.id as question_version_id,
                       lesson_versions.id as lesson_version_id
                from practice_sessions practice
                join session_questions assigned
                  on assigned.practice_session_id = practice.id
                join math_question_versions versions
                  on versions.id = assigned.question_version_id
                join math_questions questions on questions.id = versions.question_id
                join course_lessons lessons
                  on lessons.lesson_key = practice.scope->>'lesson_key'
                join lesson_versions
                  on lesson_versions.lesson_id = lessons.id and lesson_versions.is_current
                where practice.id = %s and practice.student_id = %s
                  and questions.stable_key = %s and versions.revision = %s
                  and (%s or questions.status = 'published')
                  and (%s or lesson_versions.status = 'published')
                """,
                (
                    practice_session_id,
                    learner_id,
                    question_key,
                    question_revision,
                    self.allow_draft_grounding,
                    self.allow_draft_grounding,
                ),
            ).fetchone()
            if source is None:
                raise TutorError(
                    "tutor_grounding_unavailable",
                    "This question does not yet have published tutor grounding.",
                    409,
                )
            lock = {
                "answer_locked": source["question_status"] == "pending",
                "solution_locked": source["question_status"] != "gave_up",
            }
            row = connection.execute(
                """
                insert into tutor_sessions (
                    student_id, lesson_version_id, session_question_id,
                    answer_lock_state, model_policy_version
                ) values (%s, %s, %s, %s, %s)
                on conflict (student_id, session_question_id) where status = 'active'
                do update set answer_lock_state = excluded.answer_lock_state
                returning *
                """,
                (
                    learner_id,
                    source["lesson_version_id"],
                    source["session_question_id"],
                    Jsonb(lock),
                    model_policy_version,
                ),
            ).fetchone()
            return self._with_messages(connection, row)

    def _with_messages(self, connection, row: dict) -> dict:
        messages = connection.execute(
            """
            select id, role::text as role, mode::text as mode, content,
                   safety_outcome, created_at
            from tutor_messages where tutor_session_id = %s
            order by created_at, id
            """,
            (row["id"],),
        ).fetchall()
        source = connection.execute(
            """
            select practice.id as practice_session_id, questions.stable_key as question_key,
                   versions.revision as question_revision
            from session_questions assigned
            join practice_sessions practice on practice.id=assigned.practice_session_id
            join math_question_versions versions on versions.id=assigned.question_version_id
            join math_questions questions on questions.id=versions.question_id
            where assigned.id=%s
            """,
            (row["session_question_id"],),
        ).fetchone()
        combined = dict(row)
        combined.update(source)
        combined["status"] = str(combined["status"])
        return _session_record(combined, [_message_record(item) for item in messages])

    def get_session(self, learner_id: str, session_id: str) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                "select *, status::text as status from tutor_sessions where id=%s and student_id=%s",
                (session_id, learner_id),
            ).fetchone()
            if row is None:
                raise TutorError("tutor_session_not_found", "The tutor session was not found.", 404)
            return self._with_messages(connection, row)

    def close_session(self, learner_id: str, session_id: str) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                """
                update tutor_sessions set status='closed', closed_at=coalesce(closed_at, now())
                where id=%s and student_id=%s
                returning *, status::text as status
                """,
                (session_id, learner_id),
            ).fetchone()
            if row is None:
                raise TutorError("tutor_session_not_found", "The tutor session was not found.", 404)
            return self._with_messages(connection, row)

    def grounding(self, learner_id: str, session_id: str) -> TutorGrounding:
        with self._connect() as connection:
            row = connection.execute(
                """
                select tutor.id, tutor.status::text as tutor_status,
                       tutor.lesson_version_id, assigned.id as session_question_id,
                       assigned.status::text as question_status,
                       assigned.incorrect_attempts, assigned.highest_hint_stage,
                       versions.id as question_version_id, versions.title,
                       versions.stem_blocks, questions.stable_key, questions.difficulty,
                       lesson_versions.status::text as lesson_status,
                       questions.status::text as content_status
                from tutor_sessions tutor
                join session_questions assigned on assigned.id=tutor.session_question_id
                join math_question_versions versions on versions.id=assigned.question_version_id
                join math_questions questions on questions.id=versions.question_id
                join lesson_versions on lesson_versions.id=tutor.lesson_version_id
                where tutor.id=%s and tutor.student_id=%s
                """,
                (session_id, learner_id),
            ).fetchone()
            if row is None:
                raise TutorError("tutor_session_not_found", "The tutor session was not found.", 404)
            if row["tutor_status"] != "active":
                raise TutorError("tutor_session_closed", "This tutor session is closed.", 409)
            if not self.allow_draft_grounding and (
                row["lesson_status"] != "published"
                or row["content_status"] != "published"
            ):
                raise TutorError(
                    "tutor_grounding_unavailable",
                    "The reviewed tutor grounding is no longer available.",
                    409,
                )
            parts = connection.execute(
                """
                select position, prompt_blocks, response_type::text as response_type
                from math_question_parts where question_version_id=%s order by position
                """,
                (row["question_version_id"],),
            ).fetchall()
            hints = connection.execute(
                """
                select hints.content_blocks
                from math_question_hints hints
                join math_question_parts parts on parts.id=hints.question_part_id
                where parts.question_version_id=%s and hints.stage <= %s
                order by parts.position, hints.stage
                """,
                (row["question_version_id"], row["highest_hint_stage"]),
            ).fetchall()
            sections = connection.execute(
                """
                select section_key, section_type::text as section_type, title, content
                from lesson_sections where lesson_version_id=%s order by position
                """,
                (row["lesson_version_id"],),
            ).fetchall()
            answers = connection.execute(
                """
                select specs.canonical_answer, specs.canonical_latex
                from math_answer_specs specs
                join math_question_parts parts on parts.id=specs.question_part_id
                where parts.question_version_id=%s order by parts.position
                """,
                (row["question_version_id"],),
            ).fetchall()
            solution_rows = []
            if row["question_status"] == "gave_up":
                solution_rows = connection.execute(
                    """
                    select steps.content_blocks
                    from math_solution_steps steps
                    join math_question_parts parts on parts.id=steps.question_part_id
                    where parts.question_version_id=%s
                    order by parts.position, steps.position
                    """,
                    (row["question_version_id"],),
                ).fetchall()
            latest_attempt_row = connection.execute(
                """
                select attempt_number, answers, result, is_correct, marks_awarded
                from attempts
                where student_id=%s and session_question_id=%s
                order by attempt_number desc, submitted_at desc, id desc
                limit 1
                """,
                (learner_id, row["session_question_id"]),
            ).fetchone()
            latest_attempt = _safe_attempt_evidence(latest_attempt_row)
            message_rows = connection.execute(
                """
                select role::text as role, mode::text as mode, content, model_tier
                from tutor_messages where tutor_session_id=%s
                order by created_at desc, id desc limit 8
                """,
                (session_id,),
            ).fetchall()
            premium_turns_this_session = connection.execute(
                """
                select count(*)::integer as turns
                from tutor_messages
                where tutor_session_id=%s and role='assistant' and model_tier='premium'
                """,
                (session_id,),
            ).fetchone()["turns"]
            lock = AnswerLockState(
                answer_locked=row["question_status"] == "pending",
                solution_locked=row["question_status"] != "gave_up",
            )
            connection.execute(
                "update tutor_sessions set answer_lock_state=%s where id=%s",
                (Jsonb(lock.model_dump()), session_id),
            )
            leakage = []
            for answer in answers:
                leakage.append(answer["canonical_answer"])
                if answer["canonical_latex"]:
                    leakage.append(answer["canonical_latex"])
            return TutorGrounding(
                session_id=session_id,
                question_title=row["title"],
                question_difficulty=row["difficulty"],
                question_blocks=(
                    {"kind": "stem", "blocks": row["stem_blocks"]},
                    *(
                        {
                            "kind": "part",
                            "position": part["position"],
                            "blocks": part["prompt_blocks"],
                            "response_type": part["response_type"],
                        }
                        for part in parts
                    ),
                ),
                unlocked_hint_blocks=tuple(item["content_blocks"] for item in hints),
                lesson_sections=tuple(dict(item) for item in sections),
                unlocked_solution_blocks=tuple(
                    item["content_blocks"] for item in solution_rows
                ),
                latest_attempt=latest_attempt,
                recent_messages=tuple(dict(item) for item in reversed(message_rows)),
                answer_lock_state=lock,
                incorrect_attempts=row["incorrect_attempts"],
                premium_turns_this_session=premium_turns_this_session,
                leakage_answers=tuple(leakage),
                grounding_revision_ids=(
                    str(row["lesson_version_id"]),
                    str(row["question_version_id"]),
                ),
            )

    def append_message(
        self,
        session_id: str,
        *,
        role: str,
        mode: TutorMode | None,
        content: dict,
        grounding_revision_ids: tuple[str, ...] = (),
        model_name: str | None = None,
        prompt_version: str | None = None,
        safety_outcome: str = "accepted",
        latency_ms: int | None = None,
        token_usage: dict | None = None,
        provider_name: str | None = None,
        model_tier: str | None = None,
        route_decision_id: str | None = None,
    ) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                """
                insert into tutor_messages (
                    tutor_session_id, student_id, role, mode, content, grounding_revision_ids,
                    model_name, prompt_version, safety_outcome, latency_ms, token_usage,
                    provider_name, model_tier, route_decision_id
                ) select %s, student_id, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                  from tutor_sessions where id=%s
                returning id, role::text as role, mode::text as mode, content,
                          safety_outcome, created_at
                """,
                (
                    session_id,
                    role,
                    mode,
                    Jsonb(content),
                    list(grounding_revision_ids),
                    model_name,
                    prompt_version,
                    safety_outcome,
                    latency_ms,
                    Jsonb(token_usage or {}),
                    provider_name,
                    model_tier,
                    route_decision_id,
                    session_id,
                ),
            ).fetchone()
            return _message_record(row)

    def reserve(
        self,
        learner_id: str,
        session_id: str,
        limits: TutorLimits,
        *,
        request_id: str,
        quote: UsageReservationQuote | None = None,
        routing: TutorRoutePlan | None = None,
    ) -> UsageReservation:
        now = datetime.now(UTC)
        usage_date = now.date()
        usage_month = usage_date.replace(day=1)
        reservation_id = str(uuid4())
        selected_quote = quote or UsageReservationQuote(
            max_input_tokens=limits.max_input_tokens,
            max_output_tokens=limits.max_output_tokens,
            max_cost_micros_sgd=limits.max_turn_cost_micros_sgd,
        )
        execution = routing.execution if routing is not None else None
        if execution is not None and (
            quote is None
            or selected_quote.max_output_tokens != execution.max_output_tokens
            or selected_quote.max_cost_micros_sgd
            != execution.maximum_cost_micros_sgd(selected_quote.max_input_tokens)
        ):
            raise TutorError(
                "tutor_reservation_invalid",
                "Tutor routing and usage reservation boundaries do not match.",
                503,
            )
        if (
            selected_quote.max_input_tokens <= 0
            or selected_quote.max_output_tokens <= 0
            or selected_quote.max_cost_micros_sgd < 0
            or selected_quote.max_input_tokens > limits.max_input_tokens
            or selected_quote.max_output_tokens > limits.max_output_tokens
            or selected_quote.max_cost_micros_sgd > limits.max_turn_cost_micros_sgd
        ):
            raise TutorError(
                "tutor_reservation_invalid",
                "Tutor usage could not be reserved within the configured boundary.",
                503,
            )
        route_decision_id = str(uuid4()) if routing is not None else None
        with self._connect() as connection:
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"tutor:{learner_id}",),
            )
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"tutor:academy:{usage_month.isoformat()}",),
            )
            active = connection.execute(
                "select 1 from tutor_usage_reservations where student_id=%s and status='reserved'",
                (learner_id,),
            ).fetchone()
            if active:
                raise TutorError(
                    "tutor_generation_in_progress",
                    "Wait for the current tutor response before sending another message.",
                    409,
                )
            connection.execute(
                """
                insert into tutor_usage_daily (student_id, usage_date)
                values (%s, %s) on conflict do nothing
                """,
                (learner_id, usage_date),
            )
            daily = connection.execute(
                "select * from tutor_usage_daily where student_id=%s and usage_date=%s for update",
                (learner_id, usage_date),
            ).fetchone()
            connection.execute(
                """
                insert into tutor_usage_monthly (student_id, usage_month)
                values (%s, %s) on conflict do nothing
                """,
                (learner_id, usage_month),
            )
            monthly = connection.execute(
                "select * from tutor_usage_monthly where student_id=%s and usage_month=%s for update",
                (learner_id, usage_month),
            ).fetchone()
            academy_cost = connection.execute(
                """
                select coalesce(sum(actual_cost_micros_sgd + reserved_cost_micros_sgd), 0) as cost
                from tutor_usage_monthly where usage_month=%s
                """,
                (usage_month,),
            ).fetchone()["cost"]
            if daily["actual_requests"] + daily["reserved_requests"] + 1 > limits.daily_messages:
                self._quota_error(usage_date, "daily_messages")
            if (
                daily["actual_tokens"]
                + daily["reserved_tokens"]
                + selected_quote.max_tokens
                > limits.daily_tokens
            ):
                self._quota_error(usage_date, "daily_tokens")
            if (
                monthly["actual_cost_micros_sgd"]
                + monthly["reserved_cost_micros_sgd"]
                + selected_quote.max_cost_micros_sgd
                > limits.monthly_cost_micros_sgd
            ):
                self._quota_error(usage_date, "monthly_cost")
            if (
                academy_cost + selected_quote.max_cost_micros_sgd
                > limits.academy_monthly_cost_micros_sgd
            ):
                self._quota_error(usage_date, "academy_circuit_breaker")
            connection.execute(
                """
                insert into tutor_usage_reservations (
                    id, tutor_session_id, student_id, usage_date, usage_month,
                    reserved_tokens, reserved_cost_micros_sgd
                ) values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    reservation_id,
                    session_id,
                    learner_id,
                    usage_date,
                    usage_month,
                    selected_quote.max_tokens,
                    selected_quote.max_cost_micros_sgd,
                ),
            )
            if routing is not None:
                recommendation = routing.recommendation
                connection.execute(
                    """
                    insert into tutor_route_decisions (
                        id, reservation_id, tutor_session_id, student_id, request_id,
                        policy_version, tutor_mode, question_difficulty, route_score,
                        selected_tier, provider_name, model_name, reason_codes,
                        estimated_input_tokens, max_output_tokens, reserved_cost_micros_sgd,
                        routing_mode, recommended_tier, recommended_provider_name,
                        recommended_model_name, recommended_max_output_tokens,
                        recommended_input_cost_per_million_micros_sgd,
                        recommended_output_cost_per_million_micros_sgd
                    ) values (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        route_decision_id,
                        reservation_id,
                        session_id,
                        learner_id,
                        request_id,
                        recommendation.policy_version,
                        recommendation.mode,
                        recommendation.question_difficulty,
                        recommendation.score,
                        execution.tier,
                        execution.provider_name,
                        execution.model_name,
                        list(recommendation.reason_codes),
                        selected_quote.max_input_tokens,
                        selected_quote.max_output_tokens,
                        selected_quote.max_cost_micros_sgd,
                        routing.routing_mode,
                        recommendation.tier,
                        recommendation.provider_name,
                        recommendation.model_name,
                        recommendation.max_output_tokens,
                        recommendation.input_cost_per_million_micros_sgd,
                        recommendation.output_cost_per_million_micros_sgd,
                    ),
                )
            connection.execute(
                """
                update tutor_usage_daily
                set reserved_requests=reserved_requests+1,
                    reserved_tokens=reserved_tokens+%s, updated_at=now()
                where student_id=%s and usage_date=%s
                """,
                (selected_quote.max_tokens, learner_id, usage_date),
            )
            connection.execute(
                """
                update tutor_usage_monthly
                set reserved_cost_micros_sgd=reserved_cost_micros_sgd+%s, updated_at=now()
                where student_id=%s and usage_month=%s
                """,
                (selected_quote.max_cost_micros_sgd, learner_id, usage_month),
            )
            self._event(
                connection,
                reservation_id,
                learner_id,
                session_id,
                "reserved",
                request_id,
                {
                    "tokens": selected_quote.max_tokens,
                    "cost_micros_sgd": selected_quote.max_cost_micros_sgd,
                    "route_decision_id": route_decision_id,
                    "routing_mode": routing.routing_mode if routing is not None else None,
                    "model_tier": execution.tier if execution is not None else None,
                    "provider_name": (
                        execution.provider_name if execution is not None else None
                    ),
                    "model_name": execution.model_name if execution is not None else None,
                    "recommended_model_tier": (
                        routing.recommendation.tier if routing is not None else None
                    ),
                },
            )
        return UsageReservation(
            reservation_id,
            session_id,
            learner_id,
            usage_date,
            usage_month,
            route_decision_id,
        )

    @staticmethod
    def _quota_error(usage_date: date, boundary: str) -> None:
        raise TutorError(
            "tutor_quota_exceeded",
            "The tutor allowance is currently exhausted. Lessons and authored help remain available.",
            429,
            {"boundary": boundary, "resets_at": _next_utc_day(usage_date).isoformat()},
        )

    @staticmethod
    def _event(connection, reservation_id, learner_id, session_id, event_type, request_id, usage):
        connection.execute(
            """
            insert into tutor_usage_events (
                reservation_id, student_id, tutor_session_id, event_type,
                request_id, usage
            ) values (%s, %s, %s, %s, %s, %s)
            """,
            (reservation_id, learner_id, session_id, event_type, request_id, Jsonb(usage)),
        )

    def reconcile(
        self,
        reservation: UsageReservation,
        actual: UsageActual,
        limits: TutorLimits,
        *,
        request_id: str,
    ) -> QuotaSnapshot:
        if actual.total_tokens > limits.max_turn_tokens or actual.cost_micros_sgd > limits.max_turn_cost_micros_sgd:
            self.release(reservation, request_id=request_id, reason="provider_usage_exceeded_reservation")
            raise TutorError(
                "tutor_provider_usage_invalid",
                "The tutor provider reported usage outside the reserved boundary.",
                503,
            )
        with self._connect() as connection:
            reserved = connection.execute(
                "select reserved_tokens, reserved_cost_micros_sgd from tutor_usage_reservations where id=%s",
                (reservation.reservation_id,),
            ).fetchone()
        if reserved is not None and (
            actual.total_tokens > reserved["reserved_tokens"]
            or actual.cost_micros_sgd > reserved["reserved_cost_micros_sgd"]
        ):
            self.release(
                reservation,
                request_id=request_id,
                reason="provider_usage_exceeded_route_reservation",
            )
            raise TutorError(
                "tutor_provider_usage_invalid",
                "The tutor provider reported usage outside the route reservation.",
                503,
            )
        with self._connect() as connection:
            row = connection.execute(
                "select * from tutor_usage_reservations where id=%s for update",
                (reservation.reservation_id,),
            ).fetchone()
            if row is None or row["status"] != "reserved":
                raise TutorError("tutor_reservation_invalid", "Tutor usage could not be reconciled.", 503)
            connection.execute(
                """
                update tutor_usage_daily
                set reserved_requests=reserved_requests-1,
                    reserved_tokens=reserved_tokens-%s,
                    actual_requests=actual_requests+1,
                    actual_input_tokens=actual_input_tokens+%s,
                    actual_output_tokens=actual_output_tokens+%s,
                    actual_tokens=actual_tokens+%s, updated_at=now()
                where student_id=%s and usage_date=%s
                """,
                (
                    row["reserved_tokens"], actual.input_tokens, actual.output_tokens,
                    actual.total_tokens, reservation.learner_id, reservation.usage_date,
                ),
            )
            connection.execute(
                """
                update tutor_usage_monthly
                set reserved_cost_micros_sgd=reserved_cost_micros_sgd-%s,
                    actual_cost_micros_sgd=actual_cost_micros_sgd+%s, updated_at=now()
                where student_id=%s and usage_month=%s
                """,
                (
                    row["reserved_cost_micros_sgd"], actual.cost_micros_sgd,
                    reservation.learner_id, reservation.usage_month,
                ),
            )
            connection.execute(
                """
                update tutor_usage_reservations
                set status='reconciled', actual_input_tokens=%s, actual_output_tokens=%s,
                    actual_cost_micros_sgd=%s, completed_at=now()
                where id=%s
                """,
                (actual.input_tokens, actual.output_tokens, actual.cost_micros_sgd, reservation.reservation_id),
            )
            self._event(
                connection, reservation.reservation_id, reservation.learner_id,
                reservation.session_id, "reconciled", request_id,
                {"input_tokens": actual.input_tokens, "output_tokens": actual.output_tokens,
                 "cost_micros_sgd": actual.cost_micros_sgd},
            )
            return self._quota_snapshot(connection, reservation, limits)

    def release(
        self,
        reservation: UsageReservation,
        *,
        request_id: str,
        reason: str,
    ) -> None:
        with self._connect() as connection:
            row = connection.execute(
                "select * from tutor_usage_reservations where id=%s for update",
                (reservation.reservation_id,),
            ).fetchone()
            if row is None or row["status"] != "reserved":
                return
            connection.execute(
                """
                update tutor_usage_daily
                set reserved_requests=reserved_requests-1,
                    reserved_tokens=reserved_tokens-%s, failed_requests=failed_requests+1,
                    updated_at=now()
                where student_id=%s and usage_date=%s
                """,
                (row["reserved_tokens"], reservation.learner_id, reservation.usage_date),
            )
            connection.execute(
                """
                update tutor_usage_monthly
                set reserved_cost_micros_sgd=reserved_cost_micros_sgd-%s, updated_at=now()
                where student_id=%s and usage_month=%s
                """,
                (row["reserved_cost_micros_sgd"], reservation.learner_id, reservation.usage_month),
            )
            connection.execute(
                "update tutor_usage_reservations set status='released', completed_at=now() where id=%s",
                (reservation.reservation_id,),
            )
            self._event(
                connection, reservation.reservation_id, reservation.learner_id,
                reservation.session_id, "released", request_id, {"reason": reason[:120]},
            )

    @staticmethod
    def _quota_snapshot(connection, reservation: UsageReservation, limits: TutorLimits) -> QuotaSnapshot:
        daily = connection.execute(
            "select * from tutor_usage_daily where student_id=%s and usage_date=%s",
            (reservation.learner_id, reservation.usage_date),
        ).fetchone()
        monthly = connection.execute(
            "select * from tutor_usage_monthly where student_id=%s and usage_month=%s",
            (reservation.learner_id, reservation.usage_month),
        ).fetchone()
        return QuotaSnapshot(
            daily_messages_remaining=max(0, limits.daily_messages - daily["actual_requests"] - daily["reserved_requests"]),
            daily_tokens_remaining=max(0, limits.daily_tokens - daily["actual_tokens"] - daily["reserved_tokens"]),
            monthly_cost_remaining_micros_sgd=max(0, limits.monthly_cost_micros_sgd - monthly["actual_cost_micros_sgd"] - monthly["reserved_cost_micros_sgd"]),
            resets_at=_next_utc_day(reservation.usage_date),
        )

    def admin_usage(self, usage_month: date) -> dict:
        next_month = (
            usage_month.replace(year=usage_month.year + 1, month=1)
            if usage_month.month == 12
            else usage_month.replace(month=usage_month.month + 1)
        )
        with self._connect() as connection:
            row = connection.execute(
                """
                with daily as (
                    select count(distinct student_id)::integer as learners,
                           coalesce(sum(actual_requests), 0)::bigint as actual_requests,
                           coalesce(sum(failed_requests), 0)::bigint as failed_requests,
                           coalesce(sum(actual_input_tokens), 0)::bigint as input_tokens,
                           coalesce(sum(actual_output_tokens), 0)::bigint as output_tokens
                    from tutor_usage_daily
                    where usage_date >= %(month)s and usage_date < %(next_month)s
                ), monthly as (
                    select count(distinct student_id)::integer as learners,
                           coalesce(sum(actual_cost_micros_sgd), 0)::bigint as actual_cost,
                           coalesce(sum(reserved_cost_micros_sgd), 0)::bigint as reserved_cost
                    from tutor_usage_monthly where usage_month = %(month)s
                ), active as (
                    select count(*)::integer as reservations
                    from tutor_usage_reservations
                    where usage_month = %(month)s and status = 'reserved'
                ), routes as (
                    select count(*)::integer as decisions,
                           count(*) filter (
                               where decisions.routing_mode = 'shadow'
                           )::integer as shadow_decisions,
                           count(*) filter (
                               where decisions.routing_mode = 'shadow'
                                 and decisions.selected_tier = 'premium'
                           )::integer as shadow_premium_executions,
                           count(*) filter (
                               where decisions.recommended_tier = 'premium'
                           )::integer as recommended_premium,
                           count(*) filter (
                               where decisions.selected_tier = 'premium'
                           )::integer as executed_premium,
                           coalesce(sum(
                               case when reservations.status = 'reconciled' then
                                   (
                                       reservations.actual_input_tokens
                                       * decisions.recommended_input_cost_per_million_micros_sgd
                                       + 999999
                                   ) / 1000000
                                   +
                                   (
                                       reservations.actual_output_tokens
                                       * decisions.recommended_output_cost_per_million_micros_sgd
                                       + 999999
                                   ) / 1000000
                               else 0 end
                           ), 0)::bigint as projected_recommended_cost
                    from tutor_route_decisions decisions
                    join tutor_usage_reservations reservations
                      on reservations.id = decisions.reservation_id
                    where decisions.created_at >= %(month)s
                      and decisions.created_at < %(next_month)s
                )
                select greatest(daily.learners, monthly.learners) as learners,
                       daily.actual_requests, daily.failed_requests,
                       daily.input_tokens, daily.output_tokens,
                       monthly.actual_cost, monthly.reserved_cost,
                       active.reservations, routes.decisions,
                       routes.shadow_decisions, routes.shadow_premium_executions,
                       routes.recommended_premium,
                       routes.executed_premium, routes.projected_recommended_cost
                from daily cross join monthly cross join active cross join routes
                """,
                {"month": usage_month, "next_month": next_month},
            ).fetchone()
        return {
            "usage_month": usage_month.strftime("%Y-%m"),
            "learners": row["learners"],
            "actual_requests": row["actual_requests"],
            "failed_requests": row["failed_requests"],
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "actual_cost_micros_sgd": row["actual_cost"],
            "reserved_cost_micros_sgd": row["reserved_cost"],
            "active_reservations": row["reservations"],
            "route_decisions": row["decisions"],
            "shadow_route_decisions": row["shadow_decisions"],
            "shadow_premium_executions": row["shadow_premium_executions"],
            "recommended_premium_routes": row["recommended_premium"],
            "executed_premium_routes": row["executed_premium"],
            "projected_recommended_cost_micros_sgd": row[
                "projected_recommended_cost"
            ],
        }

    def admin_route_decisions(
        self,
        usage_month: date,
        *,
        cursor: str | None = None,
        limit: int = 50,
        routing_mode: str | None = None,
        recommended_tier: str | None = None,
        executed_tier: str | None = None,
        tutor_mode: str | None = None,
        question_difficulty: int | None = None,
        reason_code: str | None = None,
        reservation_status: str | None = None,
    ) -> dict:
        if not 1 <= limit <= 100:
            raise TutorError(
                "invalid_tutor_routing_limit",
                "Tutor routing evidence pages must contain 1 to 100 decisions.",
                422,
            )
        next_month = (
            usage_month.replace(year=usage_month.year + 1, month=1)
            if usage_month.month == 12
            else usage_month.replace(month=usage_month.month + 1)
        )
        conditions = [
            "decisions.created_at >= %(month)s",
            "decisions.created_at < %(next_month)s",
        ]
        parameters: dict[str, object] = {
            "month": usage_month,
            "next_month": next_month,
            "fetch_limit": limit + 1,
        }
        filters = {
            "routing_mode": ("decisions.routing_mode", routing_mode),
            "recommended_tier": (
                "decisions.recommended_tier",
                recommended_tier,
            ),
            "executed_tier": ("decisions.selected_tier", executed_tier),
            "tutor_mode": ("decisions.tutor_mode::text", tutor_mode),
            "question_difficulty": (
                "decisions.question_difficulty",
                question_difficulty,
            ),
            "reservation_status": (
                "reservations.status::text",
                reservation_status,
            ),
        }
        for name, (column, value) in filters.items():
            if value is not None:
                conditions.append(f"{column} = %({name})s")
                parameters[name] = value
        if reason_code is not None:
            conditions.append("%(reason_code)s = any(decisions.reason_codes)")
            parameters["reason_code"] = reason_code
        if cursor is not None:
            decoded = decode_tutor_route_cursor(cursor)
            conditions.append(
                "(decisions.created_at, decisions.id) "
                "< (%(cursor_created_at)s, %(cursor_decision_id)s::uuid)"
            )
            parameters["cursor_created_at"] = decoded.created_at
            parameters["cursor_decision_id"] = decoded.decision_id

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                select decisions.id as decision_id, decisions.created_at,
                       decisions.policy_version,
                       decisions.routing_mode,
                       decisions.tutor_mode::text as tutor_mode,
                       decisions.question_difficulty,
                       decisions.route_score,
                       decisions.reason_codes,
                       decisions.recommended_tier,
                       decisions.recommended_provider_name as recommended_provider,
                       decisions.recommended_model_name as recommended_model,
                       decisions.selected_tier as executed_tier,
                       decisions.provider_name as executed_provider,
                       decisions.model_name as executed_model,
                       reservations.status::text as reservation_status,
                       case when reservations.status = 'reconciled'
                            then reservations.actual_input_tokens end
                            as actual_input_tokens,
                       case when reservations.status = 'reconciled'
                            then reservations.actual_output_tokens end
                            as actual_output_tokens,
                       case when reservations.status = 'reconciled'
                            then reservations.actual_cost_micros_sgd end
                            as actual_cost_micros_sgd,
                       case when reservations.status = 'reconciled' then
                           (
                               reservations.actual_input_tokens
                               * decisions.recommended_input_cost_per_million_micros_sgd
                               + 999999
                           ) / 1000000
                           +
                           (
                               reservations.actual_output_tokens
                               * decisions.recommended_output_cost_per_million_micros_sgd
                               + 999999
                           ) / 1000000
                       end::bigint as projected_recommended_cost_micros_sgd,
                       messages.latency_ms,
                       messages.safety_outcome::text as safety_outcome
                from tutor_route_decisions decisions
                join tutor_usage_reservations reservations
                  on reservations.id = decisions.reservation_id
                left join tutor_messages messages
                  on messages.route_decision_id = decisions.id
                where {" and ".join(conditions)}
                order by decisions.created_at desc, decisions.id desc
                limit %(fetch_limit)s
                """,
                parameters,
            ).fetchall()

        page = rows[:limit]
        next_cursor = None
        if len(rows) > limit and page:
            next_cursor = encode_tutor_route_cursor(
                page[-1]["created_at"],
                str(page[-1]["decision_id"]),
            )
        return {
            "usage_month": usage_month.strftime("%Y-%m"),
            "items": [dict(row) for row in page],
            "next_cursor": next_cursor,
        }


class InMemoryTutorRepository:
    """Deterministic repository for service tests; never selected in hosted environments."""

    def __init__(self, grounding: TutorGrounding):
        self.grounding_value = grounding
        self.sessions: dict[str, dict] = {}
        self.owners: dict[str, str] = {}
        self.messages: dict[str, list[dict]] = {}
        self.reservations: dict[str, UsageReservation] = {}
        self.actual_requests = 0
        self.actual_tokens = 0
        self.actual_cost = 0
        self.reserved = False
        self.last_routing: TutorRouteDecision | None = None
        self.last_route_plan: TutorRoutePlan | None = None
        self.last_quote: UsageReservationQuote | None = None
        self.route_plans: dict[str, TutorRoutePlan] = {}
        self.route_created_at: dict[str, datetime] = {}
        self.route_status: dict[str, str] = {}
        self.route_actuals: dict[str, UsageActual] = {}
        self.projected_recommended_cost = 0
        self._lock = threading.Lock()

    def create_session(self, learner_id: str, *, practice_session_id: str, question_key: str, question_revision: int, model_policy_version: str) -> dict:
        session_id = self.grounding_value.session_id
        now = datetime.now(UTC)
        self.sessions[session_id] = {
            "session_id": session_id,
            "practice_session_id": practice_session_id, "question_key": question_key,
            "question_revision": question_revision, "status": "active",
            "answer_lock_state": self.grounding_value.answer_lock_state.model_dump(),
            "model_policy_version": model_policy_version, "messages": [],
            "created_at": now, "closed_at": None,
        }
        self.owners[session_id] = learner_id
        self.messages[session_id] = []
        return dict(self.sessions[session_id])

    def get_session(self, learner_id: str, session_id: str) -> dict:
        row = self.sessions.get(session_id)
        if row is None or self.owners.get(session_id) != learner_id:
            raise TutorError("tutor_session_not_found", "The tutor session was not found.", 404)
        return {**row, "messages": list(self.messages[session_id])}

    def close_session(self, learner_id: str, session_id: str) -> dict:
        self.get_session(learner_id, session_id)
        self.sessions[session_id]["status"] = "closed"
        self.sessions[session_id]["closed_at"] = datetime.now(UTC)
        return self.get_session(learner_id, session_id)

    def grounding(self, learner_id: str, session_id: str) -> TutorGrounding:
        row = self.get_session(learner_id, session_id)
        if row["status"] != "active":
            raise TutorError("tutor_session_closed", "This tutor session is closed.", 409)
        stored_messages = tuple(
            {
                "role": item["role"],
                "mode": item["mode"],
                "content": {"blocks": item["blocks"]},
                "model_tier": item["model_tier"],
            }
            for item in self.messages[session_id]
        )
        recent_messages = (self.grounding_value.recent_messages + stored_messages)[-8:]
        premium_turns = sum(
            1
            for item in self.grounding_value.recent_messages + stored_messages
            if item.get("role") == "assistant" and item.get("model_tier") == "premium"
        )
        return replace(
            self.grounding_value,
            recent_messages=recent_messages,
            premium_turns_this_session=premium_turns,
        )

    def append_message(self, session_id: str, *, role: str, mode: TutorMode | None, content: dict, grounding_revision_ids: tuple[str, ...] = (), model_name: str | None = None, prompt_version: str | None = None, safety_outcome: str = "accepted", latency_ms: int | None = None, token_usage: dict | None = None, provider_name: str | None = None, model_tier: str | None = None, route_decision_id: str | None = None) -> dict:
        del grounding_revision_ids, prompt_version, token_usage
        row = {"id": str(uuid4()), "role": role, "mode": mode,
               "blocks": content.get("blocks", []), "safety_outcome": safety_outcome,
               "provider_name": provider_name, "model_name": model_name,
               "model_tier": model_tier, "route_decision_id": route_decision_id,
               "latency_ms": latency_ms, "created_at": datetime.now(UTC)}
        self.messages[session_id].append(row)
        return {
            key: row[key]
            for key in ("id", "role", "mode", "blocks", "safety_outcome", "created_at")
        }

    def reserve(self, learner_id: str, session_id: str, limits: TutorLimits, *, request_id: str, quote: UsageReservationQuote | None = None, routing: TutorRoutePlan | None = None) -> UsageReservation:
        del request_id
        selected_quote = quote or UsageReservationQuote(
            limits.max_input_tokens,
            limits.max_output_tokens,
            limits.max_turn_cost_micros_sgd,
        )
        execution = routing.execution if routing is not None else None
        if execution is not None and (
            quote is None
            or selected_quote.max_output_tokens != execution.max_output_tokens
            or selected_quote.max_cost_micros_sgd
            != execution.maximum_cost_micros_sgd(selected_quote.max_input_tokens)
        ):
            raise TutorError(
                "tutor_reservation_invalid",
                "Tutor routing and usage reservation boundaries do not match.",
                503,
            )
        with self._lock:
            if self.reserved:
                raise TutorError("tutor_generation_in_progress", "Wait for the current tutor response before sending another message.", 409)
            today = datetime.now(UTC).date()
            if self.actual_requests + 1 > limits.daily_messages or self.actual_tokens + selected_quote.max_tokens > limits.daily_tokens or self.actual_cost + selected_quote.max_cost_micros_sgd > limits.monthly_cost_micros_sgd:
                PostgresTutorRepository._quota_error(today, "test_boundary")
            self.reserved = True
            route_decision_id = str(uuid4()) if routing is not None else None
            item = UsageReservation(
                str(uuid4()), session_id, learner_id, today, today.replace(day=1), route_decision_id
            )
            self.reservations[item.reservation_id] = item
            self.last_quote = selected_quote
            self.last_route_plan = routing
            self.last_routing = execution
            if routing is not None:
                self.route_plans[item.reservation_id] = routing
                self.route_created_at[item.reservation_id] = datetime.now(UTC)
                self.route_status[item.reservation_id] = "reserved"
            return item

    def reconcile(self, reservation: UsageReservation, actual: UsageActual, limits: TutorLimits, *, request_id: str) -> QuotaSnapshot:
        del request_id
        with self._lock:
            self.reserved = False
            self.actual_requests += 1
            self.actual_tokens += actual.total_tokens
            self.actual_cost += actual.cost_micros_sgd
            if plan := self.route_plans.get(reservation.reservation_id):
                self.route_status[reservation.reservation_id] = "reconciled"
                self.route_actuals[reservation.reservation_id] = actual
                self.projected_recommended_cost += _priced_tokens(
                    actual.input_tokens,
                    plan.recommendation.input_cost_per_million_micros_sgd,
                ) + _priced_tokens(
                    actual.output_tokens,
                    plan.recommendation.output_cost_per_million_micros_sgd,
                )
        return QuotaSnapshot(
            max(0, limits.daily_messages-self.actual_requests),
            max(0, limits.daily_tokens-self.actual_tokens),
            max(0, limits.monthly_cost_micros_sgd-self.actual_cost),
            _next_utc_day(reservation.usage_date),
        )

    def release(self, reservation: UsageReservation, *, request_id: str, reason: str) -> None:
        del request_id, reason
        with self._lock:
            self.reserved = False
            if reservation.reservation_id in self.route_plans:
                self.route_status[reservation.reservation_id] = "released"

    def admin_usage(self, usage_month: date) -> dict:
        return {
            "usage_month": usage_month.strftime("%Y-%m"),
            "learners": 1 if self.actual_requests else 0,
            "actual_requests": self.actual_requests,
            "failed_requests": 0,
            "input_tokens": self.actual_tokens,
            "output_tokens": 0,
            "actual_cost_micros_sgd": self.actual_cost,
            "reserved_cost_micros_sgd": 0,
            "active_reservations": int(self.reserved),
            "route_decisions": len(self.route_plans),
            "shadow_route_decisions": sum(
                plan.routing_mode == "shadow" for plan in self.route_plans.values()
            ),
            "shadow_premium_executions": sum(
                plan.routing_mode == "shadow" and plan.execution.tier == "premium"
                for plan in self.route_plans.values()
            ),
            "recommended_premium_routes": sum(
                plan.recommendation.tier == "premium"
                for plan in self.route_plans.values()
            ),
            "executed_premium_routes": sum(
                plan.execution.tier == "premium" for plan in self.route_plans.values()
            ),
            "projected_recommended_cost_micros_sgd": (
                self.projected_recommended_cost
            ),
        }

    def admin_route_decisions(
        self,
        usage_month: date,
        *,
        cursor: str | None = None,
        limit: int = 50,
        routing_mode: str | None = None,
        recommended_tier: str | None = None,
        executed_tier: str | None = None,
        tutor_mode: str | None = None,
        question_difficulty: int | None = None,
        reason_code: str | None = None,
        reservation_status: str | None = None,
    ) -> dict:
        if not 1 <= limit <= 100:
            raise TutorError(
                "invalid_tutor_routing_limit",
                "Tutor routing evidence pages must contain 1 to 100 decisions.",
                422,
            )
        decoded = decode_tutor_route_cursor(cursor) if cursor is not None else None
        next_month = (
            usage_month.replace(year=usage_month.year + 1, month=1)
            if usage_month.month == 12
            else usage_month.replace(month=usage_month.month + 1)
        )
        records = []
        for reservation_id, plan in self.route_plans.items():
            reservation = self.reservations[reservation_id]
            decision_id = reservation.route_decision_id
            created_at = self.route_created_at[reservation_id]
            status = self.route_status[reservation_id]
            if decision_id is None or not (
                usage_month <= created_at.date() < next_month
            ):
                continue
            if decoded is not None and (created_at, decision_id) >= (
                decoded.created_at,
                decoded.decision_id,
            ):
                continue
            recommendation = plan.recommendation
            execution = plan.execution
            if routing_mode is not None and plan.routing_mode != routing_mode:
                continue
            if (
                recommended_tier is not None
                and recommendation.tier != recommended_tier
            ):
                continue
            if executed_tier is not None and execution.tier != executed_tier:
                continue
            if tutor_mode is not None and recommendation.mode != tutor_mode:
                continue
            if (
                question_difficulty is not None
                and recommendation.question_difficulty != question_difficulty
            ):
                continue
            if reason_code is not None and reason_code not in recommendation.reason_codes:
                continue
            if reservation_status is not None and status != reservation_status:
                continue
            actual = self.route_actuals.get(reservation_id)
            assistant = next(
                (
                    item
                    for item in self.messages.get(reservation.session_id, ())
                    if item.get("route_decision_id") == decision_id
                ),
                None,
            )
            projected_cost = (
                _priced_tokens(
                    actual.input_tokens,
                    recommendation.input_cost_per_million_micros_sgd,
                )
                + _priced_tokens(
                    actual.output_tokens,
                    recommendation.output_cost_per_million_micros_sgd,
                )
                if actual is not None
                else None
            )
            records.append(
                {
                    "decision_id": decision_id,
                    "created_at": created_at,
                    "policy_version": recommendation.policy_version,
                    "routing_mode": plan.routing_mode,
                    "tutor_mode": recommendation.mode,
                    "question_difficulty": recommendation.question_difficulty,
                    "route_score": recommendation.score,
                    "reason_codes": list(recommendation.reason_codes),
                    "recommended_tier": recommendation.tier,
                    "recommended_provider": recommendation.provider_name,
                    "recommended_model": recommendation.model_name,
                    "executed_tier": execution.tier,
                    "executed_provider": execution.provider_name,
                    "executed_model": execution.model_name,
                    "reservation_status": status,
                    "actual_input_tokens": (
                        actual.input_tokens if actual is not None else None
                    ),
                    "actual_output_tokens": (
                        actual.output_tokens if actual is not None else None
                    ),
                    "actual_cost_micros_sgd": (
                        actual.cost_micros_sgd if actual is not None else None
                    ),
                    "projected_recommended_cost_micros_sgd": projected_cost,
                    "latency_ms": assistant.get("latency_ms") if assistant else None,
                    "safety_outcome": (
                        assistant.get("safety_outcome") if assistant else None
                    ),
                }
            )

        records.sort(
            key=lambda item: (item["created_at"], item["decision_id"]),
            reverse=True,
        )
        page = records[:limit]
        next_cursor = None
        if len(records) > limit and page:
            next_cursor = encode_tutor_route_cursor(
                page[-1]["created_at"], page[-1]["decision_id"]
            )
        return {
            "usage_month": usage_month.strftime("%Y-%m"),
            "items": page,
            "next_cursor": next_cursor,
        }
