"""Environment-backed settings with safe development defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


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


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    cors_origins: tuple[str, ...]
    log_level: str
    repository_root: Path = DEFAULT_REPOSITORY_ROOT
    allow_draft_content: bool = False
    practice_database: Path | None = None
    development_learner_id: str | None = None
    database_url: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_jwt_audience: str = "authenticated"

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
        settings = cls(
            environment=environment,
            cors_origins=_csv("ASEAN_ACADEMY_CORS_ORIGINS", "http://localhost:3000"),
            log_level=log_level,
            repository_root=Path(
                os.getenv("ASEAN_ACADEMY_REPOSITORY_ROOT", DEFAULT_REPOSITORY_ROOT)
            ).expanduser().resolve(),
            allow_draft_content=_boolean(
                "ASEAN_ACADEMY_ALLOW_DRAFT_CONTENT",
                environment in {"development", "test"},
            ),
            practice_database=(
                Path(value).expanduser().resolve()
                if (value := os.getenv("ASEAN_ACADEMY_PRACTICE_DATABASE"))
                else None
            ),
            development_learner_id=(
                os.getenv("ASEAN_ACADEMY_DEVELOPMENT_LEARNER_ID", "development-learner")
                if environment in {"development", "test"}
                else None
            ),
            database_url=(
                value
                if (value := os.getenv(
                    "ASEAN_ACADEMY_DATABASE_URL", os.getenv("DATABASE_URL", "")
                ).strip())
                else None
            ),
            supabase_url=(
                value.rstrip("/")
                if (value := os.getenv("SUPABASE_URL", "").strip())
                else None
            ),
            supabase_anon_key=(
                value if (value := os.getenv("SUPABASE_ANON_KEY", "").strip()) else None
            ),
            supabase_jwt_audience=os.getenv(
                "SUPABASE_JWT_AUDIENCE", "authenticated"
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
        if settings.database_url and settings.development_learner_id:
            try:
                UUID(settings.development_learner_id)
            except ValueError as exc:
                raise RuntimeError(
                    "ASEAN_ACADEMY_DEVELOPMENT_LEARNER_ID must be a UUID when PostgreSQL is enabled"
                ) from exc
        return settings
