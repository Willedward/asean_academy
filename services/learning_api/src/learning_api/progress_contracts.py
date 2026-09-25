"""Learner-facing progress, checkpoint and recommendation contracts."""

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
    "start_checkpoint",
    "resume_checkpoint",
    "course_complete",
]
CheckpointState = Literal["locked", "available", "in_progress", "passed"]


class LessonProgressResponse(ApiModel):
    lesson_key: str
    lesson_title: str
    position: int
    state: ProgressState
    unlocked: bool = False
    unlock_reason: Literal["prerequisite_not_proficient"] | None = None
    question_count: int = 0
    resolved_count: int = 0
    correct_count: int = 0
    gave_up_count: int = 0
    retry_question_count: int = 0
    eventual_correct_percentage: float = 0
    checkpoint_passed: bool = False
    last_session_id: str | None = None
    updated_at: str | None = None


class CheckpointProgressResponse(ApiModel):
    unit_key: str
    state: CheckpointState
    available: bool
    question_count: int
    passing_percentage: int
    last_session_id: str | None = None
    last_percentage: float | None = None


class NextActionResponse(ApiModel):
    type: NextActionType
    title: str
    description: str
    href: str
    lesson_key: str | None = None
    unit_key: str | None = None
    session_id: str | None = None


class ProgressResponse(ApiModel):
    learner_id: str
    course_key: str
    proficiency_threshold: int
    checkpoint_required_for_mastery: bool
    lessons: list[LessonProgressResponse]
    checkpoints: list[CheckpointProgressResponse]


class LearningHomeResponse(ApiModel):
    learner_id: str
    course_key: str
    next_action: NextActionResponse
    unresolved_retry_count: int
    lessons: list[LessonProgressResponse]
    checkpoints: list[CheckpointProgressResponse]
