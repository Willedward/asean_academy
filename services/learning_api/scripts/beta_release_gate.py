"""Generate immutable, privacy-minimal B5 Beta release evidence."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from run_dev import _configure_environment

from learning_api.beta_release import (
    PHASE_LIMITS,
    REQUIRED_CONFIRMATIONS,
    BetaReleaseRequirements,
    ReleaseCheck,
    build_evidence,
    database_checks,
    evidence_markdown,
    release_metadata_checks,
    source_checks,
)
from learning_api.course_catalogue import CourseCatalogue

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail closed unless a B5 controlled-pilot candidate is fully evidenced."
    )
    parser.add_argument("--release-sha", default=os.getenv("RELEASE_SHA", ""))
    parser.add_argument("--phase", choices=sorted(PHASE_LIMITS), required=True)
    parser.add_argument("--cohort-label", required=True)
    parser.add_argument("--cohort-size", type=int, required=True)
    parser.add_argument("--attested-by", default=os.getenv("GITHUB_ACTOR", "local-operator"))
    parser.add_argument(
        "--confirm",
        action="append",
        choices=REQUIRED_CONFIRMATIONS,
        default=[],
        help="Repeat for each completed hosted/manual release confirmation.",
    )
    parser.add_argument("--output-json", type=Path, default=Path("beta-release-evidence.json"))
    parser.add_argument("--output-markdown", type=Path, default=Path("beta-release-evidence.md"))
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write evidence but return success even when blockers remain.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _configure_environment()
    current_sha = _git("rev-parse", "HEAD")
    release_sha = args.release_sha.strip() or current_sha
    repository_clean = not bool(_git("status", "--porcelain", "--untracked-files=all"))
    requirements = BetaReleaseRequirements()
    catalogue = CourseCatalogue(REPOSITORY_ROOT, allow_drafts=True)
    checks, snapshot = source_checks(catalogue, requirements)
    checks.extend(
        release_metadata_checks(
            release_sha=release_sha,
            current_sha=current_sha,
            repository_clean=repository_clean,
            phase=args.phase,
            cohort_label=args.cohort_label,
            cohort_size=args.cohort_size,
            confirmations=set(args.confirm),
        )
    )

    database_url = os.getenv("ASEAN_ACADEMY_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        checks.extend(
            [
                ReleaseCheck(
                    "database.connection",
                    False,
                    "A server-only database URL is required for hash, approval and diagnostic checks.",
                    {"configured": False},
                )
            ]
        )
    else:
        try:
            with psycopg.connect(
                database_url,
                connect_timeout=10,
                prepare_threshold=None,
                row_factory=dict_row,
            ) as connection:
                checks.extend(database_checks(connection, catalogue, requirements))
        except psycopg.Error as exc:
            checks.append(
                ReleaseCheck(
                    "database.connection",
                    False,
                    "The release gate could not complete its PostgreSQL checks.",
                    {"error_type": type(exc).__name__, "sqlstate": exc.sqlstate},
                )
            )

    evidence = build_evidence(
        release_sha=release_sha,
        phase=args.phase,
        cohort_label=args.cohort_label,
        cohort_size=args.cohort_size,
        attested_by=args.attested_by,
        source_snapshot=snapshot,
        checks=checks,
        requirements=requirements,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(evidence_markdown(evidence), encoding="utf-8")
    print(json.dumps({"status": evidence["status"], "blockers": evidence["blockers"]}))
    return 0 if args.report_only or evidence["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
