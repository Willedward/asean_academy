"""Public, provider-neutral contracts for the grounded Mathematics tutor."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from .contracts import ApiModel

TutorMode = Literal[
    "clarify_question",
    "diagnose_misconception",
    "socratic_prompt",
    "alternative_explanation",
    "analogous_example",
    "solution_explanation",
    "lesson_recommendation",
]


class AnswerLockState(ApiModel):
    answer_locked: bool
    solution_locked: bool


class CreateTutorSessionRequest(ApiModel):
    practice_session_id: UUID
    question_key: str = Field(min_length=1, max_length=100)
    question_revision: int = Field(ge=1)


class SendTutorMessageRequest(ApiModel):
    message: str = Field(min_length=1, max_length=1200)

    @field_validator("message")
    @classmethod
    def meaningful_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message must contain visible text")
        return cleaned


class TutorBlock(ApiModel):
    type: Literal["text", "inline_math", "display_math", "bullets"]
    content: str = Field(min_length=1, max_length=4000)


class TutorMessageResponse(ApiModel):
    id: UUID
    role: Literal["student", "assistant"]
    mode: TutorMode | None = None
    blocks: list[TutorBlock]
    safety_outcome: Literal["accepted", "answer_leakage_blocked", "provider_fallback"]
    created_at: datetime


class TutorSessionResponse(ApiModel):
    session_id: UUID
    practice_session_id: UUID
    question_key: str
    question_revision: int
    status: Literal["active", "closed"]
    answer_lock_state: AnswerLockState
    model_policy_version: str
    messages: list[TutorMessageResponse]
    created_at: datetime
    closed_at: datetime | None = None


class TutorQuotaResponse(ApiModel):
    daily_messages_remaining: int = Field(ge=0)
    daily_tokens_remaining: int = Field(ge=0)
    monthly_cost_remaining_micros_sgd: int = Field(ge=0)
    resets_at: datetime


class TutorReplyResponse(ApiModel):
    session_id: UUID
    message: TutorMessageResponse
    response_type: Literal["tutor_reply"] = "tutor_reply"
    suggested_replies: list[str] = Field(max_length=4)
    recommended_next_action: str | None = None
    answer_lock_state: AnswerLockState
    quota: TutorQuotaResponse


class TutorUsageAdminResponse(ApiModel):
    usage_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    learners: int = Field(ge=0)
    actual_requests: int = Field(ge=0)
    failed_requests: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    actual_cost_micros_sgd: int = Field(ge=0)
    reserved_cost_micros_sgd: int = Field(ge=0)
    active_reservations: int = Field(ge=0)
    route_decisions: int = Field(ge=0)
    shadow_route_decisions: int = Field(ge=0)
    recommended_premium_routes: int = Field(ge=0)
    executed_premium_routes: int = Field(ge=0)
    projected_recommended_cost_micros_sgd: int = Field(ge=0)
