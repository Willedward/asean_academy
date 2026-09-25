"""Typed, learner-safe contracts for answer-only Mathematics practice."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, StringConstraints, model_validator

from .contracts import ApiModel

PracticeMode = Literal["guided_practice", "retry_review", "checkpoint"]
PracticeStage = Literal["guided", "independent", "challenge", "checkpoint", "adaptive"]


class CreatePracticeSessionRequest(ApiModel):
    lesson_key: str | None = Field(default=None, pattern=r"^n1-lesson-[0-9]{2}$")
    unit_key: str | None = Field(default=None, pattern=r"^[a-z0-9-]+$")
    mode: PracticeMode = "guided_practice"
    question_count: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def target_matches_mode(self):
        if self.mode == "checkpoint":
            if self.unit_key is None or self.lesson_key is not None:
                raise ValueError("checkpoint sessions require unit_key and no lesson_key")
        elif self.lesson_key is None or self.unit_key is not None:
            raise ValueError("lesson practice sessions require lesson_key and no unit_key")
        return self


class PracticeSessionResponse(ApiModel):
    session_id: str
    status: Literal["active", "completed"]
    question_count: int
    lesson_key: str | None = None
    unit_key: str | None = None
    mode: PracticeMode
    development_drafts: bool


class PracticeSessionSummary(ApiModel):
    session_id: str
    status: Literal["active", "completed"]
    question_count: int
    assigned_count: int
    resolved_count: int
    correct_count: int
    incorrect_count: int = 0
    gave_up_count: int
    lesson_key: str | None = None
    unit_key: str | None = None
    mode: PracticeMode
    development_drafts: bool


class QuestionPartResponse(ApiModel):
    position: int
    label: str | None
    prompt: list[dict[str, Any]]
    marks: int
    response_type: Literal["numeric", "algebraic_expression"]
    input_placeholder: str


class QuestionAssetResponse(ApiModel):
    asset_key: str
    kind: str
    format: str
    path: str
    alt_text: str
    width: int | None
    height: int | None


class PublicQuestionResponse(ApiModel):
    stable_key: str
    revision: int
    title: str
    difficulty: int
    primary_outcome: str
    calculator_allowed: bool
    total_marks: int
    source_status: Literal["draft", "reviewed", "published", "retired"]
    stem: list[dict[str, Any]]
    parts: list[QuestionPartResponse]
    assets: list[QuestionAssetResponse]


class NextQuestionResponse(ApiModel):
    status: Literal["active", "completed"]
    session: PracticeSessionSummary
    position: int | None = None
    selection_reason: str | None = None
    stage: PracticeStage | None = None
    attempt_count: int | None = None
    highest_hint_stage: int | None = None
    solution_available: bool | None = None
    question: PublicQuestionResponse | None = None


AnswerText = Annotated[str, StringConstraints(max_length=500)]


class SubmitAttemptRequest(ApiModel):
    session_id: str
    question_key: str = Field(pattern=r"^n1-l[1-3]-[0-9]{2}$")
    question_revision: int = Field(ge=1)
    answers: dict[str, AnswerText] = Field(min_length=1, max_length=20)


class AttemptPartResult(ApiModel):
    position: int
    correct: bool
    error: str | None
    marks_awarded: int
    marks_available: int


class AttemptResponse(ApiModel):
    attempt_number: int
    correct: bool
    parts: list[AttemptPartResult]
    marks_awarded: int
    marks_available: int
    question_finished: bool
    solution_available: bool


class HintPartResponse(ApiModel):
    position: int
    content: list[dict[str, Any]]


class HintResponse(ApiModel):
    stage: Literal[1, 2]
    parts: list[HintPartResponse]


class SolutionPartResponse(ApiModel):
    position: int
    label: str | None
    canonical_answer: str
    canonical_latex: str
    steps: list[dict[str, Any]]


class SolutionResponse(ApiModel):
    stable_key: str
    revision: int
    parts: list[SolutionPartResponse]


class GiveUpResponse(ApiModel):
    status: Literal["gave_up"]
    solution: SolutionResponse
