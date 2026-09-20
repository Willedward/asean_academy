"""Cross-file validation for versioned course authoring sources."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .course_models import Course, Lesson, QuestionPools
from .validation import validate_bank


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
    pools: QuestionPools | None = None
    issues: list[CourseIssue] = field(default_factory=list)

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
            "lesson_count": len(self.lessons),
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


def validate_course(
    course_root: Path,
    question_bank_root: Path,
    *,
    publish: bool = False,
) -> CourseValidationReport:
    course_root = course_root.resolve()
    report = CourseValidationReport()
    course_path = course_root / "course.json"
    pools_path = course_root / "question_pools.json"
    report.course = _load(course_path, Course, report, "invalid_course")
    report.pools = _load(pools_path, QuestionPools, report, "invalid_question_pools")

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
    unit = course.units[0]
    if report.pools.course_key != course.stable_key:
        _issue(
            report,
            "error",
            "pool_course_mismatch",
            pools_path,
            f"Pool course is {report.pools.course_key}, expected {course.stable_key}",
        )
    if report.pools.unit_key != unit.stable_key:
        _issue(
            report,
            "error",
            "pool_unit_mismatch",
            pools_path,
            f"Pool unit is {report.pools.unit_key}, expected {unit.stable_key}",
        )
    lesson_by_key = {lesson.stable_key: lesson for lesson in report.lessons}
    references = {lesson.stable_key: lesson for lesson in unit.lessons}
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
        reference = references.get(key)
        if reference and (
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
            _issue(
                report,
                "error",
                "unknown_mastery_policy",
                key,
                lesson.mastery_policy_key,
            )
        for prerequisite in lesson.prerequisite_lessons:
            if prerequisite not in lesson_by_key:
                _issue(report, "error", "unknown_prerequisite", key, prerequisite)
            elif position_by_key[prerequisite] >= lesson.position:
                _issue(
                    report,
                    "error",
                    "prerequisite_order",
                    key,
                    f"Prerequisite {prerequisite} must appear earlier",
                )
        if not lesson.sections:
            severity = "error" if publish else "warning"
            _issue(
                report,
                severity,
                "lesson_content_required",
                key,
                "Lesson needs reviewed sections before publication",
            )
        if publish and lesson.status not in {"reviewed", "published"}:
            _issue(report, "error", "lesson_review_required", key, lesson.status)

    if publish and course.status not in {"reviewed", "published"}:
        _issue(report, "error", "course_review_required", course_path, course.status)

    bank_report = validate_bank(question_bank_root, publish=publish)
    for issue in bank_report.errors:
        _issue(report, "error", f"question_bank_{issue.code}", issue.path, issue.message)
    question_by_key = {question.stable_key: question for question in bank_report.questions}
    bank_keys = {question.bank_key for question in bank_report.questions}
    if bank_keys and bank_keys != {report.pools.bank_key}:
        _issue(
            report,
            "error",
            "pool_bank_mismatch",
            pools_path,
            f"Pool bank is {report.pools.bank_key}, question bank contains {sorted(bank_keys)}",
        )

    pools = report.pools.pools
    practice_pool_by_lesson = {
        pool.lesson_key: pool for pool in pools if pool.type == "lesson_practice"
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
    pool_type_counts = {pool_type: 0 for pool_type in course.question_allocation_counts}
    allocated_keys = set()
    for pool in pools:
        pool_type_counts[pool.type] += len(pool.items)
        lesson = lesson_by_key.get(pool.lesson_key) if pool.lesson_key else None
        if pool.type == "lesson_practice" and lesson is None:
            _issue(report, "error", "unknown_pool_lesson", pool.stable_key, str(pool.lesson_key))
        for item in pool.items:
            question = question_by_key.get(item.question_key)
            if question is None:
                _issue(
                    report,
                    "error",
                    "unknown_pool_question",
                    pool.stable_key,
                    item.question_key,
                )
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
            expected_difficulty = {"guided": 1, "independent": 2, "challenge": 3}.get(
                item.stage
            )
            if expected_difficulty and question.difficulty != expected_difficulty:
                _issue(
                    report,
                    "error",
                    "pool_difficulty_mismatch",
                    pool.stable_key,
                    f"{item.question_key} is difficulty {question.difficulty}, expected {expected_difficulty}",
                )

    if pool_type_counts != course.question_allocation_counts:
        _issue(
            report,
            "error",
            "allocation_counts",
            pools_path,
            f"Found {pool_type_counts}, expected {course.question_allocation_counts}",
        )
    question_keys = set(question_by_key)
    if allocated_keys != question_keys:
        _issue(
            report,
            "error",
            "question_allocation_inventory",
            pools_path,
            f"Unallocated: {sorted(question_keys - allocated_keys)}; unknown: {sorted(allocated_keys - question_keys)}",
        )

    checkpoint_pools = [pool for pool in pools if pool.type == "unit_checkpoint"]
    checkpoint_total = sum(len(pool.items) for pool in checkpoint_pools)
    if checkpoint_total < unit.checkpoint_question_count:
        _issue(
            report,
            "error",
            "checkpoint_capacity",
            pools_path,
            f"Checkpoint needs {unit.checkpoint_question_count}, pool has {checkpoint_total}",
        )
    return report


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
