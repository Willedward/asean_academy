"""PostgreSQL repository and deterministic scoring for Mathematics diagnostics."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from decimal import Decimal
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from question_bank.checking import check_answer
from question_bank.models import AlgebraicResponse, NumericResponse

BAND_POLICY_VERSION = "n1-readiness-v1"


class DiagnosticError(RuntimeError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


def _canonical(value: dict[str, Any]) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _fingerprint(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def band_for(percentage: float) -> str:
    if percentage < 50:
        return "getting_started"
    if percentage < 80:
        return "on_track"
    return "ahead"


def _number(value: Decimal | float | int) -> float:
    return round(float(value), 3)


class PostgresDiagnosticRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(
            self.database_url,
            connect_timeout=10,
            prepare_threshold=None,
            row_factory=dict_row,
        )

    @staticmethod
    def _set_identity(connection, learner_id: str) -> None:
        connection.execute(
            "select set_config('request.jwt.claim.sub', %s, true)",
            (str(UUID(learner_id)),),
        )

    @staticmethod
    def _enrolment(connection, learner_id: str) -> dict:
        row = connection.execute(
            """
            select enrolments.course_version_id, courses.course_key
            from course_enrolments enrolments
            join course_versions versions on versions.id = enrolments.course_version_id
            join courses on courses.id = versions.course_id
            where enrolments.student_id = %s and enrolments.status = 'active'
            order by enrolments.enrolled_at desc
            limit 1
            """,
            (learner_id,),
        ).fetchone()
        if row is None:
            raise DiagnosticError(
                "active_enrolment_required",
                "An active course enrolment is required.",
                403,
            )
        return row

    @staticmethod
    def _form(connection, course_version_id: UUID, purpose: str) -> dict | None:
        return connection.execute(
            """
            select forms.*,
                   (select count(*) from diagnostic_form_items items
                    where items.form_id = forms.id)::integer as question_count
            from diagnostic_forms forms
            where forms.course_version_id = %s
              and forms.purpose = %s
              and forms.status = 'published'
              and forms.is_current
            """,
            (course_version_id, purpose),
        ).fetchone()

    @staticmethod
    def _effective_session(
        connection, learner_id: str, course_version_id: UUID, purpose: str
    ) -> dict | None:
        return connection.execute(
            """
            select sessions.*, results.id as result_id
            from diagnostic_sessions sessions
            left join diagnostic_results results on results.session_id = sessions.id
            where sessions.student_id = %s
              and sessions.course_version_id = %s
              and sessions.purpose = %s
              and sessions.state <> 'reset'
            order by sessions.started_at desc
            limit 1
            """,
            (learner_id, course_version_id, purpose),
        ).fetchone()

    @staticmethod
    def _course_mastered(connection, learner_id: str, course_version_id: UUID) -> bool:
        row = connection.execute(
            """
            select count(*) filter (where progress.state = 'mastered') = count(*) as mastered
            from unit_versions units
            join unit_version_lessons assignments on assignments.unit_version_id = units.id
            join lesson_versions versions on versions.id = assignments.lesson_version_id
            left join learner_lesson_progress progress
              on progress.student_id = %s and progress.lesson_id = versions.lesson_id
            where units.course_version_id = %s
            """,
            (learner_id, course_version_id),
        ).fetchone()
        return bool(row and row["mastered"])

    def next(self, learner_id: str) -> dict:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            enrolment = self._enrolment(connection, learner_id)
            course_version_id = enrolment["course_version_id"]
            baseline = self._effective_session(
                connection, learner_id, course_version_id, "baseline"
            )
            if baseline is None:
                form = self._form(connection, course_version_id, "baseline")
                if form is None or form["question_count"] == 0:
                    return {
                        "status": "content_pending",
                        "title": "Readiness check is being prepared",
                        "message": "Reviewed diagnostic questions have not been published yet.",
                    }
                return {
                    "status": "start",
                    "purpose": "baseline",
                    "title": form["title"],
                    "message": form["instructions"],
                    "estimated_minutes": form["estimated_minutes"],
                    "question_count": form["question_count"],
                }
            if baseline["state"] == "in_progress":
                return {
                    "status": "resume",
                    "purpose": "baseline",
                    "session_id": baseline["id"],
                    "title": "Resume your Mathematics readiness check",
                    "message": "Your saved answers are ready when you return.",
                }

            endline = self._effective_session(
                connection, learner_id, course_version_id, "endline"
            )
            if endline is not None:
                if endline["state"] == "in_progress":
                    return {
                        "status": "resume",
                        "purpose": "endline",
                        "session_id": endline["id"],
                        "result_session_id": baseline["id"],
                        "title": "Resume your final Mathematics readiness check",
                        "message": "Finish the endline check to compare your progress.",
                    }
                return {
                    "status": "completed",
                    "purpose": "endline",
                    "session_id": endline["id"],
                    "result_session_id": endline["id"],
                    "title": "Your Mathematics readiness checks are complete",
                    "message": "View your baseline and endline evidence side by side.",
                }

            if not self._course_mastered(connection, learner_id, course_version_id):
                return {
                    "status": "baseline_complete",
                    "purpose": "baseline",
                    "session_id": baseline["id"],
                    "result_session_id": baseline["id"],
                    "title": "Baseline readiness recorded",
                    "message": "Complete N1 mastery before the final readiness check unlocks.",
                }
            form = self._form(connection, course_version_id, "endline")
            if form is None or form["question_count"] == 0:
                return {
                    "status": "content_pending",
                    "purpose": "endline",
                    "result_session_id": baseline["id"],
                    "title": "Final readiness check is being prepared",
                    "message": "Your baseline is safe. The reviewed endline form is not published yet.",
                }
            return {
                "status": "start",
                "purpose": "endline",
                "result_session_id": baseline["id"],
                "title": form["title"],
                "message": form["instructions"],
                "estimated_minutes": form["estimated_minutes"],
                "question_count": form["question_count"],
            }

    def create_session(
        self,
        learner_id: str,
        idempotency_key: str,
        expected_purpose: str | None,
    ) -> dict:
        fingerprint = _fingerprint({"expected_purpose": expected_purpose})
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"diagnostic:{learner_id}",),
            )
            replay = connection.execute(
                """
                select * from diagnostic_sessions
                where student_id = %s and idempotency_key = %s
                """,
                (learner_id, idempotency_key),
            ).fetchone()
            if replay is not None:
                if replay["state"] == "reset":
                    raise DiagnosticError(
                        "diagnostic_session_reset",
                        "This diagnostic session was reset. Start again with a new request.",
                        409,
                    )
                if replay["request_fingerprint"] != fingerprint:
                    raise DiagnosticError(
                        "idempotency_key_reused",
                        "This idempotency key was already used for a different request.",
                        409,
                    )
                return self._session_payload(connection, replay)

            enrolment = self._enrolment(connection, learner_id)
            course_version_id = enrolment["course_version_id"]
            for purpose in ("baseline", "endline"):
                active = self._effective_session(
                    connection, learner_id, course_version_id, purpose
                )
                if active is not None and active["state"] == "in_progress":
                    if expected_purpose and expected_purpose != purpose:
                        raise DiagnosticError(
                            "diagnostic_state_changed",
                            "The next diagnostic changed. Refresh before continuing.",
                            409,
                        )
                    return self._session_payload(connection, active)

            baseline = self._effective_session(
                connection, learner_id, course_version_id, "baseline"
            )
            purpose = "baseline" if baseline is None else "endline"
            if purpose == "endline" and not self._course_mastered(
                connection, learner_id, course_version_id
            ):
                raise DiagnosticError(
                    "endline_locked",
                    "Complete N1 mastery before starting the final readiness check.",
                    409,
                )
            if expected_purpose and expected_purpose != purpose:
                raise DiagnosticError(
                    "diagnostic_state_changed",
                    "The next diagnostic changed. Refresh before continuing.",
                    409,
                )
            if baseline is not None and purpose == "baseline":
                raise DiagnosticError(
                    "diagnostic_already_completed",
                    "The baseline readiness check is already complete.",
                    409,
                )
            if purpose == "endline":
                existing_endline = self._effective_session(
                    connection, learner_id, course_version_id, "endline"
                )
                if existing_endline is not None:
                    raise DiagnosticError(
                        "diagnostic_already_completed",
                        "The final readiness check is already complete.",
                        409,
                    )
            form = self._form(connection, course_version_id, purpose)
            if form is None or form["question_count"] == 0:
                raise DiagnosticError(
                    "diagnostic_content_pending",
                    "Reviewed diagnostic questions have not been published yet.",
                    409,
                )
            session = connection.execute(
                """
                insert into diagnostic_sessions (
                    student_id, form_id, course_version_id, purpose,
                    idempotency_key, request_fingerprint
                ) values (%s, %s, %s, %s, %s, %s)
                returning *
                """,
                (
                    learner_id,
                    form["id"],
                    course_version_id,
                    purpose,
                    idempotency_key,
                    fingerprint,
                ),
            ).fetchone()
            return self._session_payload(connection, session)

    @staticmethod
    def _owned_session(connection, learner_id: str, session_id: str, *, lock=False) -> dict:
        suffix = " for update" if lock else ""
        row = connection.execute(
            "select * from diagnostic_sessions where id = %s and student_id = %s" + suffix,
            (session_id, learner_id),
        ).fetchone()
        if row is None or row["state"] == "reset":
            raise DiagnosticError(
                "diagnostic_session_not_found", "Diagnostic session was not found.", 404
            )
        return row

    def session(self, learner_id: str, session_id: str) -> dict:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            session = self._owned_session(connection, learner_id, session_id)
            return self._session_payload(connection, session)

    @staticmethod
    def _session_payload(connection, session: dict) -> dict:
        form = connection.execute(
            "select * from diagnostic_forms where id = %s", (session["form_id"],)
        ).fetchone()
        rows = connection.execute(
            """
            select items.id as item_id, items.position, items.weight,
                   outcomes.code as outcome_code,
                   questions.stable_key, questions.difficulty,
                   versions.id as question_version_id, versions.revision,
                   versions.title, versions.calculator_allowed,
                   versions.stem_blocks, versions.total_marks,
                   responses.answer_payload, responses.updated_at as saved_at
            from diagnostic_form_items items
            join syllabus_outcomes outcomes on outcomes.id = items.outcome_id
            join math_question_versions versions on versions.id = items.question_version_id
            join math_questions questions on questions.id = versions.question_id
            left join diagnostic_responses responses
              on responses.session_id = %s and responses.form_item_id = items.id
            where items.form_id = %s
            order by items.position
            """,
            (session["id"], session["form_id"]),
        ).fetchall()
        parts = connection.execute(
            """
            select parts.question_version_id, parts.position, parts.label,
                   parts.prompt_blocks, parts.marks, parts.response_type
            from math_question_parts parts
            join diagnostic_form_items items
              on items.question_version_id = parts.question_version_id
            where items.form_id = %s
            order by parts.question_version_id, parts.position
            """,
            (session["form_id"],),
        ).fetchall()
        by_version: dict[UUID, list[dict]] = defaultdict(list)
        for part in parts:
            by_version[part["question_version_id"]].append(
                {
                    "position": part["position"],
                    "label": part["label"],
                    "prompt": part["prompt_blocks"],
                    "marks": part["marks"],
                    "response_type": part["response_type"],
                    "input_placeholder": "Enter your final answer",
                }
            )
        items = []
        for row in rows:
            items.append(
                {
                    "position": row["position"],
                    "outcome_code": row["outcome_code"],
                    "weight": _number(row["weight"]),
                    "question": {
                        "stable_key": row["stable_key"],
                        "revision": row["revision"],
                        "title": row["title"],
                        "difficulty": row["difficulty"],
                        "calculator_allowed": row["calculator_allowed"],
                        "stem": row["stem_blocks"],
                        "total_marks": row["total_marks"],
                        "parts": by_version[row["question_version_id"]],
                    },
                    "saved_answers": row["answer_payload"],
                    "saved_at": row["saved_at"],
                }
            )
        return {
            "session_id": session["id"],
            "state": session["state"],
            "purpose": session["purpose"],
            "form_key": form["stable_key"],
            "form_revision": form["revision"],
            "title": form["title"],
            "instructions": form["instructions"],
            "estimated_minutes": form["estimated_minutes"],
            "started_at": session["started_at"],
            "submitted_at": session["submitted_at"],
            "items": items,
        }

    @staticmethod
    def _spec(row: dict):
        if row["response_type"] == "numeric":
            unit = row["unit_spec"]
            return NumericResponse(
                type="numeric",
                comparison_mode=row["comparison_mode"],
                canonical_answer=row["canonical_answer"],
                canonical_latex=row["canonical_latex"] or row["canonical_answer"],
                accepted_answers=row["accepted_answers"],
                absolute_tolerance=(
                    str(row["absolute_tolerance"])
                    if row["absolute_tolerance"] is not None
                    else None
                ),
                rounding_precision=row["rounding_precision"],
                unit=unit,
            )
        return AlgebraicResponse(
            type="algebraic_expression",
            comparison_mode=row["comparison_mode"],
            canonical_expression=row["canonical_answer"],
            canonical_latex=row["canonical_latex"] or row["canonical_answer"],
            variables=row["variables"],
            domain_constraints=row["domain_constraints"],
            accepted_equivalents=row["accepted_answers"],
            checker_config=row["checker_config"],
        )

    def save_response(
        self,
        learner_id: str,
        session_id: str,
        position: int,
        answers: dict[str, str],
        idempotency_key: str,
    ) -> dict:
        fingerprint = _fingerprint({"position": position, "answers": answers})
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            session = self._owned_session(connection, learner_id, session_id, lock=True)
            if session["state"] != "in_progress":
                raise DiagnosticError(
                    "diagnostic_already_submitted",
                    "Submitted diagnostic answers cannot be changed.",
                    409,
                )
            replay = connection.execute(
                """
                select * from diagnostic_response_idempotency_keys
                where session_id = %s and idempotency_key = %s
                """,
                (session_id, idempotency_key),
            ).fetchone()
            if replay is not None:
                if replay["request_fingerprint"] != fingerprint:
                    raise DiagnosticError(
                        "idempotency_key_reused",
                        "This idempotency key was already used for another answer.",
                        409,
                    )
                saved = connection.execute(
                    """
                    select updated_at from diagnostic_responses
                    where session_id = %s and position = %s
                    """,
                    (session_id, replay["position"]),
                ).fetchone()
                return {
                    "session_id": session["id"],
                    "position": replay["position"],
                    "saved": True,
                    "saved_at": saved["updated_at"],
                }
            item = connection.execute(
                """
                select items.*, versions.total_marks
                from diagnostic_form_items items
                join math_question_versions versions on versions.id = items.question_version_id
                where items.form_id = %s and items.position = %s
                """,
                (session["form_id"], position),
            ).fetchone()
            if item is None:
                raise DiagnosticError(
                    "diagnostic_item_not_found", "Diagnostic question was not found.", 404
                )
            parts = connection.execute(
                """
                select parts.position, parts.marks, parts.response_type,
                       specs.comparison_mode, specs.canonical_answer,
                       specs.canonical_latex, specs.absolute_tolerance,
                       specs.rounding_precision, specs.variables,
                       specs.domain_constraints, specs.accepted_answers,
                       specs.checker_config, specs.unit_spec
                from math_question_parts parts
                join math_answer_specs specs on specs.question_part_id = parts.id
                where parts.question_version_id = %s
                order by parts.position
                """,
                (item["question_version_id"],),
            ).fetchall()
            expected = {str(part["position"]) for part in parts}
            if set(answers) != expected or any(not value.strip() for value in answers.values()):
                raise DiagnosticError(
                    "diagnostic_answer_incomplete",
                    "Save one final answer for every part of this question.",
                    422,
                )
            raw_score = Decimal("0")
            for part in parts:
                result = check_answer(self._spec(part), answers[str(part["position"])])
                if result["correct"]:
                    raw_score += Decimal(part["marks"])
            weight = Decimal(item["weight"])
            score = raw_score * weight
            max_score = Decimal(item["total_marks"]) * weight
            payload = {key: answers[key].strip() for key in sorted(answers)}
            saved = connection.execute(
                """
                insert into diagnostic_responses (
                    session_id, form_item_id, position, answer_payload,
                    answer_sha256, score, max_score
                ) values (%s, %s, %s, %s, %s, %s, %s)
                on conflict (session_id, form_item_id) do update set
                    answer_payload = excluded.answer_payload,
                    answer_sha256 = excluded.answer_sha256,
                    score = excluded.score,
                    max_score = excluded.max_score,
                    updated_at = now()
                returning updated_at
                """,
                (
                    session_id,
                    item["id"],
                    position,
                    Jsonb(payload),
                    hashlib.sha256(_canonical(payload).encode()).hexdigest(),
                    score,
                    max_score,
                ),
            ).fetchone()
            connection.execute(
                """
                insert into diagnostic_response_idempotency_keys (
                    session_id, idempotency_key, position, request_fingerprint
                ) values (%s, %s, %s, %s)
                """,
                (session_id, idempotency_key, position, fingerprint),
            )
            return {
                "session_id": session["id"],
                "position": position,
                "saved": True,
                "saved_at": saved["updated_at"],
            }

    def submit(self, learner_id: str, session_id: str) -> dict:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            session = self._owned_session(connection, learner_id, session_id, lock=True)
            if session["state"] == "submitted":
                return self._result_payload(connection, session_id)
            counts = connection.execute(
                """
                select (select count(*) from diagnostic_form_items where form_id = %s) as items,
                       (select count(*) from diagnostic_responses where session_id = %s) as responses
                """,
                (session["form_id"], session_id),
            ).fetchone()
            if counts["items"] == 0 or counts["responses"] != counts["items"]:
                raise DiagnosticError(
                    "diagnostic_incomplete",
                    "Answer every question before submitting the readiness check.",
                    409,
                )
            rows = connection.execute(
                """
                select outcomes.code as outcome_code, responses.score, responses.max_score
                from diagnostic_responses responses
                join diagnostic_form_items items on items.id = responses.form_item_id
                join syllabus_outcomes outcomes on outcomes.id = items.outcome_id
                where responses.session_id = %s
                order by outcomes.code
                """,
                (session_id,),
            ).fetchall()
            outcomes: dict[str, dict[str, float]] = {}
            total_score = Decimal("0")
            total_max = Decimal("0")
            for row in rows:
                code = row["outcome_code"]
                bucket = outcomes.setdefault(code, {"score": 0.0, "max_score": 0.0})
                bucket["score"] += _number(row["score"])
                bucket["max_score"] += _number(row["max_score"])
                total_score += row["score"]
                total_max += row["max_score"]
            for bucket in outcomes.values():
                bucket["score"] = round(bucket["score"], 3)
                bucket["max_score"] = round(bucket["max_score"], 3)
                bucket["percentage"] = round(
                    bucket["score"] * 100 / bucket["max_score"], 2
                )
            percentage = round(float(total_score * 100 / total_max), 2)
            form = connection.execute(
                "select * from diagnostic_forms where id = %s", (session["form_id"],)
            ).fetchone()
            connection.execute(
                """
                insert into diagnostic_results (
                    session_id, student_id, form_id, purpose, score, max_score,
                    percentage, band, outcome_scores, band_policy_version
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    learner_id,
                    session["form_id"],
                    session["purpose"],
                    total_score,
                    total_max,
                    percentage,
                    band_for(percentage),
                    Jsonb(outcomes),
                    form["band_policy_version"],
                ),
            )
            connection.execute(
                """
                update diagnostic_sessions
                set state = 'submitted', submitted_at = now(), updated_at = now()
                where id = %s
                """,
                (session_id,),
            )
            return self._result_payload(connection, session_id)

    @staticmethod
    def _result_payload(connection, session_id: str) -> dict:
        row = connection.execute(
            """
            select results.*, forms.stable_key, forms.revision,
                   sessions.submitted_at
            from diagnostic_results results
            join diagnostic_forms forms on forms.id = results.form_id
            join diagnostic_sessions sessions on sessions.id = results.session_id
            where results.session_id = %s
            """,
            (session_id,),
        ).fetchone()
        if row is None:
            raise DiagnosticError(
                "diagnostic_result_not_ready",
                "Submit the readiness check before viewing its result.",
                409,
            )
        scores = [
            {
                "outcome_code": code,
                "score": values["score"],
                "max_score": values["max_score"],
                "percentage": values["percentage"],
            }
            for code, values in sorted(row["outcome_scores"].items())
        ]
        strengths = [item["outcome_code"] for item in scores if item["percentage"] >= 80]
        priorities = [
            item["outcome_code"]
            for item in sorted(scores, key=lambda item: (item["percentage"], item["outcome_code"]))[:3]
            if item["percentage"] < 80
        ]
        return {
            "session_id": row["session_id"],
            "purpose": row["purpose"],
            "form_key": row["stable_key"],
            "form_revision": row["revision"],
            "score": _number(row["score"]),
            "max_score": _number(row["max_score"]),
            "percentage": float(row["percentage"]),
            "band": row["band"],
            "band_policy_version": row["band_policy_version"],
            "outcome_scores": scores,
            "strengths": strengths,
            "priorities": priorities,
            "submitted_at": row["submitted_at"],
        }

    def result(self, learner_id: str, session_id: str) -> dict:
        with self._connect() as connection:
            self._set_identity(connection, learner_id)
            self._owned_session(connection, learner_id, session_id)
            return self._result_payload(connection, session_id)

    def admin_student_results(self, learner_id: str) -> dict:
        with self._connect() as connection:
            rows = connection.execute(
                """
                select sessions.id, sessions.state, sessions.reset_at,
                       resets.reason as reset_reason
                from diagnostic_sessions sessions
                left join diagnostic_resets resets on resets.session_id = sessions.id
                where sessions.student_id = %s and sessions.submitted_at is not null
                order by sessions.submitted_at
                """,
                (learner_id,),
            ).fetchall()
            history = []
            for row in rows:
                result = self._result_payload(connection, row["id"])
                result.update(
                    {
                        "state": "reset" if row["state"] == "reset" else "submitted",
                        "reset_at": row["reset_at"],
                        "reset_reason": row["reset_reason"],
                    }
                )
                history.append(result)
            active = [item for item in history if item["state"] == "submitted"]
            return {
                "learner_id": learner_id,
                "baseline": next(
                    (item for item in reversed(active) if item["purpose"] == "baseline"),
                    None,
                ),
                "endline": next(
                    (item for item in reversed(active) if item["purpose"] == "endline"),
                    None,
                ),
                "history": history,
            }

    def reset(
        self,
        learner_id: str,
        purpose: str,
        administrator_id: str,
        reason: str,
        request_id: str,
    ) -> dict:
        with self._connect() as connection:
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"diagnostic:{learner_id}",),
            )
            session = connection.execute(
                """
                select * from diagnostic_sessions
                where student_id = %s and purpose = %s and state <> 'reset'
                order by started_at desc limit 1 for update
                """,
                (learner_id, purpose),
            ).fetchone()
            if session is None:
                raise DiagnosticError(
                    "diagnostic_session_not_found",
                    "No effective diagnostic session exists for this learner and purpose.",
                    404,
                )
            reset = connection.execute(
                """
                update diagnostic_sessions
                set state = 'reset', reset_at = now(), updated_at = now()
                where id = %s returning reset_at
                """,
                (session["id"],),
            ).fetchone()
            connection.execute(
                """
                insert into diagnostic_resets (
                    session_id, student_id, purpose, reset_by, reason, request_id
                ) values (%s, %s, %s, %s, %s, %s)
                """,
                (
                    session["id"],
                    learner_id,
                    purpose,
                    administrator_id,
                    reason.strip(),
                    request_id,
                ),
            )
            return {
                "learner_id": learner_id,
                "purpose": purpose,
                "reset": True,
                "reset_at": reset["reset_at"],
            }
