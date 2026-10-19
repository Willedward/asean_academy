"""Cross-file validation for the Layer 1 English foundation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .english_checking import normalise_text
from .english_models import (
    EnglishBankManifest,
    EnglishCurriculumCatalogue,
    EnglishLesson,
    EnglishObjectiveQuestion,
    EnglishPassage,
    ShortTextResponse,
    SourceInventory,
    passage_content_hash,
)


@dataclass(frozen=True)
class EnglishIssue:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class EnglishFoundationReport:
    catalogue: EnglishCurriculumCatalogue | None = None
    sources: SourceInventory | None = None
    passages: list[EnglishPassage] = field(default_factory=list)
    lessons: list[EnglishLesson] = field(default_factory=list)
    manifests: list[EnglishBankManifest] = field(default_factory=list)
    questions: list[EnglishObjectiveQuestion] = field(default_factory=list)
    issues: list[EnglishIssue] = field(default_factory=list)

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
            "curriculum_version": self.catalogue.version_key if self.catalogue else None,
            "module_count": len(self.catalogue.modules) if self.catalogue else 0,
            "curriculum_lesson_count": (
                sum(len(module.lessons) for module in self.catalogue.modules)
                if self.catalogue
                else 0
            ),
            "authored_lesson_count": len(self.lessons),
            "passage_count": len(self.passages),
            "bank_count": len(self.manifests),
            "question_count": len(self.questions),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [asdict(issue) for issue in self.issues],
        }


def _issue(report, severity, code, path, message):
    report.issues.append(EnglishIssue(severity, code, str(path), message))


def _load(path: Path, model, report: EnglishFoundationReport, code: str):
    try:
        return model.model_validate_json(path.read_text())
    except (OSError, ValueError, ValidationError) as exc:
        _issue(report, "error", code, path, str(exc))
        return None


def _load_directory(root, folder, model, report, code):
    values = []
    for path in sorted((root / folder).glob("*.json")):
        value = _load(path, model, report, code)
        if value is not None:
            values.append((path, value))
    return values


def _validate_short_text_determinism(question, path, report):
    for part in question.parts:
        spec = part.response
        if not isinstance(spec, ShortTextResponse):
            continue
        raw = [spec.canonical_answer, *spec.accepted_alternatives]
        normalised = [normalise_text(value, spec.normalisation) for value in raw]
        if len(normalised) != len(set(normalised)):
            _issue(
                report,
                "error",
                "duplicate_normalised_answer",
                path,
                "Approved short-text answers collapse to the same normalised value",
            )


def validate_english_foundation(
    root: Path, *, publish: bool = False
) -> EnglishFoundationReport:
    root = root.resolve()
    report = EnglishFoundationReport()
    report.catalogue = _load(
        root / "catalogue.json", EnglishCurriculumCatalogue, report, "invalid_catalogue"
    )
    report.sources = _load(
        root / "sources.json", SourceInventory, report, "invalid_sources"
    )
    if report.catalogue is None or report.sources is None:
        return report

    source_keys = {source.source_key for source in report.sources.sources}
    unknown_catalogue_sources = set(report.catalogue.source_refs) - source_keys
    if unknown_catalogue_sources:
        _issue(
            report,
            "error",
            "unknown_catalogue_source",
            root / "catalogue.json",
            f"Unknown source references: {sorted(unknown_catalogue_sources)}",
        )

    passage_rows = _load_directory(
        root, "passages", EnglishPassage, report, "invalid_passage"
    )
    passage_by_key = {}
    for path, passage in passage_rows:
        if path.stem != passage.stable_key:
            _issue(report, "error", "passage_filename", path, passage.stable_key)
        key = (passage.stable_key, passage.revision)
        if key in passage_by_key:
            _issue(report, "error", "duplicate_passage_revision", path, str(key))
        passage_by_key[key] = passage
        actual_hash = passage_content_hash(passage)
        if actual_hash != passage.content_sha256:
            _issue(
                report,
                "error",
                "passage_checksum",
                path,
                f"Expected {passage.content_sha256}, found {actual_hash}",
            )
        unknown = set(passage.provenance.source_refs) - source_keys
        if unknown:
            _issue(report, "error", "unknown_passage_source", path, str(sorted(unknown)))
        report.passages.append(passage)

    manifest_rows = _load_directory(
        root, "banks", EnglishBankManifest, report, "invalid_bank_manifest"
    )
    manifest_by_key = {}
    for path, manifest in manifest_rows:
        if path.stem != manifest.bank_key:
            _issue(report, "error", "bank_filename", path, manifest.bank_key)
        if manifest.bank_key in manifest_by_key:
            _issue(report, "error", "duplicate_bank", path, manifest.bank_key)
        manifest_by_key[manifest.bank_key] = manifest
        if not set(manifest.outcome_codes) <= report.catalogue.outcome_codes():
            _issue(report, "error", "unknown_manifest_outcome", path, manifest.bank_key)
        unknown = set(manifest.source_refs) - source_keys
        if unknown:
            _issue(report, "error", "unknown_manifest_source", path, str(sorted(unknown)))
        report.manifests.append(manifest)

    question_rows = _load_directory(
        root, "questions", EnglishObjectiveQuestion, report, "invalid_question"
    )
    question_by_key = {}
    for path, question in question_rows:
        if path.stem != question.stable_key:
            _issue(report, "error", "question_filename", path, question.stable_key)
        if question.stable_key in question_by_key:
            _issue(report, "error", "duplicate_question", path, question.stable_key)
        question_by_key[question.stable_key] = question
        manifest = manifest_by_key.get(question.bank_key)
        if manifest is None:
            _issue(report, "error", "unknown_question_bank", path, question.bank_key)
        elif question.outcome_code not in manifest.outcome_codes:
            _issue(report, "error", "question_outside_bank_outcomes", path, question.outcome_code)
        if question.outcome_code not in report.catalogue.outcome_codes():
            _issue(report, "error", "unknown_question_outcome", path, question.outcome_code)
        unknown = set(question.provenance.source_refs) - source_keys
        if unknown:
            _issue(report, "error", "unknown_question_source", path, str(sorted(unknown)))
        if question.passage_ref is not None:
            ref = question.passage_ref
            passage = passage_by_key.get((ref.stable_key, ref.revision))
            if passage is None:
                _issue(report, "error", "missing_passage_revision", path, ref.stable_key)
            elif passage.content_sha256 != ref.content_sha256:
                _issue(report, "error", "passage_pin_checksum", path, ref.stable_key)
        _validate_short_text_determinism(question, path, report)
        if publish and question.status not in {"reviewed", "published"}:
            _issue(report, "error", "question_review_required", path, question.stable_key)
        report.questions.append(question)

    for bank_key, manifest in manifest_by_key.items():
        questions = [question for question in report.questions if question.bank_key == bank_key]
        if len(questions) != manifest.expected_question_count:
            severity = "error" if publish else "warning"
            _issue(
                report,
                severity,
                "bank_question_count",
                root / "banks" / f"{bank_key}.json",
                f"Found {len(questions)}, expected {manifest.expected_question_count}",
            )
        actual_pools = {}
        for question in questions:
            actual_pools[question.exposure_pool] = actual_pools.get(question.exposure_pool, 0) + 1
        if actual_pools != manifest.pool_distribution:
            _issue(
                report,
                "error" if publish else "warning",
                "bank_pool_distribution",
                root / "banks" / f"{bank_key}.json",
                f"Found {actual_pools}, expected {manifest.pool_distribution}",
            )
        if publish and manifest.status not in {"reviewed", "published"}:
            _issue(
                report,
                "error",
                "bank_review_required",
                root / "banks" / f"{bank_key}.json",
                bank_key,
            )

    lesson_rows = _load_directory(
        root, "lessons", EnglishLesson, report, "invalid_lesson"
    )
    for path, lesson in lesson_rows:
        if path.stem != lesson.stable_key:
            _issue(report, "error", "lesson_filename", path, lesson.stable_key)
        if lesson.stable_key not in report.catalogue.lesson_keys():
            _issue(report, "error", "unknown_lesson", path, lesson.stable_key)
        if lesson.outcome_code not in report.catalogue.outcome_codes():
            _issue(report, "error", "unknown_lesson_outcome", path, lesson.outcome_code)
        referenced = {key for section in lesson.sections for key in section.question_keys}
        missing = referenced - set(question_by_key)
        if missing:
            _issue(report, "error", "missing_lesson_question", path, str(sorted(missing)))
        unknown = set(lesson.provenance.source_refs) - source_keys
        if unknown:
            _issue(report, "error", "unknown_lesson_source", path, str(sorted(unknown)))
        if publish and lesson.status not in {"reviewed", "published"}:
            _issue(report, "error", "lesson_review_required", path, lesson.stable_key)
        report.lessons.append(lesson)

    return report


def write_english_schemas(output: Path):
    from .english_authoring import EnglishBatchClaimRegistry, EnglishBatchManifest

    output.mkdir(parents=True, exist_ok=True)
    schemas = {
        "catalogue-v1.schema.json": EnglishCurriculumCatalogue,
        "source-inventory-v1.schema.json": SourceInventory,
        "passage-v1.schema.json": EnglishPassage,
        "objective-question-v1.schema.json": EnglishObjectiveQuestion,
        "bank-manifest-v1.schema.json": EnglishBankManifest,
        "lesson-v1.schema.json": EnglishLesson,
        "batch-manifest-v1.schema.json": EnglishBatchManifest,
        "batch-claims-v1.schema.json": EnglishBatchClaimRegistry,
    }
    for filename, model in schemas.items():
        path = output / filename
        path.write_text(json.dumps(model.model_json_schema(), indent=2) + "\n")
