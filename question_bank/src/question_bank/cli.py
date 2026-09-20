"""Command-line entry point for question-bank tooling."""

import argparse
import json
import os
from pathlib import Path

from .course_preview import serve_course
from .course_repository import CourseImporter
from .course_validation import validate_course, write_schemas
from .practice import PracticeEngine
from .practice_web import serve_practice
from .preview import serve
from .repository import QuestionImporter
from .validation import validate_bank

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BANK = (
    REPOSITORY_ROOT
    / "backend_resources/question_bank/g3_math/secondary_1/n1/v1"
)
DEFAULT_COURSE = (
    REPOSITORY_ROOT
    / "backend_resources/courses/g3_math/secondary_1/n1/v1"
)


def parser():
    root = argparse.ArgumentParser(description="Validate, preview and import authored questions")
    commands = root.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Validate a question-bank source directory")
    validate.add_argument("bank", type=Path, nargs="?", default=DEFAULT_BANK)
    validate.add_argument("--publish", action="store_true", help="Require a complete reviewed bank")
    preview = commands.add_parser("preview", help="Serve the local reviewer preview")
    preview.add_argument("bank", type=Path, nargs="?", default=DEFAULT_BANK)
    preview.add_argument("--host", default="127.0.0.1")
    preview.add_argument("--port", type=int, default=8765)
    practice = commands.add_parser(
        "practice", help="Serve the local practice API and placeholder student interface"
    )
    practice.add_argument("bank", type=Path, nargs="?", default=DEFAULT_BANK)
    practice.add_argument("--host", default="127.0.0.1")
    practice.add_argument("--port", type=int, default=8766)
    practice.add_argument(
        "--database",
        type=Path,
        default=REPOSITORY_ROOT / "question_bank/practice-local.sqlite3",
    )
    practice.add_argument(
        "--development-drafts",
        action="store_true",
        help="Allow draft questions in this localhost-only development application",
    )
    importer = commands.add_parser("import-db", help="Import validated questions into PostgreSQL")
    importer.add_argument("bank", type=Path, nargs="?", default=DEFAULT_BANK)
    importer.add_argument("--publish", action="store_true", help="Require publication validation")
    course_validate = commands.add_parser(
        "course-validate", help="Validate course, lesson and question-pool sources"
    )
    course_validate.add_argument("course", type=Path, nargs="?", default=DEFAULT_COURSE)
    course_validate.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    course_validate.add_argument(
        "--publish", action="store_true", help="Require complete reviewed course content"
    )
    course_preview = commands.add_parser(
        "course-preview", help="Serve the local course-map author preview"
    )
    course_preview.add_argument("course", type=Path, nargs="?", default=DEFAULT_COURSE)
    course_preview.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    course_preview.add_argument("--host", default="127.0.0.1")
    course_preview.add_argument("--port", type=int, default=8767)
    course_schema = commands.add_parser(
        "course-schema", help="Generate JSON Schemas for course authoring"
    )
    course_schema.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=REPOSITORY_ROOT / "backend_resources/courses/schema",
    )
    course_importer = commands.add_parser(
        "course-import-db", help="Import a validated course snapshot into PostgreSQL"
    )
    course_importer.add_argument("course", type=Path, nargs="?", default=DEFAULT_COURSE)
    course_importer.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    course_importer.add_argument(
        "--publish", action="store_true", help="Require publication validation"
    )
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    if args.command == "validate":
        report = validate_bank(args.bank, publish=args.publish)
        print(json.dumps(report.as_dict(), indent=2))
        return 0 if report.valid else 1
    if args.command == "preview":
        report = validate_bank(args.bank)
        if not report.valid:
            print(json.dumps(report.as_dict(), indent=2))
            return 1
        serve(args.bank, args.host, args.port)
        return 0
    if args.command == "practice":
        report = validate_bank(args.bank)
        if not report.valid:
            print(json.dumps(report.as_dict(), indent=2))
            return 1
        engine = PracticeEngine(
            args.database,
            report.questions,
            allow_drafts=args.development_drafts,
        )
        serve_practice(engine, args.bank, args.host, args.port)
        return 0
    if args.command == "course-validate":
        report = validate_course(args.course, args.bank, publish=args.publish)
        print(json.dumps(report.as_dict(), indent=2))
        return 0 if report.valid else 1
    if args.command == "course-preview":
        report = validate_course(args.course, args.bank)
        if not report.valid:
            print(json.dumps(report.as_dict(), indent=2))
            return 1
        serve_course(report, args.host, args.port)
        return 0
    if args.command == "course-schema":
        write_schemas(args.output)
        print(json.dumps({"status": "complete", "output": str(args.output)}, indent=2))
        return 0
    if args.command == "course-import-db":
        report = validate_course(args.course, args.bank, publish=args.publish)
        if not report.valid:
            print(json.dumps(report.as_dict(), indent=2))
            return 1
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise SystemExit("Set DATABASE_URL before running course-import-db")
        try:
            import psycopg
        except ImportError as exc:
            raise SystemExit("Install the postgres extra: uv sync --extra postgres") from exc
        with psycopg.connect(database_url) as connection:
            result = CourseImporter(connection).import_all(
                report.course, report.lessons, report.pools
            )
        print(json.dumps({"status": "complete", "result": result}, indent=2))
        return 0
    report = validate_bank(args.bank, publish=args.publish)
    if not report.valid:
        print(json.dumps(report.as_dict(), indent=2))
        return 1
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("Set DATABASE_URL before running import-db")
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit("Install the postgres extra: uv sync --extra postgres") from exc
    with psycopg.connect(database_url) as connection:
        results = QuestionImporter(connection).import_all(report.questions)
    print(json.dumps({"status": "complete", "results": results}, indent=2))
    return 0
