"""File and bank-level validation for authored question JSON."""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .models import Question


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class ValidationReport:
    questions: list[Question] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self):
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self):
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def valid(self):
        return not self.errors

    def as_dict(self):
        return {
            "valid": self.valid,
            "question_count": len(self.questions),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [asdict(issue) for issue in self.issues],
        }


def _issue(report, severity, code, path, message):
    report.issues.append(Issue(severity, code, str(path), message))


def _load_question(path: Path, report: ValidationReport):
    try:
        question = Question.model_validate_json(path.read_text())
    except (OSError, ValueError, ValidationError) as exc:
        _issue(report, "error", "invalid_question", path, str(exc))
        return None
    if path.stem != question.stable_key:
        _issue(
            report,
            "error",
            "filename_mismatch",
            path,
            f"Filename must be {question.stable_key}.json",
        )
    return question


def _validate_assets(bank_root: Path, question: Question, report: ValidationReport):
    for asset in question.assets:
        path = bank_root / asset.path
        if not path.is_file():
            _issue(report, "error", "missing_asset", path, f"Missing asset {asset.asset_key}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != asset.sha256:
            _issue(
                report,
                "error",
                "asset_checksum",
                path,
                f"Expected {asset.sha256}, found {digest}",
            )


def _compare_distribution(report, actual, expected, path, code, publish):
    for key, expected_count in expected.items():
        actual_count = actual.get(str(key), 0)
        if actual_count > expected_count:
            _issue(
                report,
                "error",
                code,
                path,
                f"{key}: found {actual_count}, blueprint allows {expected_count}",
            )
        elif actual_count < expected_count:
            severity = "error" if publish else "warning"
            _issue(
                report,
                severity,
                code,
                path,
                f"{key}: found {actual_count}, blueprint requires {expected_count}",
            )


def validate_bank(bank_root: Path, *, publish: bool = False) -> ValidationReport:
    bank_root = bank_root.resolve()
    report = ValidationReport()
    blueprint_path = bank_root / "blueprint.json"
    schema_path = bank_root.parents[3] / "schema" / "question-v1.schema.json"
    try:
        blueprint = json.loads(blueprint_path.read_text())
        json.loads(schema_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        _issue(report, "error", "invalid_bank_contract", bank_root, str(exc))
        return report

    seen = set()
    for path in sorted((bank_root / "questions").glob("*.json")):
        question = _load_question(path, report)
        if question is None:
            continue
        if question.stable_key in seen:
            _issue(report, "error", "duplicate_key", path, question.stable_key)
            continue
        seen.add(question.stable_key)
        if question.bank_key != blueprint["bank_key"]:
            _issue(report, "error", "wrong_bank", path, question.bank_key)
        _validate_assets(bank_root, question, report)
        report.questions.append(question)

    difficulty = {str(level): 0 for level in (1, 2, 3)}
    outcome = {row["code"]: 0 for row in blueprint["outcome_distribution"]}
    for question in report.questions:
        difficulty[str(question.difficulty)] += 1
        outcome[question.primary_outcome] += 1

    _compare_distribution(
        report,
        difficulty,
        blueprint["difficulty_distribution"],
        blueprint_path,
        "difficulty_distribution",
        publish,
    )
    expected_outcomes = {row["code"]: row["total"] for row in blueprint["outcome_distribution"]}
    _compare_distribution(
        report,
        outcome,
        expected_outcomes,
        blueprint_path,
        "outcome_distribution",
        publish,
    )
    if publish:
        for question in report.questions:
            if question.status not in {"reviewed", "published"}:
                _issue(
                    report,
                    "error",
                    "review_required",
                    question.stable_key,
                    "Question must be reviewed before publication",
                )
    return report
