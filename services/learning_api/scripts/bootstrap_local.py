"""Preview or apply pending migrations and validated content using saved API settings."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import psycopg
from question_bank.catalogue_repository import CatalogueImporter
from question_bank.course_repository import CourseImporter
from run_dev import REPOSITORY_ROOT, _configure_environment

from learning_api.config import Settings
from learning_api.content_sync import check_content
from learning_api.course_catalogue import CourseCatalogue

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))
from check_migration_safety import inspect_migrations  # noqa: E402


def import_question_catalogue(connection, report):
    bank_reports = list(report.bank_reports.values())
    if not bank_reports or bank_reports[0].catalogue is None:
        raise ValueError("Validated course has no syllabus catalogue")
    banks = [
        (bank.blueprint, bank.questions)
        for bank in bank_reports
        if bank.blueprint is not None
    ]
    return CatalogueImporter(connection).import_all(
        bank_reports[0].catalogue,
        banks,
    )


def migration_body(path: Path) -> str:
    sql = path.read_text(encoding="utf-8").strip()
    if not re.match(r"^begin;", sql, re.I) or not re.search(r"commit;$", sql, re.I):
        raise ValueError(f"{path.name} must wrap its statements in begin/commit.")
    return sql[len("begin;"):-len("commit;")].strip()


def lock(connection):
    # Transaction locks work through Supabase's transaction pooler.
    connection.execute("select pg_advisory_xact_lock(20260927, 9)")


def bootstrap(database_url: str, *, apply: bool) -> dict:
    catalogue = CourseCatalogue(REPOSITORY_ROOT, allow_drafts=True)
    report = catalogue.report
    questions = catalogue.questions
    directory = REPOSITORY_ROOT / "supabase/migrations"
    allowlist = json.loads((REPOSITORY_ROOT / "scripts/migration_safety_allowlist.json").read_text())
    _, unreviewed = inspect_migrations(directory, allowlist)
    if unreviewed:
        raise ValueError("Unreviewed destructive migration found; bootstrap refused.")
    with psycopg.connect(database_url, connect_timeout=15, prepare_threshold=None) as connection:
        with connection.transaction():
            lock(connection)
            ledger = connection.execute(
                "select to_regclass('supabase_migrations.schema_migrations')"
            ).fetchone()[0]
            applied = {row[0] for row in connection.execute(
                "select version from supabase_migrations.schema_migrations"
            )} if ledger else set()
            local = {p.name.split("_", 1)[0]: p for p in sorted(directory.glob("*.sql"))}
            if applied - local.keys():
                raise ValueError("Database contains migrations absent from this branch; use the newer branch.")
            pending = [p for version, p in local.items() if version not in applied]
            if applied and any(p.name.split("_", 1)[0] < max(applied) for p in pending):
                raise ValueError("Migration history has gaps; reconcile it before bootstrapping.")
        print("Pending migrations:", ", ".join(p.name for p in pending) or "none")
        print(f"Validated course revision {report.course.revision}; {len(questions)} questions.")
        if not apply:
            if not pending:
                with connection.transaction(force_rollback=True):
                    lock(connection)
                    import_question_catalogue(connection, report)
                    CourseImporter(connection).import_all(report.course, report.lessons, report.pools)
                    check_content(connection, catalogue)
                print("Content import preview passed; transaction rolled back.")
            return {"applied": False, "pending_migrations": len(pending)}
        if not ledger:
            with connection.transaction():
                lock(connection)
                connection.execute("create schema if not exists supabase_migrations")
                connection.execute("""create table if not exists supabase_migrations.schema_migrations (
                    version text primary key, statements text[], name text)""")
        for migration in pending:
            version, name = migration.stem.split("_", 1)
            with connection.transaction():
                lock(connection)
                # Another invocation may have applied this while we waited.
                if connection.execute("select 1 from supabase_migrations.schema_migrations where version=%s",
                                      (version,)).fetchone():
                    continue
                connection.execute(migration_body(migration))
                connection.execute("""insert into supabase_migrations.schema_migrations
                    (version, statements, name) values (%s, %s::text[], %s)""",
                    (version, [], name))
            print(f"Applied {migration.name}")
        with connection.transaction():
            lock(connection)
            import_question_catalogue(connection, report)
            CourseImporter(connection).import_all(report.course, report.lessons, report.pools)
            result = check_content(connection, catalogue)
        print("Imported and verified content. Enrolments and credentials were not changed.")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply the previewed plan")
    args = parser.parse_args()
    _configure_environment()
    settings = Settings.from_environment()
    if settings.environment != "development":
        raise SystemExit("Local bootstrap requires ASEAN_ACADEMY_ENV=development.")
    if not settings.database_url:
        raise SystemExit("Run corepack pnpm setup:api to save a verified database connection.")
    try:
        print(json.dumps(bootstrap(settings.database_url, apply=args.apply), indent=2))
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from None
    except psycopg.Error as exc:
        raise SystemExit(f"Database operation failed ({type(exc).__name__}, SQLSTATE {exc.sqlstate or 'unavailable'}). Check connectivity and the schema; credentials were not modified.") from None


if __name__ == "__main__":
    main()
