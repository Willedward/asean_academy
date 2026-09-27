"""Protected content review, preview, and release-request endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request, status

from ..content_review import (
    list_review_queue,
    record_review,
    request_lifecycle,
    student_preview,
)
from ..content_review_contracts import (
    ContentKind,
    ContentLifecycleRequestResponse,
    ContentReviewQueueResponse,
    ContentReviewRecordResponse,
    ContentStudentPreviewResponse,
    CreateLifecycleRequest,
    RecordContentReviewRequest,
    ReviewState,
)
from ..conventions import current_request_id
from ..dependencies import (
    AcademicAdminLearnerDependency,
    AdminAnalyticsRepositoryDependency,
    AdminLearnerDependency,
)
from .admin import _safe

LOGGER = logging.getLogger("learning_api.admin.content")
router = APIRouter(prefix="/api/v1/admin/content", tags=["admin", "content-review"])


@router.get(
    "",
    operation_id="listContentReviewQueue",
    response_model=ContentReviewQueueResponse,
    summary="List deployed content and its latest review decisions",
)
async def review_queue(
    request: Request,
    administrator: AdminLearnerDependency,
    repository: AdminAnalyticsRepositoryDependency,
    kind: ContentKind | None = None,
    source_status: str | None = Query(default=None, pattern="^(draft|reviewed|published|retired)$"),
    review_state: ReviewState | None = None,
    search: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ContentReviewQueueResponse:
    del administrator
    return _safe(
        lambda: list_review_queue(
            repository,
            request.app.state.course_catalogue,
            kind=kind,
            source_status=source_status,
            review_state=review_state,
            search=search,
            limit=limit,
            offset=offset,
        )
    )


@router.get(
    "/{kind}/{stable_key}/preview",
    operation_id="previewContentAsStudent",
    response_model=ContentStudentPreviewResponse,
    summary="Preview public content without private answers or locked feedback",
)
async def preview_content(
    kind: ContentKind,
    stable_key: str,
    request: Request,
    administrator: AdminLearnerDependency,
) -> ContentStudentPreviewResponse:
    del administrator
    return _safe(
        lambda: student_preview(request.app.state.course_catalogue, kind, stable_key)
    )


@router.post(
    "/{kind}/{stable_key}/reviews",
    operation_id="recordContentReview",
    response_model=ContentReviewRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Append a Mathematics or editorial review decision",
)
async def review_content(
    kind: ContentKind,
    stable_key: str,
    body: RecordContentReviewRequest,
    request: Request,
    administrator: AdminLearnerDependency,
    repository: AdminAnalyticsRepositoryDependency,
) -> ContentReviewRecordResponse:
    result = _safe(
        lambda: record_review(
            repository,
            request.app.state.course_catalogue,
            administrator,
            kind,
            stable_key,
            body,
            current_request_id(request),
        )
    )
    LOGGER.info(
        "content_review_recorded",
        extra={
            "request_id": current_request_id(request),
            "content_kind": kind,
            "stable_key": stable_key,
            "dimension": body.dimension,
            "decision": body.decision,
        },
    )
    return result


@router.post(
    "/{kind}/{stable_key}/lifecycle-requests",
    operation_id="requestContentLifecycleChange",
    response_model=ContentLifecycleRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a Git-authored publication or retirement release",
)
async def lifecycle_request(
    kind: ContentKind,
    stable_key: str,
    body: CreateLifecycleRequest,
    request: Request,
    administrator: AcademicAdminLearnerDependency,
    repository: AdminAnalyticsRepositoryDependency,
) -> ContentLifecycleRequestResponse:
    result = _safe(
        lambda: request_lifecycle(
            repository,
            request.app.state.course_catalogue,
            administrator,
            kind,
            stable_key,
            body,
            current_request_id(request),
        )
    )
    LOGGER.info(
        "content_lifecycle_requested",
        extra={
            "request_id": current_request_id(request),
            "content_kind": kind,
            "stable_key": stable_key,
            "action": body.action,
        },
    )
    return result
