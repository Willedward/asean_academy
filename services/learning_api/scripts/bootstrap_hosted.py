"""Apply reviewed migrations and immutable content before a preview deployment."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping

import psycopg
from bootstrap_local import bootstrap


def hosted_database_url(environment: Mapping[str, str]) -> str:
    """Return the preview database URL while refusing unsafe environments."""
    if environment.get("ASEAN_ACADEMY_ENV", "").strip().lower() != "preview":
        raise ValueError("Hosted bootstrap requires ASEAN_ACADEMY_ENV=preview.")
    value = (
        environment.get("ASEAN_ACADEMY_DATABASE_URL")
        or environment.get("DATABASE_URL")
        or ""
    ).strip()
    if not value:
        raise ValueError("ASEAN_ACADEMY_DATABASE_URL is required for hosted bootstrap.")
    return value


def main() -> None:
    try:
        result = bootstrap(hosted_database_url(os.environ), apply=True)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from None
    except psycopg.Error as exc:
        raise SystemExit(
            "Hosted database bootstrap failed "
            f"({type(exc).__name__}, SQLSTATE {exc.sqlstate or 'unavailable'})."
        ) from None
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
