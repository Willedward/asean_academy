"""Administrator learner analytics and role-management contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from .contracts import ApiModel

AdminUserRole = Literal["student", "content_admin", "academic_admin"]
AdminEnrolmentStatus = Literal["active", "completed", "withdrawn", "not_enrolled"]


class AdminStudentSummaryResponse(ApiModel):
    learner_id: UUID
    email: str
    display_name: str | None
    target_track: str | None
    enrolment_status: AdminEnrolmentStatus
    course_keys: list[str]
    enrolled_at: datetime | None
    last_activity_at: datetime | None
    lessons_started: int
    lessons_proficient: int
    lessons_mastered: int
    practice_sessions: int
    attempts: int
    correct_attempts: int
    accuracy_percentage: float
    retry_question_count: int


class AdminStudentListResponse(ApiModel):
    students: list[AdminStudentSummaryResponse]
    total: int
    limit: int
    offset: int


class AdminLessonProgressResponse(ApiModel):
    lesson_key: str
    lesson_title: str
    state: Literal["in_progress", "practice_completed", "proficient", "mastered"]
    question_count: int
    resolved_count: int
    correct_count: int
    gave_up_count: int
    eventual_correct_percentage: float
    checkpoint_passed: bool
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class AdminDifficultyPerformanceResponse(ApiModel):
    difficulty: int = Field(ge=1, le=3)
    attempts: int
    correct_attempts: int
    accuracy_percentage: float


class AdminStudentDetailResponse(ApiModel):
    student: AdminStudentSummaryResponse
    lessons: list[AdminLessonProgressResponse]
    difficulty_performance: list[AdminDifficultyPerformanceResponse]


class AdminAnalyticsOverviewResponse(ApiModel):
    total_students: int
    active_enrolments: int
    active_students_last_7_days: int
    active_students_last_30_days: int
    lessons_started: int
    lessons_mastered: int
    practice_sessions: int
    completed_practice_sessions: int
    attempts: int
    correct_attempts: int
    overall_accuracy_percentage: float
    hint_reveals: int
    give_ups: int
    students_with_retries: int
    checkpoint_attempts: int
    checkpoint_passes: int
    diagnostic_sessions_started: int
    diagnostic_sessions_submitted: int
    diagnostic_sessions_in_progress: int
    diagnostic_resets: int
    question_reports_total: int
    question_reports_open: int
    question_reports_in_review: int
    question_reports_resolved: int
    question_reports_dismissed: int
    rate_limit_rejections_last_24_hours: int


class AdminQuestionAnalyticsResponse(ApiModel):
    question_key: str
    title: str
    difficulty: int = Field(ge=1, le=3)
    outcome_code: str
    attempt_count: int
    unique_students: int
    correct_attempts: int
    accuracy_percentage: float
    hint_reveals: int
    give_up_count: int
    queued_for_retry_students: int


class AdminQuestionAnalyticsListResponse(ApiModel):
    questions: list[AdminQuestionAnalyticsResponse]
    total: int
    limit: int
    offset: int


class UpdateUserRoleRequest(ApiModel):
    role: AdminUserRole


class AdminUserRoleResponse(ApiModel):
    learner_id: UUID
    email: str
    display_name: str | None
    role: AdminUserRole
    updated_at: datetime


class AdminEnrolmentResponse(ApiModel):
    course_key: str
    course_revision: int
    status: str


class AdminManagedUserResponse(AdminUserRoleResponse):
    enrolments: list[AdminEnrolmentResponse]


class AdminUserListResponse(ApiModel):
    users: list[AdminManagedUserResponse]
    total: int
    limit: int
    offset: int


class ContentStatusResponse(ApiModel):
    status: str
    course_key: str
    course_revision: int
    lessons: int
    questions: int


class CurriculumPreviewResponse(ApiModel):
    learner_id: UUID
    course_key: str
    from_revision: int
    target_revision: int
    target_hash: str
    active_sessions: int
    incompatible_lessons: list[str]
    blockers: list[str]
    allowed: bool


class CurriculumMigrationRequest(ApiModel):
    course_key: str = Field(min_length=1, max_length=80)
    from_revision: int = Field(ge=1)
    target_revision: int = Field(ge=1)
    target_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    reason: str = Field(min_length=10, max_length=500)


class CurriculumMigrationResponse(ApiModel):
    migrated: bool
    learner_id: UUID
    course_revision: int
