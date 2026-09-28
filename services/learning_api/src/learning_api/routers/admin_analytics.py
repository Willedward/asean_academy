"""Protected administrator analytics and role-management endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Query, Request

from ..admin_analytics_contracts import (
    AdminAnalyticsOverviewResponse,
    AdminQuestionAnalyticsListResponse,
    AdminStudentDetailResponse,
    AdminStudentListResponse,
    AdminUserListResponse,
    AdminUserRoleResponse,
    ContentStatusResponse,
    CurriculumMigrationRequest,
    CurriculumMigrationResponse,
    CurriculumPreviewResponse,
    UpdateUserRoleRequest,
)
from ..content_sync import verify_database_content
from ..conventions import current_request_id
from ..curriculum_admin import migrate, preview_transition
from ..dependencies import (
    AcademicAdminLearnerDependency,
    AdminAnalyticsRepositoryDependency,
    AdminLearnerDependency,
    AdminWriteRateLimitDependency,
)
from .admin import _safe

LOGGER = logging.getLogger("learning_api.admin.analytics")
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get(
    "/students",
    operation_id="listAdminStudents",
    response_model=AdminStudentListResponse,
    summary="List privacy-limited learner progress summaries",
)
async def list_students(
    administrator: AdminLearnerDependency,
    repository: AdminAnalyticsRepositoryDependency,
    search: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AdminStudentListResponse:
    del administrator
    return _safe(
        lambda: repository.list_students(search=search, limit=limit, offset=offset)
    )


@router.get(
    "/students/{learner_id}",
    operation_id="getAdminStudentDetail",
    response_model=AdminStudentDetailResponse,
    summary="Get one learner's progress without exposing submitted answers",
)
async def student_detail(
    learner_id: UUID,
    administrator: AdminLearnerDependency,
    repository: AdminAnalyticsRepositoryDependency,
) -> AdminStudentDetailResponse:
    del administrator
    return _safe(lambda: repository.student_detail(learner_id))


@router.get(
    "/analytics/overview",
    operation_id="getAdminAnalyticsOverview",
    response_model=AdminAnalyticsOverviewResponse,
    summary="Get aggregate beta learning metrics",
)
async def analytics_overview(
    administrator: AdminLearnerDependency,
    repository: AdminAnalyticsRepositoryDependency,
) -> AdminAnalyticsOverviewResponse:
    del administrator
    return _safe(repository.overview)


@router.get(
    "/analytics/questions",
    operation_id="listAdminQuestionAnalytics",
    response_model=AdminQuestionAnalyticsListResponse,
    summary="List aggregate question performance metrics",
)
async def question_analytics(
    administrator: AdminLearnerDependency,
    repository: AdminAnalyticsRepositoryDependency,
    difficulty: int | None = Query(default=None, ge=1, le=3),
    outcome: str | None = Query(default=None, min_length=1, max_length=40),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AdminQuestionAnalyticsListResponse:
    del administrator
    return _safe(
        lambda: repository.question_analytics(
            difficulty=difficulty,
            outcome=outcome,
            limit=limit,
            offset=offset,
        )
    )


@router.patch(
    "/users/{learner_id}/role",
    operation_id="updateAdminUserRole",
    response_model=AdminUserRoleResponse,
    summary="Change a user role as an academic administrator",
)
async def update_user_role(
    learner_id: UUID,
    body: UpdateUserRoleRequest,
    request: Request,
    administrator: AcademicAdminLearnerDependency,
    repository: AdminAnalyticsRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> AdminUserRoleResponse:
    result = _safe(
        lambda: repository.change_role(
            administrator,
            learner_id,
            body.role,
            current_request_id(request),
        )
    )
    LOGGER.info(
        "admin_role_changed",
        extra={
            "request_id": current_request_id(request),
            "target_user_id": str(learner_id),
            "role": body.role,
        },
    )
    return result


@router.get("/users", operation_id="listAdminUsers", response_model=AdminUserListResponse)
async def list_users(administrator: AcademicAdminLearnerDependency,
                     repository: AdminAnalyticsRepositoryDependency,
                     search: str | None = Query(None, min_length=1, max_length=100),
                     limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0)):
    return _safe(lambda: repository.list_users(search=search, limit=limit, offset=offset))


@router.get("/operations/content", operation_id="getContentStatus", response_model=ContentStatusResponse)
async def content_status(request: Request, administrator: AcademicAdminLearnerDependency,
                         repository: AdminAnalyticsRepositoryDependency):
    return verify_database_content(repository.database_url, request.app.state.course_catalogue)


@router.get("/users/{learner_id}/curriculum-preview", operation_id="previewCurriculumMigration",
            response_model=CurriculumPreviewResponse)
async def preview_curriculum(learner_id: UUID, request: Request,
                             administrator: AcademicAdminLearnerDependency,
                             repository: AdminAnalyticsRepositoryDependency,
                             course_key: str = Query(min_length=1, max_length=80)):
    def read():
        with repository._connect() as connection:
            return preview_transition(connection, learner_id, course_key,
                                      request.app.state.course_catalogue.report.course.revision)[0]
    return _safe(read)


@router.post("/users/{learner_id}/curriculum-migration", operation_id="migrateCurriculum",
             response_model=CurriculumMigrationResponse)
async def migrate_curriculum(learner_id: UUID, body: CurriculumMigrationRequest, request: Request,
                             administrator: AcademicAdminLearnerDependency,
                             repository: AdminAnalyticsRepositoryDependency,
                             _rate_limit: AdminWriteRateLimitDependency):
    return _safe(lambda: migrate(repository, administrator, learner_id, body,
                                current_request_id(request), request.app.state.course_catalogue))
