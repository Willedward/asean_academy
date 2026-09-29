"""Learner question reports and protected administrator inbox."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..conventions import current_request_id
from ..dependencies import (
    AdminLearnerDependency,
    AdminWriteRateLimitDependency,
    EnrolledLearnerDependency,
    LearnerProgressWriteRateLimitDependency,
    QuestionReportRepositoryDependency,
)
from ..question_report_contracts import (
    AdminQuestionReportListResponse,
    AdminQuestionReportResponse,
    CreateQuestionReportRequest,
    QuestionReportListResponse,
    QuestionReportResponse,
    ResolveQuestionReportRequest,
)
from ..question_report_repository import QuestionReportError

router = APIRouter(prefix="/api/v1", tags=["question reports"])


def _safe(call):
    try:
        return call()
    except QuestionReportError as exc:
        raise HTTPException(
            status_code=exc.status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


@router.post(
    "/question-reports",
    operation_id="createQuestionReport",
    response_model=QuestionReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_report(
    body: CreateQuestionReportRequest,
    request: Request,
    learner: EnrolledLearnerDependency,
    repository: QuestionReportRepositoryDependency,
    _rate_limit: LearnerProgressWriteRateLimitDependency,
) -> QuestionReportResponse:
    return _safe(lambda: repository.create(
        learner.learner_id,
        session_id=str(body.session_id),
        question_key=body.question_key,
        question_revision=body.question_revision,
        category=body.category,
        comment=body.comment,
        request_id=current_request_id(request),
    ))


@router.get(
    "/question-reports",
    operation_id="listLearnerQuestionReports",
    response_model=QuestionReportListResponse,
)
async def learner_reports(
    learner: EnrolledLearnerDependency,
    repository: QuestionReportRepositoryDependency,
) -> QuestionReportListResponse:
    return _safe(lambda: repository.learner_list(learner.learner_id))


@router.get(
    "/question-reports/{report_id}",
    operation_id="getLearnerQuestionReport",
    response_model=QuestionReportResponse,
)
async def learner_report_detail(
    report_id: UUID,
    learner: EnrolledLearnerDependency,
    repository: QuestionReportRepositoryDependency,
) -> QuestionReportResponse:
    return _safe(
        lambda: repository.learner_get(learner.learner_id, str(report_id))
    )


@router.get(
    "/admin/question-reports",
    operation_id="listAdminQuestionReports",
    response_model=AdminQuestionReportListResponse,
    tags=["admin"],
)
async def admin_reports(
    administrator: AdminLearnerDependency,
    repository: QuestionReportRepositoryDependency,
    report_status: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminQuestionReportListResponse:
    del administrator
    if report_status not in {None, "open", "in_review", "resolved", "dismissed"}:
        raise HTTPException(422, detail={"code": "validation_error", "message": "Unknown report status."})
    return _safe(lambda: repository.admin_list(status=report_status, limit=limit, offset=offset))


@router.get(
    "/admin/question-reports/{report_id}",
    operation_id="getAdminQuestionReport",
    response_model=AdminQuestionReportResponse,
    tags=["admin"],
)
async def admin_report_detail(
    report_id: UUID,
    administrator: AdminLearnerDependency,
    repository: QuestionReportRepositoryDependency,
) -> AdminQuestionReportResponse:
    del administrator
    return _safe(lambda: repository.admin_get(str(report_id)))


@router.patch(
    "/admin/question-reports/{report_id}",
    operation_id="resolveAdminQuestionReport",
    response_model=AdminQuestionReportResponse,
    tags=["admin"],
)
async def resolve_report(
    report_id: UUID,
    body: ResolveQuestionReportRequest,
    request: Request,
    administrator: AdminLearnerDependency,
    repository: QuestionReportRepositoryDependency,
    _rate_limit: AdminWriteRateLimitDependency,
) -> AdminQuestionReportResponse:
    return _safe(lambda: repository.resolve(
        str(report_id),
        status=body.status,
        resolution=body.resolution,
        administrator_id=administrator.learner_id,
        request_id=current_request_id(request),
    ))
