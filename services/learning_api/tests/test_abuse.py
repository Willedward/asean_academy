from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from learning_api.abuse import (
    InMemoryRateLimiter,
    RateLimitPolicy,
    opaque_subject,
)
from learning_api.config import Settings
from learning_api.identity import AuthenticatedLearner, StaticTokenVerifier
from learning_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
LEARNER_ID = "00000000-0000-4000-8000-000000000091"


def _app(tmp_path: Path):
    return create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=True,
            practice_database=tmp_path / "practice.sqlite3",
            development_learner_id=None,
        ),
        token_verifier=StaticTokenVerifier(
            {
                "learner-token": AuthenticatedLearner(
                    LEARNER_ID,
                    "authenticated",
                    "learner@example.test",
                )
            }
        ),
    )


def _request(app, method: str, path: str, **kwargs):
    async def send():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_memory_limiter_resets_and_subjects_are_opaque():
    now = [1_000.0]
    limiter = InMemoryRateLimiter(clock=lambda: now[0])
    policy = RateLimitPolicy("test", limit=2, window_seconds=60)
    digest = opaque_subject("a-secret-that-is-long-enough-for-testing", "learner", LEARNER_ID)

    first = limiter.consume(policy, digest, request_id="one", path="/test")
    second = limiter.consume(policy, digest, request_id="two", path="/test")
    denied = limiter.consume(policy, digest, request_id="three", path="/test")

    assert first.allowed and first.remaining == 1
    assert second.allowed and second.remaining == 0
    assert not denied.allowed and denied.remaining == 0
    assert LEARNER_ID not in digest
    assert len(digest) == 64

    now[0] += 61
    reset = limiter.consume(policy, digest, request_id="four", path="/test")
    assert reset.allowed and reset.remaining == 1


def test_sensitive_route_returns_standard_429_and_retry_headers(tmp_path, monkeypatch):
    from learning_api import dependencies

    monkeypatch.setitem(
        dependencies.POLICIES,
        "practice_session_write",
        RateLimitPolicy("practice_session_write", limit=1, window_seconds=60),
    )
    app = _app(tmp_path)
    headers = {"Authorization": "Bearer learner-token", "Idempotency-Key": "session-one"}
    body = {"lesson_key": "n1-lesson-01", "mode": "guided_practice"}

    first = _request(app, "POST", "/api/v1/practice-sessions", headers=headers, json=body)
    headers["Idempotency-Key"] = "session-two"
    denied = _request(app, "POST", "/api/v1/practice-sessions", headers=headers, json=body)

    assert first.status_code == 201, first.text
    assert first.headers["ratelimit-limit"] == "1"
    assert first.headers["ratelimit-remaining"] == "0"
    assert denied.status_code == 429
    assert denied.headers["retry-after"]
    assert denied.json()["error"]["code"] == "rate_limit_exceeded"
    assert denied.json()["error"]["details"]["window_seconds"] == 60


def test_oversized_api_body_is_rejected_before_authentication(tmp_path):
    app = _app(tmp_path)
    response = _request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        headers={"Content-Length": "65537"},
        content=b"{}",
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "request_too_large"
    assert response.json()["error"]["details"] == {"max_bytes": 65536}


@pytest.mark.postgres
def test_postgres_limiter_is_shared_audited_and_security_events_are_immutable():
    import os
    from uuid import uuid4

    import psycopg

    from learning_api.abuse import PostgresRateLimiter

    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Requires a migrated disposable PostgreSQL database")
    limiter = PostgresRateLimiter(database_url)
    policy = RateLimitPolicy("postgres-test", limit=1, window_seconds=60)
    subject = opaque_subject(
        "a-secret-that-is-long-enough-for-testing",
        "learner",
        str(uuid4()),
    )

    assert limiter.consume(
        policy,
        subject,
        request_id="postgres-rate-one",
        path="/api/v1/test",
    ).allowed
    assert not limiter.consume(
        policy,
        subject,
        request_id="postgres-rate-two",
        path="/api/v1/test",
    ).allowed

    with psycopg.connect(database_url) as connection:
        event_id = connection.execute(
            """
            select id from api_security_events
            where policy_key = 'postgres-test' and subject_hash = %s
            """,
            (subject,),
        ).fetchone()[0]
        with pytest.raises(psycopg.errors.RaiseException, match="security events are immutable"):
            connection.execute(
                "update api_security_events set request_path = '/changed' where id = %s",
                (event_id,),
            )
