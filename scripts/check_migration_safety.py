#!/usr/bin/env python3
"""Reject unreviewed destructive SQL while preserving reviewed historical migrations."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

MIGRATION_NAME = re.compile(r"^(\d{12,})_[a-z0-9_]+\.sql$")
RISK_PATTERNS = {
    "drop_object": re.compile(
        r"\bdrop\s+(?:table|column|constraint|type|function|index|schema|view)\b",
        re.IGNORECASE,
    ),
    "truncate": re.compile(r"\btruncate\b", re.IGNORECASE),
    "rename": re.compile(r"\brename\s+(?:column|table|to)\b", re.IGNORECASE),
    "alter_column_type": re.compile(
        r"\balter\s+column\s+\S+\s+type\b",
        re.IGNORECASE,
    ),
    "unbounded_delete": re.compile(r"^\s*delete\s+from\b(?!.*\bwhere\b)", re.IGNORECASE),
}


@dataclass(frozen=True)
class Finding:
    filename: str
    line_number: int
    category: str
    statement: str


def load_allowlist(path: Path) -> dict[str, list[dict[str, str]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("Migration safety allowlist must be a JSON object.")
    return data


def inspect_migrations(
    migrations_dir: Path,
    allowlist: dict[str, list[dict[str, str]]],
) -> tuple[list[Finding], list[Finding]]:
    reviewed: list[Finding] = []
    unreviewed: list[Finding] = []
    seen_versions: set[str] = set()
    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        raise ValueError("No SQL migrations were found.")

    for migration in migration_files:
        match = MIGRATION_NAME.fullmatch(migration.name)
        if not match:
            raise ValueError(f"Invalid migration filename: {migration.name}")
        version = match.group(1)
        if version in seen_versions:
            raise ValueError(f"Duplicate migration version: {version}")
        seen_versions.add(version)
        text = migration.read_text(encoding="utf-8")
        if not re.search(r"^\s*begin\s*;", text, re.IGNORECASE | re.MULTILINE):
            raise ValueError(f"{migration.name} must start an explicit transaction.")
        if not re.search(r"^\s*commit\s*;", text, re.IGNORECASE | re.MULTILINE):
            raise ValueError(f"{migration.name} must commit its transaction.")

        entries = allowlist.get(migration.name, [])
        for line_number, line in enumerate(text.splitlines(), start=1):
            statement = line.strip()
            if not statement or statement.startswith("--"):
                continue
            for category, pattern in RISK_PATTERNS.items():
                if not pattern.search(statement):
                    continue
                finding = Finding(migration.name, line_number, category, statement)
                is_reviewed = any(
                    item.get("category") == category
                    and item.get("match", "").casefold() in statement.casefold()
                    and item.get("reason", "").strip()
                    for item in entries
                )
                (reviewed if is_reviewed else unreviewed).append(finding)

    unknown_files = sorted(set(allowlist) - {item.name for item in migration_files})
    if unknown_files:
        raise ValueError(f"Allowlist references missing migrations: {', '.join(unknown_files)}")
    return reviewed, unreviewed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--migrations", type=Path, default=Path("supabase/migrations"))
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=Path("scripts/migration_safety_allowlist.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reviewed, unreviewed = inspect_migrations(
        args.migrations,
        load_allowlist(args.allowlist),
    )
    for finding in reviewed:
        print(
            f"reviewed {finding.filename}:{finding.line_number} "
            f"[{finding.category}] {finding.statement}"
        )
    if unreviewed:
        for finding in unreviewed:
            print(
                f"UNREVIEWED {finding.filename}:{finding.line_number} "
                f"[{finding.category}] {finding.statement}"
            )
        print(
            "Add an exact, justified entry to scripts/migration_safety_allowlist.json "
            "after reviewing backward compatibility and rollback."
        )
        return 1
    print(f"Migration safety check passed ({len(reviewed)} reviewed findings).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
