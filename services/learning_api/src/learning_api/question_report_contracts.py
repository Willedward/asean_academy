"""Learner and administrator contracts for exact-revision question reports."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from .contracts import ApiModel

ReportCategory = Literal["possible_error", "unclear_wording", "display_problem", "other"]
ReportStatus = Literal["open", "in_review", "resolved", "dismissed"]


class CreateQuestionReportRequest(ApiModel):
    session_id: UUID
    question_key: str = Field(min_length=1, max_length=120)
    question_revision: int = Field(ge=1)
    category: ReportCategory
    comment: str = Field(min_length=1, max_length=1000)


class QuestionReportResponse(ApiModel):
    report_id: UUID
    question_key: str
    question_revision: int
    question_title: str
    category: ReportCategory
    comment: str
    status: ReportStatus
    resolution: str | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None


class QuestionReportListResponse(ApiModel):
    reports: list[QuestionReportResponse]
    total: int


class ResolveQuestionReportRequest(ApiModel):
    status: Literal["in_review", "resolved", "dismissed"]
    resolution: str | None = Field(default=None, max_length=2000)


class AdminQuestionReportResponse(QuestionReportResponse):
    learner_id: UUID
    learner_email: str
    session_id: UUID | None = None


class AdminQuestionReportListResponse(ApiModel):
    reports: list[AdminQuestionReportResponse]
    total: int
