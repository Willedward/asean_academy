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
