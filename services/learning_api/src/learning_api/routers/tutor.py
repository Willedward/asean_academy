"""Authenticated grounded tutor API, disabled until evaluation is complete."""

from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..config import REQUIRED_SCHEMA_REVISION
from ..conventions import current_request_id
from ..dependencies import (
    AcademicAdminLearnerDependency,
    AdminLearnerDependency,
    TutorMessageRateLimitDependency,
    TutorRepositoryDependency,
    TutorServiceDependency,
)
from ..tutor_contracts import (
    CreateTutorSessionRequest,
    SendTutorMessageRequest,
    TutorMode,
    TutorReplyResponse,
    TutorRouteDecisionListAdminResponse,
    TutorRoutingStatusAdminResponse,
    TutorSessionResponse,
    TutorUsageAdminResponse,
)
from ..tutor_repository import TutorError
from ..tutor_routing import configured_routing_mode, resolve_routing_mode

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


def _usage_month(month: str) -> date:
    try:
        return date.fromisoformat(f"{month}-01")
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "validation_error",
                "message": "month must be a real YYYY-MM value.",
            },
        ) from exc


def _model_name(settings, provider: str) -> str:
    if provider == "gemini":
        return settings.tutor_gemini_model
    if provider == "openai":
        return settings.tutor_openai_model
    if provider == "synthetic":
        return "synthetic-tutor-v1"
    return provider


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
    return repository.admin_usage(_usage_month(month))


@admin_router.get(
    "/tutor-routing/status",
    operation_id="getAdminTutorRoutingStatus",
    response_model=TutorRoutingStatusAdminResponse,
)
async def tutor_routing_status(
    request: Request,
    administrator: AcademicAdminLearnerDependency,
) -> TutorRoutingStatusAdminResponse:
    settings = request.app.state.settings
    configured_mode = configured_routing_mode(
        live_enabled=settings.tutor_hybrid_routing_enabled,
        shadow_enabled=settings.tutor_hybrid_routing_shadow_enabled,
    )
    resolved_mode = resolve_routing_mode(
        configured_mode,
        settings.tutor_routing_cohort,
        administrator.role,
    )
    has_premium_target = configured_mode != "off"
    return TutorRoutingStatusAdminResponse(
        configured_mode=configured_mode,
        resolved_mode=resolved_mode,
        cohort=settings.tutor_routing_cohort,
        policy_version=settings.tutor_routing_policy_version,
        schema_revision=REQUIRED_SCHEMA_REVISION,
        economy_provider=settings.tutor_provider,
        economy_model=_model_name(settings, settings.tutor_provider),
        premium_provider=(
            settings.tutor_premium_provider if has_premium_target else None
        ),
        premium_model=(
            _model_name(settings, settings.tutor_premium_provider)
            if has_premium_target
            else None
        ),
    )


@admin_router.get(
    "/tutor-routing/decisions",
    operation_id="listAdminTutorRoutingDecisions",
    response_model=TutorRouteDecisionListAdminResponse,
)
async def tutor_routing_decisions(
    administrator: AcademicAdminLearnerDependency,
    repository: TutorRepositoryDependency,
    month: str = Query(pattern=r"^\d{4}-\d{2}$"),
    cursor: str | None = Query(default=None, min_length=1, max_length=500),
    limit: int = Query(default=50, ge=1, le=100),
    routing_mode: Literal["legacy", "off", "shadow", "live"] | None = None,
    recommended_tier: Literal["economy", "premium"] | None = None,
    executed_tier: Literal["economy", "premium"] | None = None,
    tutor_mode: TutorMode | None = None,
    question_difficulty: int | None = Query(default=None, ge=1, le=5),
    reason_code: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9_]+$",
    ),
    reservation_status: Literal["reserved", "reconciled", "released"] | None = None,
) -> TutorRouteDecisionListAdminResponse:
    del administrator
    return _safe(
        lambda: repository.admin_route_decisions(
            _usage_month(month),
            cursor=cursor,
            limit=limit,
            routing_mode=routing_mode,
            recommended_tier=recommended_tier,
            executed_tier=executed_tier,
            tutor_mode=tutor_mode,
            question_difficulty=question_difficulty,
            reason_code=reason_code,
            reservation_status=reservation_status,
        )
    )
