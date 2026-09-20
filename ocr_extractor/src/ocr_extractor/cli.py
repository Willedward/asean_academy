import argparse
import json
import logging
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from .files import atomic_json
from .models import DEFAULT_MODEL, ExtractionResult, Metadata, Settings
from .pdf import ExtractionError
from .repository import Repository
from .service import ExtractionService, discover_pdfs


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Extract PDF exam questions into JSON and a database."
    )
    commands = root.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="Process one PDF or recursively process a folder")
    extract.add_argument(
        "input", nargs="?", type=Path, default=Path("backend_resources/sample_papers")
    )
    extract.add_argument("--output", type=Path, default=Path("ocr_extractor/output"))
    extract.add_argument("--backend", choices=["hybrid", "local", "vision"], default="hybrid")
    extract.add_argument("--ocr", choices=["auto", "off", "required"], default="auto")
    extract.add_argument("--language", default="eng")
    extract.add_argument("--tessdata", help="Directory containing Tesseract .traineddata files")
    extract.add_argument("--dpi", type=int, default=220)
    extract.add_argument("--no-preprocess", action="store_true")
    extract.add_argument("--review-threshold", type=float, default=0.9)
    extract.add_argument("--paddle-device", default="cpu")
    extract.add_argument(
        "--formula-model",
        choices=["PP-FormulaNet_plus-M", "PP-FormulaNet_plus-L", "UniMERNet"],
        default="PP-FormulaNet_plus-M",
    )
    extract.add_argument("--max-pages", type=int, default=100)
    extract.add_argument("--max-file-mb", type=int, default=100)
    extract.add_argument("--model", default=os.environ.get("OCR_MODEL", DEFAULT_MODEL))
    extract.add_argument("--school")
    extract.add_argument("--year", type=int)
    extract.add_argument("--assessment-type")
    extract.add_argument("--source-level")
    extract.add_argument("--track", choices=["sec1_entry", "sec3_entry"])
    extract.add_argument(
        "--force",
        action="store_true",
        help="Rebuild document output (successful vision page calls remain cached)",
    )
    extract.add_argument("--verbose", action="store_true")
    storage = extract.add_mutually_exclusive_group()
    storage.add_argument(
        "--database", type=Path, help="SQLite path; default: OUTPUT/questions.sqlite3"
    )
    storage.add_argument(
        "--postgres", action="store_true", help="Use DATABASE_URL from the environment"
    )
    storage.add_argument("--json-only", action="store_true", help="Skip database persistence")
    initialize = commands.add_parser("init-db", help="Initialize the extractor staging schema")
    db = initialize.add_mutually_exclusive_group(required=True)
    db.add_argument("--database", type=Path)
    db.add_argument("--postgres", action="store_true", help="Use DATABASE_URL from the environment")
    commands.add_parser("schema", help="Print the versioned result JSON schema")
    review = commands.add_parser("review", help="Open the local human review workbench")
    review.add_argument("--output", type=Path, default=Path("ocr_extractor/output"))
    review.add_argument("--port", type=int, default=8765)
    review_db = review.add_mutually_exclusive_group()
    review_db.add_argument("--database", type=Path)
    review_db.add_argument("--postgres", action="store_true")
    evaluate = commands.add_parser("evaluate", help="Compare an export with an annotated paper")
    evaluate.add_argument("result", type=Path)
    evaluate.add_argument("fixture", type=Path)
    evaluate.add_argument("--output", type=Path)
    return root


def _postgres():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ExtractionError("missing_database_url", "Set DATABASE_URL before using --postgres.")
    return Repository.connect_postgres(url)


def _extract(args) -> int:
    settings = Settings(
        backend=args.backend,
        ocr=args.ocr,
        language=args.language,
        tessdata=args.tessdata,
        dpi=args.dpi,
        preprocess=not args.no_preprocess,
        review_threshold=args.review_threshold,
        paddle_device=args.paddle_device,
        formula_model=args.formula_model,
        max_pages=args.max_pages,
        max_file_mb=args.max_file_mb,
        model=args.model,
        metadata=Metadata(
            school=args.school,
            year=args.year,
            assessment_type=args.assessment_type,
            source_level=args.source_level,
            target_track=args.track,
        ),
    )
    paths = discover_pdfs(args.input)
    if args.input.is_dir():
        # Generated original.pdf copies must not become new inputs on subsequent batches.
        paths = [p for p in paths if not p.resolve().is_relative_to(args.output.resolve())]
        if not paths:
            raise ExtractionError("no_pdfs", "No input PDFs found outside the output directory.")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("ocr_extractor").setLevel(logging.DEBUG if args.verbose else logging.INFO)
    repository = None
    if not args.json_only:
        repository = (
            _postgres()
            if args.postgres
            else Repository.sqlite(
                args.database or args.output / "questions.sqlite3",
            )
        )
    service = ExtractionService(args.output, settings)
    outcomes = []
    try:
        for path in paths:
            try:
                result = service.extract_file(path, force=args.force)
                if repository:
                    repository.save(result)
                outcome = {
                    "input": str(path),
                    "status": "complete" if result.questions else "no_questions",
                    "document_id": str(result.document.id),
                    "questions": len(result.questions),
                    "review_status": "needs_review",
                    "questions_needing_review": len(result.questions),
                    "json": str(service.result_path(result)),
                    "warnings": result.warnings,
                }
            except Exception as exc:
                # One bad PDF must not stop a batch. Keep provider/DB internals out of logs.
                outcome = {
                    "input": str(path),
                    "status": "failed",
                    "error_code": exc.code
                    if isinstance(exc, ExtractionError)
                    else "processing_failed",
                    "message": str(exc)
                    if isinstance(exc, ExtractionError)
                    else (f"Processing or database write failed ({type(exc).__name__})."),
                }
            outcomes.append(outcome)
            print(json.dumps(outcome, ensure_ascii=False))
    finally:
        if repository:
            repository.close()
    atomic_json(args.output / "batch-report.json", {"files": outcomes})
    return 1 if any(o["status"] != "complete" for o in outcomes) else 0


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "schema":
            print(json.dumps(ExtractionResult.model_json_schema(), indent=2))
            return 0
        if args.command == "init-db":
            with _postgres() if args.postgres else Repository.sqlite(args.database) as repository:
                repository.initialize()
            print("Extractor staging schema initialized.")
            return 0
        if args.command == "review":
            from .review import serve

            with (
                _postgres()
                if args.postgres
                else Repository.sqlite(
                    args.database or args.output / "questions.sqlite3"
                ) as repository
            ):
                repository.initialize()
                serve(args.output, args.port, repository)
            return 0
        if args.command == "evaluate":
            from .evaluate import evaluate

            report = evaluate(
                ExtractionResult.model_validate_json(args.result.read_text()),
                json.loads(args.fixture.read_text()),
            )
            if args.output:
                atomic_json(args.output, report)
            print(json.dumps(report, indent=2))
            return 0 if report["passed"] else 1
        return _extract(args)
    except (ExtractionError, ValidationError) as exc:
        message = (
            str(exc)
            if isinstance(exc, ExtractionError)
            else str(
                [{"field": e["loc"], "message": e["msg"]} for e in exc.errors(include_input=False)]
            )
        )
        print(json.dumps({"error": message}), file=sys.stderr)
        return 2
    except Exception as exc:
        print(json.dumps({"error": f"Command failed ({type(exc).__name__})."}), file=sys.stderr)
        return 2
