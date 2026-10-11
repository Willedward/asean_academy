"""Protected content review, preview, and release-request endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request, status

from ..content_review import (
    bulk_reviewer_preview,
    list_review_queue,
    record_bulk_reviews,
    record_review,
    request_lifecycle,
    reviewer_preview,
    student_preview,
)
from ..content_review_contracts import (
    BulkContentReviewerPreviewResponse,
    BulkContentReviewPreviewRequest,
    BulkContentReviewRequest,
    BulkContentReviewResponse,
    ContentKind,
    ContentLifecycleRequestResponse,
    ContentReviewerPreviewResponse,
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
    AdminWriteRateLimitDependency,
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
    batch_id: str | None = Query(default=None, pattern=r"^[a-z0-9-]+$"),
    unit_key: str | None = Query(default=None, pattern=r"^[a-z0-9-]+$"),
    limit: int = Query(default=25, ge=1, le=250),
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
            batch_id=batch_id,
            unit_key=unit_key,
        )
    )


@router.post(
    "/bulk-review-preview",
    operation_id="previewBulkContentForReview",
    response_model=BulkContentReviewerPreviewResponse,
    summary="Preview an exact batch or unit selection in one review session",
)
async def preview_bulk_content_for_review(
    body: BulkContentReviewPreviewRequest,
    request: Request,
    administrator: AdminLearnerDependency,
) -> BulkContentReviewerPreviewResponse:
    del administrator
    return _safe(
        lambda: bulk_reviewer_preview(request.app.state.course_catalogue, body)
    )


@router.post(
    "/bulk-reviews",
    operation_id="recordBulkContentReview",
    response_model=BulkContentReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Append one review decision for every selected content fingerprint",
)
async def review_bulk_content(
    body: BulkContentReviewRequest,
    request: Request,
    administrator: AdminLearnerDependency,
    repository: AdminAnalyticsRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> BulkContentReviewResponse:
    result = _safe(
        lambda: record_bulk_reviews(
            repository,
            request.app.state.course_catalogue,
            administrator,
            body,
            current_request_id(request),
        )
    )
    LOGGER.info(
        "bulk_content_review_recorded",
        extra={
            "request_id": current_request_id(request),
            "scope": body.scope,
            "scope_key": body.scope_key,
            "recorded_count": result["recorded_count"],
            "dimension": body.dimension,
            "decision": body.decision,
        },
    )
    return result


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


@router.get(
    "/{kind}/{stable_key}/review-preview",
    operation_id="previewContentForReview",
    response_model=ContentReviewerPreviewResponse,
    summary="Preview protected authoring content with answers and feedback",
)
async def preview_content_for_review(
    kind: ContentKind,
    stable_key: str,
    request: Request,
    administrator: AdminLearnerDependency,
) -> ContentReviewerPreviewResponse:
    del administrator
    return _safe(
        lambda: reviewer_preview(request.app.state.course_catalogue, kind, stable_key)
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
    _rate_limit: AdminWriteRateLimitDependency,
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
    _rate_limit: AdminWriteRateLimitDependency,
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
