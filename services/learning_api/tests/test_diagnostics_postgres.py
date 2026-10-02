"""Opt-in B1 diagnostic integration tests against disposable PostgreSQL."""

from __future__ import annotations

import json
import os
from uuid import uuid4

import psycopg
import pytest

from learning_api.diagnostic_repository import PostgresDiagnosticRepository


def _database_url() -> str:
    value = os.getenv("TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set TEST_DATABASE_URL to a migrated and imported disposable database")
    return value


def _seed_diagnostics(connection, learner_id: str, administrator_id: str) -> None:
    learner_email = f"diagnostic-{learner_id}@example.test"
    admin_email = f"diagnostic-{administrator_id}@example.test"
    connection.execute(
        "insert into auth.users (id, email) values (%s, %s), (%s, %s)",
        (learner_id, learner_email, administrator_id, admin_email),
    )
    connection.execute(
        """
        insert into profiles (id, role, email, display_name)
        values (%s, 'student', %s, 'Diagnostic learner'),
               (%s, 'academic_admin', %s, 'Diagnostic administrator')
        """,
        (learner_id, learner_email, administrator_id, admin_email),
    )
    course = connection.execute(
        """
        select courses.id as course_id, versions.id as course_version_id,
               courses.curriculum_version_id
        from courses join course_versions versions on versions.course_id = courses.id
        where courses.course_key = 'g3-sec1-math' and versions.is_current
        """
    ).fetchone()
    assert course is not None, "Import the N1 course before running diagnostic tests"
    connection.execute(
        """
        update diagnostic_forms
        set is_current = false
        where course_version_id = %s and purpose in (%s, %s)
        """,
        (course[1], "baseline", "endline"),
    )
    connection.execute(
        """
        insert into course_enrolments (student_id, course_id, course_version_id)
        values (%s, %s, %s)
        """,
        (learner_id, course[0], course[1]),
    )
    topic = connection.execute(
        """
        select topics.id
        from syllabus_topics topics
        where topics.curriculum_version_id = %s and topics.code = 'N1'
        """,
        (course[2],),
    ).fetchone()[0]
    bank_id = uuid4()
    connection.execute(
        """
        insert into math_question_banks (
            id, bank_key, curriculum_version_id, topic_id, school_level,
            title, status, expected_question_count, difficulty_counts,
            source_style_references, published_at
        ) values (%s, %s, %s, %s, 'secondary_1', 'Diagnostic test bank',
                  'published', 2, '{"1": 2, "2": 0, "3": 0, "4": 0, "5": 0}'::jsonb,
                  '[]'::jsonb, now())
        """,
        (bank_id, f"diagnostic-test-{learner_id}", course[2], topic),
    )
    outcomes = dict(
        connection.execute(
            """
            select code, id from syllabus_outcomes
            where topic_id = %s and code in ('1.1', '1.2')
            """,
            (topic,),
        ).fetchall()
    )
    version_ids = []
    for position, (outcome, canonical) in enumerate((("1.1", "12"), ("1.2", "18")), 1):
        question_id = uuid4()
        version_id = uuid4()
        part_id = uuid4()
        connection.execute(
            """
            insert into math_questions (
                id, bank_id, primary_outcome_id, stable_key, difficulty, status
            ) values (%s, %s, %s, %s, 1, 'published')
            """,
            (question_id, bank_id, outcomes[outcome], f"diag-{learner_id}-{position}"),
        )
        connection.execute(
            """
            insert into math_question_versions (
                id, question_id, revision, title, calculator_allowed, question_type,
                stem_blocks, total_marks, content_sha256, provenance, is_current,
                reviewed_at, review_notes
            ) values (%s, %s, 1, %s, true, 'structured', '[]'::jsonb, 1,
                      %s, '{"authoring_method": "test_fixture"}'::jsonb,
                      true, now(), 'Disposable integration fixture')
            """,
            (version_id, question_id, f"Diagnostic item {position}", f"{position}" * 64),
        )
        connection.execute(
            """
            insert into math_question_parts (
                id, question_version_id, position, prompt_blocks, marks, response_type
            ) values (%s, %s, 1, %s::jsonb, 1, 'numeric')
            """,
            (part_id, version_id, json.dumps([{"type": "text", "text": f"Enter {canonical}."}])),
        )
        connection.execute(
            """
            insert into math_question_outcomes (question_part_id, outcome_id, role)
            values (%s, %s, 'primary')
            """,
            (part_id, outcomes[outcome]),
        )
        connection.execute(
            """
            insert into math_answer_specs (
                question_part_id, response_type, comparison_mode,
                canonical_answer, canonical_latex, accepted_answers
            ) values (%s, 'numeric', 'exact_numeric', %s, %s, '[]'::jsonb)
            """,
            (part_id, canonical, canonical),
        )
        version_ids.append((version_id, outcomes[outcome]))

    for purpose in ("baseline", "endline"):
        form_id = uuid4()
        connection.execute(
            """
            insert into diagnostic_forms (
                id, stable_key, revision, course_version_id, purpose, status,
                title, instructions, estimated_minutes, content_sha256,
                band_policy_version, is_current, reviewed_at, published_at
            ) values (%s, %s, 1, %s, %s, 'published', %s,
                      'Answer every question. Correctness is shown after submission.',
                      20, %s, 'n1-readiness-v1', true, now(), now())
            """,
            (
                form_id,
                f"n1-{purpose}-{learner_id}",
                course[1],
                purpose,
                f"N1 {purpose} readiness check",
                ("a" if purpose == "baseline" else "b") * 64,
            ),
        )
        for position, (version_id, outcome_id) in enumerate(version_ids, 1):
            connection.execute(
                """
                insert into diagnostic_form_items (
                    form_id, question_version_id, outcome_id, position, weight
                ) values (%s, %s, %s, %s, 1)
                """,
                (form_id, version_id, outcome_id, position),
            )


@pytest.mark.postgres
def test_diagnostic_is_refresh_safe_scored_immutable_and_resettable():
    database_url = _database_url()
    learner_id = str(uuid4())
    administrator_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        _seed_diagnostics(connection, learner_id, administrator_id)

    repository = PostgresDiagnosticRepository(database_url)
    assert repository.next(learner_id)["status"] == "start"
    session = repository.create_session(learner_id, "create-one", "baseline")
    replay = repository.create_session(learner_id, "create-one", "baseline")
    assert replay["session_id"] == session["session_id"]
    assert len(session["items"]) == 2

    first = repository.save_response(
        learner_id, str(session["session_id"]), 1, {"1": "0"}, "save-one"
    )
    assert first["saved"] is True
    assert "correct" not in first
    first_replay = repository.save_response(
        learner_id, str(session["session_id"]), 1, {"1": "0"}, "save-one"
    )
    assert first_replay["saved_at"] == first["saved_at"]
    repository.save_response(
        learner_id, str(session["session_id"]), 2, {"1": "18"}, "save-two"
    )
    resumed = repository.session(learner_id, str(session["session_id"]))
    assert resumed["items"][0]["saved_answers"] == {"1": "0"}
    assert repository.next(learner_id)["status"] == "resume"

    result = repository.submit(learner_id, str(session["session_id"]))
    assert result["percentage"] == 50
    assert result["band"] == "on_track"
    assert result["strengths"] == ["1.2"]
    assert result["priorities"] == ["1.1"]
    assert repository.submit(learner_id, str(session["session_id"])) == result
    assert repository.next(learner_id)["status"] == "baseline_complete"

    admin = repository.admin_student_results(learner_id)
    assert admin["baseline"]["session_id"] == session["session_id"]
    assert admin["endline"] is None

    with psycopg.connect(database_url) as connection:
        with pytest.raises(psycopg.errors.RaiseException, match="diagnostic results are immutable"):
            connection.execute(
                "update diagnostic_results set percentage = 0 where session_id = %s",
                (session["session_id"],),
            )

    reset = repository.reset(
        learner_id,
        "baseline",
        administrator_id,
        "Learner experienced a verified connectivity interruption.",
        "diagnostic-reset-test",
    )
    assert reset["reset"] is True
    assert repository.next(learner_id)["status"] == "start"
    history = repository.admin_student_results(learner_id)["history"]
    assert history[0]["state"] == "reset"
    assert history[0]["reset_reason"].startswith("Learner experienced")


@pytest.mark.postgres
def test_diagnostic_form_rejects_learning_pool_questions():
    database_url = _database_url()
    with psycopg.connect(database_url) as connection:
        pooled = connection.execute(
            """
            select question_versions.id as question_version_id,
                   questions.id as question_id, outcomes.id as outcome_id,
                   versions.course_version_id
            from lesson_question_pool_items items
            join lesson_question_pools pools on pools.id = items.pool_id
            join unit_versions versions on versions.id = pools.unit_version_id
            join math_questions questions on questions.id = items.question_id
            join math_question_versions question_versions
              on question_versions.question_id = questions.id and question_versions.is_current
            join syllabus_outcomes outcomes on outcomes.id = questions.primary_outcome_id
            limit 1
            """
        ).fetchone()
        assert pooled is not None
        connection.execute(
            "update math_questions set status = 'published' where id = %s",
            (pooled[1],),
        )
        connection.execute(
            "update math_question_versions set reviewed_at = now() where id = %s",
            (pooled[0],),
        )
        form_id = uuid4()
        connection.execute(
            """
            insert into diagnostic_forms (
                id, stable_key, revision, course_version_id, purpose, status,
                title, instructions, estimated_minutes, content_sha256,
                band_policy_version, is_current
            ) values (%s, %s, 1, %s, 'baseline', 'draft', 'Isolation test',
                      'Never reuse practice questions.', 20, %s,
                      'n1-readiness-v1', false)
            """,
            (form_id, f"isolation-{form_id}", pooled[3], "c" * 64),
        )
        with pytest.raises(
            psycopg.errors.RaiseException,
            match="diagnostic questions cannot belong",
        ):
            connection.execute(
                """
                insert into diagnostic_form_items (
                    form_id, question_version_id, outcome_id, position
                ) values (%s, %s, %s, 1)
                """,
                (form_id, pooled[0], pooled[2]),
            )
