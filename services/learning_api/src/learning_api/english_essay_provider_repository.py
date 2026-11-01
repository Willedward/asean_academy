"""Persistence for calibrated-candidate essay feedback attempts.

The PostgreSQL completion and failure paths update the attempt, immutable feedback,
reservation, learner usage, academy usage and audit event in one transaction.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .english_essay_allowance import (
    EssayFeedbackActual,
    EssayFeedbackLimits,
    EssayFeedbackReservation,
)
from .english_essay_repository import EnglishEssayError


class InMemoryEnglishEssayProviderFeedbackRepository:
    def __init__(self, essay_repository, allowance_repository, limits: EssayFeedbackLimits):
        self.essay_repository = essay_repository
        self.allowance_repository = allowance_repository
        self.limits = limits
        self.attempts: dict[str, dict] = {}
        shared_feedback = getattr(essay_repository, "provider_feedback", None)
        self.feedback: dict[str, dict] = (
            shared_feedback if shared_feedback is not None else {}
        )
        if shared_feedback is None:
            essay_repository.provider_feedback = self.feedback
        self._lock = Lock()

    def enqueue(
        self,
        learner_id: str,
        submission_id: str,
        *,
        reservation: EssayFeedbackReservation,
        rubric_key: str,
        rubric_revision: int,
        rubric_criteria: list[dict],
        provider_name: str,
        model_name: str,
        policy_version: str,
        schema_version: str,
    ) -> dict:
        with self._lock:
            if (
                reservation.learner_id != learner_id
                or reservation.submission_id != submission_id
                or reservation.status != "reserved"
            ):
                raise EnglishEssayError(
                    "essay_feedback_reservation_invalid",
                    "The provider attempt does not match its active reservation.",
                    409,
                )
            existing = next(
                (
                    row
                    for row in self.attempts.values()
                    if row["submission_id"] == submission_id
                    and row["status"] in {"queued", "processing", "succeeded"}
                ),
                None,
            )
            if existing:
                return dict(existing)
            submission = self.essay_repository.get_submission(learner_id, submission_id)
            attempt_id = str(uuid4())
            now = datetime.now(UTC).isoformat()
            row = {
                "attempt_id": attempt_id,
                "learner_id": learner_id,
                "submission_id": submission_id,
                "reservation_id": reservation.reservation_id,
                "rubric_key": rubric_key,
                "rubric_revision": rubric_revision,
                "rubric_criteria": json.loads(json.dumps(rubric_criteria)),
                "submission_body": submission["body"],
                "provider_name": provider_name,
                "model_name": model_name,
                "policy_version": policy_version,
                "schema_version": schema_version,
                "status": "queued",
                "lease_token": None,
                "worker_id": None,
                "last_error_code": None,
                "last_error_message": None,
                "created_at": now,
                "updated_at": now,
                "completed_at": None,
            }
            self.attempts[attempt_id] = row
            return dict(row)

    def claim(self, attempt_id: str, *, worker_id: str) -> dict | None:
        with self._lock:
            attempt = self.attempts.get(attempt_id)
            if not attempt or attempt["status"] != "queued":
                return None
            now = datetime.now(UTC).isoformat()
            attempt.update(
                status="processing",
                lease_token=str(uuid4()),
                worker_id=worker_id,
                updated_at=now,
            )
            return json.loads(json.dumps(attempt))

    def complete_validated(
        self,
        attempt_id: str,
        *,
        lease_token: str,
        feedback: dict,
        actual_cost_micros_sgd: int,
        request_id: str,
    ) -> dict:
        with self._lock:
            attempt = self._owned_processing(attempt_id, lease_token)
            reservation = EssayFeedbackReservation(
                attempt["reservation_id"],
                attempt["learner_id"],
                attempt["submission_id"],
                self.allowance_repository.reservations[attempt["reservation_id"]]["usage_month"],
            )
            feedback_id = str(uuid4())
            stored = {
                "feedback_id": feedback_id,
                "attempt_id": attempt_id,
                "learner_id": attempt["learner_id"],
                "submission_id": attempt["submission_id"],
                "reservation_id": attempt["reservation_id"],
                **json.loads(json.dumps(feedback)),
            }
            self.feedback[feedback_id] = stored
            try:
                self.allowance_repository.commit(
                    reservation,
                    EssayFeedbackActual(actual_cost_micros_sgd),
                    self.limits,
                    request_id=request_id,
                )
            except Exception:
                self.feedback.pop(feedback_id, None)
                raise
            now = datetime.now(UTC).isoformat()
            attempt.update(
                status="succeeded",
                lease_token=None,
                completed_at=now,
                updated_at=now,
            )
            return dict(stored)

    def fail_and_release(
        self,
        attempt_id: str,
        *,
        lease_token: str,
        error_code: str,
        error_message: str,
        request_id: str,
    ) -> dict:
        with self._lock:
            attempt = self._owned_processing(attempt_id, lease_token)
            reservation_row = self.allowance_repository.reservations[attempt["reservation_id"]]
            reservation = EssayFeedbackReservation(
                attempt["reservation_id"],
                attempt["learner_id"],
                attempt["submission_id"],
                reservation_row["usage_month"],
            )
            self.allowance_repository.release(
                reservation,
                self.limits,
                request_id=request_id,
                reason=error_code,
            )
            now = datetime.now(UTC).isoformat()
            attempt.update(
                status="permanent_failed",
                lease_token=None,
                last_error_code=error_code,
                last_error_message=error_message[:1000],
                completed_at=now,
                updated_at=now,
            )
            return dict(attempt)

    def _owned_processing(self, attempt_id: str, lease_token: str) -> dict:
        attempt = self.attempts.get(attempt_id)
        if (
            not attempt
            or attempt["status"] != "processing"
            or attempt["lease_token"] != lease_token
        ):
            raise EnglishEssayError(
                "essay_feedback_attempt_lease_lost",
                "The provider feedback attempt lease is no longer owned by this worker.",
                409,
            )
        return attempt


class PostgresEnglishEssayProviderFeedbackRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def enqueue(
        self,
        learner_id: str,
        submission_id: str,
        *,
        reservation: EssayFeedbackReservation,
        rubric_key: str,
        rubric_revision: int,
        rubric_criteria: list[dict],
        provider_name: str,
        model_name: str,
        policy_version: str,
        schema_version: str,
    ) -> dict:
        del rubric_criteria
        with self._connect() as connection, connection.transaction():
            source = connection.execute(
                """
                select submissions.rubric_version_id,
                       rubrics.stable_key as rubric_key,
                       rubric_versions.revision as rubric_revision
                  from english_essay_submissions submissions
                  join english_essay_rubric_versions rubric_versions
                    on rubric_versions.id = submissions.rubric_version_id
                  join english_essay_rubrics rubrics on rubrics.id = rubric_versions.rubric_id
                 where submissions.id=%s and submissions.student_id=%s
                """,
                (submission_id, learner_id),
            ).fetchone()
            if not source:
                raise EnglishEssayError(
                    "essay_submission_not_found", "Essay submission not found.", 404
                )
            if source["rubric_key"] != rubric_key or source["rubric_revision"] != rubric_revision:
                raise EnglishEssayError(
                    "essay_rubric_changed", "The pinned essay rubric changed.", 409
                )
            created = connection.execute(
                """
                insert into english_essay_provider_feedback_attempts(
                    student_id, submission_id, rubric_version_id, reservation_id,
                    provider_name, model_name, policy_version, schema_version
                ) values (%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (reservation_id) do nothing
                returning id::text as attempt_id
                """,
                (
                    learner_id,
                    submission_id,
                    source["rubric_version_id"],
                    reservation.reservation_id,
                    provider_name,
                    model_name,
                    policy_version,
                    schema_version,
                ),
            ).fetchone()
            attempt_id = (
                created["attempt_id"]
                if created
                else connection.execute(
                    "select id::text as attempt_id from english_essay_provider_feedback_attempts where submission_id=%s and student_id=%s",
                    (submission_id, learner_id),
                ).fetchone()["attempt_id"]
            )
            return self._attempt(connection, learner_id, attempt_id)

    def claim(self, attempt_id: str, *, worker_id: str) -> dict | None:
        with self._connect() as connection, connection.transaction():
            row = connection.execute(
                """
                update english_essay_provider_feedback_attempts
                   set status='processing', lease_token=gen_random_uuid(),
                       worker_id=%s, updated_at=now()
                 where id=%s and status='queued'
                returning id::text as attempt_id, student_id::text as learner_id,
                          submission_id::text as submission_id,
                          reservation_id::text as reservation_id,
                          lease_token::text as lease_token,
                          provider_name, model_name, policy_version, schema_version
                """,
                (worker_id, attempt_id),
            ).fetchone()
            if not row:
                return None
            source = connection.execute(
                """
                select submissions.body as submission_body,
                       rubrics.stable_key as rubric_key,
                       versions.revision as rubric_revision,
                       versions.criteria as rubric_criteria
                  from english_essay_provider_feedback_attempts attempts
                  join english_essay_submissions submissions on submissions.id=attempts.submission_id
                  join english_essay_rubric_versions versions on versions.id=attempts.rubric_version_id
                  join english_essay_rubrics rubrics on rubrics.id=versions.rubric_id
                 where attempts.id=%s
                """,
                (attempt_id,),
            ).fetchone()
            return {**dict(row), **dict(source)}

    def complete_validated(
        self,
        attempt_id: str,
        *,
        lease_token: str,
        feedback: dict,
        actual_cost_micros_sgd: int,
        request_id: str,
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            attempt, reservation = self._locked_attempt_and_reservation(
                connection, attempt_id, lease_token
            )
            reserved_cost = reservation["reserved_cost_micros_sgd"]
            if actual_cost_micros_sgd < 0 or actual_cost_micros_sgd > reserved_cost:
                raise EnglishEssayError(
                    "essay_feedback_provider_usage_invalid",
                    "The feedback provider reported usage outside the reserved boundary.",
                    503,
                )
            created = connection.execute(
                """
                insert into english_essay_provider_feedback(
                    student_id, attempt_id, submission_id, rubric_version_id,
                    reservation_id, schema_version, validation_version,
                    preparation_estimate, criterion_feedback, overall_summary,
                    strengths, priorities, revision_task, transfer_goal, learner_disclaimer
                ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                returning id::text as feedback_id
                """,
                (
                    attempt["student_id"],
                    attempt_id,
                    attempt["submission_id"],
                    attempt["rubric_version_id"],
                    attempt["reservation_id"],
                    feedback["schema_version"],
                    feedback["validation_version"],
                    feedback["preparation_estimate"],
                    Jsonb(feedback["criterion_feedback"]),
                    feedback["overall_summary"],
                    Jsonb(feedback["strengths"]),
                    Jsonb(feedback["priorities"]),
                    feedback["revision_task"],
                    feedback["transfer_goal"],
                    feedback["learner_disclaimer"],
                ),
            ).fetchone()
            self._commit_reservation(connection, reservation, actual_cost_micros_sgd, request_id)
            connection.execute(
                """
                update english_essay_provider_feedback_attempts
                   set status='succeeded', lease_token=null, completed_at=now(), updated_at=now()
                 where id=%s
                """,
                (attempt_id,),
            )
            return {"feedback_id": created["feedback_id"], **feedback}

    def fail_and_release(
        self,
        attempt_id: str,
        *,
        lease_token: str,
        error_code: str,
        error_message: str,
        request_id: str,
    ) -> dict:
        with self._connect() as connection, connection.transaction():
            attempt, reservation = self._locked_attempt_and_reservation(
                connection, attempt_id, lease_token
            )
            self._release_reservation(connection, reservation, request_id, error_code)
            connection.execute(
                """
                update english_essay_provider_feedback_attempts
                   set status='permanent_failed', lease_token=null,
                       last_error_code=%s, last_error_message=%s,
                       completed_at=now(), updated_at=now()
                 where id=%s
                """,
                (error_code, error_message[:1000], attempt_id),
            )
            return self._attempt(connection, str(attempt["student_id"]), attempt_id)

    @staticmethod
    def _attempt(connection, learner_id: str, attempt_id: str) -> dict:
        row = connection.execute(
            """
            select id::text as attempt_id, submission_id::text as submission_id,
                   reservation_id::text as reservation_id, provider_name, model_name,
                   policy_version, schema_version, status, last_error_code,
                   last_error_message, created_at, updated_at, completed_at
              from english_essay_provider_feedback_attempts
             where id=%s and student_id=%s
            """,
            (attempt_id, learner_id),
        ).fetchone()
        if not row:
            raise EnglishEssayError(
                "essay_feedback_attempt_not_found", "Feedback attempt not found.", 404
            )
        return dict(row)

    @staticmethod
    def _locked_attempt_and_reservation(connection, attempt_id: str, lease_token: str):
        attempt = connection.execute(
            "select * from english_essay_provider_feedback_attempts where id=%s and status='processing' and lease_token=%s for update",
            (attempt_id, lease_token),
        ).fetchone()
        if not attempt:
            raise EnglishEssayError(
                "essay_feedback_attempt_lease_lost",
                "The provider feedback attempt lease is no longer owned by this worker.",
                409,
            )
        reservation = connection.execute(
            "select * from english_essay_feedback_reservations where id=%s for update",
            (attempt["reservation_id"],),
        ).fetchone()
        if not reservation or reservation["status"] != "reserved":
            raise EnglishEssayError(
                "essay_feedback_reservation_invalid",
                "The feedback reservation is no longer active.",
                409,
            )
        return attempt, reservation

    @staticmethod
    def _commit_reservation(connection, reservation: dict, actual_cost: int, request_id: str):
        month = reservation["usage_month"]
        student = reservation["student_id"]
        reserved = reservation["reserved_cost_micros_sgd"]
        connection.execute(
            "update english_essay_feedback_monthly_usage set reserved_feedback=reserved_feedback-1, committed_feedback=committed_feedback+1, reserved_cost_micros_sgd=reserved_cost_micros_sgd-%s, actual_cost_micros_sgd=actual_cost_micros_sgd+%s, updated_at=now() where student_id=%s and usage_month=%s",
            (reserved, actual_cost, student, month),
        )
        connection.execute(
            "update english_essay_feedback_academy_monthly_usage set reserved_cost_micros_sgd=reserved_cost_micros_sgd-%s, actual_cost_micros_sgd=actual_cost_micros_sgd+%s, updated_at=now() where usage_month=%s",
            (reserved, actual_cost, month),
        )
        connection.execute(
            "update english_essay_feedback_reservations set status='committed', actual_cost_micros_sgd=%s, completed_at=now() where id=%s",
            (actual_cost, reservation["id"]),
        )
        PostgresEnglishEssayProviderFeedbackRepository._event(
            connection,
            reservation,
            "committed",
            request_id,
            {"actual_cost_micros_sgd": actual_cost},
        )

    @staticmethod
    def _release_reservation(connection, reservation: dict, request_id: str, reason: str):
        month = reservation["usage_month"]
        student = reservation["student_id"]
        reserved = reservation["reserved_cost_micros_sgd"]
        connection.execute(
            "update english_essay_feedback_monthly_usage set reserved_feedback=reserved_feedback-1, released_feedback=released_feedback+1, reserved_cost_micros_sgd=reserved_cost_micros_sgd-%s, updated_at=now() where student_id=%s and usage_month=%s",
            (reserved, student, month),
        )
        connection.execute(
            "update english_essay_feedback_academy_monthly_usage set reserved_cost_micros_sgd=reserved_cost_micros_sgd-%s, updated_at=now() where usage_month=%s",
            (reserved, month),
        )
        connection.execute(
            "update english_essay_feedback_reservations set status='released', completed_at=now() where id=%s",
            (reservation["id"],),
        )
        PostgresEnglishEssayProviderFeedbackRepository._event(
            connection,
            reservation,
            "released",
            request_id,
            {"reason": reason[:120]},
        )

    @staticmethod
    def _event(connection, reservation: dict, event_type: str, request_id: str, usage: dict):
        connection.execute(
            "insert into english_essay_feedback_usage_events(reservation_id, student_id, submission_id, event_type, request_id, usage) values (%s,%s,%s,%s,%s,%s)",
            (
                reservation["id"],
                reservation["student_id"],
                reservation["submission_id"],
                event_type,
                request_id,
                Jsonb(usage),
            ),
        )
