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
            "required_schema_revision": "202609270008",
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
            "required_schema_revision": "202609270008",
        },
        "dependencies": {"database": "local", "schema_status": "local"},
    }
