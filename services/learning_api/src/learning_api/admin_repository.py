"""Server-only beta operations and invitation administration."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .admin_contracts import CreateInvitationRequest, InvitationStatus
from .identity import AuthenticatedLearner
from .identity_repository import invitation_digest


class BetaOperationsError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


class PostgresBetaOperationsRepository:
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
    def _status_sql(alias: str = "invitations") -> str:
        return f"""
            case
                when {alias}.revoked_at is not null then 'revoked'
                when {alias}.use_count >= {alias}.max_uses then 'exhausted'
                when {alias}.expires_at <= now() then 'expired'
                else 'active'
            end
        """

    @staticmethod
    def _serialize(row: dict) -> dict:
        return {
            "invitation_id": row["invitation_id"],
            "email": row["email"],
            "course_key": row["course_key"],
            "course_revision": row["course_revision"],
            "status": row["status"],
            "max_uses": row["max_uses"],
            "use_count": row["use_count"],
            "expires_at": row["expires_at"],
            "revoked_at": row["revoked_at"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
        }

    def role_for(self, learner_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "select role::text as role from profiles where id = %s",
                (learner_id,),
            ).fetchone()
        return str(row["role"]) if row else None

    def create_invitation(
        self,
        administrator: AuthenticatedLearner,
        body: CreateInvitationRequest,
        request_id: str,
    ) -> dict:
        raw_code = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(days=body.expires_days)
        with self._connect() as connection:
            version = connection.execute(
                """
                select versions.id, versions.revision, courses.course_key
                from course_versions versions
                join courses on courses.id = versions.course_id
                where courses.course_key = %s and versions.is_current
                """,
                (body.course_key,),
            ).fetchone()
            if version is None:
                raise BetaOperationsError(
                    "course_not_found",
                    "The requested current course revision was not found.",
                    404,
                )
            row = connection.execute(
                f"""
                insert into beta_invitations (
                    token_sha256, email, course_version_id, max_uses,
                    expires_at, created_by
                ) values (%s, %s, %s, %s, %s, %s)
                returning id as invitation_id, email, max_uses, use_count,
                          expires_at, revoked_at, created_by, created_at,
                          {self._status_sql('beta_invitations')} as status
                """,
                (
                    invitation_digest(raw_code),
                    body.email,
                    version["id"],
                    body.max_uses,
                    expires_at,
                    administrator.learner_id,
                ),
            ).fetchone()
            assert row is not None
            connection.execute(
                """
                insert into beta_audit_events (
                    event_type, actor_user_id, invitation_id, request_id, metadata
                ) values ('invitation_created', %s, %s, %s, %s::jsonb)
                """,
                (
                    administrator.learner_id,
                    row["invitation_id"],
                    request_id,
                    Jsonb(
                        {
                            "course_key": version["course_key"],
                            "course_revision": version["revision"],
                            "max_uses": body.max_uses,
                            "expires_days": body.expires_days,
                        }
                    ),
                ),
            )
            invitation = {
                **dict(row),
                "course_key": version["course_key"],
                "course_revision": version["revision"],
            }
        return {**self._serialize(invitation), "invitation_code": raw_code}

    def list_invitations(
        self,
        *,
        status: InvitationStatus | None,
        limit: int,
        offset: int,
    ) -> dict:
        status_expression = self._status_sql()
        where = f"where ({status_expression}) = %s" if status else ""
        parameters: tuple = (status, limit, offset) if status else (limit, offset)
        count_parameters: tuple = (status,) if status else ()
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                select invitations.id as invitation_id, invitations.email,
                       courses.course_key, versions.revision as course_revision,
                       {status_expression} as status,
                       invitations.max_uses, invitations.use_count,
                       invitations.expires_at, invitations.revoked_at,
                       invitations.created_by, invitations.created_at
                from beta_invitations invitations
                join course_versions versions on versions.id = invitations.course_version_id
                join courses on courses.id = versions.course_id
                {where}
                order by invitations.created_at desc, invitations.id desc
                limit %s offset %s
                """,
                parameters,
            ).fetchall()
            total = connection.execute(
                f"select count(*) as total from beta_invitations invitations {where}",
                count_parameters,
            ).fetchone()["total"]
        return {
            "invitations": [self._serialize(dict(row)) for row in rows],
            "total": total,
        }

    def revoke_invitation(
        self,
        administrator: AuthenticatedLearner,
        invitation_id: UUID,
        request_id: str,
    ) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                f"""
                update beta_invitations
                set revoked_at = now()
                where id = %s and revoked_at is null
                returning id as invitation_id, email, course_version_id,
                          max_uses, use_count, expires_at, revoked_at,
                          created_by, created_at,
                          {self._status_sql('beta_invitations')} as status
                """,
                (invitation_id,),
            ).fetchone()
            revoked_now = row is not None
            if row is None:
                row = connection.execute(
                    f"""
                    select id as invitation_id, email, course_version_id,
                           max_uses, use_count, expires_at, revoked_at,
                           created_by, created_at,
                           {self._status_sql('beta_invitations')} as status
                    from beta_invitations
                    where id = %s
                    """,
                    (invitation_id,),
                ).fetchone()
            if row is None:
                raise BetaOperationsError(
                    "invitation_not_found", "The invitation was not found.", 404
                )
            version = connection.execute(
                """
                select courses.course_key, versions.revision as course_revision
                from course_versions versions
                join courses on courses.id = versions.course_id
                where versions.id = %s
                """,
                (row["course_version_id"],),
            ).fetchone()
            assert version is not None
            if revoked_now:
                connection.execute(
                    """
                    insert into beta_audit_events (
                        event_type, actor_user_id, invitation_id, request_id
                    ) values ('invitation_revoked', %s, %s, %s)
                    """,
                    (administrator.learner_id, invitation_id, request_id),
                )
            invitation = {**dict(row), **dict(version)}
        return self._serialize(invitation)

    def summary(self) -> dict:
        status_expression = self._status_sql()
        with self._connect() as connection:
            row = connection.execute(
                f"""
                select
                    (select count(*) from profiles where role = 'student') as total_students,
                    (select count(distinct student_id) from course_enrolments
                     where status = 'active') as active_students,
                    count(*) filter (where ({status_expression}) = 'active') as invitations_active,
                    count(*) filter (where ({status_expression}) = 'expired') as invitations_expired,
                    count(*) filter (where ({status_expression}) = 'exhausted') as invitations_exhausted,
                    count(*) filter (where ({status_expression}) = 'revoked') as invitations_revoked,
                    (select count(*) from course_enrolments
                     where enrolled_at >= now() - interval '7 days') as enrolments_last_7_days
                from beta_invitations invitations
                """
            ).fetchone()
        assert row is not None
        return dict(row)

    def audit_events(self, *, limit: int) -> dict:
        with self._connect() as connection:
            rows = connection.execute(
                """
                select id as event_id, event_type::text as event_type,
                       actor_user_id, invitation_id, target_user_id,
                       request_id, metadata, created_at
                from beta_audit_events
                order by created_at desc, id desc
                limit %s
                """,
                (limit,),
            ).fetchall()
        return {"events": [dict(row) for row in rows]}
