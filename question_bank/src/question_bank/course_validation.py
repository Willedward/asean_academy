"""Cross-file validation for versioned course authoring sources."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .catalogue import load_blueprint
from .course_models import (
    Course,
    Lesson,
    QuestionPoolCollection,
    QuestionPools,
)
from .difficulty import PRACTICE_STAGE_DIFFICULTIES
from .validation import ValidationReport, validate_bank


@dataclass(frozen=True)
class CourseIssue:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class CourseValidationReport:
    course: Course | None = None
    lessons: list[Lesson] = field(default_factory=list)
    pools: QuestionPoolCollection | None = None
    bank_reports: dict[str, ValidationReport] = field(default_factory=dict)
    issues: list[CourseIssue] = field(default_factory=list)

    @property
    def questions(self):
        return [
            question
            for bank in self.bank_reports.values()
            for question in bank.questions
        ]

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
            "course_key": self.course.stable_key if self.course else None,
            "unit_count": len(self.course.units) if self.course else 0,
            "lesson_count": len(self.lessons),
            "pool_manifest_count": len(self.pools.manifests) if self.pools else 0,
            "pool_count": len(self.pools.pools) if self.pools else 0,
            "allocated_question_count": (
                sum(len(pool.items) for pool in self.pools.pools) if self.pools else 0
            ),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [asdict(issue) for issue in self.issues],
        }


def _issue(report, severity, code, path, message):
    report.issues.append(CourseIssue(severity, code, str(path), message))


def _load(path: Path, model, report: CourseValidationReport, code: str):
    try:
        return model.model_validate_json(path.read_text())
    except (OSError, ValueError, ValidationError) as exc:
        _issue(report, "error", code, path, str(exc))
        return None


def _validate_assets(course_root: Path, lesson: Lesson, report: CourseValidationReport):
    for asset in lesson.assets:
        path = course_root / asset.path
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


def _pool_paths(course_root: Path) -> list[Path]:
    legacy = course_root / "question_pools.json"
    paths = [legacy] if legacy.is_file() else []
    paths.extend(sorted((course_root / "question_pools").glob("*.json")))
    return paths


def _bank_root_for(question_bank_root: Path, bank_key: str) -> Path | None:
    direct = question_bank_root / "blueprint.json"
    candidates = [direct] if direct.is_file() else sorted(question_bank_root.glob("**/blueprint.json"))
    for path in candidates:
        try:
            if load_blueprint(path).bank_key == bank_key:
                return path.parent
        except (OSError, ValueError, ValidationError):
            continue
    return None


def validate_course(
    course_root: Path,
    question_bank_root: Path,
    *,
    publish: bool = False,
) -> CourseValidationReport:
    course_root = course_root.resolve()
    question_bank_root = question_bank_root.resolve()
    report = CourseValidationReport()
    course_path = course_root / "course.json"
    report.course = _load(course_path, Course, report, "invalid_course")

    manifests = []
    pool_paths = _pool_paths(course_root)
    if not pool_paths:
        _issue(
            report,
            "error",
            "invalid_question_pools",
            course_root,
            "No question-pool manifests were found",
        )
    for path in pool_paths:
        manifest = _load(path, QuestionPools, report, "invalid_question_pools")
        if manifest is not None:
            manifests.append(manifest)
    if manifests:
        try:
            report.pools = QuestionPoolCollection(manifests=manifests)
        except ValidationError as exc:
            _issue(report, "error", "invalid_question_pools", course_root, str(exc))

    lessons_dir = course_root / "lessons"
    seen = set()
    for path in sorted(lessons_dir.glob("*.json")):
        lesson = _load(path, Lesson, report, "invalid_lesson")
        if lesson is None:
            continue
        if path.stem != lesson.stable_key:
            _issue(
                report,
                "error",
                "lesson_filename_mismatch",
                path,
                f"Filename must be {lesson.stable_key}.json",
            )
        if lesson.stable_key in seen:
            _issue(report, "error", "duplicate_lesson", path, lesson.stable_key)
            continue
        seen.add(lesson.stable_key)
        _validate_assets(course_root, lesson, report)
        report.lessons.append(lesson)

    if report.course is None or report.pools is None:
        return report

    course = report.course
    unit_by_key = {unit.stable_key: unit for unit in course.units}
    manifest_by_unit = {manifest.unit_key: manifest for manifest in report.pools.manifests}
    if set(manifest_by_unit) != set(unit_by_key):
        _issue(
            report,
            "error",
            "pool_unit_inventory",
            course_root,
            f"Missing manifests: {sorted(set(unit_by_key) - set(manifest_by_unit))}; "
            f"extra manifests: {sorted(set(manifest_by_unit) - set(unit_by_key))}",
        )

    references = {
        lesson.stable_key: (unit, lesson)
        for unit in course.units
        for lesson in unit.lessons
    }
    lesson_by_key = {lesson.stable_key: lesson for lesson in report.lessons}
    if set(lesson_by_key) != set(references):
        missing = sorted(set(references) - set(lesson_by_key))
        extra = sorted(set(lesson_by_key) - set(references))
        _issue(
            report,
            "error",
            "lesson_inventory",
            lessons_dir,
            f"Missing lessons: {missing}; extra lessons: {extra}",
        )

    policy_keys = {policy.key for policy in course.mastery_policies}
    position_by_key = {key: lesson.position for key, lesson in lesson_by_key.items()}
    for key, lesson in lesson_by_key.items():
        parent = references.get(key)
        if parent is None:
            continue
        unit, reference = parent
        if (
            lesson.position != reference.position
            or lesson.title != reference.title
            or lesson.outcomes != reference.outcomes
        ):
            _issue(
                report,
                "error",
                "lesson_reference_mismatch",
                key,
                "Lesson position, title, or outcomes differ from course.json",
            )
        if lesson.course_key != course.stable_key or lesson.unit_key != unit.stable_key:
            _issue(report, "error", "lesson_parent", key, "Lesson has the wrong course or unit")
        if lesson.mastery_policy_key not in policy_keys:
            _issue(report, "error", "unknown_mastery_policy", key, lesson.mastery_policy_key)
        for prerequisite in lesson.prerequisite_lessons:
            prerequisite_parent = references.get(prerequisite)
            if prerequisite not in lesson_by_key or prerequisite_parent is None:
                _issue(report, "error", "unknown_prerequisite", key, prerequisite)
            elif prerequisite_parent[0].stable_key != unit.stable_key:
                _issue(
                    report,
                    "error",
                    "cross_unit_prerequisite",
                    key,
                    f"Prerequisite {prerequisite} belongs to another unit",
                )
            elif position_by_key[prerequisite] >= lesson.position:
                _issue(
                    report,
                    "error",
                    "prerequisite_order",
                    key,
                    f"Prerequisite {prerequisite} must appear earlier",
                )
        if not lesson.sections:
            _issue(
                report,
                "error" if publish else "warning",
                "lesson_content_required",
                key,
                "Lesson needs reviewed sections before publication",
            )
        if publish and lesson.status not in {"reviewed", "published"}:
            _issue(report, "error", "lesson_review_required", key, lesson.status)

    if publish and course.status not in {"reviewed", "published"}:
        _issue(report, "error", "course_review_required", course_path, course.status)

    pool_type_counts = {pool_type: 0 for pool_type in course.question_allocation_counts}
    for unit in course.units:
        manifest = manifest_by_unit.get(unit.stable_key)
        if manifest is None:
            continue
        path = next(
            (item for item in pool_paths if _load_pool_identity(item) == (manifest.unit_key, manifest.bank_key)),
            course_root,
        )
        if manifest.course_key != course.stable_key:
            _issue(
                report,
                "error",
                "pool_course_mismatch",
                path,
                f"Pool course is {manifest.course_key}, expected {course.stable_key}",
            )
        bank_root = _bank_root_for(question_bank_root, manifest.bank_key)
        if bank_root is None:
            _issue(report, "error", "missing_pool_bank", path, manifest.bank_key)
            continue
        bank_report = validate_bank(bank_root, publish=publish)
        report.bank_reports[manifest.bank_key] = bank_report
        for issue in bank_report.errors:
            _issue(report, "error", f"question_bank_{issue.code}", issue.path, issue.message)
        blueprint = bank_report.blueprint
        if blueprint is not None:
            if blueprint.topic.code != unit.topic_code:
                _issue(
                    report,
                    "error",
                    "unit_bank_topic_mismatch",
                    path,
                    f"Unit uses {unit.topic_code}; bank uses {blueprint.topic.code}",
                )
            if (
                blueprint.curriculum_version != course.curriculum_version
                or blueprint.school_level != course.school_level
            ):
                _issue(
                    report,
                    "error",
                    "unit_bank_curriculum_mismatch",
                    path,
                    "Bank curriculum or school level differs from the course",
                )
            syllabus_topic = (
                bank_report.catalogue.topic(unit.topic_code)
                if bank_report.catalogue is not None
                else None
            )
            allowed_outcomes = (
                syllabus_topic.outcome_codes(course.school_level)
                if syllabus_topic is not None
                else set()
            )
            for reference in unit.lessons:
                if not reference.stable_key.startswith(f"{unit.topic_code.lower()}-lesson-"):
                    _issue(
                        report,
                        "error",
                        "lesson_topic_key_mismatch",
                        reference.stable_key,
                        f"Lesson key must match unit topic {unit.topic_code}",
                    )
                unknown_outcomes = set(reference.outcomes) - allowed_outcomes
                if unknown_outcomes:
                    _issue(
                        report,
                        "error",
                        "lesson_outcome_catalogue_mismatch",
                        reference.stable_key,
                        f"Outcomes are outside {unit.topic_code} {course.school_level}: "
                        f"{sorted(unknown_outcomes)}",
                    )
        question_by_key = {question.stable_key: question for question in bank_report.questions}
        lesson_refs = {reference.stable_key: reference for reference in unit.lessons}
        practice_pool_by_lesson = {
            pool.lesson_key: pool
            for pool in manifest.pools
            if pool.type == "lesson_practice"
        }
        for reference in unit.lessons:
            pool = practice_pool_by_lesson.get(reference.stable_key)
            if pool is None:
                _issue(
                    report,
                    "error",
                    "missing_lesson_pool",
                    reference.stable_key,
                    "Lesson has no practice pool",
                )
            elif pool.expected_question_count != reference.required_practice_count:
                _issue(
                    report,
                    "error",
                    "required_practice_count",
                    reference.stable_key,
                    f"Course requires {reference.required_practice_count}, pool contains "
                    f"{pool.expected_question_count}",
                )
        allocated_keys = set()
        for pool in manifest.pools:
            pool_type_counts[pool.type] += len(pool.items)
            lesson = lesson_by_key.get(pool.lesson_key) if pool.lesson_key else None
            if pool.type == "lesson_practice" and pool.lesson_key not in lesson_refs:
                _issue(report, "error", "unknown_pool_lesson", pool.stable_key, str(pool.lesson_key))
            for item in pool.items:
                question = question_by_key.get(item.question_key)
                if question is None:
                    _issue(report, "error", "unknown_pool_question", pool.stable_key, item.question_key)
                    continue
                allocated_keys.add(item.question_key)
                if lesson and question.primary_outcome not in lesson.outcomes:
                    _issue(
                        report,
                        "error",
                        "pool_outcome_mismatch",
                        pool.stable_key,
                        f"{item.question_key} outcome {question.primary_outcome} is outside {lesson.outcomes}",
                    )
                allowed_difficulties = PRACTICE_STAGE_DIFFICULTIES[item.stage]
                if question.difficulty not in allowed_difficulties:
                    _issue(
                        report,
                        "error",
                        "pool_difficulty_mismatch",
                        pool.stable_key,
                        f"{item.question_key} is difficulty {question.difficulty}; "
                        f"{item.stage} allows {sorted(allowed_difficulties)}",
                    )
        question_keys = set(question_by_key)
        if allocated_keys != question_keys:
            _issue(
                report,
                "error",
                "question_allocation_inventory",
                path,
                f"Unallocated: {sorted(question_keys - allocated_keys)}; "
                f"unknown: {sorted(allocated_keys - question_keys)}",
            )
        checkpoint_total = sum(
            len(pool.items) for pool in manifest.pools if pool.type == "unit_checkpoint"
        )
        if checkpoint_total < unit.checkpoint_question_count:
            _issue(
                report,
                "error",
                "checkpoint_capacity",
                path,
                f"Checkpoint needs {unit.checkpoint_question_count}, pool has {checkpoint_total}",
            )

    if pool_type_counts != course.question_allocation_counts:
        _issue(
            report,
            "error",
            "allocation_counts",
            course_root,
            f"Found {pool_type_counts}, expected {course.question_allocation_counts}",
        )
    return report


def _load_pool_identity(path: Path) -> tuple[str, str] | None:
    try:
        item = QuestionPools.model_validate_json(path.read_text())
        return item.unit_key, item.bank_key
    except (OSError, ValueError, ValidationError):
        return None


def schema_documents():
    return {
        "course-v1.schema.json": Course.model_json_schema(),
        "lesson-v1.schema.json": Lesson.model_json_schema(),
        "question-pools-v1.schema.json": QuestionPools.model_json_schema(),
    }


def write_schemas(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    for filename, schema in schema_documents().items():
        (output / filename).write_text(json.dumps(schema, indent=2) + "\n")
