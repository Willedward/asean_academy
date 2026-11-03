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
# Sec 3-entry scholarship track journeys (apps/web/e2e/sec3-entry-*.spec.ts).
SEC3_TWO_COURSE_ID = "30000000-0000-4000-8000-000000000001"
SEC3_MASTERY_ID = "30000000-0000-4000-8000-000000000002"
SEC3_SUPPORT_ID = "30000000-0000-4000-8000-000000000003"
SEC3_REVIEW_ID = "30000000-0000-4000-8000-000000000004"

ACADEMIC_ADMIN_EMAIL = "academic.e2e@example.test"
CONTENT_ADMIN_EMAIL = "content.e2e@example.test"
STUDENT_A_EMAIL = "student.a.e2e@example.test"
STUDENT_B_EMAIL = "student.b.e2e@example.test"
SEC3_TWO_COURSE_EMAIL = "sec3.two-course.e2e@example.test"
SEC3_MASTERY_EMAIL = "sec3.mastery.e2e@example.test"
SEC3_SUPPORT_EMAIL = "sec3.support.e2e@example.test"
SEC3_REVIEW_EMAIL = "sec3.review.e2e@example.test"

STUDENT_A_CODE = "e2e-student-a-invitation-2026"
STUDENT_B_CODE = "e2e-student-b-invitation-2026"
SEC3_TWO_COURSE_SEC1_CODE = "e2e-sec3-two-course-sec1-invitation-2026"
SEC3_TWO_COURSE_SEC2_CODE = "e2e-sec3-two-course-sec2-invitation-2026"
SEC3_MASTERY_CODE = "e2e-sec3-mastery-invitation-2026"
SEC3_SUPPORT_CODE = "e2e-sec3-support-invitation-2026"
SEC3_REVIEW_CODE = "e2e-sec3-review-invitation-2026"

# The review learner starts with one Give up that became due an hour ago. The API
# trusts database time and has no test clock, so a one-shot seed is the only way to
# exercise a due spaced review without sleeping for the two-day interval.
SEC3_REVIEW_DUE_QUESTION_KEY = "n1-l1-01"


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


def _current_course_version(connection, course_key: str):
    row = connection.execute(
        """
        select versions.id
        from course_versions versions
        join courses on courses.id = versions.course_id
        where courses.course_key = %s and versions.is_current
        """,
        (course_key,),
    ).fetchone()
    return None if row is None else row[0]


def main() -> None:
    database_url = _database_url()
    identities = (
        (ACADEMIC_ADMIN_ID, ACADEMIC_ADMIN_EMAIL, "academic_admin"),
        (CONTENT_ADMIN_ID, CONTENT_ADMIN_EMAIL, "content_admin"),
    )
    students = (
        (STUDENT_A_ID, STUDENT_A_EMAIL, STUDENT_A_CODE),
        (STUDENT_B_ID, STUDENT_B_EMAIL, STUDENT_B_CODE),
        (SEC3_TWO_COURSE_ID, SEC3_TWO_COURSE_EMAIL, SEC3_TWO_COURSE_SEC1_CODE),
        (SEC3_MASTERY_ID, SEC3_MASTERY_EMAIL, SEC3_MASTERY_CODE),
        (SEC3_SUPPORT_ID, SEC3_SUPPORT_EMAIL, SEC3_SUPPORT_CODE),
        (SEC3_REVIEW_ID, SEC3_REVIEW_EMAIL, SEC3_REVIEW_CODE),
    )
    with psycopg.connect(database_url) as connection:
        existing = connection.execute(
            "select count(*) from auth.users where id = any(%s::uuid[])",
            ([row[0] for row in (*identities, *students)],),
        ).fetchone()[0]
        if existing:
            raise SystemExit("The E2E database already contains fixture identities; recreate it.")
        sec1_version = _current_course_version(connection, "g3-sec1-math")
        if sec1_version is None:
            raise SystemExit("Import the current course catalogue before seeding E2E identities.")
        sec2_version = _current_course_version(connection, "g3-sec2-math")
        if sec2_version is None:
            raise SystemExit("Import both Mathematics courses before seeding E2E identities.")
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
                (_digest(invitation_code), email, sec1_version, ACADEMIC_ADMIN_ID),
            )
        connection.execute(
            """
            insert into beta_invitations(
                token_sha256, email, course_version_id, max_uses,
                expires_at, created_by
            ) values (%s, %s, %s, 1, now() + interval '1 day', %s)
            """,
            (
                _digest(SEC3_TWO_COURSE_SEC2_CODE),
                SEC3_TWO_COURSE_EMAIL,
                sec2_version,
                ACADEMIC_ADMIN_ID,
            ),
        )
        seeded_review = connection.execute(
            """
            insert into question_progress(
                student_id, question_id, latest_question_version_id, state,
                attempts_total, incorrect_total, last_attempted_at, due_at,
                interval_days, review_stage, review_streak, last_resolution
            )
            select %s, questions.id, versions.id, 'gave_up',
                   2, 2, now() - interval '2 days 1 hour', now() - interval '1 hour',
                   2, 0, 0, 'gave_up'
            from math_questions questions
            join math_question_versions versions on versions.question_id = questions.id
            where questions.stable_key = %s and versions.is_current
            """,
            (SEC3_REVIEW_ID, SEC3_REVIEW_DUE_QUESTION_KEY),
        ).rowcount
        if seeded_review != 1:
            raise SystemExit("Import the question catalogue before seeding E2E identities.")
    print(f"Seeded two administrators and {len(students)} invitation-only learners.")


if __name__ == "__main__":
    main()
