"""Opt-in Stage 4 integration test; TEST_DATABASE_URL must be disposable."""

from __future__ import annotations

import asyncio
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
        connection.execute(
            "select set_config('request.jwt.claim.sub', %s, true)", (learner_b,)
        )
        visible = connection.execute(
            "select count(*) from practice_sessions where id = %s",
            (first.json()["session_id"],),
        ).fetchone()[0]
        assert visible == 0
    with psycopg.connect(database_url) as connection:
        connection.execute("set local role authenticated")
        connection.execute(
            "select set_config('request.jwt.claim.sub', %s, true)", (learner_a,)
        )
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
        engine = PostgresPracticeEngine(
            database_url, questions, learner_id, allow_drafts=True
        )
        return engine.create_session(
            question_count=1,
            ordered_question_keys=["n1-l1-01"],
            context={"lesson_key": "n1-lesson-01", "mode": "guided_practice"},
            idempotency_key=idempotency_key,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = list(
            executor.map(create, ["concurrent-create-a", "concurrent-create-b"])
        )

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
            "insert into profiles (id, role, display_name) values (%s, 'content_admin', 'Admin')",
            (administrator_id,),
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
    assert any(
        item["invitation_id"] == created["invitation_id"]
        for item in listed["invitations"]
    )
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
