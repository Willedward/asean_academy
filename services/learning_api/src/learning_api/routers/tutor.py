"""Authenticated grounded tutor API, disabled until evaluation is complete."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..conventions import current_request_id
from ..dependencies import (
    AdminLearnerDependency,
    TutorMessageRateLimitDependency,
    TutorRepositoryDependency,
    TutorServiceDependency,
)
from ..tutor_contracts import (
    CreateTutorSessionRequest,
    SendTutorMessageRequest,
    TutorReplyResponse,
    TutorSessionResponse,
    TutorUsageAdminResponse,
)
from ..tutor_repository import TutorError

router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _safe(call):
    try:
        return call()
    except TutorError as exc:
        raise HTTPException(
            status_code=exc.status,
            detail={"code": exc.code, "message": str(exc), "details": exc.details},
        ) from exc


@router.post(
    "/sessions",
    operation_id="createTutorSession",
    response_model=TutorSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    body: CreateTutorSessionRequest,
    service: TutorServiceDependency,
) -> TutorSessionResponse:
    return _safe(lambda: service.create_session(
        practice_session_id=str(body.practice_session_id),
        question_key=body.question_key,
        question_revision=body.question_revision,
    ))


@router.get(
    "/sessions/{session_id}",
    operation_id="getTutorSession",
    response_model=TutorSessionResponse,
)
async def get_session(
    session_id: UUID,
    service: TutorServiceDependency,
) -> TutorSessionResponse:
    return _safe(lambda: service.session(str(session_id)))


@router.post(
    "/sessions/{session_id}/messages",
    operation_id="sendTutorMessage",
    response_model=TutorReplyResponse,
)
async def send_message(
    session_id: UUID,
    body: SendTutorMessageRequest,
    request: Request,
    service: TutorServiceDependency,
    _rate_limit: TutorMessageRateLimitDependency,
) -> TutorReplyResponse:
    try:
        return await service.send_message(
            str(session_id), body.message, request_id=current_request_id(request)
        )
    except TutorError as exc:
        raise HTTPException(
            status_code=exc.status,
            detail={"code": exc.code, "message": str(exc), "details": exc.details},
        ) from exc


@router.post(
    "/sessions/{session_id}/close",
    operation_id="closeTutorSession",
    response_model=TutorSessionResponse,
)
async def close_session(
    session_id: UUID,
    service: TutorServiceDependency,
) -> TutorSessionResponse:
    return _safe(lambda: service.close(str(session_id)))


@admin_router.get(
    "/tutor-usage",
    operation_id="getAdminTutorUsage",
    response_model=TutorUsageAdminResponse,
)
async def tutor_usage(
    administrator: AdminLearnerDependency,
    repository: TutorRepositoryDependency,
    month: str = Query(pattern=r"^\d{4}-\d{2}$"),
) -> TutorUsageAdminResponse:
    del administrator
    try:
        usage_month = date.fromisoformat(f"{month}-01")
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": "month must be a real YYYY-MM value."},
        ) from exc
    return repository.admin_usage(usage_month)
