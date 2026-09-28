"""Seed fixed identities and invitations into a fresh local E2E database."""

from __future__ import annotations

import hashlib
import os
from urllib.parse import urlparse

import psycopg

ACADEMIC_ADMIN_ID = "10000000-0000-4000-8000-000000000001"
CONTENT_ADMIN_ID = "10000000-0000-4000-8000-000000000002"
STUDENT_A_ID = "20000000-0000-4000-8000-000000000001"
STUDENT_B_ID = "20000000-0000-4000-8000-000000000002"

ACADEMIC_ADMIN_EMAIL = "academic.e2e@example.test"
CONTENT_ADMIN_EMAIL = "content.e2e@example.test"
STUDENT_A_EMAIL = "student.a.e2e@example.test"
STUDENT_B_EMAIL = "student.b.e2e@example.test"

STUDENT_A_CODE = "e2e-student-a-invitation-2026"
STUDENT_B_CODE = "e2e-student-b-invitation-2026"


def _database_url() -> str:
    value = os.getenv("E2E_DATABASE_URL", "").strip()
    if not value:
        raise SystemExit("Set E2E_DATABASE_URL to a fresh disposable local PostgreSQL database.")
    parsed = urlparse(value)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("E2E_DATABASE_URL must point to local PostgreSQL.")
    if "e2e" not in parsed.path.casefold():
        raise SystemExit("The disposable database name must contain 'e2e'.")
    return value


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def main() -> None:
    database_url = _database_url()
    identities = (
        (ACADEMIC_ADMIN_ID, ACADEMIC_ADMIN_EMAIL, "academic_admin"),
        (CONTENT_ADMIN_ID, CONTENT_ADMIN_EMAIL, "content_admin"),
    )
    students = (
        (STUDENT_A_ID, STUDENT_A_EMAIL, STUDENT_A_CODE),
        (STUDENT_B_ID, STUDENT_B_EMAIL, STUDENT_B_CODE),
    )
    with psycopg.connect(database_url) as connection:
        existing = connection.execute(
            "select count(*) from auth.users where id = any(%s::uuid[])",
            ([row[0] for row in (*identities, *students)],),
        ).fetchone()[0]
        if existing:
            raise SystemExit("The E2E database already contains fixture identities; recreate it.")
        version = connection.execute(
            """
            select versions.id
            from course_versions versions
            join courses on courses.id = versions.course_id
            where courses.course_key = 'g3-sec1-math' and versions.is_current
            """
        ).fetchone()
        if version is None:
            raise SystemExit("Import the current course catalogue before seeding E2E identities.")
        for user_id, email, role in identities:
            connection.execute(
                "insert into auth.users(id, email) values (%s, %s)", (user_id, email)
            )
            connection.execute(
                """
                insert into profiles(id, email, display_name, role)
                values (%s, %s, %s, %s)
                """,
                (user_id, email, role.replace("_", " ").title(), role),
            )
        for user_id, email, invitation_code in students:
            connection.execute(
                "insert into auth.users(id, email) values (%s, %s)", (user_id, email)
            )
            connection.execute(
                """
                insert into beta_invitations(
                    token_sha256, email, course_version_id, max_uses,
                    expires_at, created_by
                ) values (%s, %s, %s, 1, now() + interval '1 day', %s)
                """,
                (_digest(invitation_code), email, version[0], ACADEMIC_ADMIN_ID),
            )
    print("Seeded two administrators and two invitation-only learners.")


if __name__ == "__main__":
    main()
