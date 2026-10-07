"""Durable tutor sessions and atomic usage accounting."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Protocol
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .tutor_contracts import AnswerLockState, TutorMode


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
    question_blocks: tuple[dict, ...]
    unlocked_hint_blocks: tuple[dict, ...]
    lesson_sections: tuple[dict, ...]
    unlocked_solution_blocks: tuple[dict, ...]
    latest_attempt: dict | None
    recent_messages: tuple[dict, ...]
    answer_lock_state: AnswerLockState
    incorrect_attempts: int
    leakage_answers: tuple[str, ...]
    grounding_revision_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UsageReservation:
    reservation_id: str
    session_id: str
    learner_id: str
    usage_date: date
    usage_month: date


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
    ) -> dict: ...

    def reserve(
        self,
        learner_id: str,
        session_id: str,
        limits: TutorLimits,
        *,
        request_id: str,
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


def _next_utc_day(day: date) -> datetime:
    return datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=UTC)


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
    def __init__(self, database_url: str):
        self.database_url = database_url

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
                  and questions.status = 'published'
                  and lesson_versions.status = 'published'
                """,
                (practice_session_id, learner_id, question_key, question_revision),
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
                       versions.stem_blocks, questions.stable_key,
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
            if row["lesson_status"] != "published" or row["content_status"] != "published":
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
                select role::text as role, mode::text as mode, content
                from tutor_messages where tutor_session_id=%s
                order by created_at desc, id desc limit 8
                """,
                (session_id,),
            ).fetchall()
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
    ) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                """
                insert into tutor_messages (
                    tutor_session_id, student_id, role, mode, content, grounding_revision_ids,
                    model_name, prompt_version, safety_outcome, latency_ms, token_usage
                ) select %s, student_id, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
    ) -> UsageReservation:
        now = datetime.now(UTC)
        usage_date = now.date()
        usage_month = usage_date.replace(day=1)
        reservation_id = str(uuid4())
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
            if daily["actual_tokens"] + daily["reserved_tokens"] + limits.max_turn_tokens > limits.daily_tokens:
                self._quota_error(usage_date, "daily_tokens")
            if monthly["actual_cost_micros_sgd"] + monthly["reserved_cost_micros_sgd"] + limits.max_turn_cost_micros_sgd > limits.monthly_cost_micros_sgd:
                self._quota_error(usage_date, "monthly_cost")
            if academy_cost + limits.max_turn_cost_micros_sgd > limits.academy_monthly_cost_micros_sgd:
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
                    limits.max_turn_tokens,
                    limits.max_turn_cost_micros_sgd,
                ),
            )
            connection.execute(
                """
                update tutor_usage_daily
                set reserved_requests=reserved_requests+1,
                    reserved_tokens=reserved_tokens+%s, updated_at=now()
                where student_id=%s and usage_date=%s
                """,
                (limits.max_turn_tokens, learner_id, usage_date),
            )
            connection.execute(
                """
                update tutor_usage_monthly
                set reserved_cost_micros_sgd=reserved_cost_micros_sgd+%s, updated_at=now()
                where student_id=%s and usage_month=%s
                """,
                (limits.max_turn_cost_micros_sgd, learner_id, usage_month),
            )
            self._event(
                connection,
                reservation_id,
                learner_id,
                session_id,
                "reserved",
                request_id,
                {"tokens": limits.max_turn_tokens, "cost_micros_sgd": limits.max_turn_cost_micros_sgd},
            )
        return UsageReservation(reservation_id, session_id, learner_id, usage_date, usage_month)

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
                )
                select greatest(daily.learners, monthly.learners) as learners,
                       daily.actual_requests, daily.failed_requests,
                       daily.input_tokens, daily.output_tokens,
                       monthly.actual_cost, monthly.reserved_cost,
                       active.reservations
                from daily cross join monthly cross join active
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
        return self.grounding_value

    def append_message(self, session_id: str, *, role: str, mode: TutorMode | None, content: dict, grounding_revision_ids: tuple[str, ...] = (), model_name: str | None = None, prompt_version: str | None = None, safety_outcome: str = "accepted", latency_ms: int | None = None, token_usage: dict | None = None) -> dict:
        del grounding_revision_ids, model_name, prompt_version, latency_ms, token_usage
        row = {"id": str(uuid4()), "role": role, "mode": mode,
               "blocks": content.get("blocks", []), "safety_outcome": safety_outcome,
               "created_at": datetime.now(UTC)}
        self.messages[session_id].append(row)
        return row

    def reserve(self, learner_id: str, session_id: str, limits: TutorLimits, *, request_id: str) -> UsageReservation:
        del request_id
        with self._lock:
            if self.reserved:
                raise TutorError("tutor_generation_in_progress", "Wait for the current tutor response before sending another message.", 409)
            today = datetime.now(UTC).date()
            if self.actual_requests + 1 > limits.daily_messages or self.actual_tokens + limits.max_turn_tokens > limits.daily_tokens or self.actual_cost + limits.max_turn_cost_micros_sgd > limits.monthly_cost_micros_sgd:
                PostgresTutorRepository._quota_error(today, "test_boundary")
            self.reserved = True
            item = UsageReservation(str(uuid4()), session_id, learner_id, today, today.replace(day=1))
            self.reservations[item.reservation_id] = item
            return item

    def reconcile(self, reservation: UsageReservation, actual: UsageActual, limits: TutorLimits, *, request_id: str) -> QuotaSnapshot:
        del request_id
        with self._lock:
            self.reserved = False
            self.actual_requests += 1
            self.actual_tokens += actual.total_tokens
            self.actual_cost += actual.cost_micros_sgd
        return QuotaSnapshot(
            max(0, limits.daily_messages-self.actual_requests),
            max(0, limits.daily_tokens-self.actual_tokens),
            max(0, limits.monthly_cost_micros_sgd-self.actual_cost),
            _next_utc_day(reservation.usage_date),
        )

    def release(self, reservation: UsageReservation, *, request_id: str, reason: str) -> None:
        del reservation, request_id, reason
        with self._lock:
            self.reserved = False

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
        }
