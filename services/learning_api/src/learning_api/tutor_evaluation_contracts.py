"""Administrator contracts for controlled AI tutor calibration runs."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import ApiModel


class TutorEvaluationRunRequest(ApiModel):
    provider: Literal["synthetic", "gemini"] = "synthetic"
    confirm_live: bool = False

    @model_validator(mode="after")
    def confirm_paid_run(self):
        if self.provider == "gemini" and not self.confirm_live:
            raise ValueError("confirm_live must be true for a Gemini evaluation run")
        return self


class TutorEvaluationReviewRequest(ApiModel):
    dimension: Literal["mathematics", "editorial"]
    decision: Literal["approved", "changes_requested"]
    mathematics_correctness: int = Field(ge=1, le=5)
    pedagogical_quality: int = Field(ge=1, le=5)
    curriculum_fit: int = Field(ge=1, le=5)
    safety_and_leakage: int = Field(ge=1, le=5)
    notes: str = Field(min_length=10, max_length=2000)


class TutorProviderConnectionResponse(ApiModel):
    connected: bool
    probe_model: str
    configured_tutor_model: str
    response_text: str
    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
