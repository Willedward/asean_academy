"""B2 spaced-retry and question-report integration tests on disposable PostgreSQL."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row
from question_bank.practice import PracticeError

from learning_api.course_catalogue import CourseCatalogue
from learning_api.postgres_practice import (
    PostgresPracticeEngine,
    _canonical_submission,
)
from learning_api.question_report_repository import (
    PostgresQuestionReportRepository,
    QuestionReportError,
)

ROOT = Path(__file__).resolve().parents[3]


def _database_url() -> str:
    value = os.getenv("TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set TEST_DATABASE_URL to a migrated and imported disposable database")
    return value


def _seed_users(connection, learner_id, administrator_id) -> None:
    learner_email = f"b2-{learner_id}@example.test"
    administrator_email = f"b2-{administrator_id}@example.test"
    connection.execute(
        "insert into auth.users (id, email) values (%s, %s), (%s, %s)",
        (learner_id, learner_email, administrator_id, administrator_email),
    )
    connection.execute(
        """
        insert into profiles (id, email, display_name, role)
        values (%s, %s, 'B2 learner', 'student'),
               (%s, %s, 'B2 administrator', 'academic_admin')
        """,
        (learner_id, learner_email, administrator_id, administrator_email),
    )


@pytest.mark.postgres
def test_due_cap_reserve_provenance_and_report_lifecycle() -> None:
    url = _database_url()
    learner_id, administrator_id, other_learner_id = uuid4(), uuid4(), uuid4()
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)
    questions = {question.stable_key: question for question in catalogue.questions}
    reserve_keys = [
        item.question_key
        for pool in catalogue.report.pools.pools
        if pool.type == "adaptive_reserve"
        for item in pool.items
    ]
    reserve_set = set(reserve_keys)
    pair = next(
        (
            (origin, questions[reserve_key])
            for origin in questions.values()
            if origin.stable_key not in reserve_set
            for reserve_key in reserve_keys
            if questions[reserve_key].primary_outcome == origin.primary_outcome
            and questions[reserve_key].difficulty == origin.difficulty
        ),
        None,
    )
    assert pair is not None, "The pilot bank needs at least one same-skill reserve variant"
    origin, expected_variant = pair
    extra_keys = [
        key
        for key in questions
        if key not in reserve_set and key != origin.stable_key
    ][:5]
    due_keys = [origin.stable_key, *extra_keys]
    assert len(due_keys) == 6

    with psycopg.connect(url, row_factory=dict_row) as connection:
        _seed_users(connection, learner_id, administrator_id)
        connection.execute(
            "insert into auth.users (id, email) values (%s, %s)",
            (other_learner_id, f"other-{other_learner_id}@example.test"),
        )
        connection.execute(
            """
            insert into profiles (id, email, display_name, role)
            values (%s, %s, 'Other learner', 'student')
            """,
            (other_learner_id, f"other-{other_learner_id}@example.test"),
        )
        rows = connection.execute(
            """
            select questions.id as question_id, questions.stable_key,
                   versions.id as version_id
            from math_questions questions
            join math_question_versions versions
              on versions.question_id = questions.id and versions.is_current
            where questions.stable_key = any(%s)
            """,
            (due_keys,),
        ).fetchall()
        identities = {row["stable_key"]: row for row in rows}
        now = datetime.now(UTC)
        for position, key in enumerate(due_keys):
            identity = identities[key]
            connection.execute(
                """
                insert into question_progress (
                    student_id, question_id, latest_question_version_id, state,
                    attempts_total, incorrect_total, last_attempted_at, due_at,
                    interval_days, review_stage, review_streak, last_resolution
                ) values (%s, %s, %s, 'queued_for_retry', 1, 1, %s, %s,
                          7, %s, 1, 'clean_correct')
                """,
                (
                    learner_id,
                    identity["question_id"],
                    identity["version_id"],
                    now - timedelta(days=10 - position),
                    now - timedelta(days=9 - position),
                    1 if key == origin.stable_key else 0,
                ),
            )

    engine = PostgresPracticeEngine(
        url, catalogue.questions, str(learner_id), allow_drafts=True
    )
    assignments = engine.retry_assignments(due_keys, reserve_keys)
    assert len(assignments) == 5
    assert assignments[0] == {
        "served_key": expected_variant.stable_key,
        "origin_key": origin.stable_key,
    }

    created = engine.create_session(
        question_count=1,
        ordered_question_keys=[expected_variant.stable_key],
        context={
            "lesson_key": "n1-lesson-01",
            "mode": "retry_review",
            "selection_reason": "required_retry",
            "stages": {expected_variant.stable_key: "adaptive"},
            "retry_origins": {
                expected_variant.stable_key: origin.stable_key,
            },
        },
        idempotency_key=str(uuid4()),
    )
    current = engine.next_question(created["session_id"])
    assert current["question"]["stable_key"] == expected_variant.stable_key
    with psycopg.connect(url, row_factory=dict_row) as connection:
        linked = connection.execute(
            """
            select origin.stable_key
            from session_questions assigned
            join math_questions origin on origin.id = assigned.retry_origin_question_id
            where assigned.practice_session_id = %s
            """,
            (created["session_id"],),
        ).fetchone()
    assert linked["stable_key"] == origin.stable_key

    engine.create_session(
        question_count=4,
        ordered_question_keys=extra_keys[:4],
        context={
            "lesson_key": "n1-lesson-02",
            "mode": "retry_review",
            "selection_reason": "required_retry",
        },
        idempotency_key=str(uuid4()),
    )
    with pytest.raises(PracticeError) as capped:
        engine.create_session(
            question_count=1,
            ordered_question_keys=[extra_keys[4]],
            context={
                "lesson_key": "n1-lesson-03",
                "mode": "retry_review",
                "selection_reason": "required_retry",
            },
            idempotency_key=str(uuid4()),
        )
    assert capped.value.code == "retry_daily_cap_reached"

    report_repository = PostgresQuestionReportRepository(url)
    report = report_repository.create(
        str(learner_id),
        session_id=created["session_id"],
        question_key=expected_variant.stable_key,
        question_revision=expected_variant.revision,
        category="unclear_wording",
        comment="I could not tell which form the answer should use.",
        request_id="b2-report-create",
    )
    report_id = str(report["report_id"])
    assert report_repository.learner_get(str(learner_id), report_id)["status"] == "open"
    assert report_repository.admin_get(report_id)["learner_id"] == learner_id
    with pytest.raises(QuestionReportError) as hidden:
        report_repository.learner_get(str(other_learner_id), report_id)
    assert hidden.value.status == 404
    assert report_repository.admin_list(status="open", limit=25, offset=0)["total"] >= 1

    in_review = report_repository.resolve(
        report_id,
        status="in_review",
        resolution=None,
        administrator_id=str(administrator_id),
        request_id="b2-report-review",
    )
    assert in_review["status"] == "in_review"
    resolved = report_repository.resolve(
        report_id,
        status="resolved",
        resolution="Clarified in the next revision.",
        administrator_id=str(administrator_id),
        request_id="b2-report-resolve",
    )
    assert resolved["status"] == "resolved"

    answers = {
        str(part.position): _canonical_submission(part.response)
        for part in expected_variant.parts
    }
    result = engine.submit_attempt(
        session_id=created["session_id"],
        stable_key=expected_variant.stable_key,
        revision=expected_variant.revision,
        answers=answers,
        idempotency_key=str(uuid4()),
    )
    assert result["correct"]
    with psycopg.connect(url, row_factory=dict_row) as connection:
        scheduled = connection.execute(
            """
            select questions.stable_key, progress.interval_days, progress.review_stage,
                   progress.due_at > now() as is_future
            from question_progress progress
            join math_questions questions on questions.id = progress.question_id
            where progress.student_id = %s and questions.stable_key = %s
            """,
            (learner_id, origin.stable_key),
        ).fetchone()
        audit = connection.execute(
            """
            select metadata::text
            from beta_audit_events
            where target_user_id = %s and event_type = 'question_report_created'
            order by created_at desc limit 1
            """,
            (learner_id,),
        ).fetchone()
    assert scheduled == {
        "stable_key": origin.stable_key,
        "interval_days": 14,
        "review_stage": 2,
        "is_future": True,
    }
    assert "answer" not in audit["metadata"].lower()

