"""Read validated Git-authored course snapshots for development and import previews."""

from __future__ import annotations

from functools import cached_property
from pathlib import Path

from question_bank.course_models import ActiveRecallSection
from question_bank.course_validation import validate_course
from question_bank.validation import validate_bank

from .course_contracts import (
    CourseLessonMap,
    CourseMapResponse,
    CourseUnitMap,
    LessonResponse,
    PracticeEntry,
)

COURSE_ROOT = Path("backend_resources/courses/g3_math/secondary_1/n1/v1")
BANK_ROOT = Path("backend_resources/question_bank/g3_math/secondary_1/n1/v1")


class CatalogueError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def public_lesson_section(section) -> dict:
    """Remove checker answers and locked feedback from lesson concept checks."""
    if not isinstance(section, ActiveRecallSection):
        return section.model_dump(mode="json")
    return {
        "stable_key": section.stable_key,
        "position": section.position,
        "type": section.type,
        "title": section.title,
        "prompt": [block.model_dump(mode="json") for block in section.prompt],
        "response_type": section.response.type,
    }


class CourseCatalogue:
    def __init__(self, repository_root: Path, *, allow_drafts: bool):
        self.repository_root = repository_root.resolve()
        self.allow_drafts = allow_drafts

    @cached_property
    def report(self):
        report = validate_course(
            self.repository_root / COURSE_ROOT,
            self.repository_root / BANK_ROOT,
        )
        if not report.valid or report.course is None or report.pools is None:
            raise CatalogueError(
                "course_content_invalid",
                "The course source failed validation and is temporarily unavailable.",
                503,
            )
        return report

    @cached_property
    def questions(self):
        report = validate_bank(self.repository_root / BANK_ROOT)
        if not report.valid:
            raise CatalogueError(
                "question_bank_invalid",
                "The question bank failed validation and is temporarily unavailable.",
                503,
            )
        return report.questions

    def _assert_visible(self, status: str):
        if status != "published" and not self.allow_drafts:
            raise CatalogueError(
                "course_not_found",
                "The requested course is not available.",
                404,
            )

    def course_map(self, course_key: str) -> CourseMapResponse:
        report = self.report
        course = report.course
        if course.stable_key != course_key:
            raise CatalogueError("course_not_found", "The requested course was not found.", 404)
        self._assert_visible(course.status)

        lesson_by_key = {lesson.stable_key: lesson for lesson in report.lessons}
        units = []
        for unit in course.units:
            lesson_maps = []
            for reference in unit.lessons:
                lesson = lesson_by_key[reference.stable_key]
                material_ready = bool(lesson.sections) and lesson.status == "published"
                unlocked = not lesson.prerequisite_lessons
                lesson_maps.append(
                    CourseLessonMap(
                        stable_key=lesson.stable_key,
                        position=lesson.position,
                        title=lesson.title,
                        summary=lesson.summary,
                        outcomes=lesson.outcomes,
                        estimated_minutes=lesson.estimated_minutes,
                        objectives=lesson.objectives,
                        required_practice_count=reference.required_practice_count,
                        content_status=lesson.status,
                        learning_material_state="ready" if material_ready else "pending",
                        availability="available" if material_ready else "content_pending",
                        unlocked=unlocked,
                        unlock_reason=(
                            None if unlocked else "prerequisite_not_proficient"
                        ),
                        href=f"/lessons/{lesson.stable_key}",
                    )
                )
            units.append(
                CourseUnitMap(
                    stable_key=unit.stable_key,
                    position=unit.position,
                    title=unit.title,
                    checkpoint_question_count=unit.checkpoint_question_count,
                    checkpoint_available=False,
                    lessons=lesson_maps,
                )
            )
        return CourseMapResponse(
            stable_key=course.stable_key,
            revision=course.revision,
            title=course.title,
            description=course.description,
            subject=course.subject,
            school_level=course.school_level,
            content_status=course.status,
            development_preview=course.status != "published",
            units=units,
        )

    def lesson(self, lesson_key: str) -> LessonResponse:
        report = self.report
        course = report.course
        self._assert_visible(course.status)
        lesson = next(
            (candidate for candidate in report.lessons if candidate.stable_key == lesson_key),
            None,
        )
        if lesson is None:
            raise CatalogueError("lesson_not_found", "The requested lesson was not found.", 404)
        self._assert_visible(lesson.status)
        pool = next(
            (
                candidate
                for candidate in report.pools.pools
                if candidate.type == "lesson_practice" and candidate.lesson_key == lesson.stable_key
            ),
            None,
        )
        if pool is None:
            raise CatalogueError(
                "lesson_pool_missing",
                "Practice has not been configured for this lesson.",
                503,
            )
        material_ready = bool(lesson.sections) and lesson.status == "published"
        return LessonResponse(
            stable_key=lesson.stable_key,
            revision=lesson.revision,
            course_key=lesson.course_key,
            unit_key=lesson.unit_key,
            position=lesson.position,
            title=lesson.title,
            summary=lesson.summary,
            outcomes=lesson.outcomes,
            estimated_minutes=lesson.estimated_minutes,
            objectives=lesson.objectives,
            content_status=lesson.status,
            development_preview=lesson.status != "published",
            learning_material_state="ready" if material_ready else "pending",
            sections=[public_lesson_section(section) for section in lesson.sections],
            assets=[asset.model_dump(mode="json") for asset in lesson.assets],
            practice=PracticeEntry(
                lesson_key=lesson.stable_key,
                question_count=pool.expected_question_count,
                available=material_ready,
                development_available=self.allow_drafts and not material_ready,
                unavailable_reason=None if material_ready else "content_not_reviewed",
            ),
        )
