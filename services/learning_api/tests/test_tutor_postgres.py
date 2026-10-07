"""Opt-in PostgreSQL proof for tutor grounding, locks and atomic accounting."""

from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest

from learning_api.tutor_repository import (
    PostgresTutorRepository,
    TutorError,
    TutorLimits,
    UsageActual,
)


def _database_url() -> str:
    value = os.environ.get("TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set TEST_DATABASE_URL to a migrated, imported disposable database")
    return value


@pytest.mark.postgres
def test_postgres_tutor_pins_grounding_and_reconciles_reserved_usage():
    database_url = _database_url()
    learner_id = str(uuid4())
    practice_session_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "insert into auth.users (id, email) values (%s, %s)",
            (learner_id, f"{learner_id}@example.test"),
        )
        source = connection.execute(
            """
            select banks.id as bank_id, versions.id as question_version_id,
                   questions.status::text as question_status,
                   lesson_versions.status::text as lesson_status
            from math_questions questions
            join math_question_banks banks on banks.id=questions.bank_id
            join math_question_versions versions
              on versions.question_id=questions.id and versions.is_current
            cross join course_lessons lessons
            join lesson_versions
              on lesson_versions.lesson_id=lessons.id and lesson_versions.is_current
            where questions.stable_key='n1-l1-01'
              and lessons.lesson_key='n1-lesson-01'
            """
        ).fetchone()
        assert source is not None, "Import questions and course content before this test"
        connection.execute(
            "update math_questions set status='published' where stable_key='n1-l1-01'"
        )
        connection.execute(
            """
            update lesson_versions set status='published'
            where lesson_id=(select id from course_lessons where lesson_key='n1-lesson-01')
              and is_current
            """
        )
        connection.execute(
            """
            insert into practice_sessions (
                id, student_id, bank_id, requested_question_count, scope
            ) values (%s, %s, %s, 1, '{"lesson_key":"n1-lesson-01"}'::jsonb)
            """,
            (practice_session_id, learner_id, source[0]),
        )
        connection.execute(
            """
            insert into session_questions (
                practice_session_id, question_version_id, position, selection_reason
            ) values (%s, %s, 1, 'unseen')
            """,
            (practice_session_id, source[1]),
        )

    repository = PostgresTutorRepository(database_url)
    limits = TutorLimits(
        daily_messages=10,
        daily_tokens=20_000,
        monthly_cost_micros_sgd=7_000_000,
        academy_monthly_cost_micros_sgd=7_000_000_000,
        max_input_tokens=5_000,
        max_output_tokens=1_000,
        max_turn_cost_micros_sgd=250_000,
    )
    try:
        session = repository.create_session(
            learner_id,
            practice_session_id=practice_session_id,
            question_key="n1-l1-01",
            question_revision=1,
            model_policy_version="test-policy-v1",
        )
        assert session["answer_lock_state"] == {
            "answer_locked": True,
            "solution_locked": True,
        }
        grounding = repository.grounding(learner_id, session["session_id"])
        assert grounding.answer_lock_state.answer_locked is True
        assert grounding.unlocked_solution_blocks == ()
        assert grounding.latest_attempt is None
        assert grounding.leakage_answers

        with psycopg.connect(database_url) as connection:
            assignment = connection.execute(
                """
                select id, question_version_id from session_questions
                where practice_session_id=%s
                """,
                (practice_session_id,),
            ).fetchone()
            connection.execute(
                """
                insert into attempts (
                    student_id, session_question_id, question_version_id, attempt_number,
                    idempotency_key, answers, result, is_correct, marks_awarded
                ) values (
                    %s, %s, %s, 1, %s, '{"1":"learner response"}'::jsonb,
                    '{"parts":[{"position":1,"correct":false,"error":null,"marks_awarded":0,"marks_available":1,"canonical_answer":"must not escape"}],"marks_available":1,"canonical_answer":"must not escape"}'::jsonb,
                    false, 0
                )
                """,
                (learner_id, assignment[0], assignment[1], str(uuid4())),
            )
        attempt_grounding = repository.grounding(learner_id, session["session_id"])
        assert attempt_grounding.latest_attempt == {
            "attempt_number": 1,
            "submitted_answers": {"1": "learner response"},
            "correct": False,
            "parts": [
                {
                    "position": 1,
                    "correct": False,
                    "error": None,
                    "marks_awarded": 0,
                    "marks_available": 1,
                }
            ],
            "marks_awarded": 0,
            "marks_available": 1,
        }

        reserved = repository.reserve(
            learner_id, session["session_id"], limits, request_id="reserve-test"
        )
        with pytest.raises(TutorError, match="current tutor response") as concurrent:
            repository.reserve(
                learner_id, session["session_id"], limits, request_id="concurrent-test"
            )
        assert concurrent.value.code == "tutor_generation_in_progress"
        quota = repository.reconcile(
            reserved,
            UsageActual(input_tokens=100, output_tokens=50, cost_micros_sgd=1_000),
            limits,
            request_id="reconcile-test",
        )
        assert quota.daily_messages_remaining == 9
        assert quota.daily_tokens_remaining == 19_850
        admin_usage = repository.admin_usage(reserved.usage_month)
        assert admin_usage["learners"] >= 1
        assert admin_usage["actual_requests"] >= 1
        assert admin_usage["actual_cost_micros_sgd"] >= 1_000

        repository.append_message(
            session["session_id"],
            role="student",
            mode=None,
            content={"blocks": [{"type": "text", "content": "Help me begin."}]},
        )
        assistant = repository.append_message(
            session["session_id"],
            role="assistant",
            mode="socratic_prompt",
            content={"blocks": [{"type": "text", "content": "What fact applies first?"}]},
            grounding_revision_ids=grounding.grounding_revision_ids,
            model_name="test-provider",
            prompt_version="test-prompt-v1",
            token_usage={"input_tokens": 100, "output_tokens": 50},
        )
        assert assistant["role"] == "assistant"
        assert len(repository.get_session(learner_id, session["session_id"])["messages"]) == 2

        with psycopg.connect(database_url) as connection:
            with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
                connection.execute(
                    "update tutor_messages set safety_outcome='provider_fallback' where id=%s",
                    (assistant["id"],),
                )
        with psycopg.connect(database_url) as connection:
            connection.execute(
                """
                update session_questions set status='gave_up', resolved_at=now()
                where practice_session_id=%s
                """,
                (practice_session_id,),
            )
        unlocked = repository.grounding(learner_id, session["session_id"])
        assert unlocked.answer_lock_state.solution_locked is False
        assert unlocked.unlocked_solution_blocks
    finally:
        with psycopg.connect(database_url) as connection:
            connection.execute(
                "update math_questions set status=%s where stable_key='n1-l1-01'",
                (source[2],),
            )
            connection.execute(
                """
                update lesson_versions set status=%s
                where lesson_id=(select id from course_lessons where lesson_key='n1-lesson-01')
                  and is_current
                """,
                (source[3],),
            )
            connection.execute(
                "select set_config('app.account_deletion_target', %s, true)",
                (learner_id,),
            )
            connection.execute("delete from auth.users where id=%s", (learner_id,))
            remaining = connection.execute(
                "select count(*) from tutor_sessions where student_id=%s",
                (learner_id,),
            ).fetchone()[0]
            assert remaining == 0
