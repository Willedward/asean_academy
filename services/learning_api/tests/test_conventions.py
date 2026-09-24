import asyncio
from uuid import UUID

import pytest
from fastapi import HTTPException

from learning_api.config import Settings
from learning_api.conventions import require_idempotency_key


def test_idempotency_key_accepts_a_uuid():
    value = "7dc32a1b-1238-4f22-9bf1-fb712e15504d"
    result = asyncio.run(require_idempotency_key(value))
    assert result == UUID(value)


@pytest.mark.parametrize("value", [None, "", "not-a-uuid"])
def test_idempotency_key_fails_closed(value):
    with pytest.raises(HTTPException) as caught:
        asyncio.run(require_idempotency_key(value))
    assert caught.value.status_code == 400


def test_invalid_environment_fails_with_a_readable_error(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ENV", "somewhere")
    with pytest.raises(RuntimeError, match="ASEAN_ACADEMY_ENV"):
        Settings.from_environment()


def test_invalid_draft_content_flag_fails_with_a_readable_error(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ALLOW_DRAFT_CONTENT", "sometimes")
    with pytest.raises(RuntimeError, match="ASEAN_ACADEMY_ALLOW_DRAFT_CONTENT"):
        Settings.from_environment()


def test_production_requires_supabase_and_postgres(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ENV", "production")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("ASEAN_ACADEMY_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="SUPABASE_URL"):
        Settings.from_environment()


def test_postgres_development_learner_must_be_a_uuid(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ENV", "development")
    monkeypatch.setenv("ASEAN_ACADEMY_DATABASE_URL", "postgresql://example.test/db")
    monkeypatch.setenv("ASEAN_ACADEMY_DEVELOPMENT_LEARNER_ID", "development-learner")
    with pytest.raises(RuntimeError, match="must be a UUID"):
        Settings.from_environment()
