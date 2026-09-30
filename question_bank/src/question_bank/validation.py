"""File, bank, and multi-bank catalogue validation for authored question JSON."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .catalogue import BankBlueprint, SyllabusCatalogue, load_blueprint, load_catalogue
from .difficulty import DIFFICULTY_KEYS
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
    blueprint: BankBlueprint | None = None
    catalogue: SyllabusCatalogue | None = None

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
            "bank_key": self.blueprint.bank_key if self.blueprint else None,
            "bank_role": self.blueprint.bank_role if self.blueprint else None,
            "topic_code": self.blueprint.topic.code if self.blueprint else None,
            "school_level": self.blueprint.school_level if self.blueprint else None,
            "question_count": len(self.questions),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [asdict(issue) for issue in self.issues],
        }


@dataclass
class CatalogueValidationReport:
    syllabus: SyllabusCatalogue | None = None
    banks: list[ValidationReport] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def questions(self):
        return [question for bank in self.banks for question in bank.questions]

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
        known_topics = len(self.syllabus.topics) if self.syllabus else 0
        expected_topics = self.syllabus.expected_topic_count if self.syllabus else 0
        known_topic_groups = self.syllabus.topic_group_count if self.syllabus else 0
        expected_topic_groups = (
            self.syllabus.expected_topic_group_count if self.syllabus else 0
        )
        authored = {
            (bank.blueprint.school_level, bank.blueprint.topic.code)
            for bank in self.banks
            if bank.blueprint is not None
        }
        return {
            "valid": self.valid,
            "catalogue_version": self.syllabus.version_key if self.syllabus else None,
            "known_topic_count": known_topics,
            "expected_topic_count": expected_topics,
            "unconfirmed_topic_count": max(0, expected_topics - known_topics),
            "known_topic_group_count": known_topic_groups,
            "expected_topic_group_count": expected_topic_groups,
            "unconfirmed_topic_group_count": max(
                0, expected_topic_groups - known_topic_groups
            ),
            "bank_count": len(self.banks),
            "authored_topic_level_count": len(authored),
            "question_count": len(self.questions),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [asdict(issue) for issue in self.issues],
            "banks": [bank.as_dict() for bank in self.banks],
        }


def _issue(report, severity, code, path, message):
    report.issues.append(Issue(severity, code, str(path), message))


def _default_catalogue_path(bank_root: Path) -> Path:
    try:
        resources_root = bank_root.parents[4]
    except IndexError:
        return Path("__missing_catalogue__")
    return resources_root / "syllabi/g3_math/v1/catalogue.json"


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


def _validate_blueprint_against_catalogue(
    bank_root: Path,
    report: ValidationReport,
) -> set[str]:
    blueprint = report.blueprint
    catalogue = report.catalogue
    if blueprint is None or catalogue is None:
        return set()
    if blueprint.curriculum_version != catalogue.version_key:
        _issue(
            report,
            "error",
            "curriculum_mismatch",
            bank_root / "blueprint.json",
            f"Blueprint uses {blueprint.curriculum_version}; catalogue is {catalogue.version_key}",
        )
    topic = catalogue.topic(blueprint.topic.code)
    if topic is None:
        _issue(
            report,
            "error",
            "unknown_topic",
            bank_root / "blueprint.json",
            blueprint.topic.code,
        )
        return set()
    if topic.title.casefold() != blueprint.topic.title.casefold():
        _issue(
            report,
            "error",
            "topic_title_mismatch",
            bank_root / "blueprint.json",
            f"Blueprint title '{blueprint.topic.title}' differs from catalogue title '{topic.title}'",
        )
    allowed = topic.outcome_codes(blueprint.school_level)
    declared = {item.code for item in blueprint.outcome_distribution}
    unknown = declared - allowed
    if unknown:
        _issue(
            report,
            "error",
            "unknown_blueprint_outcome",
            bank_root / "blueprint.json",
            f"Outcomes are outside {blueprint.topic.code} {blueprint.school_level}: {sorted(unknown)}",
        )
    return allowed


def validate_bank(
    bank_root: Path,
    *,
    publish: bool = False,
    catalogue_path: Path | None = None,
) -> ValidationReport:
    bank_root = bank_root.resolve()
    report = ValidationReport()
    blueprint_path = bank_root / "blueprint.json"
    schema_path = bank_root.parents[3] / "schema" / "question-v1.schema.json"
    catalogue_path = (catalogue_path or _default_catalogue_path(bank_root)).resolve()
    try:
        report.blueprint = load_blueprint(blueprint_path)
        report.catalogue = load_catalogue(catalogue_path)
        json.loads(schema_path.read_text())
    except (OSError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        _issue(report, "error", "invalid_bank_contract", bank_root, str(exc))
        return report

    blueprint = report.blueprint
    allowed_outcomes = _validate_blueprint_against_catalogue(bank_root, report)
    declared_outcomes = {row.code for row in blueprint.outcome_distribution}
    seen = set()
    for path in sorted((bank_root / "questions").glob("*.json")):
        question = _load_question(path, report)
        if question is None:
            continue
        if question.stable_key in seen:
            _issue(report, "error", "duplicate_key", path, question.stable_key)
            continue
        seen.add(question.stable_key)
        expected = {
            "bank_key": blueprint.bank_key,
            "curriculum_version": blueprint.curriculum_version,
            "school_level": blueprint.school_level,
            "topic_code": blueprint.topic.code,
        }
        for field_name, expected_value in expected.items():
            actual_value = getattr(question, field_name)
            if actual_value != expected_value:
                _issue(
                    report,
                    "error",
                    f"wrong_{field_name}",
                    path,
                    f"Found {actual_value}, expected {expected_value}",
                )
        referenced_outcomes = {
            question.primary_outcome,
            *(part.primary_outcome for part in question.parts),
            *(code for part in question.parts for code in part.secondary_outcomes),
        }
        unknown = referenced_outcomes - allowed_outcomes
        if unknown:
            _issue(
                report,
                "error",
                "unknown_question_outcome",
                path,
                f"Outcomes are outside the syllabus catalogue: {sorted(unknown)}",
            )
        undeclared = referenced_outcomes - declared_outcomes
        if undeclared:
            _issue(
                report,
                "error",
                "undeclared_question_outcome",
                path,
                f"Outcomes are absent from the bank blueprint: {sorted(undeclared)}",
            )
        _validate_assets(bank_root, question, report)
        report.questions.append(question)

    difficulty = {level: 0 for level in DIFFICULTY_KEYS}
    outcome = {row.code: 0 for row in blueprint.outcome_distribution}
    for question in report.questions:
        difficulty[str(question.difficulty)] += 1
        if question.primary_outcome in outcome:
            outcome[question.primary_outcome] += 1

    _compare_distribution(
        report,
        difficulty,
        blueprint.difficulty_distribution,
        blueprint_path,
        "difficulty_distribution",
        publish,
    )
    expected_outcomes = {row.code: row.total for row in blueprint.outcome_distribution}
    _compare_distribution(
        report,
        outcome,
        expected_outcomes,
        blueprint_path,
        "outcome_distribution",
        publish,
    )
    if publish:
        if blueprint.status not in {"reviewed", "published"}:
            _issue(
                report,
                "error",
                "bank_review_required",
                blueprint_path,
                "Question bank must be reviewed before publication",
            )
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


def _question_fingerprint(question: Question) -> str:
    payload = question.model_dump(
        mode="json",
        exclude={
            "stable_key",
            "bank_key",
            "curriculum_version",
            "school_level",
            "topic_code",
            "status",
            "provenance",
        },
    )
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_catalogue(
    bank_catalogue_root: Path,
    syllabus_path: Path,
    *,
    publish: bool = False,
) -> CatalogueValidationReport:
    bank_catalogue_root = bank_catalogue_root.resolve()
    syllabus_path = syllabus_path.resolve()
    report = CatalogueValidationReport()
    try:
        report.syllabus = load_catalogue(syllabus_path)
    except (OSError, ValueError, ValidationError) as exc:
        _issue(report, "error", "invalid_syllabus_catalogue", syllabus_path, str(exc))
        return report

    blueprint_paths = sorted(bank_catalogue_root.glob("**/blueprint.json"))
    if not blueprint_paths:
        _issue(
            report,
            "error",
            "no_question_banks",
            bank_catalogue_root,
            "No blueprint.json files were found",
        )
        return report

    for path in blueprint_paths:
        bank_report = validate_bank(
            path.parent,
            publish=publish,
            catalogue_path=syllabus_path,
        )
        report.banks.append(bank_report)
        report.issues.extend(bank_report.issues)

    bank_keys: dict[str, Path] = {}
    stable_keys: dict[str, str] = {}
    fingerprints: dict[str, str] = {}
    for bank in report.banks:
        if bank.blueprint is None:
            continue
        key = bank.blueprint.bank_key
        if key in bank_keys:
            _issue(report, "error", "duplicate_bank_key", key, str(bank_keys[key]))
        bank_keys[key] = Path(key)
        for question in bank.questions:
            previous_bank = stable_keys.get(question.stable_key)
            if previous_bank is not None and previous_bank != key:
                _issue(
                    report,
                    "error",
                    "cross_bank_duplicate_key",
                    question.stable_key,
                    f"Appears in {previous_bank} and {key}",
                )
            stable_keys[question.stable_key] = key
            fingerprint = _question_fingerprint(question)
            previous_question = fingerprints.get(fingerprint)
            if previous_question is not None and previous_question != question.stable_key:
                _issue(
                    report,
                    "error",
                    "cross_bank_duplicate_content",
                    question.stable_key,
                    f"Matches authored content in {previous_question}",
                )
            fingerprints[fingerprint] = question.stable_key

    syllabus = report.syllabus
    missing_topics = syllabus.expected_topic_count - len(syllabus.topics)
    missing_groups = syllabus.expected_topic_group_count - syllabus.topic_group_count
    if missing_topics or missing_groups:
        _issue(
            report,
            "error" if publish else "warning",
            "incomplete_syllabus_catalogue",
            syllabus_path,
            f"Missing {missing_topics} unique topics and {missing_groups} level-specific topic groups",
        )
    if publish and syllabus.status != "active":
        _issue(
            report,
            "error",
            "syllabus_catalogue_not_active",
            syllabus_path,
            f"Catalogue status is {syllabus.status}",
        )
    return report
