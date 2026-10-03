"""Environment-backed settings with safe development defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
REQUIRED_SCHEMA_REVISION = "202610030017"


def _csv(name: str, default: str) -> tuple[str, ...]:
    values = tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())
    if not values:
        raise RuntimeError(f"{name} must contain at least one value")
    return values


def _boolean(name: str, default: bool) -> bool:
    raw = os.getenv(name, "true" if default else "false").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be true or false")


def _positive_integer(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a positive integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    cors_origins: tuple[str, ...]
    log_level: str
    log_format: str = "text"
    slow_request_ms: int = 1000
    release_sha: str = "local"
    deployment_id: str | None = None
    repository_root: Path = DEFAULT_REPOSITORY_ROOT
    allow_draft_content: bool = False
    practice_database: Path | None = None
    development_learner_id: str | None = None
    database_url: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_jwt_audience: str = "authenticated"
    e2e_auth_secret: str | None = None
    rate_limits_enabled: bool = True
    abuse_hash_secret: str = "development-only-abuse-hash-secret"
    trust_proxy_headers: bool = False
    max_request_body_bytes: int = 65536
    tutor_enabled: bool = False
    tutor_provider: str = "disabled"
    tutor_daily_message_limit: int = 10
    tutor_daily_token_limit: int = 20000
    tutor_monthly_cost_limit_micros_sgd: int = 7_000_000
    tutor_academy_monthly_cost_limit_micros_sgd: int = 7_000_000_000
    tutor_max_input_tokens: int = 5000
    tutor_max_output_tokens: int = 1000
    tutor_max_turn_cost_micros_sgd: int = 250_000
    tutor_model_policy_version: str = "math-tutor-policy-v1"
    tutor_prompt_version: str = "math-tutor-prompt-v1"

    @classmethod
    def from_environment(cls) -> Settings:
        environment = os.getenv("ASEAN_ACADEMY_ENV", "development").strip().lower()
        if environment not in {"development", "test", "preview", "production"}:
            raise RuntimeError(
                "ASEAN_ACADEMY_ENV must be development, test, preview, or production"
            )
        log_level = os.getenv("ASEAN_ACADEMY_LOG_LEVEL", "INFO").strip().upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise RuntimeError("ASEAN_ACADEMY_LOG_LEVEL is invalid")
        log_format = (
            os.getenv(
                "ASEAN_ACADEMY_LOG_FORMAT",
                "json" if environment in {"preview", "production"} else "text",
            )
            .strip()
            .lower()
        )
        if log_format not in {"text", "json"}:
            raise RuntimeError("ASEAN_ACADEMY_LOG_FORMAT must be text or json")
        release_sha = (
            os.getenv("ASEAN_ACADEMY_RELEASE_SHA")
            or os.getenv("RAILWAY_GIT_COMMIT_SHA")
            or os.getenv("RENDER_GIT_COMMIT")
            or os.getenv("OTEL_SERVICE_VERSION")
            or "local"
        ).strip()
        if not release_sha or len(release_sha) > 128:
            raise RuntimeError("ASEAN_ACADEMY_RELEASE_SHA must contain 1 to 128 characters")
        database_url = (
            value
            if (
                value := os.getenv(
                    "ASEAN_ACADEMY_DATABASE_URL", os.getenv("DATABASE_URL", "")
                ).strip()
            )
            else None
        )
        development_learner_value = os.getenv("ASEAN_ACADEMY_DEVELOPMENT_LEARNER_ID")
        if environment in {"development", "test"}:
            if development_learner_value is None:
                development_learner_id = None if database_url else "development-learner"
            else:
                development_learner_id = development_learner_value.strip() or None
        else:
            development_learner_id = None
        e2e_auth_secret = os.getenv("ASEAN_ACADEMY_E2E_AUTH_SECRET", "").strip() or None
        if e2e_auth_secret and environment != "test":
            raise RuntimeError("ASEAN_ACADEMY_E2E_AUTH_SECRET is allowed only in test")
        if e2e_auth_secret and len(e2e_auth_secret) < 32:
            raise RuntimeError("ASEAN_ACADEMY_E2E_AUTH_SECRET must contain at least 32 characters")
        settings = cls(
            environment=environment,
            cors_origins=_csv("ASEAN_ACADEMY_CORS_ORIGINS", "http://localhost:3000"),
            log_level=log_level,
            log_format=log_format,
            slow_request_ms=_positive_integer("ASEAN_ACADEMY_SLOW_REQUEST_MS", 1000),
            release_sha=release_sha,
            deployment_id=(
                value
                if (
                    value := (
                        os.getenv("RAILWAY_DEPLOYMENT_ID")
                        or os.getenv("RENDER_INSTANCE_ID")
                        or ""
                    ).strip()
                )
                else None
            ),
            repository_root=Path(
                os.getenv("ASEAN_ACADEMY_REPOSITORY_ROOT", DEFAULT_REPOSITORY_ROOT)
            )
            .expanduser()
            .resolve(),
            allow_draft_content=_boolean(
                "ASEAN_ACADEMY_ALLOW_DRAFT_CONTENT",
                environment in {"development", "test"},
            ),
            practice_database=(
                Path(value).expanduser().resolve()
                if (value := os.getenv("ASEAN_ACADEMY_PRACTICE_DATABASE"))
                else None
            ),
            development_learner_id=development_learner_id,
            database_url=database_url,
            supabase_url=(
                value.rstrip("/") if (value := os.getenv("SUPABASE_URL", "").strip()) else None
            ),
            supabase_anon_key=(
                value if (value := os.getenv("SUPABASE_ANON_KEY", "").strip()) else None
            ),
            supabase_jwt_audience=os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated").strip(),
            e2e_auth_secret=e2e_auth_secret,
            rate_limits_enabled=_boolean("ASEAN_ACADEMY_RATE_LIMITS_ENABLED", True),
            abuse_hash_secret=os.getenv(
                "ASEAN_ACADEMY_ABUSE_HASH_SECRET",
                "development-only-abuse-hash-secret",
            ).strip(),
            trust_proxy_headers=_boolean("ASEAN_ACADEMY_TRUST_PROXY_HEADERS", False),
            max_request_body_bytes=_positive_integer(
                "ASEAN_ACADEMY_MAX_REQUEST_BODY_BYTES", 65536
            ),
            tutor_enabled=_boolean("ASEAN_ACADEMY_TUTOR_ENABLED", False),
            tutor_provider=os.getenv("ASEAN_ACADEMY_TUTOR_PROVIDER", "disabled")
            .strip()
            .lower(),
            tutor_daily_message_limit=_positive_integer(
                "ASEAN_ACADEMY_TUTOR_DAILY_MESSAGE_LIMIT", 10
            ),
            tutor_daily_token_limit=_positive_integer(
                "ASEAN_ACADEMY_TUTOR_DAILY_TOKEN_LIMIT", 20000
            ),
            tutor_monthly_cost_limit_micros_sgd=_positive_integer(
                "ASEAN_ACADEMY_TUTOR_MONTHLY_COST_LIMIT_MICROS_SGD", 7_000_000
            ),
            tutor_academy_monthly_cost_limit_micros_sgd=_positive_integer(
                "ASEAN_ACADEMY_TUTOR_ACADEMY_MONTHLY_COST_LIMIT_MICROS_SGD",
                7_000_000_000,
            ),
            tutor_max_input_tokens=_positive_integer(
                "ASEAN_ACADEMY_TUTOR_MAX_INPUT_TOKENS", 5000
            ),
            tutor_max_output_tokens=_positive_integer(
                "ASEAN_ACADEMY_TUTOR_MAX_OUTPUT_TOKENS", 1000
            ),
            tutor_max_turn_cost_micros_sgd=_positive_integer(
                "ASEAN_ACADEMY_TUTOR_MAX_TURN_COST_MICROS_SGD", 250_000
            ),
            tutor_model_policy_version=os.getenv(
                "ASEAN_ACADEMY_TUTOR_MODEL_POLICY_VERSION", "math-tutor-policy-v1"
            ).strip(),
            tutor_prompt_version=os.getenv(
                "ASEAN_ACADEMY_TUTOR_PROMPT_VERSION", "math-tutor-prompt-v1"
            ).strip(),
        )
        if environment in {"preview", "production"}:
            if not settings.supabase_url:
                raise RuntimeError("SUPABASE_URL is required in preview and production")
            if not settings.database_url:
                raise RuntimeError(
                    "ASEAN_ACADEMY_DATABASE_URL is required in preview and production"
                )
        if environment == "production" and settings.allow_draft_content:
            raise RuntimeError("Draft course content cannot be enabled in production")
        if settings.rate_limits_enabled and len(settings.abuse_hash_secret) < 32:
            raise RuntimeError(
                "ASEAN_ACADEMY_ABUSE_HASH_SECRET must contain at least 32 characters"
            )
        if environment in {"preview", "production"} and (
            settings.abuse_hash_secret == "development-only-abuse-hash-secret"
        ):
            raise RuntimeError(
                "ASEAN_ACADEMY_ABUSE_HASH_SECRET must be set in preview and production"
            )
        if settings.database_url and settings.development_learner_id:
            try:
                UUID(settings.development_learner_id)
            except ValueError as exc:
                raise RuntimeError(
                    "ASEAN_ACADEMY_DEVELOPMENT_LEARNER_ID must be a UUID when PostgreSQL is enabled"
                ) from exc
        if settings.tutor_provider not in {"disabled", "synthetic"}:
            raise RuntimeError(
                "ASEAN_ACADEMY_TUTOR_PROVIDER must be disabled or synthetic"
            )
        if settings.tutor_provider == "synthetic" and environment != "test":
            raise RuntimeError(
                "ASEAN_ACADEMY_TUTOR_PROVIDER=synthetic is allowed only in test"
            )
        if not settings.tutor_model_policy_version or not settings.tutor_prompt_version:
            raise RuntimeError("Tutor policy and prompt versions must not be empty")
        return settings
