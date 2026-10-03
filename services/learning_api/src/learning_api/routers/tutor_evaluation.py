"""Protected administrator endpoints for the AI tutor evaluation lab."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from ..admin_repository import BetaOperationsError
from ..conventions import current_request_id
from ..dependencies import AdminLearnerDependency, BetaOperationsRepositoryDependency
from ..tutor_evaluation_contracts import TutorEvaluationReviewRequest, TutorEvaluationRunRequest
from ..tutor_evaluation_lab import execute_case, lab_state, record_evaluation_review

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
