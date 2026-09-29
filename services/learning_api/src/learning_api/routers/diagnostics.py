"""Refresh-safe learner diagnostics and protected administrator comparison."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, status

from ..conventions import current_request_id
from ..dependencies import (
    AcademicAdminLearnerDependency,
    AdminWriteRateLimitDependency,
    DiagnosticRepositoryDependency,
    EnrolledLearnerDependency,
    PracticeAttemptRateLimitDependency,
    PracticeSessionRateLimitDependency,
)
from ..diagnostic_contracts import (
    AdminStudentDiagnosticsResponse,
    CreateDiagnosticSessionRequest,
    DiagnosticNextResponse,
    DiagnosticResultResponse,
    DiagnosticSessionResponse,
    ResetDiagnosticRequest,
    ResetDiagnosticResponse,
    SaveDiagnosticResponse,
    SaveDiagnosticResponseRequest,
)
from ..diagnostic_repository import DiagnosticError

LOGGER = logging.getLogger("learning_api.diagnostics")
router = APIRouter(prefix="/api/v1", tags=["diagnostics"])

IdempotencyHeader = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=1, max_length=200),
]


def _safe(call):
    try:
        return call()
    except DiagnosticError as exc:
        raise HTTPException(
            status_code=exc.status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


@router.get(
    "/diagnostics/next",
    operation_id="getNextDiagnostic",
    response_model=DiagnosticNextResponse,
    summary="Get the server-owned next baseline or endline diagnostic action",
)
async def next_diagnostic(
    learner: EnrolledLearnerDependency,
    repository: DiagnosticRepositoryDependency,
) -> DiagnosticNextResponse:
    return _safe(lambda: repository.next(learner.learner_id))


@router.post(
    "/diagnostics/sessions",
    operation_id="createDiagnosticSession",
    response_model=DiagnosticSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start or replay the eligible diagnostic session",
)
async def create_session(
    body: CreateDiagnosticSessionRequest,
    idempotency_key: IdempotencyHeader,
    learner: EnrolledLearnerDependency,
    repository: DiagnosticRepositoryDependency,
    _rate_limit: PracticeSessionRateLimitDependency,
) -> DiagnosticSessionResponse:
    return _safe(
        lambda: repository.create_session(
            learner.learner_id,
            idempotency_key,
            body.expected_purpose,
        )
    )


@router.get(
    "/diagnostics/sessions/{session_id}",
    operation_id="getDiagnosticSession",
    response_model=DiagnosticSessionResponse,
    summary="Resume a learner-owned diagnostic with saved answers",
)
async def get_session(
    session_id: UUID,
    learner: EnrolledLearnerDependency,
    repository: DiagnosticRepositoryDependency,
) -> DiagnosticSessionResponse:
    return _safe(lambda: repository.session(learner.learner_id, str(session_id)))


@router.put(
    "/diagnostics/sessions/{session_id}/responses/{position}",
    operation_id="saveDiagnosticResponse",
    response_model=SaveDiagnosticResponse,
    summary="Autosave one diagnostic response without exposing correctness",
)
async def save_response(
    session_id: UUID,
    position: int,
    body: SaveDiagnosticResponseRequest,
    idempotency_key: IdempotencyHeader,
    learner: EnrolledLearnerDependency,
    repository: DiagnosticRepositoryDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> SaveDiagnosticResponse:
    if position < 1:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": "Position must be positive."},
        )
    return _safe(
        lambda: repository.save_response(
            learner.learner_id,
            str(session_id),
            position,
            body.answers,
            idempotency_key,
        )
    )


@router.post(
    "/diagnostics/sessions/{session_id}/submit",
    operation_id="submitDiagnosticSession",
    response_model=DiagnosticResultResponse,
    summary="Submit a complete diagnostic and create immutable score evidence",
)
async def submit_session(
    session_id: UUID,
    learner: EnrolledLearnerDependency,
    repository: DiagnosticRepositoryDependency,
    _rate_limit: PracticeAttemptRateLimitDependency,
) -> DiagnosticResultResponse:
    result = _safe(lambda: repository.submit(learner.learner_id, str(session_id)))
    LOGGER.info(
        "diagnostic_submitted",
        extra={
            "learner_id": learner.learner_id,
            "session_id": str(session_id),
            "purpose": result["purpose"],
        },
    )
    return result


@router.get(
    "/diagnostics/sessions/{session_id}/result",
    operation_id="getDiagnosticResult",
    response_model=DiagnosticResultResponse,
    summary="Get submitted diagnostic outcome scores and readiness band",
)
async def get_result(
    session_id: UUID,
    learner: EnrolledLearnerDependency,
    repository: DiagnosticRepositoryDependency,
) -> DiagnosticResultResponse:
    return _safe(lambda: repository.result(learner.learner_id, str(session_id)))


@router.get(
    "/admin/students/{learner_id}/diagnostics",
    operation_id="getAdminStudentDiagnostics",
    response_model=AdminStudentDiagnosticsResponse,
    tags=["admin"],
    summary="Compare one learner's baseline and endline score evidence",
)
async def admin_student_diagnostics(
    learner_id: UUID,
    administrator: AcademicAdminLearnerDependency,
    repository: DiagnosticRepositoryDependency,
) -> AdminStudentDiagnosticsResponse:
    del administrator
    return _safe(lambda: repository.admin_student_results(str(learner_id)))


@router.post(
    "/admin/students/{learner_id}/diagnostics/{purpose}/reset",
    operation_id="resetAdminStudentDiagnostic",
    response_model=ResetDiagnosticResponse,
    tags=["admin"],
    summary="Audit and reset one exceptional diagnostic attempt",
)
async def reset_diagnostic(
    learner_id: UUID,
    purpose: str,
    body: ResetDiagnosticRequest,
    request: Request,
    administrator: AcademicAdminLearnerDependency,
    repository: DiagnosticRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> ResetDiagnosticResponse:
    if purpose not in {"baseline", "endline"}:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": "Unknown diagnostic purpose."},
        )
    result = _safe(
        lambda: repository.reset(
            str(learner_id),
            purpose,
            administrator.learner_id,
            body.reason,
            current_request_id(request),
        )
    )
    LOGGER.warning(
        "diagnostic_reset",
        extra={
            "request_id": current_request_id(request),
            "learner_id": str(learner_id),
            "purpose": purpose,
            "administrator_id": administrator.learner_id,
        },
    )
    return result
