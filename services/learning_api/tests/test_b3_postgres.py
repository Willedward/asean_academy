"""B3 account-deletion integration tests against disposable PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row
from question_bank.models import NumericResponse

from learning_api.account_deletion_repository import PostgresAccountDeletionRepository
from learning_api.admin_repository import BetaOperationsError
from learning_api.course_catalogue import CourseCatalogue
from learning_api.identity import AuthenticatedLearner
from learning_api.postgres_practice import PostgresPracticeEngine
from learning_api.question_report_repository import PostgresQuestionReportRepository

ROOT = Path(__file__).resolve().parents[3]


def _url() -> str:
    value = os.getenv("TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set TEST_DATABASE_URL to a migrated and imported disposable database")
    return value


def _answer(response) -> str:
    if isinstance(response, NumericResponse):
        return response.canonical_answer
    if response.comparison_mode == "prime_factorisation":
        return response.canonical_latex
    return response.canonical_expression


@pytest.mark.postgres
def test_preview_then_delete_removes_private_learning_data_and_keeps_pseudonymous_audit():
    url = _url()
    learner_id, administrator_id = uuid4(), uuid4()
    learner_email = f"delete-{learner_id}@example.test"
    report_request_id = f"b3-report-{uuid4()}"
    deletion_request_id = f"b3-delete-{uuid4()}"
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)
    question = catalogue.questions[0]

    with psycopg.connect(url, row_factory=dict_row) as connection:
        for user_id, email, role in (
            (learner_id, learner_email, "student"),
            (administrator_id, f"admin-{administrator_id}@example.test", "academic_admin"),
        ):
            connection.execute(
                "insert into auth.users (id, email) values (%s, %s)",
                (user_id, email),
            )
            connection.execute(
                """
                insert into profiles (id, email, display_name, role)
                values (%s, %s, %s, %s)
                """,
                (user_id, email, role.title(), role),
            )
        course = connection.execute(
            """
            select courses.id as course_id, versions.id as version_id
            from courses join course_versions versions on versions.course_id = courses.id
            where courses.course_key = 'g3-sec1-math' and versions.is_current
            """
        ).fetchone()
        connection.execute(
            """
            insert into course_enrolments (student_id, course_id, course_version_id)
            values (%s, %s, %s)
            """,
            (learner_id, course["course_id"], course["version_id"]),
        )

    engine = PostgresPracticeEngine(
        url, catalogue.questions, str(learner_id), allow_drafts=True
    )
    session = engine.create_session(
        question_count=1,
        ordered_question_keys=[question.stable_key],
        context={
            "lesson_key": "n1-lesson-01",
            "mode": "guided_practice",
            "selection_reason": "configured_lesson_pool",
        },
        idempotency_key=str(uuid4()),
    )
    engine.next_question(session["session_id"])
    answers = {
        str(part.position): _answer(part.response)
        for part in question.parts
    }
    assert engine.submit_attempt(
        session_id=session["session_id"],
        stable_key=question.stable_key,
        revision=question.revision,
        answers=answers,
        idempotency_key=str(uuid4()),
    )["correct"]

    report_repository = PostgresQuestionReportRepository(url)
    report_repository.create(
        str(learner_id),
        session_id=session["session_id"],
        question_key=question.stable_key,
        question_revision=question.revision,
        category="display_problem",
        comment="The mathematical expression wrapped on my screen.",
        request_id=report_request_id,
    )
    with psycopg.connect(url) as connection:
        connection.execute(
            """
            insert into mastery_events (
                student_id, event_type, source_practice_session_id, evidence
            ) values (%s, 'lesson_proficient', %s, '{}'::jsonb)
            """,
            (learner_id, session["session_id"]),
        )

    repository = PostgresAccountDeletionRepository(url, "b3-test-secret")
    preview = repository.preview(learner_id)
    assert preview["counts"]["attempts"] == 1
    assert preview["counts"]["mastery_events"] == 1
    assert preview["counts"]["question_reports"] == 1

    with pytest.raises(BetaOperationsError) as mismatch:
        repository.execute(
            AuthenticatedLearner(str(administrator_id), "academic_admin"),
            learner_id,
            preview_token=preview["preview_token"],
            confirmation_email="different@example.test",
            reason="This confirmation must be rejected.",
            request_id=f"b3-mismatch-{uuid4()}",
        )
    assert mismatch.value.code == "deletion_confirmation_mismatch"

    result = repository.execute(
        AuthenticatedLearner(str(administrator_id), "academic_admin"),
        learner_id,
        preview_token=preview["preview_token"],
        confirmation_email=learner_email.upper(),
        reason="Learner requested permanent account deletion.",
        request_id=deletion_request_id,
    )
    assert result["deleted"]
    assert learner_email not in str(result)

    with psycopg.connect(url, row_factory=dict_row) as connection:
        remaining = {
            "auth": connection.execute(
                "select count(*) from auth.users where id = %s", (learner_id,)
            ).fetchone()["count"],
            "profiles": connection.execute(
                "select count(*) from profiles where id = %s", (learner_id,)
            ).fetchone()["count"],
            "attempts": connection.execute(
                "select count(*) from attempts where student_id = %s", (learner_id,)
            ).fetchone()["count"],
            "mastery": connection.execute(
                "select count(*) from mastery_events where student_id = %s", (learner_id,)
            ).fetchone()["count"],
            "reports": connection.execute(
                "select count(*) from question_reports where student_id = %s", (learner_id,)
            ).fetchone()["count"],
        }
        record = connection.execute(
            """
            select target_user_id, target_reference, email_reference, preview_counts
            from account_deletion_records
            where request_id = %s
            """,
            (deletion_request_id,),
        ).fetchone()
        audit = connection.execute(
            """
            select actor_user_id, target_user_id, metadata::text
            from beta_audit_events
            where request_id = %s
            """,
            (deletion_request_id,),
        ).fetchone()
    assert set(remaining.values()) == {0}
    assert record["target_user_id"] is None
    assert record["target_reference"] == result["target_reference"]
    assert learner_email not in str(record)
    assert audit["actor_user_id"] == administrator_id
    assert audit["target_user_id"] is None
    assert learner_email not in audit["metadata"]

