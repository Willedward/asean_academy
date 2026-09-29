"""Admin-only beta invitation management and operational summaries."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..admin_contracts import (
    AccountDeletionPreviewResponse,
    AccountDeletionResponse,
    AuditEventListResponse,
    BetaOperationsSummaryResponse,
    CreatedInvitationResponse,
    CreateInvitationRequest,
    DeploymentStatusResponse,
    ExecuteAccountDeletionRequest,
    InvitationListResponse,
    InvitationResponse,
)
from ..admin_repository import BetaOperationsError
from ..config import REQUIRED_SCHEMA_REVISION
from ..contracts import ReleaseMetadata
from ..conventions import current_request_id
from ..dependencies import (
    AcademicAdminLearnerDependency,
    AccountDeletionRepositoryDependency,
    AdminLearnerDependency,
    AdminWriteRateLimitDependency,
    BetaOperationsRepositoryDependency,
)

LOGGER = logging.getLogger("learning_api.admin")
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _safe(call):
    try:
        return call()
    except BetaOperationsError as exc:
        raise HTTPException(
            status_code=exc.status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


@router.get(
    "/invitations",
    operation_id="listBetaInvitations",
    response_model=InvitationListResponse,
    summary="List beta invitations for authorized administrators",
)
async def list_invitations(
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
    invitation_status: Literal["active", "expired", "exhausted", "revoked"] | None = Query(
        default=None, alias="status"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> InvitationListResponse:
    del administrator
    return _safe(
        lambda: repository.list_invitations(
            status=invitation_status,
            limit=limit,
            offset=offset,
        )
    )


@router.post(
    "/invitations",
    operation_id="createBetaInvitation",
    response_model=CreatedInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a beta invitation and return its raw code once",
)
async def create_invitation(
    body: CreateInvitationRequest,
    request: Request,
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> CreatedInvitationResponse:
    result = _safe(
        lambda: repository.create_invitation(
            administrator,
            body,
            current_request_id(request),
        )
    )
    LOGGER.info(
        "beta_invitation_created",
        extra={
            "request_id": current_request_id(request),
            "invitation_id": str(result["invitation_id"]),
        },
    )
    return result


@router.post(
    "/invitations/{invitation_id}/revoke",
    operation_id="revokeBetaInvitation",
    response_model=InvitationResponse,
    summary="Idempotently revoke a beta invitation",
)
async def revoke_invitation(
    invitation_id: UUID,
    request: Request,
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> InvitationResponse:
    result = _safe(
        lambda: repository.revoke_invitation(
            administrator,
            invitation_id,
            current_request_id(request),
        )
    )
    LOGGER.info(
        "beta_invitation_revoked",
        extra={
            "request_id": current_request_id(request),
            "invitation_id": str(invitation_id),
        },
    )
    return result


@router.get(
    "/operations/summary",
    operation_id="getBetaOperationsSummary",
    response_model=BetaOperationsSummaryResponse,
    summary="Get a privacy-minimal beta operations summary",
)
async def operations_summary(
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
) -> BetaOperationsSummaryResponse:
    del administrator
    return _safe(repository.summary)


@router.get(
    "/operations/status",
    operation_id="getDeploymentStatus",
    response_model=DeploymentStatusResponse,
    summary="Inspect the active release and database as an academic administrator",
)
async def deployment_status(
    request: Request,
    administrator: AcademicAdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
) -> DeploymentStatusResponse:
    del administrator
    settings = request.app.state.settings
    return DeploymentStatusResponse(
        checked_at=datetime.now(UTC),
        request_id=current_request_id(request),
        environment=settings.environment,
        uptime_seconds=max(
            0,
            (datetime.now(UTC) - request.app.state.started_at).total_seconds(),
        ),
        release=ReleaseMetadata(
            sha=settings.release_sha,
            deployment_id=settings.deployment_id,
            required_schema_revision=REQUIRED_SCHEMA_REVISION,
        ),
        database=_safe(repository.service_status),
    )


@router.get(
    "/audit-events",
    operation_id="listBetaAuditEvents",
    response_model=AuditEventListResponse,
    summary="List recent immutable beta audit events",
)
async def audit_events(
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
    limit: int = Query(default=50, ge=1, le=200),
) -> AuditEventListResponse:
    del administrator
    return _safe(lambda: repository.audit_events(limit=limit))


@router.post(
    "/students/{learner_id}/deletion/preview",
    operation_id="previewStudentAccountDeletion",
    response_model=AccountDeletionPreviewResponse,
    summary="Preview the exact learner records affected by account deletion",
)
async def preview_account_deletion(
    learner_id: UUID,
    administrator: AcademicAdminLearnerDependency,
    repository: AccountDeletionRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> AccountDeletionPreviewResponse:
    del administrator
    return _safe(lambda: repository.preview(learner_id))


@router.post(
    "/students/{learner_id}/deletion/execute",
    operation_id="executeStudentAccountDeletion",
    response_model=AccountDeletionResponse,
    summary="Delete a learner after signed preview and exact email confirmation",
)
async def execute_account_deletion(
    learner_id: UUID,
    body: ExecuteAccountDeletionRequest,
    request: Request,
    administrator: AcademicAdminLearnerDependency,
    repository: AccountDeletionRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> AccountDeletionResponse:
    result = _safe(
        lambda: repository.execute(
            administrator,
            learner_id,
            preview_token=body.preview_token,
            confirmation_email=body.confirmation_email,
            reason=body.reason,
            request_id=current_request_id(request),
        )
    )
    LOGGER.warning(
        "student_account_deleted",
        extra={
            "request_id": current_request_id(request),
            "target_reference": result["target_reference"],
        },
    )
    return result
