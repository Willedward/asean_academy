import asyncio

import httpx

from learning_api.config import Settings
from learning_api.main import create_app


def app():
    return create_app(
        Settings(environment="test", cors_origins=("http://localhost:3000",), log_level="INFO")
    )


def get(path: str, *, headers: dict[str, str] | None = None):
    async def request():
        transport = httpx.ASGITransport(app=app(), raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path, headers=headers)

    return asyncio.run(request())


def test_health_uses_versioned_contract_and_request_id():
    response = get("/api/v1/health", headers={"X-Request-ID": "browser-test-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "browser-test-1"
    assert response.headers["X-Release-SHA"] == "local"
    assert response.json() == {
        "status": "ok",
        "service": "learning-api",
        "version": "0.1.0",
        "environment": "test",
        "request_id": "browser-test-1",
        "release": {
            "sha": "local",
            "deployment_id": None,
            "required_schema_revision": "202610080023",
        },
        "dependencies": {
            "course_content": "versioned_catalogue",
            "authentication": "supabase_bearer",
            "tutor": "disabled",
        },
    }


def test_invalid_request_id_is_replaced():
    response = get("/api/v1/health", headers={"X-Request-ID": "invalid id"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "invalid id"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_errors_use_the_standard_envelope():
    response = get("/api/v1/_error-contract", headers={"X-Request-ID": "error-test"})

    assert response.status_code == 418
    assert response.json() == {
        "error": {
            "code": "contract_test",
            "message": "Error contract test.",
            "request_id": "error-test",
            "details": None,
        }
    }


def test_unexpected_errors_hide_private_details():
    response = get(
        "/api/v1/_unexpected-error-contract",
        headers={"X-Request-ID": "unexpected-test"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "The server could not complete the request.",
            "request_id": "unexpected-test",
            "details": None,
        }
    }
    assert "private failure detail" not in response.text



def test_readiness_uses_local_dependencies_without_postgres():
    response = get("/api/v1/ready", headers={"X-Request-ID": "ready-test"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "learning-api",
        "version": "0.1.0",
        "environment": "test",
        "request_id": "ready-test",
        "release": {
            "sha": "local",
            "deployment_id": None,
            "required_schema_revision": "202610080023",
        },
        "dependencies": {"database": "local", "schema_status": "local", "content_status": "local"},
    }


def test_readiness_reports_content_and_connection_failures(monkeypatch):
    from unittest.mock import MagicMock

    import psycopg

    from learning_api import main
    from learning_api.content_sync import ContentSyncError

    connection = MagicMock()
    connection.__enter__.return_value.execute.return_value.fetchone.return_value = {"schema_ready": True}
    monkeypatch.setattr(main.psycopg, "connect", lambda *args, **kwargs: connection)
    configured = create_app(Settings(environment="test", cors_origins=("http://localhost:3000",),
                                     log_level="INFO", database_url="postgresql://unused"))
    async def request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=configured),
                                     base_url="http://test") as client:
            return await client.get("/api/v1/ready", headers={"X-Request-ID": "content-test"})
    for error, code in [(ContentSyncError("private mismatch"), "content_out_of_sync"),
                        (psycopg.OperationalError("private connection"), "database_unavailable")]:
        def fail(*args, error=error):
            raise error
        monkeypatch.setattr(main, "verify_database_content", fail)
        response = asyncio.run(request())
        assert response.status_code == 503
        assert response.json()["error"]["code"] == code
        assert response.json()["error"]["request_id"] == "content-test"
        assert "private" not in response.text


def test_startup_refuses_unsynchronized_content(monkeypatch):
    import pytest

    from learning_api import main
    from learning_api.content_sync import ContentSyncError

    def fail(*args):
        raise ContentSyncError("Required revision is absent")
    monkeypatch.setattr(main, "verify_database_content", fail)
    configured = create_app(Settings(environment="development", cors_origins=("http://localhost:3000",),
                                     log_level="INFO", database_url="postgresql://unused"))
    async def start():
        async with configured.router.lifespan_context(configured):
            pass
    with pytest.raises(ContentSyncError, match="Required revision"):
        asyncio.run(start())
