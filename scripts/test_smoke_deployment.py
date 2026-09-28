import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import smoke_deployment as smoke
import verify_supabase_auth_config as auth_config


class FakeResponse:
    def __init__(self, body: dict | str, *, url: str, status: int = 200):
        self.status = status
        self.body = json.dumps(body).encode() if isinstance(body, dict) else body.encode()
        self.url = url
        self.headers = {}

    def read(self):
        return self.body

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_api_smoke_requires_release_and_environment(monkeypatch):
    replies = iter(
        [
            (
                200,
                {
                    "status": "ok",
                    "environment": "preview",
                    "release": {"sha": "abcdef123456"},
                },
                {"x-release-sha": "abcdef123456"},
            ),
            (
                200,
                {
                    "status": "ready",
                    "environment": "preview",
                    "release": {"sha": "abcdef123456"},
                },
                {},
            ),
        ]
    )
    monkeypatch.setattr(smoke, "request", lambda *_args, **_kwargs: next(replies))

    results = smoke.check_api(
        "https://api.staging.example/",
        expected_release="abcdef",
        expected_environment="preview",
        timeout=1,
    )

    assert [result.name for result in results] == ["api_health", "api_readiness"]


def test_api_smoke_rejects_the_wrong_environment(monkeypatch):
    monkeypatch.setattr(
        smoke,
        "request",
        lambda *_args, **_kwargs: (
            200,
            {
                "status": "ok",
                "environment": "production",
                "release": {"sha": "abcdef"},
            },
            {"x-release-sha": "abcdef"},
        ),
    )

    with pytest.raises(smoke.SmokeCheckError, match="not 'preview'"):
        smoke.check_api(
            "https://api.staging.example/",
            expected_release="abcdef",
            expected_environment="preview",
            timeout=1,
        )


def test_web_auth_gate_follows_protected_page_to_google_login(monkeypatch):
    response = FakeResponse(
        "<html>Continue with Google</html>",
        url="https://staging.example/login?next=%2Flearn",
    )
    monkeypatch.setattr(smoke, "urlopen", lambda *_args, **_kwargs: response)

    result = smoke.check_web_auth_gate("https://staging.example/", timeout=1)

    assert result.name == "web_auth_gate"


def test_web_auth_gate_rejects_an_unprotected_learner_page(monkeypatch):
    response = FakeResponse(
        "<html>course content</html>",
        url="https://staging.example/learn",
    )
    monkeypatch.setattr(smoke, "urlopen", lambda *_args, **_kwargs: response)

    with pytest.raises(smoke.SmokeCheckError, match="did not redirect"):
        smoke.check_web_auth_gate("https://staging.example/", timeout=1)


def test_supabase_public_smoke_requires_google(monkeypatch):
    replies = iter(
        [
            (200, {"name": "GoTrue"}, {}),
            (200, {"external": {"google": True}}, {}),
        ]
    )
    monkeypatch.setattr(smoke, "request", lambda *_args, **_kwargs: next(replies))

    results = smoke.check_supabase_auth(
        "https://project.supabase.co/",
        publishable_key="sb_publishable_test",
        timeout=1,
    )

    assert [result.name for result in results] == [
        "supabase_auth_health",
        "supabase_google_provider",
    ]


def test_management_config_requires_exact_site_callback_and_google():
    origin = "https://staging.example"
    valid = {
        "disable_signup": False,
        "external_google_enabled": True,
        "site_url": origin,
        "uri_allow_list": f"{origin}/auth/callback, http://localhost:3000/auth/callback",
    }

    assert auth_config.verify_auth_config(valid, origin)["status"] == "passed"

    invalid = {
        **valid,
        "external_google_enabled": False,
        "uri_allow_list": "http://localhost:3000/auth/callback",
    }
    with pytest.raises(RuntimeError, match="enable the Google provider"):
        auth_config.verify_auth_config(invalid, origin)


def test_management_api_request_does_not_put_token_in_url(monkeypatch):
    captured = {}

    def fake_open(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.headers["Authorization"]
        captured["timeout"] = timeout
        return FakeResponse(
            {"external_google_enabled": True},
            url=request.full_url,
        )

    monkeypatch.setattr(auth_config, "urlopen", fake_open)
    result = auth_config.fetch_auth_config("abcdefgh", "private-access-token")

    assert result["external_google_enabled"] is True
    assert "private-access-token" not in captured["url"]
    assert captured["authorization"] == "Bearer private-access-token"
    assert captured["timeout"] == 20
