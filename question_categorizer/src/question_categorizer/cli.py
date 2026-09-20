"""Command-line interface for local question categorization."""

import argparse
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from .models import CategorizationResult
from .repository import Repository
from .service import CategorizationService
from .taxonomy import load_taxonomy


def parser():
    root = argparse.ArgumentParser(
        description="Categorize reviewed OCR questions into the fixed mathematics syllabus."
    )
    commands = root.add_subparsers(dest="command", required=True)
    categorize = commands.add_parser("categorize", help="Categorize an OCR questions.json")
    categorize.add_argument("input", type=Path)
    categorize.add_argument("--output", type=Path)
    categorize.add_argument("--source-level", choices=["secondary_1", "secondary_2"])
    categorize.add_argument("--minimum-score", type=float, default=3)
    categorize.add_argument("--minimum-margin", type=float, default=0.75)
    storage = categorize.add_mutually_exclusive_group()
    storage.add_argument("--database", type=Path)
    storage.add_argument("--postgres", action="store_true")
    storage.add_argument("--json-only", action="store_true")

    initialize = commands.add_parser("init-db", help="Create tables and seed the taxonomy")
    init_storage = initialize.add_mutually_exclusive_group(required=True)
    init_storage.add_argument("--database", type=Path)
    init_storage.add_argument("--postgres", action="store_true")

    confirm = commands.add_parser("confirm", help="Confirm one suggested assignment")
    confirm.add_argument("assignment_id")
    confirm.add_argument("--reviewer", required=True)
    confirm_storage = confirm.add_mutually_exclusive_group(required=True)
    confirm_storage.add_argument("--database", type=Path)
    confirm_storage.add_argument("--postgres", action="store_true")

    review = commands.add_parser("review", help="Confirm or reject one suggested assignment")
    review.add_argument("assignment_id")
    review.add_argument("--decision", choices=["confirmed", "rejected"], required=True)
    review.add_argument("--reviewer", required=True)
    review_storage = review.add_mutually_exclusive_group(required=True)
    review_storage.add_argument("--database", type=Path)
    review_storage.add_argument("--postgres", action="store_true")

    commands.add_parser("taxonomy", help="Print the bundled taxonomy as JSON")
    commands.add_parser("schema", help="Print the categorization result JSON Schema")
    return root


def postgres_repository():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("Set DATABASE_URL before using --postgres")
    return Repository.connect_postgres(url)


def selected_repository(args, default=True):
    if getattr(args, "postgres", False):
        return postgres_repository()
    database = getattr(args, "database", None)
    if database:
        return Repository.sqlite(database)
    if default and not getattr(args, "json_only", False):
        return Repository.sqlite(Path("question_categorizer/output/categorizations.sqlite3"))
    return None


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "schema":
            print(json.dumps(CategorizationResult.model_json_schema(), indent=2))
            return 0
        if args.command == "taxonomy":
            print(load_taxonomy().model_dump_json(indent=2))
            return 0
        if args.command == "init-db":
            with selected_repository(args, default=False) as repository:
                repository.seed_taxonomy(load_taxonomy())
            print(json.dumps({"status": "initialized"}))
            return 0
        if args.command == "confirm":
            with selected_repository(args, default=False) as repository:
                repository.confirm(args.assignment_id, args.reviewer)
            print(json.dumps({"status": "confirmed", "assignment_id": args.assignment_id}))
            return 0
        if args.command == "review":
            with selected_repository(args, default=False) as repository:
                repository.review_assignment(args.assignment_id, args.reviewer, args.decision)
            print(json.dumps({"status": args.decision, "assignment_id": args.assignment_id}))
            return 0

        service = CategorizationService(
            minimum_score=args.minimum_score,
            minimum_margin=args.minimum_margin,
        )
        result = service.categorize_file(args.input, source_level=args.source_level)
        destination = args.output or args.input.with_name("categorization.json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(result.model_dump_json(indent=2) + "\n")
        temporary.replace(destination)
        repository = selected_repository(args)
        if repository:
            with repository:
                repository.save(result, service.taxonomy)
        print(
            json.dumps(
                {
                    "status": "complete",
                    "branch": "question_categorier",
                    "run_id": str(result.run_id),
                    "questions": len(result.questions),
                    "classified": sum(q.status == "classified" for q in result.questions),
                    "unclassified": sum(q.status == "unclassified" for q in result.questions),
                    "rejected": sum(q.status == "rejected" for q in result.questions),
                    "output": str(destination.resolve()),
                }
            )
        )
        return 0
    except (OSError, ValueError, RuntimeError, ValidationError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
