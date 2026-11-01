#!/usr/bin/env python3
"""Evaluate a private, already-captured essay calibration package offline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from learning_api.english_essay_calibration import (
    CalibrationPackage,
    evaluate_calibration,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate 12-16 private educator anchors and captured provider outputs. "
            "This command never calls a provider."
        )
    )
    parser.add_argument("package", type=Path, help="Private calibration package JSON")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the privacy-safe aggregate gate report",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        source = json.loads(args.package.read_text(encoding="utf-8"))
        package = CalibrationPackage.model_validate(source)
        report = evaluate_calibration(package)
    except (OSError, json.JSONDecodeError, ValidationError):
        # Pydantic details may echo private essay text, so never print them here.
        print("Calibration package is missing or invalid; no report was produced.", file=sys.stderr)
        return 2

    rendered = report.model_dump_json(indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
