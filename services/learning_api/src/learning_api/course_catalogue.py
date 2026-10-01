"""Read validated Git-authored course snapshots for development and import previews."""

from __future__ import annotations

from functools import cached_property
from pathlib import Path

from question_bank.authoring import load_manifest
from question_bank.course_models import ActiveRecallSection
from question_bank.course_registry import validate_course_registry
from question_bank.course_validation import validate_course
from question_bank.validation import validate_catalogue

from .course_contracts import (
    CourseLessonMap,
    CourseMapResponse,
    CourseRegistryCourseResponse,
    CourseRegistryLessonResponse,
    CourseRegistryResponse,
    CourseRegistryUnitResponse,
    CourseUnitMap,
    LessonResponse,
    PracticeEntry,
)

COURSE_ROOT = Path("backend_resources/courses/g3_math/secondary_1/n1/v1")
BANK_ROOT = Path("backend_resources/question_bank/g3_math")
COURSE_REGISTRY_PATH = Path("backend_resources/courses/g3_math/v1/registry.json")
SYLLABUS_PATH = Path("backend_resources/syllabi/g3_math/v1/catalogue.json")


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
    def registry_report(self):
        report = validate_course_registry(
            self.repository_root / COURSE_REGISTRY_PATH,
            self.repository_root / SYLLABUS_PATH,
        )
        if not report.valid or report.registry is None:
            raise CatalogueError(
                "course_registry_invalid",
                "The course registry failed validation and is temporarily unavailable.",
                503,
            )
        return report

    @cached_property
    def questions(self):
        return self.report.questions

    @cached_property
    def review_catalogue_report(self):
        report = validate_catalogue(
            self.repository_root / BANK_ROOT,
            self.repository_root / SYLLABUS_PATH,
        )
        if not report.valid:
            raise CatalogueError(
                "review_content_invalid",
                "The authored question catalogue failed validation and cannot be reviewed.",
                503,
            )
        return report

    @cached_property
    def review_questions(self):
        """Return every valid authored question, including banks not deployed to learners."""
        return self.review_catalogue_report.questions

    @cached_property
    def review_question_batches(self) -> dict[str, str]:
        """Map authored question keys to their controlled authoring batch."""
        authored_keys = {question.stable_key for question in self.review_questions}
        batches: dict[str, str] = {}
        for path in sorted((self.repository_root / BANK_ROOT).glob("**/batches/*.json")):
            manifest = load_manifest(path)
            for question_key in manifest.question_keys:
                if question_key in authored_keys:
                    batches[question_key] = manifest.batch_id
        return batches

    def course_registry(self) -> CourseRegistryResponse:
        registry = self.registry_report.registry

        def available(status: str) -> bool:
            return status == "published" or (
                self.allow_drafts and status in {"draft", "reviewed"}
            )

        courses = []
        for course in registry.courses:
            course_available = available(course.content_status)
            units = []
            for unit in course.units:
                unit_available = course_available and available(unit.content_status)
                lessons = []
                for lesson in unit.lessons:
                    lesson_available = unit_available and available(lesson.content_status)
                    lessons.append(
                        CourseRegistryLessonResponse(
                            stable_key=lesson.stable_key,
                            position=lesson.position,
                            title=lesson.title,
                            outcomes=lesson.outcomes,
                            content_status=lesson.content_status,
                            available=lesson_available,
                            href=(
                                f"/lessons/{lesson.stable_key}"
                                if lesson_available
                                else None
                            ),
                        )
                    )
                units.append(
                    CourseRegistryUnitResponse(
                        stable_key=unit.stable_key,
                        position=unit.position,
                        syllabus_position=unit.syllabus_position,
                        topic_code=unit.topic_code,
                        title=unit.title,
                        strand=unit.strand,
                        content_status=unit.content_status,
                        available=unit_available,
                        lessons=lessons,
                    )
                )
            courses.append(
                CourseRegistryCourseResponse(
                    stable_key=course.stable_key,
                    position=course.position,
                    school_level=course.school_level,
                    title=course.title,
                    description=course.description,
                    content_status=course.content_status,
                    available=course_available,
                    href=(
                        f"/courses/{course.stable_key}" if course_available else None
                    ),
                    units=units,
                )
            )
        return CourseRegistryResponse(
            version_key=registry.version_key,
            programme_key=registry.programme_key,
            curriculum_version=registry.curriculum_version,
            subject=registry.subject,
            content_status=registry.status,
            course_count=len(registry.courses),
            topic_group_count=registry.topic_group_count,
            lesson_count=registry.lesson_count,
            outcome_count=registry.outcome_count,
            courses=courses,
        )

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
