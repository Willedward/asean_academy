"""Student-safe course map and lesson response contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field
from question_bank.course_models import (
    ExplanationSection,
    SummarySection,
    WorkedExampleSection,
)
from question_bank.models import Asset, ContentBlock

from .contracts import ApiModel

ContentStatus = Literal["draft", "reviewed", "published", "retired"]
LearningMaterialState = Literal["pending", "ready"]
LessonAvailability = Literal["content_pending", "available"]
LessonProgressState = Literal[
    "not_started", "in_progress", "practice_completed", "proficient", "mastered"
]


class PublicActiveRecallSection(ApiModel):
    stable_key: str = Field(pattern=r"^[a-z0-9-]+$")
    position: int = Field(ge=1)
    type: Literal["active_recall"]
    title: str = Field(min_length=1, max_length=160)
    prompt: list[ContentBlock]
    response_type: Literal["numeric", "algebraic_expression"]


PublicLessonSection = Annotated[
    ExplanationSection
    | WorkedExampleSection
    | PublicActiveRecallSection
    | SummarySection,
    Field(discriminator="type"),
]


class PracticeEntry(ApiModel):
    lesson_key: str
    mode: Literal["guided_practice"] = "guided_practice"
    question_count: int = Field(ge=1, le=20)
    available: bool
    development_available: bool = False
    unavailable_reason: Literal["content_not_reviewed", "questions_not_published"] | None = None


class CourseLessonMap(ApiModel):
    stable_key: str
    position: int
    title: str
    summary: str
    outcomes: list[str]
    estimated_minutes: int
    objectives: list[str]
    required_practice_count: int
    content_status: ContentStatus
    learning_material_state: LearningMaterialState
    availability: LessonAvailability
    progress_state: LessonProgressState = "not_started"
    unlocked: bool = False
    unlock_reason: Literal["prerequisite_not_proficient"] | None = None
    href: str


class CourseUnitMap(ApiModel):
    stable_key: str
    position: int
    title: str
    checkpoint_question_count: int
    checkpoint_available: bool
    lessons: list[CourseLessonMap]


class CourseMapResponse(ApiModel):
    stable_key: str
    revision: int
    title: str
    description: str
    subject: str
    school_level: str
    content_status: ContentStatus
    development_preview: bool
    units: list[CourseUnitMap]


class LessonResponse(ApiModel):
    stable_key: str
    revision: int
    course_key: str
    unit_key: str
    position: int
    title: str
    summary: str
    outcomes: list[str]
    estimated_minutes: int
    objectives: list[str]
    content_status: ContentStatus
    development_preview: bool
    learning_material_state: LearningMaterialState
    sections: list[PublicLessonSection]
    assets: list[Asset]
    practice: PracticeEntry


RegistryContentStatus = Literal["planned", "draft", "reviewed", "published"]


class CourseRegistryLessonResponse(ApiModel):
    stable_key: str
    position: int
    title: str
    outcomes: list[str]
    content_status: RegistryContentStatus
    available: bool
    href: str | None


class CourseRegistryUnitResponse(ApiModel):
    stable_key: str
    position: int
    syllabus_position: int
    topic_code: str
    title: str
    strand: str
    content_status: RegistryContentStatus
    available: bool
    lessons: list[CourseRegistryLessonResponse]


class CourseRegistryCourseResponse(ApiModel):
    stable_key: str
    position: int
    school_level: str
    title: str
    description: str
    content_status: RegistryContentStatus
    available: bool
    href: str | None
    units: list[CourseRegistryUnitResponse]


class CourseRegistryResponse(ApiModel):
    version_key: str
    programme_key: str
    curriculum_version: str
    subject: str
    content_status: Literal["draft", "active", "retired"]
    course_count: int
    topic_group_count: int
    lesson_count: int
    outcome_count: int
    courses: list[CourseRegistryCourseResponse]
