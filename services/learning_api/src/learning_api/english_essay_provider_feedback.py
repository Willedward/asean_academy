"""Fail-closed validation for future provider-generated essay feedback.

This module deliberately contains no network client.  It defines the only shape a
future provider adapter may return and verifies that its evidence points back to
the immutable learner submission before any allowance can be committed.
"""

from __future__ import annotations

import re
import socket
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .english_essay_repository import EnglishEssayError

PROVIDER_FEEDBACK_SCHEMA_VERSION = "english-essay-provider-feedback-v1"
PROVIDER_FEEDBACK_VALIDATION_VERSION = "english-essay-evidence-validation-v1"
PROVIDER_FEEDBACK_DISCLAIMER = (
    "This is a NextScholar AI preparation estimate based on an instructional rubric. "
    "It is not an official ASEAN Scholarship score, result or admission prediction."
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvidenceSpan(_StrictModel):
    quote: str = Field(min_length=1, max_length=320)
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def end_follows_start(self) -> EvidenceSpan:
        if self.end <= self.start:
            raise ValueError("end must be greater than start")
        return self


class ProviderCriterionFeedback(_StrictModel):
    criterion_key: str = Field(min_length=1, max_length=100)
    criterion_title: str = Field(min_length=1, max_length=200)
    preparation_level: int = Field(ge=1, le=5)
    evidence_spans: list[EvidenceSpan] = Field(min_length=1, max_length=4)
    what_works: str = Field(min_length=1, max_length=1000)
    next_step: str = Field(min_length=1, max_length=1000)


class ProviderEssayFeedback(_StrictModel):
    schema_version: Literal[PROVIDER_FEEDBACK_SCHEMA_VERSION]
    rubric_key: str = Field(min_length=1, max_length=200)
    rubric_revision: int = Field(ge=1)
    preparation_estimate: Literal["limited", "emerging", "developing", "secure", "strong"]
    criterion_feedback: list[ProviderCriterionFeedback] = Field(min_length=3, max_length=6)
    overall_summary: str = Field(min_length=1, max_length=1600)
    strengths: list[str] = Field(min_length=1, max_length=4)
    priorities: list[str] = Field(min_length=2, max_length=2)
    revision_task: str = Field(min_length=1, max_length=1000)
    transfer_goal: str = Field(min_length=1, max_length=1000)
    learner_disclaimer: Literal[PROVIDER_FEEDBACK_DISCLAIMER]


_PROHIBITED_CLAIM_PATTERNS = (
    re.compile(r"\bofficial\s+(?:asean\s+scholarship\s+)?(?:score|mark|grade|result)\b", re.I),
    re.compile(r"\b(?:admission|acceptance|selection)\s+(?:chance|probability|likelihood)\b", re.I),
    re.compile(
        r"\b(?:chance|probability|likelihood)\s+of\s+(?:admission|acceptance|selection|passing|qualifying)\b",
        re.I,
    ),
    re.compile(r"\b\d{1,3}%\s+(?:chance|probability|likelihood)\b", re.I),
    re.compile(
        r"\b(?:will|guaranteed?\s+to)\s+(?:pass|qualify|be selected|win the scholarship)\b", re.I
    ),
)


def _generated_text(feedback: ProviderEssayFeedback) -> list[str]:
    values = [
        feedback.overall_summary,
        *feedback.strengths,
        *feedback.priorities,
        feedback.revision_task,
        feedback.transfer_goal,
    ]
    for criterion in feedback.criterion_feedback:
        values.extend((criterion.what_works, criterion.next_step))
    return values


def validate_provider_feedback(
    raw: dict[str, Any],
    *,
    submission_body: str,
    rubric_key: str,
    rubric_revision: int,
    rubric_criteria: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate schema, rubric coverage and exact immutable evidence offsets."""

    try:
        feedback = ProviderEssayFeedback.model_validate(raw)
    except ValidationError as exc:
        raise EnglishEssayError(
            "essay_feedback_provider_schema_invalid",
            "The feedback provider returned an invalid structured response.",
            503,
        ) from exc

    if feedback.rubric_key != rubric_key or feedback.rubric_revision != rubric_revision:
        raise EnglishEssayError(
            "essay_feedback_provider_rubric_mismatch",
            "The feedback provider did not use the submission's pinned rubric revision.",
            503,
        )

    expected = {
        str(criterion["criterion_key"]): str(criterion["title"]) for criterion in rubric_criteria
    }
    received = [criterion.criterion_key for criterion in feedback.criterion_feedback]
    if len(received) != len(set(received)) or set(received) != set(expected):
        raise EnglishEssayError(
            "essay_feedback_provider_coverage_invalid",
            "The feedback provider must cover every pinned rubric criterion exactly once.",
            503,
        )

    for criterion in feedback.criterion_feedback:
        if criterion.criterion_title != expected[criterion.criterion_key]:
            raise EnglishEssayError(
                "essay_feedback_provider_rubric_mismatch",
                "The feedback provider changed a pinned rubric criterion.",
                503,
            )
        for evidence in criterion.evidence_spans:
            if (
                evidence.end > len(submission_body)
                or submission_body[evidence.start : evidence.end] != evidence.quote
            ):
                raise EnglishEssayError(
                    "essay_feedback_evidence_mismatch",
                    "Quoted feedback evidence does not match the immutable essay submission.",
                    503,
                )

    if any(not value.strip() for value in _generated_text(feedback)):
        raise EnglishEssayError(
            "essay_feedback_provider_schema_invalid",
            "The feedback provider returned empty learner feedback.",
            503,
        )

    if any(
        pattern.search(value)
        for value in _generated_text(feedback)
        for pattern in _PROHIBITED_CLAIM_PATTERNS
    ):
        raise EnglishEssayError(
            "essay_feedback_prohibited_claim",
            "The feedback provider returned a prohibited official-score or admission claim.",
            503,
        )

    validated = feedback.model_dump(mode="json")
    validated["validation_version"] = PROVIDER_FEEDBACK_VALIDATION_VERSION
    return validated


@dataclass(frozen=True, slots=True)
class ProviderFeedbackResult:
    output: dict[str, Any]
    actual_cost_micros_sgd: int


class EssayFeedbackProvider(Protocol):
    def generate(self, attempt: dict[str, Any]) -> ProviderFeedbackResult: ...


def process_provider_feedback_attempt(
    repository,
    attempt_id: str,
    *,
    provider: EssayFeedbackProvider,
    worker_id: str | None = None,
    request_id: str,
) -> bool:
    """Validate and atomically finalise one provider candidate attempt.

    Provider and validation failures permanently fail this candidate and atomically
    release its reservation. A later retry therefore requires a fresh learner
    action and reservation rather than silently making another paid call.
    """

    claimed = repository.claim(
        attempt_id,
        worker_id=worker_id or f"essay-feedback-worker:{socket.gethostname()}",
    )
    if claimed is None:
        return False
    try:
        result = provider.generate(claimed)
        if result.actual_cost_micros_sgd < 0:
            raise EnglishEssayError(
                "essay_feedback_provider_usage_invalid",
                "The feedback provider reported invalid usage.",
                503,
            )
        validated = validate_provider_feedback(
            result.output,
            submission_body=claimed["submission_body"],
            rubric_key=claimed["rubric_key"],
            rubric_revision=claimed["rubric_revision"],
            rubric_criteria=claimed["rubric_criteria"],
        )
        repository.complete_validated(
            attempt_id,
            lease_token=claimed["lease_token"],
            feedback=validated,
            actual_cost_micros_sgd=result.actual_cost_micros_sgd,
            request_id=request_id,
        )
    except Exception as exc:
        repository.fail_and_release(
            attempt_id,
            lease_token=claimed["lease_token"],
            error_code=(
                exc.code if isinstance(exc, EnglishEssayError) else "essay_feedback_provider_failed"
            ),
            error_message=f"{type(exc).__name__}: {exc}",
            request_id=request_id,
        )
        return False
    return True
