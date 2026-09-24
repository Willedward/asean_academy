"""Invitation onboarding and current learner endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from ..conventions import current_request_id
from ..dependencies import IdentityRepositoryDependency, LearnerDependency
from ..identity_contracts import (
    AcceptInvitationRequest,
    CurrentLearnerResponse,
    InvitationAcceptanceResponse,
)
from ..identity_repository import IdentityError

LOGGER = logging.getLogger("learning_api.identity")
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
    request: Request,
    learner: LearnerDependency,
    repository: IdentityRepositoryDependency,
) -> InvitationAcceptanceResponse:
    try:
        result = repository.accept_invitation(
            learner,
            body.invitation_code,
            body.display_name,
            current_request_id(request),
        )
    except IdentityError as exc:
        LOGGER.warning(
            "onboarding_rejected request_id=%s code=%s",
            current_request_id(request),
            exc.code,
        )
        raise HTTPException(
            status_code=exc.status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    LOGGER.info("onboarding_accepted request_id=%s", current_request_id(request))
    return result


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
