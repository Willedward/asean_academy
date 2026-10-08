"""Protected administrator endpoints for the AI tutor evaluation lab."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from ..admin_repository import BetaOperationsError
from ..conventions import current_request_id
from ..dependencies import AdminLearnerDependency, BetaOperationsRepositoryDependency
from ..tutor_evaluation_contracts import (
    TutorEvaluationConversationRequest,
    TutorEvaluationConversationTurnRequest,
    TutorEvaluationReviewRequest,
    TutorEvaluationRunRequest,
    TutorProviderConnectionResponse,
)
from ..tutor_evaluation_lab import (
    check_gemini_connection,
    create_conversation,
    create_conversation_turn,
    execute_case,
    get_conversation,
    lab_state,
    latest_conversation,
    record_evaluation_review,
)

router = APIRouter(prefix="/api/v1/admin/tutor-evaluation", tags=["admin"])


def _safe(call):
    try:
        return call()
    except BetaOperationsError as exc:
        raise HTTPException(
            status_code=exc.status, detail={"code": exc.code, "message": str(exc)}
        ) from exc


@router.get("", operation_id="getTutorEvaluationLab")
def get_lab(
    request: Request,
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
):
    del administrator
    return _safe(
        lambda: lab_state(
            repository, request.app.state.course_catalogue, request.app.state.settings
        )
    )


@router.post(
    "/connection-check",
    operation_id="checkTutorProviderConnection",
    response_model=TutorProviderConnectionResponse,
)
async def check_connection(
    request: Request,
    administrator: AdminLearnerDependency,
):
    del administrator
    try:
        return await check_gemini_connection(request.app.state.settings)
    except BetaOperationsError as exc:
        raise HTTPException(
            status_code=exc.status, detail={"code": exc.code, "message": str(exc)}
        ) from exc


@router.post(
    "/cases/{case_id}/runs",
    operation_id="runTutorEvaluationCase",
    status_code=status.HTTP_201_CREATED,
)
async def run_case(
    case_id: str,
    body: TutorEvaluationRunRequest,
    request: Request,
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
):
    try:
        return await execute_case(
            repository,
            request.app.state.course_catalogue,
            request.app.state.settings,
            administrator,
            case_id,
            body.provider,
            current_request_id(request),
        )
    except BetaOperationsError as exc:
        raise HTTPException(
            status_code=exc.status, detail={"code": exc.code, "message": str(exc)}
        ) from exc


@router.get(
    "/cases/{case_id}/conversations/latest",
    operation_id="getLatestTutorEvaluationConversation",
)
def get_latest_conversation(
    case_id: str,
    request: Request,
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
):
    return _safe(
        lambda: latest_conversation(
            repository, request.app.state.settings, administrator, case_id
        )
    )


@router.post(
    "/cases/{case_id}/conversations",
    operation_id="createTutorEvaluationConversation",
    status_code=status.HTTP_201_CREATED,
)
def start_conversation(
    case_id: str,
    body: TutorEvaluationConversationRequest,
    request: Request,
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
):
    return _safe(
        lambda: create_conversation(
            repository,
            request.app.state.course_catalogue,
            request.app.state.settings,
            administrator,
            case_id,
            body.provider,
            current_request_id(request),
        )
    )


@router.get(
    "/conversations/{conversation_id}",
    operation_id="getTutorEvaluationConversation",
)
def read_conversation(
    conversation_id: UUID,
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
):
    return _safe(
        lambda: get_conversation(repository, administrator, conversation_id)
    )


@router.post(
    "/conversations/{conversation_id}/turns",
    operation_id="createTutorEvaluationConversationTurn",
    status_code=status.HTTP_201_CREATED,
)
async def send_conversation_turn(
    conversation_id: UUID,
    body: TutorEvaluationConversationTurnRequest,
    request: Request,
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
):
    try:
        return await create_conversation_turn(
            repository,
            request.app.state.course_catalogue,
            request.app.state.settings,
            administrator,
            conversation_id,
            body.message,
            current_request_id(request),
        )
    except BetaOperationsError as exc:
        raise HTTPException(
            status_code=exc.status, detail={"code": exc.code, "message": str(exc)}
        ) from exc


@router.post(
    "/runs/{run_id}/reviews",
    operation_id="reviewTutorEvaluationRun",
    status_code=status.HTTP_201_CREATED,
)
def review_run(
    run_id: UUID,
    body: TutorEvaluationReviewRequest,
    request: Request,
    administrator: AdminLearnerDependency,
    repository: BetaOperationsRepositoryDependency,
):
    return _safe(
        lambda: record_evaluation_review(
            repository, administrator, run_id, body, current_request_id(request)
        )
    )
