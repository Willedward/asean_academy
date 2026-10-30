"""Opt-in Stage 4 integration test; TEST_DATABASE_URL must be disposable."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
import pytest
from question_bank.practice import solution_for
from question_bank.validation import validate_bank

from learning_api.admin_contracts import CreateInvitationRequest
from learning_api.admin_repository import PostgresBetaOperationsRepository
from learning_api.config import Settings
from learning_api.identity import AuthenticatedLearner, StaticTokenVerifier
from learning_api.identity_repository import invitation_digest
from learning_api.main import create_app
from learning_api.postgres_practice import PostgresPracticeEngine
from learning_api.progress_repository import PostgresProgressRepository

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BANK_ROOT = REPOSITORY_ROOT / "backend_resources/question_bank/g3_math/secondary_1/n1/v1"


def _database_url() -> str:
    value = os.environ.get("TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set TEST_DATABASE_URL to a migrated, imported disposable database")
    return value


def _seed_learner(connection, learner_id: str, email: str, code: str) -> None:
    connection.execute(
        "insert into auth.users (id, email) values (%s, %s)",
        (learner_id, email),
    )
    version = connection.execute(
        """
        select versions.id
        from course_versions versions
        join courses on courses.id = versions.course_id
        where courses.course_key = 'g3-sec1-math' and versions.is_current
        """
    ).fetchone()
    assert version is not None, "Import the N1 course before running PostgreSQL tests"
    connection.execute(
        """
        insert into beta_invitations (
            token_sha256, email, course_version_id, expires_at
        ) values (%s, %s, %s, %s)
        """,
        (
            invitation_digest(code),
            email,
            version[0],
            datetime.now(UTC) + timedelta(hours=1),
        ),
    )


def _request(app, method: str, path: str, token: str, **kwargs):
    async def send():
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {token}"
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, headers=headers, **kwargs)

    return asyncio.run(send())


def _english_answers(question_key: str) -> dict:
    source = json.loads(
        (
            REPOSITORY_ROOT / "backend_resources/english/v1/questions" / f"{question_key}.json"
        ).read_text()
    )
    answers = {}
    for part in source["parts"]:
        response = part["response"]
        if response["type"] == "single_choice":
            answer = response["correct_key"]
        elif response["type"] == "multiple_response":
            answer = response["correct_keys"]
        else:
            answer = response["canonical_answer"]
        answers[str(part["position"])] = answer
    return answers


@pytest.mark.postgres
def test_postgres_english_baseline_is_protected_idempotent_and_immutable():
    database_url = _database_url()
    learner_id = str(uuid4())
    email = f"{learner_id}@example.test"
    invitation_code = secrets.token_urlsafe(32)
    with psycopg.connect(database_url) as connection:
        _seed_learner(connection, learner_id, email, invitation_code)

    app = create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=True,
            development_learner_id=None,
            database_url=database_url,
            rate_limits_enabled=False,
        ),
        token_verifier=StaticTokenVerifier(
            {"english-diagnostic-learner": AuthenticatedLearner(learner_id, "authenticated", email)}
        ),
    )
    accepted = _request(
        app,
        "POST",
        "/api/v1/onboarding/accept-invitation",
        "english-diagnostic-learner",
        json={"invitation_code": invitation_code, "display_name": "English diagnostic learner"},
    )
    assert accepted.status_code == 200, accepted.text

    created = _request(
        app,
        "POST",
        "/api/v1/english/diagnostic-sessions",
        "english-diagnostic-learner",
        headers={"Idempotency-Key": "postgres-english-baseline"},
        json={"expected_purpose": "baseline"},
    )
    assert created.status_code == 201, created.text
    session_id = created.json()["session_id"]
    replay = _request(
        app,
        "POST",
        "/api/v1/english/diagnostic-sessions",
        "english-diagnostic-learner",
        headers={"Idempotency-Key": "postgres-english-baseline"},
        json={"expected_purpose": "baseline"},
    )
    assert replay.status_code == 201, replay.text
    assert replay.json()["session_id"] == session_id

    expected_questions = ["ev-l5-003", "eb-l1-003", "eo-l5-003", "er-l5-005"]
    for position, expected_key in enumerate(expected_questions, 1):
        current = _request(
            app,
            "GET",
            f"/api/v1/english/diagnostic-sessions/{session_id}/next",
            "english-diagnostic-learner",
        )
        assert current.status_code == 200, current.text
        question = current.json()["question"]
        assert question["stable_key"] == expected_key
        assert "correct_key" not in json.dumps(question)
        answered = _request(
            app,
            "POST",
            "/api/v1/english/diagnostic-attempts",
            "english-diagnostic-learner",
            headers={"Idempotency-Key": f"postgres-english-baseline-{position}"},
            json={
                "session_id": session_id,
                "question_key": question["stable_key"],
                "question_revision": question["revision"],
                "answers": _english_answers(question["stable_key"]),
            },
        )
        assert answered.status_code == 200, answered.text
        if position < len(expected_questions):
            assert answered.json()["session"]["score"] is None
            assert answered.json()["session"]["correct_parts"] == 0

    assert answered.json()["diagnostic_completed"] is True
    assert answered.json()["session"]["score"] == 1
    assert answered.json()["session"]["total_parts"] == 20
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """
            select status::text, score, expected_part_count
            from english_diagnostic_sessions where id=%s
            """,
            (session_id,),
        ).fetchone()
        assert row[0] == "completed"
        assert float(row[1]) == 1
        assert row[2] == 20
        with pytest.raises(psycopg.errors.RaiseException):
            connection.execute(
                "update english_diagnostic_attempts set correct_parts=0 where student_id=%s",
                (learner_id,),
            )
        connection.rollback()


@pytest.mark.postgres
def test_postgres_english_e1_checkpoint_persists_and_records_mastery_atomically():
    database_url = _database_url()
    learner_id = str(uuid4())
    email = f"{learner_id}@example.test"
    invitation_code = secrets.token_urlsafe(32)
    with psycopg.connect(database_url) as connection:
        _seed_learner(connection, learner_id, email, invitation_code)

    app = create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=True,
            development_learner_id=None,
            database_url=database_url,
            rate_limits_enabled=False,
        ),
        token_verifier=StaticTokenVerifier(
            {"english-checkpoint-learner": AuthenticatedLearner(learner_id, "authenticated", email)}
        ),
    )
    accepted = _request(
        app,
        "POST",
        "/api/v1/onboarding/accept-invitation",
        "english-checkpoint-learner",
        json={"invitation_code": invitation_code, "display_name": "English learner"},
    )
    assert accepted.status_code == 200, accepted.text
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            insert into english_lesson_progress (
                student_id, lesson_key, lesson_revision, state, question_count,
                resolved_count, correct_count, incorrect_count
            ) values
                (%s, 'e1-lesson-01', 1, 'proficient', 1, 1, 1, 0),
                (%s, 'e1-lesson-06', 1, 'proficient', 1, 1, 1, 0)
            """,
            (learner_id, learner_id),
        )

    created = _request(
        app,
        "POST",
        "/api/v1/english/checkpoint-sessions",
        "english-checkpoint-learner",
        headers={"Idempotency-Key": "postgres-english-e1-checkpoint"},
        json={"module_code": "E1"},
    )
    assert created.status_code == 201, created.text
    session_id = created.json()["session_id"]
    assert created.json()["form_key"] == "english-checkpoint-e1-vocabulary-a-v1"
    current = _request(
        app,
        "GET",
        f"/api/v1/english/checkpoint-sessions/{session_id}/next",
        "english-checkpoint-learner",
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    answered = _request(
        app,
        "POST",
        "/api/v1/english/checkpoint-attempts",
        "english-checkpoint-learner",
        headers={"Idempotency-Key": "postgres-english-e1-answer"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {"1": "A", "2": "A", "3": "A", "4": "A", "5": "B"},
        },
    )
    assert answered.status_code == 200, answered.text
    assert answered.json()["session"]["score"] == 0.8
    assert answered.json()["session"]["passed"] is True
    with psycopg.connect(database_url) as connection:
        checkpoint = connection.execute(
            """
            select status::text, score, passed, mastery_lesson_keys
            from english_checkpoint_sessions where id=%s
            """,
            (session_id,),
        ).fetchone()
        assert checkpoint[0] == "completed"
        assert float(checkpoint[1]) == 0.8
        assert checkpoint[2] is True
        assert checkpoint[3] == ["e1-lesson-01", "e1-lesson-06"]
        states = connection.execute(
            """
            select lesson_key, state::text from english_lesson_progress
            where student_id=%s and lesson_key=any(%s)
            order by lesson_key
            """,
            (learner_id, ["e1-lesson-01", "e1-lesson-06"]),
        ).fetchall()
        assert states == [
            ("e1-lesson-01", "mastered"),
            ("e1-lesson-06", "mastered"),
        ]
        with pytest.raises(psycopg.errors.RaiseException):
            connection.execute(
                "update english_checkpoint_attempts set correct_parts=0 where student_id=%s",
                (learner_id,),
            )
        connection.rollback()


@pytest.mark.postgres
def test_authenticated_postgres_practice_is_idempotent_immutable_and_isolated():
    database_url = _database_url()
    learner_a = str(uuid4())
    learner_b = str(uuid4())
    email_a = f"{learner_a}@example.test"
    email_b = f"{learner_b}@example.test"
    code_a = secrets.token_urlsafe(32)
    code_b = secrets.token_urlsafe(32)
    with psycopg.connect(database_url) as connection:
        _seed_learner(connection, learner_a, email_a, code_a)
        _seed_learner(connection, learner_b, email_b, code_b)

    app = create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=True,
            development_learner_id=None,
            database_url=database_url,
        ),
        token_verifier=StaticTokenVerifier(
            {
                "learner-a": AuthenticatedLearner(learner_a, "authenticated", email_a),
                "learner-b": AuthenticatedLearner(learner_b, "authenticated", email_b),
            }
        ),
    )
    for token, code, name in (
        ("learner-a", code_a, "Learner A"),
        ("learner-b", code_b, "Learner B"),
    ):
        accepted = _request(
            app,
            "POST",
            "/api/v1/onboarding/accept-invitation",
            token,
            json={"invitation_code": code, "display_name": name},
        )
        assert accepted.status_code == 200, accepted.text

    payload = {"lesson_key": "n1-lesson-01", "mode": "guided_practice", "question_count": 1}
    first = _request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        "learner-a",
        headers={"Idempotency-Key": "same-key"},
        json=payload,
    )
    replay = _request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        "learner-a",
        headers={"Idempotency-Key": "same-key"},
        json=payload,
    )
    second_learner = _request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        "learner-b",
        headers={"Idempotency-Key": "same-key"},
        json=payload,
    )
    assert first.status_code == replay.status_code == second_learner.status_code == 201
    assert first.json()["session_id"] == replay.json()["session_id"]
    assert first.json()["session_id"] != second_learner.json()["session_id"]

    hidden = _request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{first.json()['session_id']}",
        "learner-b",
    )
    assert hidden.status_code == 404

    current = _request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{first.json()['session_id']}/next",
        "learner-a",
    ).json()
    question_key = current["question"]["stable_key"]
    questions = {item.stable_key: item for item in validate_bank(BANK_ROOT).questions}
    answers = {
        str(part["position"]): part["canonical_answer"]
        for part in solution_for(questions[question_key])["parts"]
    }
    attempt_payload = {
        "session_id": first.json()["session_id"],
        "question_key": question_key,
        "question_revision": current["question"]["revision"],
        "answers": answers,
    }
    attempt = _request(
        app,
        "POST",
        "/api/v1/attempts",
        "learner-a",
        headers={"Idempotency-Key": "attempt-key"},
        json=attempt_payload,
    )
    attempt_replay = _request(
        app,
        "POST",
        "/api/v1/attempts",
        "learner-a",
        headers={"Idempotency-Key": "attempt-key"},
        json=attempt_payload,
    )
    assert attempt.status_code == 200
    assert attempt.json() == attempt_replay.json()

    with psycopg.connect(database_url) as connection:
        count = connection.execute(
            "select count(*) from attempts where student_id = %s", (learner_a,)
        ).fetchone()[0]
        assert count == 1
    with psycopg.connect(database_url) as connection:
        connection.execute("set local role authenticated")
        connection.execute("select set_config('request.jwt.claim.sub', %s, true)", (learner_b,))
        visible = connection.execute(
            "select count(*) from practice_sessions where id = %s",
            (first.json()["session_id"],),
        ).fetchone()[0]
        assert visible == 0
    with psycopg.connect(database_url) as connection:
        connection.execute("set local role authenticated")
        connection.execute("select set_config('request.jwt.claim.sub', %s, true)", (learner_a,))
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute(
                "update learner_lesson_progress set state = 'mastered' where student_id = %s",
                (learner_a,),
            )
    with psycopg.connect(database_url) as connection:
        with pytest.raises(psycopg.errors.RaiseException, match="attempts are immutable"):
            connection.execute(
                "update attempts set marks_awarded = 0 where student_id = %s",
                (learner_a,),
            )


@pytest.mark.postgres
def test_concurrent_session_creation_replays_one_postgres_session():
    database_url = _database_url()
    learner_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "insert into auth.users (id, email) values (%s, %s)",
            (learner_id, f"{learner_id}@example.test"),
        )
    questions = validate_bank(BANK_ROOT).questions

    def create(idempotency_key: str):
        engine = PostgresPracticeEngine(database_url, questions, learner_id, allow_drafts=True)
        return engine.create_session(
            question_count=1,
            ordered_question_keys=["n1-l1-01"],
            context={"lesson_key": "n1-lesson-01", "mode": "guided_practice"},
            idempotency_key=idempotency_key,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = list(executor.map(create, ["concurrent-create-a", "concurrent-create-b"]))

    assert first["session_id"] == second["session_id"]
    with psycopg.connect(database_url) as connection:
        count = connection.execute(
            "select count(*) from practice_sessions where student_id = %s",
            (learner_id,),
        ).fetchone()[0]
    assert count == 1


@pytest.mark.postgres
def test_beta_operations_are_admin_authorized_audited_and_immutable():
    database_url = _database_url()
    administrator_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "insert into auth.users (id, email) values (%s, %s)",
            (administrator_id, f"{administrator_id}@example.test"),
        )
        connection.execute(
            "insert into profiles (id, email, role, display_name) values (%s, %s, 'content_admin', 'Admin')",
            (administrator_id, f"{administrator_id}@example.test"),
        )

    repository = PostgresBetaOperationsRepository(database_url)
    administrator = AuthenticatedLearner(
        administrator_id,
        "content_admin",
        f"{administrator_id}@example.test",
    )
    assert repository.role_for(administrator_id) == "content_admin"

    created = repository.create_invitation(
        administrator,
        CreateInvitationRequest(email=f"{uuid4()}@example.test"),
        "postgres-admin-create",
    )
    assert created["status"] == "active"
    assert len(created["invitation_code"]) >= 16

    listed = repository.list_invitations(status="active", limit=200, offset=0)
    assert any(item["invitation_id"] == created["invitation_id"] for item in listed["invitations"])
    events = repository.audit_events(limit=200)["events"]
    assert any(
        event["request_id"] == "postgres-admin-create"
        and event["event_type"] == "invitation_created"
        for event in events
    )

    revoked = repository.revoke_invitation(
        administrator,
        created["invitation_id"],
        "postgres-admin-revoke",
    )
    assert revoked["status"] == "revoked"
    revoked_again = repository.revoke_invitation(
        administrator,
        created["invitation_id"],
        "postgres-admin-revoke-again",
    )
    assert revoked_again["revoked_at"] == revoked["revoked_at"]
    assert repository.summary()["invitations_revoked"] >= 1

    with psycopg.connect(database_url) as connection:
        repeated_revoke_events = connection.execute(
            "select count(*) from beta_audit_events where request_id = %s",
            ("postgres-admin-revoke-again",),
        ).fetchone()[0]
        assert repeated_revoke_events == 0
        stored = connection.execute(
            "select token_sha256 from beta_invitations where id = %s",
            (created["invitation_id"],),
        ).fetchone()[0]
        assert stored == invitation_digest(created["invitation_code"])
        assert created["invitation_code"] != stored
        event_id = connection.execute(
            "select id from beta_audit_events where request_id = 'postgres-admin-create'"
        ).fetchone()[0]
        with pytest.raises(psycopg.errors.RaiseException, match="audit events are immutable"):
            connection.execute(
                "update beta_audit_events set metadata = '{}'::jsonb where id = %s",
                (event_id,),
            )


@pytest.mark.postgres
def test_postgres_checkpoint_records_mastery_and_replays_one_active_session():
    database_url = _database_url()
    learner_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "insert into auth.users (id, email) values (%s, %s)",
            (learner_id, f"{learner_id}@example.test"),
        )
        lesson_rows = connection.execute(
            """
            select lessons.id as lesson_id, versions.id as lesson_version_id,
                   lessons.lesson_key
            from course_lessons lessons
            join course_units units on units.id = lessons.unit_id
            join lesson_versions versions on versions.lesson_id = lessons.id
            where versions.is_current and units.unit_key = 'g3-sec1-n1'
            order by lessons.lesson_key
            """
        ).fetchall()
        assert len(lesson_rows) == 7, "Import the complete N1 course before this test"
        for lesson_id, lesson_version_id, _lesson_key in lesson_rows:
            connection.execute(
                """
                insert into learner_lesson_progress (
                    student_id, lesson_id, lesson_version_id, state,
                    question_count, resolved_count, correct_count,
                    eventual_correct_percentage, completed_at
                ) values (%s, %s, %s, 'proficient', 1, 1, 1, 100, now())
                """,
                (learner_id, lesson_id, lesson_version_id),
            )

    questions = validate_bank(BANK_ROOT).questions
    by_key = {question.stable_key: question for question in questions}
    checkpoint_keys = [
        "n1-l1-03",
        "n1-l2-04",
        "n1-l2-01",
        "n1-l3-04",
        "n1-l2-07",
        "n1-l3-06",
        "n1-l3-07",
        "n1-l3-01",
    ]
    context = {
        "unit_key": "g3-sec1-n1",
        "mode": "checkpoint",
        "stages": {key: "checkpoint" for key in checkpoint_keys},
        "selection_reason": "configured_checkpoint_pool",
    }
    engine = PostgresPracticeEngine(database_url, questions, learner_id, allow_drafts=True)
    created = engine.create_session(
        question_count=8,
        ordered_question_keys=checkpoint_keys,
        context=context,
        idempotency_key="postgres-checkpoint-a",
    )
    replay = engine.create_session(
        question_count=8,
        ordered_question_keys=checkpoint_keys,
        context=context,
        idempotency_key="postgres-checkpoint-b",
    )
    assert replay["session_id"] == created["session_id"]

    repository = PostgresProgressRepository(database_url)
    repository.attach_checkpoint_session(
        learner_id,
        "g3-sec1-n1",
        created["session_id"],
        8,
    )
    assert repository.active_session(learner_id) is None
    assert repository.checkpoint_session(learner_id, created["session_id"]) is not None
    for number in range(1, 9):
        current = engine.next_question(created["session_id"])
        question_key = current["question"]["stable_key"]
        answers = (
            {"1": "not an answer"}
            if number == 1
            else {
                str(part["position"]): part["canonical_answer"]
                for part in solution_for(by_key[question_key])["parts"]
            }
        )
        result = engine.submit_attempt(
            session_id=created["session_id"],
            stable_key=question_key,
            revision=current["question"]["revision"],
            answers=answers,
            idempotency_key=f"postgres-checkpoint-answer-{number}",
        )
        assert result["question_finished"] is True
        assert result["solution_available"] is False

    completed = engine.next_question(created["session_id"])["session"]
    assert completed["status"] == "completed"
    assert completed["correct_count"] == 7
    assert completed["incorrect_count"] == 1
    recorded = repository.sync_checkpoint(
        learner_id,
        completed,
        lesson_keys=[row[2] for row in lesson_rows],
        passing_percentage=70,
        policy_key="n1-default-v1",
    )
    assert recorded.percentage == 87.5
    assert all(
        progress.state == "mastered" and progress.checkpoint_passed
        for progress in repository.lesson_progress(learner_id)
    )

    with psycopg.connect(database_url) as connection:
        events = connection.execute(
            """
            select event_type::text from mastery_events
            where student_id = %s and source_practice_session_id = %s
            order by event_type::text
            """,
            (learner_id, created["session_id"]),
        ).fetchall()
        assert events == [("checkpoint_passed",), ("lesson_mastered",)]
        with pytest.raises(psycopg.errors.RaiseException, match="mastery events are immutable"):
            connection.execute(
                """
                update mastery_events set evidence = '{}'::jsonb
                where student_id = %s and source_practice_session_id = %s
                """,
                (learner_id, created["session_id"]),
            )


@pytest.mark.postgres
def test_postgres_lesson_section_completion_is_revision_pinned_and_owner_isolated():
    database_url = _database_url()
    learner_id = str(uuid4())
    other_learner_id = str(uuid4())
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "insert into auth.users (id, email) values (%s, %s), (%s, %s)",
            (
                learner_id,
                f"{learner_id}@example.test",
                other_learner_id,
                f"{other_learner_id}@example.test",
            ),
        )

    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            insert into course_enrolments(student_id, course_id, course_version_id)
            select %s, course_id, id from course_versions where is_current
        """,
            (learner_id,),
        )
    repository = PostgresProgressRepository(database_url)
    repository.start_lesson(learner_id, "n1-lesson-01", 2)
    repository.set_section_completion(
        learner_id,
        "n1-lesson-01",
        2,
        "prime-numbers",
        True,
    )

    assert repository.completed_section_keys(learner_id, "n1-lesson-01", 2) == ["prime-numbers"]
    assert repository.completed_section_keys(learner_id, "n1-lesson-01", 1) == []
    assert repository.completed_section_keys(other_learner_id, "n1-lesson-01", 2) == []

    with psycopg.connect(database_url) as connection:
        connection.execute("set local role authenticated")
        connection.execute(
            "select set_config('request.jwt.claim.sub', %s, true)",
            (other_learner_id,),
        )
        visible = connection.execute(
            "select count(*) from learner_lesson_section_progress where student_id = %s",
            (learner_id,),
        ).fetchone()[0]
        assert visible == 0

    repository.set_section_completion(
        learner_id,
        "n1-lesson-01",
        2,
        "prime-numbers",
        False,
    )
    assert repository.completed_section_keys(learner_id, "n1-lesson-01", 2) == []
