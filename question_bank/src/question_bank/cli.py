"""Command-line entry point for question-bank tooling."""

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from pydantic import ValidationError

from .authoring import (
    export_reviewer_batch,
    plan_all_batches,
    validate_authoring_pipeline,
    write_authoring_schemas,
    write_missing_blueprints,
)
from .catalogue import write_schemas as write_catalogue_schemas
from .catalogue_repository import CatalogueImporter
from .collaboration import (
    check_pull_request,
    claim_batch,
    release_batch_claim,
    validate_claim_registry,
)
from .course_preview import serve_course
from .course_registry import validate_course_registry
from .course_repository import CourseImporter
from .course_validation import validate_course, write_schemas
from .practice import PracticeEngine
from .practice_web import serve_practice
from .preview import serve
from .validation import validate_bank, validate_catalogue

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BANK = (
    REPOSITORY_ROOT
    / "backend_resources/question_bank/g3_math/secondary_1/n1/v1"
)
DEFAULT_COURSE = (
    REPOSITORY_ROOT
    / "backend_resources/courses/g3_math/secondary_1/n1/v1"
)
DEFAULT_BANK_CATALOGUE = REPOSITORY_ROOT / "backend_resources/question_bank/g3_math"
DEFAULT_SYLLABUS = REPOSITORY_ROOT / "backend_resources/syllabi/g3_math/v1/catalogue.json"
DEFAULT_COURSE_REGISTRY = (
    REPOSITORY_ROOT / "backend_resources/courses/g3_math/v1/registry.json"
)
DEFAULT_HOUSE_RULES = (
    REPOSITORY_ROOT / "backend_resources/question_bank/authoring/house-rules-v1.json"
)
DEFAULT_AUTHORING_SCHEMA = REPOSITORY_ROOT / "backend_resources/question_bank/schema"
DEFAULT_CLAIMS = (
    REPOSITORY_ROOT / "backend_resources/question_bank/authoring/batch-claims-v1.json"
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
    course_registry_validate = commands.add_parser(
        "course-registry-validate",
        help="Validate the complete planned and authored course registry",
    )
    course_registry_validate.add_argument(
        "registry", type=Path, nargs="?", default=DEFAULT_COURSE_REGISTRY
    )
    course_registry_validate.add_argument(
        "--syllabus", type=Path, default=DEFAULT_SYLLABUS
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
    catalogue_validate = commands.add_parser(
        "catalogue-validate", help="Validate the syllabus and every discovered question bank"
    )
    catalogue_validate.add_argument(
        "banks", type=Path, nargs="?", default=DEFAULT_BANK_CATALOGUE
    )
    catalogue_validate.add_argument("--syllabus", type=Path, default=DEFAULT_SYLLABUS)
    catalogue_validate.add_argument(
        "--publish", action="store_true", help="Require a complete reviewed catalogue"
    )
    catalogue_schema = commands.add_parser(
        "catalogue-schema", help="Generate syllabus and bank blueprint JSON Schemas"
    )
    catalogue_schema.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=REPOSITORY_ROOT / "backend_resources/syllabi/schema",
    )
    catalogue_importer = commands.add_parser(
        "catalogue-import-db",
        help="Seed syllabus metadata and import every validated question bank",
    )
    catalogue_importer.add_argument(
        "banks", type=Path, nargs="?", default=DEFAULT_BANK_CATALOGUE
    )
    catalogue_importer.add_argument("--syllabus", type=Path, default=DEFAULT_SYLLABUS)
    catalogue_importer.add_argument(
        "--publish", action="store_true", help="Require publication validation"
    )
    authoring_blueprints = commands.add_parser(
        "authoring-blueprints",
        help="Create missing 104-question blueprints for all syllabus topic groups",
    )
    authoring_blueprints.add_argument(
        "banks", type=Path, nargs="?", default=DEFAULT_BANK_CATALOGUE
    )
    authoring_blueprints.add_argument("--syllabus", type=Path, default=DEFAULT_SYLLABUS)
    authoring_blueprints.add_argument("--question-count", type=int, default=104)
    authoring_plan = commands.add_parser(
        "authoring-plan",
        help="Create controlled 20–30-question batch manifests for incomplete banks",
    )
    authoring_plan.add_argument("banks", type=Path, nargs="?", default=DEFAULT_BANK_CATALOGUE)
    authoring_plan.add_argument("--syllabus", type=Path, default=DEFAULT_SYLLABUS)
    authoring_plan.add_argument("--house-rules", type=Path, default=DEFAULT_HOUSE_RULES)
    authoring_plan.add_argument("--batch-size", type=int, default=26)
    authoring_validate = commands.add_parser(
        "authoring-validate",
        help="Validate blueprints, manifests, answers, assets, and cross-bank duplicates",
    )
    authoring_validate.add_argument(
        "banks", type=Path, nargs="?", default=DEFAULT_BANK_CATALOGUE
    )
    authoring_validate.add_argument("--syllabus", type=Path, default=DEFAULT_SYLLABUS)
    authoring_validate.add_argument("--near-duplicate-threshold", type=float, default=0.82)
    authoring_export = commands.add_parser(
        "authoring-export", help="Export one authored batch for mathematics and editorial review"
    )
    authoring_export.add_argument("manifest", type=Path)
    authoring_export.add_argument("output", type=Path)
    authoring_export.add_argument("--syllabus", type=Path, default=DEFAULT_SYLLABUS)
    authoring_schema = commands.add_parser(
        "authoring-schema", help="Generate batch-manifest and house-rule JSON Schemas"
    )
    authoring_schema.add_argument(
        "output", type=Path, nargs="?", default=DEFAULT_AUTHORING_SCHEMA
    )
    authoring_claim = commands.add_parser(
        "authoring-claim", help="Claim one planned authoring batch for a named Git branch"
    )
    authoring_claim.add_argument("batch_id")
    authoring_claim.add_argument("--owner", required=True)
    authoring_claim.add_argument("--branch", required=True)
    authoring_claim.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    authoring_claim.add_argument("--banks", type=Path, default=DEFAULT_BANK_CATALOGUE)
    authoring_release = commands.add_parser(
        "authoring-release", help="Release a completed or abandoned batch claim"
    )
    authoring_release.add_argument("batch_id")
    authoring_release.add_argument("--owner", required=True)
    authoring_release.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    authoring_claims_validate = commands.add_parser(
        "authoring-claims-validate",
        help="Validate exclusive batch claims against the current manifests",
    )
    authoring_claims_validate.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    authoring_claims_validate.add_argument(
        "--banks", type=Path, default=DEFAULT_BANK_CATALOGUE
    )
    authoring_pr_check = commands.add_parser(
        "authoring-pr-check",
        help="Validate changed authoring files, claims, duplicates, and reviewer artifacts",
    )
    authoring_pr_check.add_argument("--changed-files", type=Path, required=True)
    authoring_pr_check.add_argument("--head-branch", required=True)
    authoring_pr_check.add_argument("--output", type=Path, required=True)
    authoring_pr_check.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    authoring_pr_check.add_argument("--banks", type=Path, default=DEFAULT_BANK_CATALOGUE)
    authoring_pr_check.add_argument("--syllabus", type=Path, default=DEFAULT_SYLLABUS)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    if args.command == "authoring-claim":
        try:
            result = claim_batch(
                args.claims,
                args.banks,
                batch_id=args.batch_id,
                owner=args.owner,
                branch=args.branch,
            )
        except (OSError, ValueError, ValidationError) as exc:
            raise SystemExit(str(exc)) from exc
        print(json.dumps({"status": "complete", **result}, indent=2))
        return 0
    if args.command == "authoring-release":
        try:
            result = release_batch_claim(
                args.claims,
                batch_id=args.batch_id,
                owner=args.owner,
            )
        except (OSError, ValueError, ValidationError) as exc:
            raise SystemExit(str(exc)) from exc
        print(json.dumps({"status": "complete", **result}, indent=2))
        return 0
    if args.command == "authoring-claims-validate":
        registry, issues = validate_claim_registry(args.claims, args.banks)
        errors = [issue for issue in issues if issue.severity == "error"]
        active = [claim for claim in registry.claims if claim.active] if registry else []
        print(
            json.dumps(
                {
                    "valid": not errors,
                    "active_claim_count": len(active),
                    "history_count": len(registry.claims) if registry else 0,
                    "issues": [asdict(issue) for issue in issues],
                },
                indent=2,
            )
        )
        return 0 if not errors else 1
    if args.command == "authoring-pr-check":
        report = check_pull_request(
            changed_files=args.changed_files.read_text().splitlines(),
            head_branch=args.head_branch,
            repository_root=REPOSITORY_ROOT,
            bank_root=args.banks,
            syllabus_path=args.syllabus,
            registry_path=args.claims,
            output=args.output,
        )
        print(
            json.dumps(
                {
                    "valid": report.valid,
                    "changed_batches": report.changed_batches,
                    "exported_batches": report.exported_batches,
                    "error_count": len(report.errors),
                    "warning_count": len(report.warnings),
                    "output": str(args.output),
                },
                indent=2,
            )
        )
        return 0 if report.valid else 1
    if args.command == "authoring-blueprints":
        result = write_missing_blueprints(
            args.syllabus, args.banks, question_count=args.question_count
        )
        print(json.dumps({"status": "complete", **result}, indent=2))
        return 0
    if args.command == "authoring-plan":
        result = plan_all_batches(
            args.banks,
            REPOSITORY_ROOT,
            args.syllabus,
            args.house_rules,
            preferred_batch_size=args.batch_size,
        )
        print(json.dumps({"status": "complete", **result}, indent=2))
        return 0
    if args.command == "authoring-validate":
        report = validate_authoring_pipeline(
            args.banks,
            args.syllabus,
            repository_root=REPOSITORY_ROOT,
            near_duplicate_threshold=args.near_duplicate_threshold,
        )
        print(json.dumps(report.as_dict(), indent=2))
        return 0 if report.valid else 1
    if args.command == "authoring-export":
        result = export_reviewer_batch(
            args.manifest,
            args.output,
            repository_root=REPOSITORY_ROOT,
            syllabus_path=args.syllabus,
        )
        print(json.dumps({"status": "complete", **result}, indent=2))
        return 0
    if args.command == "authoring-schema":
        write_authoring_schemas(args.output)
        print(json.dumps({"status": "complete", "output": str(args.output)}, indent=2))
        return 0
    if args.command == "course-registry-validate":
        report = validate_course_registry(args.registry, args.syllabus)
        print(json.dumps(report.as_dict(), indent=2))
        return 0 if report.valid else 1
    if args.command == "catalogue-validate":
        report = validate_catalogue(args.banks, args.syllabus, publish=args.publish)
        print(json.dumps(report.as_dict(), indent=2))
        return 0 if report.valid else 1
    if args.command == "catalogue-schema":
        write_catalogue_schemas(args.output)
        print(json.dumps({"status": "complete", "output": str(args.output)}, indent=2))
        return 0
    if args.command == "catalogue-import-db":
        report = validate_catalogue(args.banks, args.syllabus, publish=args.publish)
        if not report.valid:
            print(json.dumps(report.as_dict(), indent=2))
            return 1
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise SystemExit("Set DATABASE_URL before running catalogue-import-db")
        try:
            import psycopg
        except ImportError as exc:
            raise SystemExit("Install the postgres extra: uv sync --extra postgres") from exc
        banks = [
            (bank.blueprint, bank.questions)
            for bank in report.banks
            if bank.blueprint is not None
        ]
        with psycopg.connect(database_url, prepare_threshold=None) as connection:
            result = CatalogueImporter(connection).import_all(report.syllabus, banks)
        print(json.dumps({"status": "complete", "result": result}, indent=2))
        return 0
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
        with psycopg.connect(database_url, prepare_threshold=None) as connection:
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
    with psycopg.connect(database_url, prepare_threshold=None) as connection:
        result = CatalogueImporter(connection).import_all(
            report.catalogue,
            [(report.blueprint, report.questions)],
        )
    print(json.dumps({"status": "complete", "result": result}, indent=2))
    return 0
