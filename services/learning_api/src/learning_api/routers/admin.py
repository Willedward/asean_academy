"""Admin-only beta invitation management and operational summaries."""

from __future__ import annotations

import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..admin_contracts import (
    AuditEventListResponse,
    BetaOperationsSummaryResponse,
    CreatedInvitationResponse,
    CreateInvitationRequest,
    InvitationListResponse,
    InvitationResponse,
)
from ..admin_repository import BetaOperationsError
from ..conventions import current_request_id
from ..dependencies import AdminLearnerDependency, BetaOperationsRepositoryDependency

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
) -> CreatedInvitationResponse:
    result = _safe(
        lambda: repository.create_invitation(
            administrator,
            body,
            current_request_id(request),
        )
    )
    LOGGER.info(
        "beta_invitation_created request_id=%s invitation_id=%s",
        current_request_id(request),
        result["invitation_id"],
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
) -> InvitationResponse:
    result = _safe(
        lambda: repository.revoke_invitation(
            administrator,
            invitation_id,
            current_request_id(request),
        )
    )
    LOGGER.info(
        "beta_invitation_revoked request_id=%s invitation_id=%s",
        current_request_id(request),
        invitation_id,
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
