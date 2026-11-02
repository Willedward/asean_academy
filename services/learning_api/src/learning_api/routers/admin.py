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
    EnglishEssayReleaseRepositoryDependency,
)
from ..english_essay_release import (
    CalibrationEvidenceResponse,
    ConsentDecisionRequest,
    ConsentDecisionResponse,
    EssayFeedbackReleaseEvidenceResponse,
    PrivacyReviewRequest,
    PrivacyReviewResponse,
    RecordCalibrationReportRequest,
    ReleaseDecisionRequest,
    ReleaseDecisionResponse,
)
from ..english_essay_release_repository import EnglishEssayReleaseError

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


def _release_safe(call):
    try:
        return call()
    except EnglishEssayReleaseError as exc:
        raise HTTPException(
            status_code=exc.status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


def _release_evidence(request: Request, repository) -> dict:
    settings = request.app.state.settings
    return repository.evidence(
        settings.english_essay_provider_name,
        settings.english_essay_model_name,
        settings.english_essay_provider_policy_version,
        environment_enabled=settings.english_essay_feedback_enabled,
    )


@router.get(
    "/english-essay-feedback/release-evidence",
    operation_id="getEnglishEssayFeedbackReleaseEvidence",
    response_model=EssayFeedbackReleaseEvidenceResponse,
    summary="Inspect privacy-safe evidence and blockers for live essay feedback",
)
async def english_essay_feedback_release_evidence(
    request: Request,
    administrator: AcademicAdminLearnerDependency,
    repository: EnglishEssayReleaseRepositoryDependency,
) -> EssayFeedbackReleaseEvidenceResponse:
    del administrator
    return _release_evidence(request, repository)


@router.post(
    "/english-essay-feedback/calibration-reports",
    operation_id="recordEnglishEssayCalibrationReport",
    response_model=CalibrationEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a privacy-safe offline calibration report",
)
async def record_english_essay_calibration_report(
    body: RecordCalibrationReportRequest,
    request: Request,
    administrator: AcademicAdminLearnerDependency,
    repository: EnglishEssayReleaseRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> CalibrationEvidenceResponse:
    return _release_safe(
        lambda: repository.record_calibration(
            body, administrator.learner_id, current_request_id(request)
        )
    )


@router.post(
    "/english-essay-feedback/privacy-reviews",
    operation_id="recordEnglishEssayPrivacyReview",
    response_model=PrivacyReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an immutable privacy and safeguarding review",
)
async def record_english_essay_privacy_review(
    body: PrivacyReviewRequest,
    request: Request,
    administrator: AcademicAdminLearnerDependency,
    repository: EnglishEssayReleaseRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> PrivacyReviewResponse:
    return _release_safe(
        lambda: repository.record_privacy_review(
            body, administrator.learner_id, current_request_id(request)
        )
    )


@router.post(
    "/english-essay-feedback/release-decisions",
    operation_id="recordEnglishEssayFeedbackReleaseDecision",
    response_model=ReleaseDecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Explicitly release or suspend live essay feedback",
)
async def record_english_essay_feedback_release_decision(
    body: ReleaseDecisionRequest,
    request: Request,
    administrator: AcademicAdminLearnerDependency,
    repository: EnglishEssayReleaseRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> ReleaseDecisionResponse:
    return _release_safe(
        lambda: repository.record_release_decision(
            calibration_gate_report_id=body.calibration_gate_report_id,
            privacy_review_id=body.privacy_review_id,
            action=body.action,
            reason=body.reason,
            actor_user_id=administrator.learner_id,
            request_id=current_request_id(request),
        )
    )


@router.post(
    "/students/{learner_id}/english-essay-consent-events",
    operation_id="recordEnglishEssayProcessingConsent",
    response_model=ConsentDecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record opaque guardian consent or revocation evidence",
)
async def record_english_essay_processing_consent(
    learner_id: UUID,
    body: ConsentDecisionRequest,
    request: Request,
    administrator: AcademicAdminLearnerDependency,
    repository: EnglishEssayReleaseRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> ConsentDecisionResponse:
    return _release_safe(
        lambda: repository.record_consent(
            learner_id, body, administrator.learner_id, current_request_id(request)
        )
    )


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
