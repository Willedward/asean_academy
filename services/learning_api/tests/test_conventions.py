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


def test_postgres_disables_the_implicit_development_learner(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ENV", "development")
    monkeypatch.setenv("ASEAN_ACADEMY_DATABASE_URL", "postgresql://example.test/db")
    monkeypatch.delenv("ASEAN_ACADEMY_DEVELOPMENT_LEARNER_ID", raising=False)

    settings = Settings.from_environment()

    assert settings.development_learner_id is None


def test_empty_development_learner_is_treated_as_disabled(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ENV", "development")
    monkeypatch.setenv("ASEAN_ACADEMY_DEVELOPMENT_LEARNER_ID", "")

    settings = Settings.from_environment()

    assert settings.development_learner_id is None


def test_e2e_authentication_secret_is_rejected_outside_test(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ENV", "development")
    monkeypatch.setenv(
        "ASEAN_ACADEMY_E2E_AUTH_SECRET",
        "asean-academy-local-e2e-secret-2026-only",
    )

    with pytest.raises(RuntimeError, match="allowed only in test"):
        Settings.from_environment()


def test_e2e_authentication_secret_requires_32_characters(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ENV", "test")
    monkeypatch.setenv("ASEAN_ACADEMY_E2E_AUTH_SECRET", "too-short")

    with pytest.raises(RuntimeError, match="at least 32"):
        Settings.from_environment()


def test_hosted_environment_requires_a_non_default_abuse_secret(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ENV", "preview")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("ASEAN_ACADEMY_DATABASE_URL", "postgresql://example.test/db")
    monkeypatch.delenv("ASEAN_ACADEMY_ABUSE_HASH_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="must be set"):
        Settings.from_environment()


def test_enabled_rate_limits_require_a_long_abuse_secret(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ABUSE_HASH_SECRET", "too-short")

    with pytest.raises(RuntimeError, match="at least 32"):
        Settings.from_environment()


def test_render_metadata_identifies_the_release_and_deployment(monkeypatch):
    monkeypatch.delenv("ASEAN_ACADEMY_RELEASE_SHA", raising=False)
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("RAILWAY_DEPLOYMENT_ID", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_VERSION", raising=False)
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc123")
    monkeypatch.setenv("RENDER_INSTANCE_ID", "srv-instance-1")

    settings = Settings.from_environment()

    assert settings.release_sha == "abc123"
    assert settings.deployment_id == "srv-instance-1"


def test_synthetic_tutor_provider_is_rejected_outside_tests(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_ENV", "development")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_PROVIDER", "synthetic")

    with pytest.raises(RuntimeError, match="allowed only in test"):
        Settings.from_environment()


def test_enabled_gemini_tutor_requires_server_key(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_ENABLED", "true")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        Settings.from_environment()


def test_enabled_gemini_tutor_requires_shadow_prices(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_ENABLED", "true")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "private-test-key")

    with pytest.raises(RuntimeError, match="shadow input and output prices"):
        Settings.from_environment()


def test_enabled_gemini_tutor_loads_server_only_configuration(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_ENABLED", "true")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "private-test-key")
    monkeypatch.setenv(
        "ASEAN_ACADEMY_TUTOR_GEMINI_INPUT_COST_PER_MILLION_MICROS_SGD", "1000"
    )
    monkeypatch.setenv(
        "ASEAN_ACADEMY_TUTOR_GEMINI_OUTPUT_COST_PER_MILLION_MICROS_SGD", "2000"
    )

    settings = Settings.from_environment()

    assert settings.tutor_provider == "gemini"
    assert settings.tutor_gemini_api_key == "private-test-key"
    assert settings.tutor_gemini_input_cost_per_million_micros_sgd == 1000
    assert settings.tutor_gemini_output_cost_per_million_micros_sgd == 2000


def test_hybrid_tutor_requires_the_premium_provider_key(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_ENABLED", "true")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "private-gemini-key")
    monkeypatch.setenv(
        "ASEAN_ACADEMY_TUTOR_GEMINI_INPUT_COST_PER_MILLION_MICROS_SGD", "1000"
    )
    monkeypatch.setenv(
        "ASEAN_ACADEMY_TUTOR_GEMINI_OUTPUT_COST_PER_MILLION_MICROS_SGD", "2000"
    )
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_HYBRID_ROUTING_ENABLED", "true")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_PREMIUM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        Settings.from_environment()


def test_hybrid_tutor_loads_server_only_routing_and_openai_prices(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_ENABLED", "true")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "private-gemini-key")
    monkeypatch.setenv(
        "ASEAN_ACADEMY_TUTOR_GEMINI_INPUT_COST_PER_MILLION_MICROS_SGD", "384000"
    )
    monkeypatch.setenv(
        "ASEAN_ACADEMY_TUTOR_GEMINI_OUTPUT_COST_PER_MILLION_MICROS_SGD", "3200000"
    )
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_HYBRID_ROUTING_ENABLED", "true")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_PREMIUM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "private-openai-key")
    monkeypatch.setenv(
        "ASEAN_ACADEMY_TUTOR_OPENAI_INPUT_COST_PER_MILLION_MICROS_SGD", "3200000"
    )
    monkeypatch.setenv(
        "ASEAN_ACADEMY_TUTOR_OPENAI_OUTPUT_COST_PER_MILLION_MICROS_SGD", "12800000"
    )

    settings = Settings.from_environment()

    assert settings.tutor_hybrid_routing_enabled is True
    assert settings.tutor_provider == "gemini"
    assert settings.tutor_premium_provider == "openai"
    assert settings.tutor_routing_policy_version == "math-tutor-routing-v1"
    assert settings.tutor_openai_api_key == "private-openai-key"
    assert settings.tutor_openai_input_cost_per_million_micros_sgd == 3_200_000
    assert settings.tutor_openai_output_cost_per_million_micros_sgd == 12_800_000


def test_hybrid_tutor_rejects_identical_economy_and_premium_providers(monkeypatch):
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_ENABLED", "true")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_PROVIDER", "gemini")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_PREMIUM_PROVIDER", "gemini")
    monkeypatch.setenv("ASEAN_ACADEMY_TUTOR_HYBRID_ROUTING_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "private-gemini-key")
    monkeypatch.setenv(
        "ASEAN_ACADEMY_TUTOR_GEMINI_INPUT_COST_PER_MILLION_MICROS_SGD", "1000"
    )
    monkeypatch.setenv(
        "ASEAN_ACADEMY_TUTOR_GEMINI_OUTPUT_COST_PER_MILLION_MICROS_SGD", "2000"
    )

    with pytest.raises(RuntimeError, match="distinct economy and premium providers"):
        Settings.from_environment()
