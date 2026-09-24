"""Invitation onboarding and current learner endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..dependencies import IdentityRepositoryDependency, LearnerDependency
from ..identity_contracts import (
    AcceptInvitationRequest,
    CurrentLearnerResponse,
    InvitationAcceptanceResponse,
)
from ..identity_repository import IdentityError

router = APIRouter(prefix="/api/v1", tags=["identity"])


def _safe(call):
    try:
        return call()
    except IdentityError as exc:
        raise HTTPException(
            status_code=exc.status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


@router.post(
    "/onboarding/accept-invitation",
    operation_id="acceptBetaInvitation",
    response_model=InvitationAcceptanceResponse,
    summary="Accept a beta invitation and pin the learner to its course revision",
)
async def accept_invitation(
    body: AcceptInvitationRequest,
    learner: LearnerDependency,
    repository: IdentityRepositoryDependency,
) -> InvitationAcceptanceResponse:
    return _safe(
        lambda: repository.accept_invitation(
            learner,
            body.invitation_code,
            body.display_name,
        )
    )


@router.get(
    "/me",
    operation_id="getCurrentLearner",
    response_model=CurrentLearnerResponse,
    summary="Get the authenticated learner profile and pinned enrolments",
)
async def current_learner(
    learner: LearnerDependency,
    repository: IdentityRepositoryDependency,
) -> CurrentLearnerResponse:
    return _safe(lambda: repository.current_learner(learner))
