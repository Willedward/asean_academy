"""API contracts for revision-pinned Mathematics baseline and endline diagnostics."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from .contracts import ApiModel

DiagnosticPurpose = Literal["baseline", "endline"]
DiagnosticSessionState = Literal["in_progress", "submitted"]
AnswerText = Annotated[str, StringConstraints(max_length=500)]


class DiagnosticNextResponse(ApiModel):
    status: Literal["content_pending", "start", "resume", "baseline_complete", "completed"]
    purpose: DiagnosticPurpose | None = None
    session_id: UUID | None = None
    result_session_id: UUID | None = None
    title: str
    message: str
    estimated_minutes: int | None = None
    question_count: int | None = None


class CreateDiagnosticSessionRequest(ApiModel):
    expected_purpose: DiagnosticPurpose | None = None


class DiagnosticPartResponse(ApiModel):
    position: int
    label: str | None
    prompt: list[dict[str, Any]]
    marks: int
    response_type: Literal["numeric", "algebraic_expression"]
    input_placeholder: str


class DiagnosticQuestionResponse(ApiModel):
    stable_key: str
    revision: int
    title: str
    difficulty: int = Field(ge=1, le=5)
    calculator_allowed: bool
    stem: list[dict[str, Any]]
    total_marks: int
    parts: list[DiagnosticPartResponse]


class DiagnosticItemResponse(ApiModel):
    position: int
    outcome_code: str
    weight: float
    question: DiagnosticQuestionResponse
    saved_answers: dict[str, str] | None = None
    saved_at: datetime | None = None


class DiagnosticSessionResponse(ApiModel):
    session_id: UUID
    state: DiagnosticSessionState
    purpose: DiagnosticPurpose
    form_key: str
    form_revision: int
    title: str
    instructions: str
    estimated_minutes: int
    started_at: datetime
    submitted_at: datetime | None = None
    items: list[DiagnosticItemResponse]


class SaveDiagnosticResponseRequest(ApiModel):
    answers: dict[str, AnswerText] = Field(min_length=1, max_length=20)


class SaveDiagnosticResponse(ApiModel):
    session_id: UUID
    position: int
    saved: Literal[True] = True
    saved_at: datetime


class DiagnosticOutcomeScore(ApiModel):
    outcome_code: str
    score: float
    max_score: float
    percentage: float


class DiagnosticResultResponse(ApiModel):
    session_id: UUID
    purpose: DiagnosticPurpose
    form_key: str
    form_revision: int
    score: float
    max_score: float
    percentage: float
    band: Literal["getting_started", "on_track", "ahead"]
    band_policy_version: str
    outcome_scores: list[DiagnosticOutcomeScore]
    strengths: list[str]
    priorities: list[str]
    submitted_at: datetime


class AdminDiagnosticAttemptResponse(DiagnosticResultResponse):
    state: Literal["submitted", "reset"]
    reset_at: datetime | None = None
    reset_reason: str | None = None


class AdminStudentDiagnosticsResponse(ApiModel):
    learner_id: UUID
    baseline: AdminDiagnosticAttemptResponse | None = None
    endline: AdminDiagnosticAttemptResponse | None = None
    history: list[AdminDiagnosticAttemptResponse]


class ResetDiagnosticRequest(ApiModel):
    reason: str = Field(min_length=10, max_length=500)


class ResetDiagnosticResponse(ApiModel):
    learner_id: UUID
    purpose: DiagnosticPurpose
    reset: Literal[True] = True
    reset_at: datetime
