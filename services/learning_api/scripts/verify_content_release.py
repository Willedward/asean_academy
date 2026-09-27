"""Fail a release when non-draft content lacks recorded human approval."""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from run_dev import _configure_environment

from learning_api.content_review import verify_release_workflow
from learning_api.course_catalogue import CourseCatalogue

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    _configure_environment()
    database_url = (
        os.getenv("ASEAN_ACADEMY_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("PRODUCTION_DATABASE_URL")
    )
    if not database_url:
        raise SystemExit("Set a server-only database URL before checking a content release.")
    catalogue = CourseCatalogue(REPOSITORY_ROOT, allow_drafts=True)
    try:
        with psycopg.connect(
            database_url,
            connect_timeout=10,
            prepare_threshold=None,
            row_factory=dict_row,
        ) as connection:
            result = verify_release_workflow(connection, catalogue)
    except psycopg.Error as exc:
        raise SystemExit(
            f"Content release check could not reach PostgreSQL "
            f"({type(exc).__name__}, SQLSTATE {exc.sqlstate or 'unavailable'})."
        ) from None
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
