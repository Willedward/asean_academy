"""Environment-backed settings with safe development defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _csv(name: str, default: str) -> tuple[str, ...]:
    values = tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())
    if not values:
        raise RuntimeError(f"{name} must contain at least one value")
    return values


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    cors_origins: tuple[str, ...]
    log_level: str

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
        return cls(
            environment=environment,
            cors_origins=_csv("ASEAN_ACADEMY_CORS_ORIGINS", "http://localhost:3000"),
            log_level=log_level,
        )
