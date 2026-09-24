import asyncio
from pathlib import Path

import httpx

from learning_api.config import Settings
from learning_api.identity import AuthenticatedLearner, StaticTokenVerifier
from learning_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
LEARNER_A = "00000000-0000-4000-8000-000000000001"
LEARNER_B = "00000000-0000-4000-8000-000000000002"


def application(tmp_path: Path):
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
                "token-a": AuthenticatedLearner(LEARNER_A, "authenticated", "a@example.test"),
                "token-b": AuthenticatedLearner(LEARNER_B, "authenticated", "b@example.test"),
            }
        ),
    )


def request(app, method: str, path: str, token: str | None = None, **kwargs):
    async def send():
        headers = dict(kwargs.pop("headers", {}))
        if token:
            headers["Authorization"] = f"Bearer {token}"
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, headers=headers, **kwargs)

    return asyncio.run(send())


def create_session(app, token: str, key: str):
    return request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        token,
        headers={"Idempotency-Key": key},
        json={"lesson_key": "n1-lesson-01", "mode": "guided_practice"},
    )


def test_private_routes_require_a_valid_bearer_token(tmp_path):
    app = application(tmp_path)

    missing = request(app, "GET", "/api/v1/progress")
    invalid = request(app, "GET", "/api/v1/progress", "invalid")

    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert missing.json()["error"]["code"] == "authentication_required"
    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == "invalid_access_token"


def test_verified_learners_have_isolated_progress_and_sessions(tmp_path):
    app = application(tmp_path)

    started = request(app, "POST", "/api/v1/lessons/n1-lesson-01/start", "token-a")
    assert started.status_code == 200

    learner_a = request(app, "GET", "/api/v1/progress", "token-a").json()
    learner_b = request(app, "GET", "/api/v1/progress", "token-b").json()
    assert learner_a["learner_id"] == LEARNER_A
    assert learner_a["lessons"][0]["state"] == "in_progress"
    assert learner_b["learner_id"] == LEARNER_B
    assert learner_b["lessons"][0]["state"] == "not_started"

    first = create_session(app, "token-a", "same-browser-key")
    second = create_session(app, "token-b", "same-browser-key")
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["session_id"] != second.json()["session_id"]

    forbidden_as_not_found = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{first.json()['session_id']}",
        "token-b",
    )
    assert forbidden_as_not_found.status_code == 404
    assert forbidden_as_not_found.json()["error"]["code"] == "session_not_found"


def test_supabase_asymmetric_token_verification_checks_signature_issuer_and_audience():
    from datetime import UTC, datetime, timedelta
    from types import SimpleNamespace

    import jwt
    import pytest
    from cryptography.hazmat.primitives.asymmetric import rsa

    from learning_api.identity import AuthenticationError, SupabaseTokenVerifier

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = SupabaseTokenVerifier("https://project-ref.supabase.co")
    verifier.jwks = SimpleNamespace(
        get_signing_key_from_jwt=lambda _token: SimpleNamespace(key=private_key.public_key())
    )
    now = datetime.now(UTC)
    claims = {
        "sub": LEARNER_A,
        "email": "a@example.test",
        "role": "authenticated",
        "aud": "authenticated",
        "iss": "https://project-ref.supabase.co/auth/v1",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    token = jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test"})

    learner = verifier.verify(token)
    assert learner.learner_id == LEARNER_A
    assert learner.email == "a@example.test"
    assert learner.source == "supabase_jwks"

    wrong_audience = jwt.encode(
        {**claims, "aud": "unexpected"},
        private_key,
        algorithm="RS256",
        headers={"kid": "test"},
    )
    with pytest.raises(AuthenticationError, match="expired or invalid"):
        verifier.verify(wrong_audience)
