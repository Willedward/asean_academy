"""Learner-facing progress and recommendation contracts."""

from __future__ import annotations

from typing import Literal

from .contracts import ApiModel

ProgressState = Literal[
    "not_started",
    "in_progress",
    "practice_completed",
    "proficient",
    "mastered",
]
NextActionType = Literal[
    "start_lesson",
    "resume_practice",
    "retry_practice",
    "continue_lesson",
    "content_pending",
    "checkpoint_pending",
]


class LessonProgressResponse(ApiModel):
    lesson_key: str
    lesson_title: str
    position: int
    state: ProgressState
    question_count: int = 0
    resolved_count: int = 0
    correct_count: int = 0
    gave_up_count: int = 0
    eventual_correct_percentage: float = 0
    checkpoint_passed: bool = False
    last_session_id: str | None = None
    updated_at: str | None = None


class NextActionResponse(ApiModel):
    type: NextActionType
    title: str
    description: str
    href: str
    lesson_key: str | None = None
    session_id: str | None = None


class ProgressResponse(ApiModel):
    learner_id: str
    course_key: str
    proficiency_threshold: int
    checkpoint_required_for_mastery: bool
    lessons: list[LessonProgressResponse]


class LearningHomeResponse(ApiModel):
    learner_id: str
    course_key: str
    next_action: NextActionResponse
    unresolved_retry_count: int
    lessons: list[LessonProgressResponse]
