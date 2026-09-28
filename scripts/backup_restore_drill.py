#!/usr/bin/env python3
"""Prove that a PostgreSQL backup restores critical ASEAN Academy data exactly."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

CRITICAL_TABLES = (
    ("auth", "users"),
    ("public", "profiles"),
    ("public", "course_enrolments"),
    ("public", "practice_sessions"),
    ("public", "session_questions"),
    ("public", "attempts"),
    ("public", "question_progress"),
    ("public", "learner_lesson_progress"),
    ("public", "learner_lesson_section_progress"),
    ("public", "mastery_events"),
    ("public", "math_question_versions"),
    ("public", "course_versions"),
    ("public", "lesson_versions"),
    ("public", "content_review_records"),
    ("public", "beta_audit_events"),
    ("public", "api_rate_limit_counters"),
    ("public", "api_security_events"),
    ("supabase_migrations", "schema_migrations"),
)


@dataclass(frozen=True, slots=True)
class TableSignature:
    rows: int
    sha256: str


def _required_url(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Set {name} to a PostgreSQL connection string.")
    return value


def _identity(database_url: str) -> tuple[str, str, str]:
    values = conninfo_to_dict(database_url)
    return (
        values.get("host", ""),
        values.get("port", "5432"),
        values.get("dbname", ""),
    )


def _pg_environment(database_url: str) -> dict[str, str]:
    values = conninfo_to_dict(database_url)
    mapping = {
        "host": "PGHOST",
        "port": "PGPORT",
        "dbname": "PGDATABASE",
        "user": "PGUSER",
        "password": "PGPASSWORD",
        "sslmode": "PGSSLMODE",
        "sslrootcert": "PGSSLROOTCERT",
    }
    environment = os.environ.copy()
    for source, target in mapping.items():
        if value := values.get(source):
            environment[target] = value
    return environment


def _assert_empty(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        count = connection.execute(
            """
            select count(*)
            from pg_tables
            where schemaname not in ('pg_catalog', 'information_schema')
            """
        ).fetchone()[0]
    if count:
        raise RuntimeError(
            "RESTORE_DATABASE_URL must point to an empty disposable database."
        )


def _signature(connection, schema: str, table: str) -> TableSignature:
    row = connection.execute(
        sql.SQL(
            """
            select count(*)::bigint,
                   encode(
                       digest(
                           coalesce(string_agg(row_text, '|' order by row_text), ''),
                           'sha256'
                       ),
                       'hex'
                   )
            from (
                select to_jsonb(source_row)::text as row_text
                from {}.{} as source_row
            ) rows
            """
        ).format(sql.Identifier(schema), sql.Identifier(table))
    ).fetchone()
    return TableSignature(rows=row[0], sha256=row[1])


def _signatures(database_url: str) -> dict[str, TableSignature]:
    with psycopg.connect(database_url) as connection:
        return {
            f"{schema}.{table}": _signature(connection, schema, table)
            for schema, table in CRITICAL_TABLES
        }


def _run(command: list[str], *, environment: dict[str, str]) -> None:
    result = subprocess.run(
        command,
        env=environment,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        executable = command[0]
        raise RuntimeError(f"{executable} failed with exit code {result.returncode}.")


def run_drill(source_url: str, restore_url: str) -> dict:
    if _identity(source_url) == _identity(restore_url):
        raise ValueError("Source and restore databases must be different.")
    for executable in ("pg_dump", "pg_restore"):
        if not shutil.which(executable):
            raise RuntimeError(f"{executable} is required for the recovery drill.")
    _assert_empty(restore_url)
    source_signatures = _signatures(source_url)

    with tempfile.TemporaryDirectory(prefix="asean-academy-recovery-") as directory:
        dump_path = os.path.join(directory, "backup.dump")
        _run(
            [
                "pg_dump",
                "--format=custom",
                "--no-owner",
                "--no-privileges",
                "--file",
                dump_path,
            ],
            environment=_pg_environment(source_url),
        )
        _run(
            [
                "pg_restore",
                "--exit-on-error",
                "--no-owner",
                "--no-privileges",
                "--dbname",
                conninfo_to_dict(restore_url)["dbname"],
                dump_path,
            ],
            environment=_pg_environment(restore_url),
        )

    restored_signatures = _signatures(restore_url)
    mismatches = [
        name
        for name, signature in source_signatures.items()
        if restored_signatures.get(name) != signature
    ]
    if mismatches:
        raise RuntimeError("Restored data differs for: " + ", ".join(mismatches))
    return {
        "status": "passed",
        "tables_verified": len(source_signatures),
        "rows_verified": {
            name: signature.rows for name, signature in source_signatures.items()
        },
    }


def main() -> int:
    result = run_drill(
        _required_url("SOURCE_DATABASE_URL"),
        _required_url("RESTORE_DATABASE_URL"),
    )
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
