"""Two-step academic-admin learner deletion with pseudonymous evidence."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .admin_repository import BetaOperationsError
from .identity import AuthenticatedLearner


class PostgresAccountDeletionRepository:
    PREVIEW_LIFETIME = timedelta(minutes=15)
    RETAINED_RECORDS = [
        "pseudonymous account deletion completion record",
        "audit events with learner references set to null",
        "HMAC-only security and rate-limit evidence until scheduled retention expiry",
        "provider backups until their configured expiry",
    ]

    def __init__(self, database_url: str, signing_secret: str):
        self.database_url = database_url
        self.secret = signing_secret.encode("utf-8")

    def _connect(self):
        return psycopg.connect(
            self.database_url,
            connect_timeout=10,
            prepare_threshold=None,
            row_factory=dict_row,
        )

    @staticmethod
    def _counts(connection, learner_id: str) -> dict[str, int]:
        row = connection.execute(
            """
            select
                (select count(*) from auth.users where id = %(learner_id)s)::integer
                    as auth_accounts,
                (select count(*) from profiles where id = %(learner_id)s)::integer
                    as profiles,
                (select count(*) from course_enrolments
                 where student_id = %(learner_id)s)::integer as course_enrolments,
                (select count(*) from practice_sessions
                 where student_id = %(learner_id)s)::integer as practice_sessions,
                (select count(*) from session_questions questions
                 join practice_sessions sessions on sessions.id = questions.practice_session_id
                 where sessions.student_id = %(learner_id)s)::integer
                    as session_questions,
                (select count(*) from attempts
                 where student_id = %(learner_id)s)::integer as attempts,
                (select count(*) from question_progress
                 where student_id = %(learner_id)s)::integer as question_progress,
                (select count(*) from learner_lesson_progress
                 where student_id = %(learner_id)s)::integer as lesson_progress,
                (select count(*) from learner_lesson_section_progress
                 where student_id = %(learner_id)s)::integer as lesson_section_progress,
                (select count(*) from mastery_events
                 where student_id = %(learner_id)s)::integer as mastery_events,
                (select count(*) from diagnostic_sessions
                 where student_id = %(learner_id)s)::integer as diagnostic_sessions,
                (select count(*) from diagnostic_responses responses
                 join diagnostic_sessions sessions on sessions.id = responses.session_id
                 where sessions.student_id = %(learner_id)s)::integer
                    as diagnostic_responses,
                (select count(*) from diagnostic_response_idempotency_keys keys
                 join diagnostic_sessions sessions on sessions.id = keys.session_id
                 where sessions.student_id = %(learner_id)s)::integer
                    as diagnostic_response_idempotency_keys,
                (select count(*) from diagnostic_results
                 where student_id = %(learner_id)s)::integer as diagnostic_results,
                (select count(*) from diagnostic_resets
                 where student_id = %(learner_id)s)::integer as diagnostic_resets,
                (select count(*) from question_reports
                 where student_id = %(learner_id)s)::integer as question_reports,
                (select count(*) from tutor_sessions
                 where student_id = %(learner_id)s)::integer as tutor_sessions,
                (select count(*) from tutor_messages
                 where student_id = %(learner_id)s)::integer as tutor_messages,
                (select count(*) from tutor_usage_reservations
                 where student_id = %(learner_id)s)::integer as tutor_usage_reservations,
                (select count(*) from tutor_usage_events
                 where student_id = %(learner_id)s)::integer as tutor_usage_events,
                (select count(*) from tutor_route_decisions
                 where student_id = %(learner_id)s)::integer as tutor_route_decisions,
                (select count(*) from beta_audit_events
                 where actor_user_id = %(learner_id)s
                    or target_user_id = %(learner_id)s)::integer
                    as audit_references_retained
            """,
            {"learner_id": learner_id},
        ).fetchone()
        assert row is not None
        return dict(row)

    def _student(self, connection, learner_id: str, *, lock: bool = False):
        suffix = " for update" if lock else ""
        row = connection.execute(
            """
            select id, email, display_name, role::text as role
            from profiles where id = %s
            """ + suffix,
            (learner_id,),
        ).fetchone()
        if row is None or row["role"] != "student":
            raise BetaOperationsError(
                "student_not_found",
                "The requested student account was not found.",
                404,
            )
        return row

    def _reference(self, prefix: str, value: str) -> str:
        return hmac.new(
            self.secret,
            f"{prefix}:{value}".encode(),
            hashlib.sha256,
        ).hexdigest()

    def _snapshot(self, learner_id: str, email: str, counts: dict[str, int]) -> str:
        value = json.dumps(
            {
                "learner_id": learner_id,
                "email": email,
                "counts": counts,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(value).hexdigest()

    def _sign(self, payload: dict) -> str:
        encoded = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).rstrip(b"=")
        signature = hmac.new(self.secret, encoded, hashlib.sha256).hexdigest()
        return f"{encoded.decode('ascii')}.{signature}"

    def _verify(self, token: str) -> dict:
        try:
            encoded, supplied = token.rsplit(".", 1)
            expected = hmac.new(
                self.secret, encoded.encode("ascii"), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(supplied, expected):
                raise ValueError
            padding = "=" * (-len(encoded) % 4)
            payload = json.loads(
                base64.urlsafe_b64decode(encoded + padding).decode("utf-8")
            )
            if int(payload["expires_at"]) < int(datetime.now(UTC).timestamp()):
                raise BetaOperationsError(
                    "deletion_preview_expired",
                    "The deletion preview expired. Generate a new preview.",
                    409,
                )
            return payload
        except BetaOperationsError:
            raise
        except (ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
            raise BetaOperationsError(
                "invalid_deletion_preview",
                "The deletion preview token is invalid.",
                409,
            ) from exc

    def preview(self, learner_id: UUID) -> dict:
        with self._connect() as connection:
            student = self._student(connection, str(learner_id))
            counts = self._counts(connection, str(learner_id))
        email = student["email"].strip().casefold()
        expires_at = datetime.now(UTC) + self.PREVIEW_LIFETIME
        token = self._sign(
            {
                "learner_id": str(learner_id),
                "snapshot": self._snapshot(str(learner_id), email, counts),
                "expires_at": int(expires_at.timestamp()),
            }
        )
        return {
            "learner_id": learner_id,
            "email": email,
            "display_name": student["display_name"],
            "counts": counts,
            "retained_records": self.RETAINED_RECORDS,
            "preview_token": token,
            "expires_at": expires_at,
            "confirmation_value": email,
        }

    def execute(
        self,
        administrator: AuthenticatedLearner,
        learner_id: UUID,
        *,
        preview_token: str,
        confirmation_email: str,
        reason: str,
        request_id: str,
    ) -> dict:
        if administrator.learner_id == str(learner_id):
            raise BetaOperationsError(
                "self_deletion_forbidden",
                "Administrators cannot delete their own account through this operation.",
                409,
            )
        payload = self._verify(preview_token)
        if payload.get("learner_id") != str(learner_id):
            raise BetaOperationsError(
                "deletion_preview_target_mismatch",
                "The preview was created for a different learner.",
                409,
            )
        with self._connect() as connection:
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"account-deletion:{learner_id}",),
            )
            student = self._student(connection, str(learner_id), lock=True)
            email = student["email"].strip().casefold()
            counts = self._counts(connection, str(learner_id))
            if not hmac.compare_digest(confirmation_email.strip().casefold(), email):
                raise BetaOperationsError(
                    "deletion_confirmation_mismatch",
                    "The confirmation email does not match the learner account.",
                    409,
                )
            current_snapshot = self._snapshot(str(learner_id), email, counts)
            if not hmac.compare_digest(str(payload.get("snapshot", "")), current_snapshot):
                raise BetaOperationsError(
                    "deletion_preview_stale",
                    "Learner data changed after the preview. Generate a new preview.",
                    409,
                )
            target_reference = self._reference("learner", str(learner_id))
            email_reference = self._reference("email", email)
            completed_at = datetime.now(UTC)
            connection.execute(
                """
                insert into account_deletion_records (
                    target_user_id, target_reference, email_reference, requested_by,
                    reason, preview_counts, request_id, completed_at
                ) values (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    learner_id,
                    target_reference,
                    email_reference,
                    administrator.learner_id,
                    reason.strip(),
                    Jsonb(counts),
                    request_id,
                    completed_at,
                ),
            )
            connection.execute(
                """
                insert into beta_audit_events (
                    event_type, actor_user_id, target_user_id, request_id, metadata
                ) values ('account_deletion_completed', %s, %s, %s, %s)
                """,
                (
                    administrator.learner_id,
                    learner_id,
                    request_id,
                    Jsonb(
                        {
                            "target_reference": target_reference,
                            "record_categories": sorted(counts),
                        }
                    ),
                ),
            )
            connection.execute(
                "select set_config('app.account_deletion_target', %s, true)",
                (str(learner_id),),
            )
            deleted = connection.execute(
                "delete from auth.users where id = %s returning id",
                (learner_id,),
            ).fetchone()
            if deleted is None:
                raise BetaOperationsError(
                    "student_not_found",
                    "The requested student account was not found.",
                    404,
                )
        return {
            "deleted": True,
            "target_reference": target_reference,
            "completed_at": completed_at,
            "retained_records": self.RETAINED_RECORDS,
        }
