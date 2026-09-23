"""Student-safe course map and lesson response contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .contracts import ApiModel

ContentStatus = Literal["draft", "reviewed", "published", "retired"]
LearningMaterialState = Literal["pending", "ready"]
LessonAvailability = Literal["content_pending", "available"]
LessonProgressState = Literal["not_started", "in_progress", "proficient", "mastered"]


class PracticeEntry(ApiModel):
    lesson_key: str
    mode: Literal["guided_practice"] = "guided_practice"
    question_count: int = Field(ge=1, le=20)
    available: bool
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
    sections: list[dict[str, Any]]
    assets: list[dict[str, Any]]
    practice: PracticeEntry
