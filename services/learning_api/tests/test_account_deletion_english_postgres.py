from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from psycopg import sql
from test_english_learning import (
    _completed_essay_self_review,
    complete_diagnostic,
    create_checkpoint,
    create_session,
    diagnostic_answers,
    request,
    submit,
    submit_checkpoint,
)

from learning_api.account_deletion_repository import PostgresAccountDeletionRepository
from learning_api.config import Settings
from learning_api.english_essay_release import ConsentDecisionRequest
from learning_api.english_essay_release_repository import PostgresEnglishEssayReleaseRepository
from learning_api.identity import AuthenticatedLearner
from learning_api.main import create_app

ROOT = Path(__file__).resolve().parents[3]
SECRET = "account-deletion-test-secret-at-least-32-characters"
COUNT_NAMES = {
    "learner_lesson_progress": "lesson_progress",
    "learner_lesson_section_progress": "lesson_section_progress",
}


def _url() -> str:
    value = os.getenv("TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set TEST_DATABASE_URL to a migrated and imported disposable database")
    return value


def _student_tables(connection) -> list[str]:
    return [
        row[0]
        for row in connection.execute(
            """
            select columns.table_name from information_schema.columns columns
            join information_schema.tables tables
              on tables.table_schema = columns.table_schema
             and tables.table_name = columns.table_name
            where columns.table_schema = 'public' and columns.column_name = 'student_id'
              and tables.table_type = 'BASE TABLE'
            order by 1
            """
        )
    ]


def _rows_by_table(connection, learner_id: UUID) -> dict[str, int]:
    return {
        table: connection.execute(
            sql.SQL("select count(*) from {} where student_id = %s").format(
                sql.Identifier(table)
            ),
            (learner_id,),
        ).fetchone()[0]
        for table in _student_tables(connection)
    }


def _add_user(connection, user_id: UUID, role: str) -> str:
    email = f"{role}-{user_id}@example.test"
    connection.execute("insert into auth.users (id, email) values (%s, %s)", (user_id, email))
    connection.execute(
        "insert into profiles (id, email, display_name, role) values (%s, %s, %s, %s)",
        (user_id, email, role.title(), role),
    )
    return email


@pytest.mark.postgres
def test_deleting_a_learner_removes_every_learner_record():
    url = _url()
    learner_id, administrator_id = uuid4(), uuid4()
    with psycopg.connect(url) as connection:
        email = _add_user(connection, learner_id, "student")
        _add_user(connection, administrator_id, "academic_admin")
        connection.execute(
            """
            insert into course_enrolments (student_id, course_id, course_version_id)
            select %s, courses.id, versions.id
            from courses join course_versions versions on versions.course_id = courses.id
            where courses.course_key = 'g3-sec1-math' and versions.is_current
            """,
            (learner_id,),
        )

    app = create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=ROOT,
            allow_draft_content=True,
            development_learner_id=str(learner_id),
            rate_limits_enabled=False,
            database_url=url,
        )
    )

    created = create_session(app, f"practice-{learner_id}")
    assert created.status_code in (200, 201), created.text
    session_id = created.json()["session_id"]
    question = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next").json()[
        "question"
    ]
    attempt = submit(app, session_id, question, "wrong answer", f"attempt-{learner_id}")
    assert attempt.status_code == 200, attempt.text
    classified = request(
        app,
        "POST",
        f"/api/v1/english/attempts/{attempt.json()['attempt_id']}/error-classification",
        json={"category": "missed_clue"},
    )
    assert classified.status_code < 300, classified.text

    baseline = request(
        app,
        "POST",
        "/api/v1/english/diagnostic-sessions",
        headers={"Idempotency-Key": f"baseline-{learner_id}"},
        json={"expected_purpose": "baseline"},
    )
    assert baseline.status_code in (200, 201), baseline.text
    complete_diagnostic(app, baseline.json()["session_id"], f"baseline-{learner_id}")

    with psycopg.connect(url) as connection:
        for lesson_key in ("e1-lesson-01", "e1-lesson-06"):
            connection.execute(
                """
                insert into english_lesson_progress (
                    student_id, lesson_key, lesson_revision, state, question_count,
                    resolved_count, correct_count, incorrect_count
                ) values (%s, %s, 1, 'proficient', 1, 1, 1, 0)
                on conflict (student_id, lesson_key) do update set state = 'proficient'
                """,
                (learner_id, lesson_key),
            )
    checkpoint = create_checkpoint(app, f"checkpoint-{learner_id}")
    assert checkpoint.status_code in (200, 201), checkpoint.text
    checkpoint_id = checkpoint.json()["session_id"]
    checkpoint_question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{checkpoint_id}/next"
    ).json()["question"]
    checkpoint_attempt = submit_checkpoint(
        app,
        checkpoint_id,
        checkpoint_question,
        diagnostic_answers(checkpoint_question["stable_key"]),
        f"checkpoint-attempt-{learner_id}",
    )
    assert checkpoint_attempt.status_code == 200, checkpoint_attempt.text

    submission_id = _completed_essay_self_review(app, f"essay-{learner_id}")
    queued = request(
        app,
        "POST",
        f"/api/v1/english/essay-submissions/{submission_id}/marking-jobs",
        headers={"Idempotency-Key": f"marking-{learner_id}"},
    )
    assert queued.status_code == 202, queued.text
    assert (
        request(
            app, "GET", f"/api/v1/english/essay-submissions/{submission_id}/marking"
        ).status_code
        == 200
    )

    PostgresEnglishEssayReleaseRepository(url).record_consent(
        learner_id,
        ConsentDecisionRequest(
            action="granted",
            consent_policy_version="english-essay-consent-v1",
            guardian_reference_sha256="c" * 64,
            expires_at=datetime.now(UTC) + timedelta(days=30),
            reason="Guardian consent was verified through the private academy workflow.",
        ),
        str(administrator_id),
        f"consent-{learner_id}",
    )

    with psycopg.connect(url) as connection:
        before = _rows_by_table(connection, learner_id)
    for table in (
        "english_objective_attempts",
        "english_error_classifications",
        "english_diagnostic_attempts",
        "english_checkpoint_attempts",
        "english_essay_submissions",
        "english_essay_self_reviews",
        "english_essay_marking_feedback",
        "english_essay_processing_consent_events",
    ):
        assert before[table] > 0, table

    repository = PostgresAccountDeletionRepository(url, SECRET)
    preview = repository.preview(learner_id)
    for table, count in before.items():
        assert preview["counts"][COUNT_NAMES.get(table, table)] == count, table

    repository.execute(
        AuthenticatedLearner(str(administrator_id), "academic_admin"),
        learner_id,
        preview_token=preview["preview_token"],
        confirmation_email=email,
        reason="Learner requested permanent account deletion.",
        request_id=f"deletion-{learner_id}",
    )

    with psycopg.connect(url) as connection:
        remaining = {
            table: count
            for table, count in _rows_by_table(connection, learner_id).items()
            if count
        }
        assert remaining == {}
        assert (
            connection.execute(
                "select count(*) from auth.users where id = %s", (learner_id,)
            ).fetchone()[0]
            == 0
        )
