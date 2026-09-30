"""Canonical programme registry for planned and authored Mathematics courses."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from .catalogue import SchoolLevel, Strand, load_catalogue
from .models import OUTCOME_PATTERN, TOPIC_PATTERN, Model

REGISTRY_SCHEMA_VERSION = "1.0.0"
RegistryStatus = Literal["draft", "active", "retired"]
RegistryContentStatus = Literal["planned", "draft", "reviewed", "published"]


class RegisteredLesson(Model):
    stable_key: str = Field(pattern=r"^[ngs][0-9]+-lesson-[0-9]{2,3}$")
    position: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    outcomes: list[str] = Field(min_length=1)
    content_status: RegistryContentStatus

    @model_validator(mode="after")
    def outcomes_are_valid(self):
        if any(re.fullmatch(OUTCOME_PATTERN, code) is None for code in self.outcomes):
            raise ValueError("Registered lesson outcomes must use the numeric syllabus format")
        if len(self.outcomes) != len(set(self.outcomes)):
            raise ValueError("Registered lesson outcomes must be unique")
        return self


class RegisteredUnit(Model):
    stable_key: str = Field(pattern=r"^g3-sec[12]-[ngs][0-9]+$")
    position: int = Field(ge=1)
    syllabus_position: int = Field(ge=1)
    topic_code: str = Field(pattern=TOPIC_PATTERN)
    title: str = Field(min_length=1, max_length=160)
    strand: Strand
    content_status: RegistryContentStatus
    lessons: list[RegisteredLesson] = Field(min_length=1)

    @model_validator(mode="after")
    def lessons_are_consistent(self):
        positions = [lesson.position for lesson in self.lessons]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Registered lesson positions must be consecutive from 1")
        keys = [lesson.stable_key for lesson in self.lessons]
        if len(keys) != len(set(keys)):
            raise ValueError("Registered lesson keys must be unique within a unit")
        return self


class RegisteredCourse(Model):
    stable_key: str = Field(pattern=r"^g3-sec[12]-math$")
    position: int = Field(ge=1)
    school_level: SchoolLevel
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1)
    content_status: RegistryContentStatus
    expected_unit_count: int = Field(ge=1)
    expected_lesson_count: int = Field(ge=1)
    expected_outcome_count: int = Field(ge=1)
    units: list[RegisteredUnit] = Field(min_length=1)

    @model_validator(mode="after")
    def course_is_consistent(self):
        positions = [unit.position for unit in self.units]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Registered unit positions must be consecutive from 1")
        keys = [unit.stable_key for unit in self.units]
        if len(keys) != len(set(keys)):
            raise ValueError("Registered unit keys must be unique")
        lesson_count = sum(len(unit.lessons) for unit in self.units)
        outcome_count = sum(
            len(lesson.outcomes) for unit in self.units for lesson in unit.lessons
        )
        if len(self.units) != self.expected_unit_count:
            raise ValueError("Registered unit count does not match expected_unit_count")
        if lesson_count != self.expected_lesson_count:
            raise ValueError("Registered lesson count does not match expected_lesson_count")
        if outcome_count != self.expected_outcome_count:
            raise ValueError("Registered outcome count does not match expected_outcome_count")
        return self


class CourseRegistry(Model):
    schema_version: Literal["1.0.0"] = REGISTRY_SCHEMA_VERSION
    version_key: str = Field(pattern=r"^[a-z0-9_]+$")
    programme_key: str = Field(pattern=r"^[a-z0-9-]+$")
    curriculum_version: str = Field(pattern=r"^[a-z0-9_]+$")
    subject: Literal["Mathematics"]
    status: RegistryStatus
    expected_course_count: int = Field(ge=1)
    expected_topic_group_count: int = Field(ge=1)
    expected_lesson_count: int = Field(ge=1)
    expected_outcome_count: int = Field(ge=1)
    courses: list[RegisteredCourse] = Field(min_length=1)

    @model_validator(mode="after")
    def registry_is_consistent(self):
        positions = [course.position for course in self.courses]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("Registered course positions must be consecutive from 1")
        keys = [course.stable_key for course in self.courses]
        if len(keys) != len(set(keys)):
            raise ValueError("Registered course keys must be unique")
        levels = [course.school_level for course in self.courses]
        if len(levels) != len(set(levels)):
            raise ValueError("A school level can appear in only one registered course")
        unit_count = sum(len(course.units) for course in self.courses)
        lesson_count = sum(
            len(unit.lessons) for course in self.courses for unit in course.units
        )
        outcome_count = sum(
            len(lesson.outcomes)
            for course in self.courses
            for unit in course.units
            for lesson in unit.lessons
        )
        lesson_keys = [
            lesson.stable_key
            for course in self.courses
            for unit in course.units
            for lesson in unit.lessons
        ]
        if len(lesson_keys) != len(set(lesson_keys)):
            raise ValueError("Registered lesson keys must be globally unique")
        if len(self.courses) != self.expected_course_count:
            raise ValueError("Course count does not match expected_course_count")
        if unit_count != self.expected_topic_group_count:
            raise ValueError("Topic-group count does not match expected_topic_group_count")
        if lesson_count != self.expected_lesson_count:
            raise ValueError("Lesson count does not match expected_lesson_count")
        if outcome_count != self.expected_outcome_count:
            raise ValueError("Outcome count does not match expected_outcome_count")
        return self

    @property
    def topic_group_count(self) -> int:
        return sum(len(course.units) for course in self.courses)

    @property
    def lesson_count(self) -> int:
        return sum(len(unit.lessons) for course in self.courses for unit in course.units)

    @property
    def outcome_count(self) -> int:
        return sum(
            len(lesson.outcomes)
            for course in self.courses
            for unit in course.units
            for lesson in unit.lessons
        )


@dataclass(frozen=True)
class CourseRegistryIssue:
    code: str
    path: str
    message: str


@dataclass
class CourseRegistryValidationReport:
    registry: CourseRegistry | None = None
    issues: list[CourseRegistryIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict:
        registry = self.registry
        return {
            "valid": self.valid,
            "registry_version": registry.version_key if registry else None,
            "course_count": len(registry.courses) if registry else 0,
            "topic_group_count": registry.topic_group_count if registry else 0,
            "lesson_count": registry.lesson_count if registry else 0,
            "outcome_count": registry.outcome_count if registry else 0,
            "error_count": len(self.issues),
            "issues": [asdict(issue) for issue in self.issues],
        }


def load_course_registry(path: Path) -> CourseRegistry:
    return CourseRegistry.model_validate_json(path.read_text())


def validate_course_registry(
    registry_path: Path,
    syllabus_path: Path,
) -> CourseRegistryValidationReport:
    report = CourseRegistryValidationReport()
    try:
        report.registry = load_course_registry(registry_path)
    except (OSError, ValueError, ValidationError) as exc:
        report.issues.append(CourseRegistryIssue("invalid_registry", str(registry_path), str(exc)))
        return report
    try:
        syllabus = load_catalogue(syllabus_path)
    except (OSError, ValueError, ValidationError) as exc:
        report.issues.append(CourseRegistryIssue("invalid_syllabus", str(syllabus_path), str(exc)))
        return report

    registry = report.registry
    if registry.curriculum_version != syllabus.version_key:
        report.issues.append(
            CourseRegistryIssue(
                "curriculum_version_mismatch",
                str(registry_path),
                f"Registry uses {registry.curriculum_version}; syllabus uses {syllabus.version_key}",
            )
        )

    expected_groups = {
        (outcome.school_level, topic.code)
        for topic in syllabus.topics
        for outcome in topic.outcomes
    }
    actual_groups = {
        (course.school_level, unit.topic_code)
        for course in registry.courses
        for unit in course.units
    }
    if actual_groups != expected_groups:
        report.issues.append(
            CourseRegistryIssue(
                "topic_group_inventory",
                str(registry_path),
                f"Missing {sorted(expected_groups - actual_groups)}; extra {sorted(actual_groups - expected_groups)}",
            )
        )

    topic_by_code = {topic.code: topic for topic in syllabus.topics}
    for course in registry.courses:
        level_number = course.school_level[-1]
        expected_course_key = f"g3-sec{level_number}-math"
        if course.stable_key != expected_course_key:
            report.issues.append(
                CourseRegistryIssue(
                    "course_key_mismatch", course.stable_key, f"Expected {expected_course_key}"
                )
            )
        expected_topics = [
            topic
            for topic in syllabus.topics
            if any(outcome.school_level == course.school_level for outcome in topic.outcomes)
        ]
        if [unit.topic_code for unit in course.units] != [topic.code for topic in expected_topics]:
            report.issues.append(
                CourseRegistryIssue(
                    "course_topic_order",
                    course.stable_key,
                    "Units must follow the canonical syllabus topic order",
                )
            )
        for unit in course.units:
            topic = topic_by_code.get(unit.topic_code)
            if topic is None:
                continue
            expected_unit_key = f"g3-sec{level_number}-{unit.topic_code.lower()}"
            if unit.stable_key != expected_unit_key:
                report.issues.append(
                    CourseRegistryIssue(
                        "unit_key_mismatch", unit.stable_key, f"Expected {expected_unit_key}"
                    )
                )
            if (
                unit.title != topic.title
                or unit.strand != topic.strand
                or unit.syllabus_position != topic.position
            ):
                report.issues.append(
                    CourseRegistryIssue(
                        "unit_syllabus_mismatch",
                        unit.stable_key,
                        "Unit title, strand, or syllabus position differs from the catalogue",
                    )
                )
            expected_outcomes = [
                outcome.code
                for outcome in topic.outcomes
                if outcome.school_level == course.school_level
            ]
            actual_outcomes = [
                code for lesson in unit.lessons for code in lesson.outcomes
            ]
            if actual_outcomes != expected_outcomes:
                report.issues.append(
                    CourseRegistryIssue(
                        "unit_outcome_inventory",
                        unit.stable_key,
                        f"Expected {expected_outcomes}; found {actual_outcomes}",
                    )
                )
            prefix = f"{unit.topic_code.lower()}-lesson-"
            if any(not lesson.stable_key.startswith(prefix) for lesson in unit.lessons):
                report.issues.append(
                    CourseRegistryIssue(
                        "lesson_topic_key_mismatch",
                        unit.stable_key,
                        f"Every lesson key must start with {prefix}",
                    )
                )
    return report


def write_registry_schema(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    path = output / "course-registry-v1.schema.json"
    path.write_text(json.dumps(CourseRegistry.model_json_schema(), indent=2) + "\n")
