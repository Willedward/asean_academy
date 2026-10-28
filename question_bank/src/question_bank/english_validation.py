"""Cross-file validation for the Layer 1 English foundation."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .english_checking import normalise_text
from .english_models import (
    EnglishAssessmentForm,
    EnglishBankManifest,
    EnglishCurriculumCatalogue,
    EnglishExamProfile,
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
    exam_profile: EnglishExamProfile | None = None
    sources: SourceInventory | None = None
    passages: list[EnglishPassage] = field(default_factory=list)
    lessons: list[EnglishLesson] = field(default_factory=list)
    manifests: list[EnglishBankManifest] = field(default_factory=list)
    questions: list[EnglishObjectiveQuestion] = field(default_factory=list)
    forms: list[EnglishAssessmentForm] = field(default_factory=list)
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
        routes = ("full", "core", "sprint")
        authored_keys = {lesson.stable_key for lesson in self.lessons}
        route_keys = {
            route: self.catalogue.route_lesson_keys(route) if self.catalogue else []
            for route in routes
        }
        lesson_by_key = {lesson.stable_key: lesson for lesson in self.lessons}
        exit_ticket_keys = {
            question.stable_key
            for question in self.questions
            if question.exposure_pool == "exit_ticket"
        }
        parallel_source_keys = {
            question.parallel_form_of
            for question in self.questions
            if question.exposure_pool == "retry_review"
            and question.parallel_form_of is not None
        }

        def lesson_references(lesson_key):
            lesson = lesson_by_key.get(lesson_key)
            if lesson is None:
                return set()
            return {
                question_key
                for section in lesson.sections
                for question_key in section.question_keys
            }

        return {
            "valid": self.valid,
            "curriculum_version": self.catalogue.version_key if self.catalogue else None,
            "exam_profile_key": self.exam_profile.profile_key if self.exam_profile else None,
            "module_count": len(self.catalogue.modules) if self.catalogue else 0,
            "curriculum_lesson_count": (
                sum(len(module.lessons) for module in self.catalogue.modules)
                if self.catalogue
                else 0
            ),
            "authored_lesson_count": len(self.lessons),
            "route_lesson_counts": {route: len(route_keys[route]) for route in routes},
            "route_authored_lesson_counts": {
                route: len(set(route_keys[route]) & authored_keys) for route in routes
            },
            "route_exit_ticket_lesson_counts": {
                route: sum(
                    bool(lesson_references(lesson_key) & exit_ticket_keys)
                    for lesson_key in route_keys[route]
                )
                for route in routes
            },
            "route_parallel_retry_lesson_counts": {
                route: sum(
                    bool(lesson_references(lesson_key) & parallel_source_keys)
                    for lesson_key in route_keys[route]
                )
                for route in routes
            },
            "route_unauthored_lesson_codes": {
                route: (
                    [
                        lesson.lesson_code
                        for module in self.catalogue.modules
                        for lesson in module.lessons
                        if route in lesson.route_tags and lesson.stable_key not in authored_keys
                    ]
                    if self.catalogue
                    else []
                )
                for route in routes
            },
            "passage_count": len(self.passages),
            "bank_count": len(self.manifests),
            "question_count": len(self.questions),
            "form_count": len(self.forms),
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


def _validate_cloze_markers(question, passage, path, report):
    if question.question_type not in {"banked_cloze", "open_cloze"} or passage is None:
        return
    markers = re.findall(r"\{\{([1-9][0-9]*)\}\}", "\n".join(passage.paragraphs))
    expected = [str(part.position) for part in question.parts]
    if markers != expected:
        issue_code = (
            "banked_cloze_gap_markers"
            if question.question_type == "banked_cloze"
            else "open_cloze_gap_markers"
        )
        _issue(
            report,
            "error",
            issue_code,
            path,
            f"Passage gap markers must appear once in order: {expected}; found {markers}",
        )


def validate_english_foundation(root: Path, *, publish: bool = False) -> EnglishFoundationReport:
    root = root.resolve()
    report = EnglishFoundationReport()
    report.catalogue = _load(
        root / "catalogue.json", EnglishCurriculumCatalogue, report, "invalid_catalogue"
    )
    report.sources = _load(root / "sources.json", SourceInventory, report, "invalid_sources")
    if report.catalogue is None or report.sources is None:
        return report

    profile_path = root / "exam_profiles" / f"{report.catalogue.exam_profile_key}.json"
    report.exam_profile = _load(profile_path, EnglishExamProfile, report, "invalid_exam_profile")
    if report.exam_profile is None:
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
    unknown_profile_sources = set(report.exam_profile.source_refs) - source_keys
    if unknown_profile_sources:
        _issue(
            report,
            "error",
            "unknown_exam_profile_source",
            profile_path,
            f"Unknown source references: {sorted(unknown_profile_sources)}",
        )

    passage_rows = _load_directory(root, "passages", EnglishPassage, report, "invalid_passage")
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
            _validate_cloze_markers(question, passage, path, report)
        _validate_short_text_determinism(question, path, report)
        if publish and question.status not in {"reviewed", "published"}:
            _issue(report, "error", "question_review_required", path, question.stable_key)
        report.questions.append(question)

    retry_sources: dict[str, list[EnglishObjectiveQuestion]] = {}
    for question in report.questions:
        if question.parallel_form_of is None:
            continue
        source = question_by_key.get(question.parallel_form_of)
        if source is None:
            _issue(
                report,
                "error",
                "missing_parallel_source",
                root / "questions" / f"{question.stable_key}.json",
                question.parallel_form_of,
            )
            continue
        if source.exposure_pool != "exit_ticket":
            _issue(
                report,
                "error",
                "parallel_source_not_exit_ticket",
                root / "questions" / f"{question.stable_key}.json",
                question.parallel_form_of,
            )
        if source.outcome_code != question.outcome_code:
            _issue(
                report,
                "error",
                "parallel_outcome_mismatch",
                root / "questions" / f"{question.stable_key}.json",
                f"{question.outcome_code} does not match {source.outcome_code}",
            )
        if source.question_type != question.question_type:
            _issue(
                report,
                "error",
                "parallel_question_type_mismatch",
                root / "questions" / f"{question.stable_key}.json",
                f"{question.question_type} does not match {source.question_type}",
            )
        retry_sources.setdefault(question.parallel_form_of, []).append(question)
    for source_key, retries in retry_sources.items():
        if len(retries) > 1:
            _issue(
                report,
                "error",
                "duplicate_parallel_retry",
                root / "questions",
                f"{source_key} has parallel forms {[item.stable_key for item in retries]}",
            )

    form_rows = _load_directory(
        root, "forms", EnglishAssessmentForm, report, "invalid_assessment_form"
    )
    form_by_key = {}
    protected_form_question_owner = {}
    expected_form_pools = {
        "baseline": "baseline_diagnostic",
        "endline": "endline_diagnostic",
        "endline_reserve": "protected_reserve",
        "checkpoint": "module_checkpoint",
        "mock": "full_mock",
    }
    for path, form in form_rows:
        if path.stem != form.form_key:
            _issue(report, "error", "assessment_form_filename", path, form.form_key)
        if form.form_key in form_by_key:
            _issue(report, "error", "duplicate_assessment_form", path, form.form_key)
        form_by_key[form.form_key] = form
        if form.profile_key != report.exam_profile.profile_key:
            _issue(report, "error", "assessment_form_profile", path, form.profile_key)
        if form.form_type == "checkpoint":
            module = next(
                (
                    candidate
                    for candidate in report.catalogue.modules
                    if candidate.module_code == form.module_code
                ),
                None,
            )
            if module is None:
                _issue(
                    report,
                    "error",
                    "assessment_form_module",
                    path,
                    str(form.module_code),
                )
            else:
                module_lesson_keys = {lesson.stable_key for lesson in module.lessons}
                wrong_mastery_keys = set(form.mastery_lesson_keys) - module_lesson_keys
                if wrong_mastery_keys:
                    _issue(
                        report,
                        "error",
                        "assessment_form_mastery_scope",
                        path,
                        str(sorted(wrong_mastery_keys)),
                    )
        missing_questions = set(form.question_keys) - set(question_by_key)
        if missing_questions:
            _issue(
                report,
                "error",
                "missing_assessment_form_question",
                path,
                str(sorted(missing_questions)),
            )
        elif form.status != "planned":
            selected = [question_by_key[key] for key in form.question_keys]
            actual_distribution = {
                task_type: sum(
                    len(question.parts)
                    for question in selected
                    if question.question_type == task_type
                )
                for task_type in form.task_part_distribution
            }
            if actual_distribution != form.task_part_distribution:
                _issue(
                    report,
                    "error",
                    "assessment_form_distribution",
                    path,
                    f"Found {actual_distribution}, expected {form.task_part_distribution}",
                )
            actual_total = sum(len(question.parts) for question in selected)
            if actual_total != form.expected_scored_part_count:
                _issue(
                    report,
                    "error",
                    "assessment_form_part_count",
                    path,
                    f"Found {actual_total}, expected {form.expected_scored_part_count}",
                )
            expected_pool = expected_form_pools[form.form_type]
            wrong_pools = {
                question.stable_key: question.exposure_pool
                for question in selected
                if question.exposure_pool != expected_pool
            }
            if wrong_pools:
                _issue(
                    report,
                    "error",
                    "assessment_form_exposure_pool",
                    path,
                    f"Expected {expected_pool}; found {wrong_pools}",
                )
            if form.protected:
                for question in selected:
                    owner = protected_form_question_owner.get(question.stable_key)
                    if owner is not None:
                        _issue(
                            report,
                            "error",
                            "assessment_form_question_reuse",
                            path,
                            f"{question.stable_key} is already pinned by {owner}",
                        )
                    else:
                        protected_form_question_owner[question.stable_key] = form.form_key
        unknown = set(form.source_refs) - source_keys
        if unknown:
            _issue(report, "error", "unknown_assessment_form_source", path, str(sorted(unknown)))
        report.forms.append(form)
    for path, form in form_rows:
        if form.paired_form_key is None:
            continue
        paired = form_by_key.get(form.paired_form_key)
        if paired is None:
            _issue(
                report,
                "error",
                "missing_paired_assessment_form",
                path,
                form.paired_form_key,
            )
        elif paired.paired_form_key != form.form_key:
            _issue(
                report,
                "error",
                "asymmetric_paired_assessment_form",
                path,
                f"{form.form_key} pairs with {form.paired_form_key}, but the reverse link is absent",
            )
        elif form.form_type == "checkpoint" and (
            paired.form_type != "checkpoint"
            or paired.module_code != form.module_code
            or paired.mastery_lesson_keys != form.mastery_lesson_keys
            or paired.task_part_distribution != form.task_part_distribution
        ):
            _issue(
                report,
                "error",
                "checkpoint_pair_scope_mismatch",
                path,
                f"{form.form_key} and {paired.form_key} must share module, mastery and distribution",
            )

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

    lesson_rows = _load_directory(root, "lessons", EnglishLesson, report, "invalid_lesson")
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
        "exam-profile-v1.schema.json": EnglishExamProfile,
        "source-inventory-v1.schema.json": SourceInventory,
        "passage-v1.schema.json": EnglishPassage,
        "objective-question-v1.schema.json": EnglishObjectiveQuestion,
        "bank-manifest-v1.schema.json": EnglishBankManifest,
        "lesson-v1.schema.json": EnglishLesson,
        "assessment-form-v1.schema.json": EnglishAssessmentForm,
        "batch-manifest-v1.schema.json": EnglishBatchManifest,
        "batch-claims-v1.schema.json": EnglishBatchClaimRegistry,
    }
    for filename, model in schemas.items():
        path = output / filename
        path.write_text(json.dumps(model.model_json_schema(), indent=2) + "\n")
