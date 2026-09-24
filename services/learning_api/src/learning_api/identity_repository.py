"""Server-side invitation onboarding backed by PostgreSQL."""

from __future__ import annotations

import hashlib
from typing import Protocol

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .identity import AuthenticatedLearner


class IdentityError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


class IdentityRepository(Protocol):
    def accept_invitation(
        self,
        learner: AuthenticatedLearner,
        invitation_code: str,
        display_name: str,
        request_id: str,
    ) -> dict: ...

    def current_learner(self, learner: AuthenticatedLearner) -> dict: ...


def invitation_digest(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


class PostgresIdentityRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(
            self.database_url,
            connect_timeout=10,
            row_factory=dict_row,
        )

    @staticmethod
    def _set_identity(connection, learner_id: str) -> None:
        connection.execute(
            "select set_config('request.jwt.claim.sub', %s, true)",
            (learner_id,),
        )

    @staticmethod
    def _response(connection, learner_id: str) -> dict:
        profile = connection.execute(
            """
            select profiles.id, users.email, profiles.display_name,
                   profiles.role::text as role, profiles.target_track
            from profiles
            join auth.users users on users.id = profiles.id
            where profiles.id = %s
            """,
            (learner_id,),
        ).fetchone()
        if profile is None:
            raise IdentityError(
                "onboarding_required",
                "Accept a valid beta invitation before using the course.",
                403,
            )
        enrolments = connection.execute(
            """
            select courses.course_key, versions.revision as course_revision,
                   enrolments.status::text as status, enrolments.enrolled_at
            from course_enrolments enrolments
            join courses on courses.id = enrolments.course_id
            join course_versions versions on versions.id = enrolments.course_version_id
            where enrolments.student_id = %s
            order by enrolments.enrolled_at, courses.course_key
            """,
            (learner_id,),
        ).fetchall()
        return {
            "profile": {
                "learner_id": str(profile["id"]),
                "email": profile["email"],
                "display_name": profile["display_name"],
                "role": profile["role"],
                "target_track": profile["target_track"],
            },
            "enrolments": [dict(row) for row in enrolments],
        }

    def accept_invitation(
        self,
        learner: AuthenticatedLearner,
        invitation_code: str,
        display_name: str,
        request_id: str,
    ) -> dict:
        if not learner.email:
            raise IdentityError(
                "verified_email_required",
                "A verified email address is required to accept an invitation.",
                409,
            )
        digest = invitation_digest(invitation_code)
        with self._connect() as connection:
            self._set_identity(connection, learner.learner_id)
            invitation = connection.execute(
                """
                select invitations.*, versions.course_id, courses.course_key,
                       versions.revision as course_revision
                from beta_invitations invitations
                join course_versions versions on versions.id = invitations.course_version_id
                join courses on courses.id = versions.course_id
                where invitations.token_sha256 = %s
                for update of invitations
                """,
                (digest,),
            ).fetchone()
            if invitation is None:
                raise IdentityError(
                    "invitation_invalid", "The beta invitation is invalid or expired.", 404
                )
            if invitation["email"].casefold() != learner.email.casefold():
                raise IdentityError(
                    "invitation_email_mismatch",
                    "Sign in with the email address that received this invitation.",
                    403,
                )
            existing = connection.execute(
                """
                select * from course_enrolments
                where student_id = %s and course_id = %s
                for update
                """,
                (learner.learner_id, invitation["course_id"]),
            ).fetchone()
            if existing is not None:
                if existing["course_version_id"] != invitation["course_version_id"]:
                    raise IdentityError(
                        "curriculum_migration_required",
                        "This learner is already pinned to another course revision.",
                        409,
                    )
                connection.execute(
                    """
                    update profiles set display_name = %s, updated_at = now()
                    where id = %s
                    """,
                    (display_name.strip(), learner.learner_id),
                )
                response = self._response(connection, learner.learner_id)
                return {"accepted": True, **response}
            if (
                invitation["revoked_at"] is not None
                or invitation["expires_at"] <= connection.execute(
                    "select now() as current_time"
                ).fetchone()["current_time"]
                or invitation["use_count"] >= invitation["max_uses"]
            ):
                raise IdentityError(
                    "invitation_invalid", "The beta invitation is invalid or expired.", 404
                )
            connection.execute(
                """
                insert into profiles (id, role, display_name, target_track)
                values (%s, 'student', %s, %s)
                on conflict (id) do update set
                    display_name = excluded.display_name,
                    target_track = coalesce(profiles.target_track, excluded.target_track),
                    updated_at = now()
                """,
                (
                    learner.learner_id,
                    display_name.strip(),
                    invitation["course_key"],
                ),
            )
            connection.execute(
                """
                insert into course_enrolments (
                    student_id, course_id, course_version_id, accepted_invitation_id
                ) values (%s, %s, %s, %s)
                """,
                (
                    learner.learner_id,
                    invitation["course_id"],
                    invitation["course_version_id"],
                    invitation["id"],
                ),
            )
            connection.execute(
                "update beta_invitations set use_count = use_count + 1 where id = %s",
                (invitation["id"],),
            )
            connection.execute(
                """
                insert into beta_audit_events (
                    event_type, actor_user_id, invitation_id,
                    target_user_id, request_id, metadata
                ) values ('invitation_accepted', %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    learner.learner_id,
                    invitation["id"],
                    learner.learner_id,
                    request_id,
                    Jsonb({"course_key": invitation["course_key"]}),
                ),
            )
            response = self._response(connection, learner.learner_id)
            return {"accepted": True, **response}

    def current_learner(self, learner: AuthenticatedLearner) -> dict:
        with self._connect() as connection:
            self._set_identity(connection, learner.learner_id)
            return self._response(connection, learner.learner_id)
