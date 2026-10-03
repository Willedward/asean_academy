"""Provider boundary for live tutoring; no provider credential reaches a client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .tutor_contracts import TutorBlock, TutorMode


class TutorProviderError(RuntimeError):
    """Safe provider failure surfaced by the tutor orchestration layer."""


@dataclass(frozen=True, slots=True)
class TutorProviderUsage:
    input_tokens: int
    output_tokens: int
    cost_micros_sgd: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True, slots=True)
class TutorProviderRequest:
    mode: TutorMode
    learner_message: str
    question_title: str
    question_blocks: tuple[dict, ...]
    unlocked_hint_blocks: tuple[dict, ...]
    lesson_sections: tuple[dict, ...]
    unlocked_solution_blocks: tuple[dict, ...]
    recent_messages: tuple[dict, ...]
    answer_locked: bool
    solution_locked: bool
    prompt_version: str
    max_output_tokens: int


@dataclass(frozen=True, slots=True)
class TutorProviderResult:
    blocks: tuple[TutorBlock, ...]
    suggested_replies: tuple[str, ...]
    recommended_next_action: str | None
    model_name: str
    usage: TutorProviderUsage


class TutorProvider(Protocol):
    async def generate(self, request: TutorProviderRequest) -> TutorProviderResult: ...


class DisabledTutorProvider:
    async def generate(self, request: TutorProviderRequest) -> TutorProviderResult:
        del request
        raise TutorProviderError("The live tutor provider is disabled.")


class SyntheticTutorProvider:
    """Deterministic test double. It is rejected outside the test environment."""

    _RESPONSES = {
        "clarify_question": "Let's restate the task in smaller pieces. What quantity is the question asking you to find?",
        "diagnose_misconception": "Let's inspect the step that changed the value. Which operation did you apply first?",
        "socratic_prompt": "What is the first mathematical fact from this topic that could help you begin?",
        "alternative_explanation": "Try viewing the quantities as equal groups. What would one group contain?",
        "analogous_example": "Use the same method on a simpler example first, then identify the matching step in your question.",
        "solution_explanation": "The approved solution is now available. Which step would you like me to unpack first?",
        "lesson_recommendation": "Review the matching lesson explanation, then return and describe the first step in your own words.",
    }

    async def generate(self, request: TutorProviderRequest) -> TutorProviderResult:
        text = self._RESPONSES[request.mode]
        input_tokens = max(1, len(request.learner_message.split()) + 24)
        output_tokens = max(1, len(text.split()))
        return TutorProviderResult(
            blocks=(TutorBlock(type="text", content=text),),
            suggested_replies=("Can you give me one hint?", "Can you explain that differently?"),
            recommended_next_action="Try one step, then submit your answer for checking.",
            model_name="synthetic-tutor-v1",
            usage=TutorProviderUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_micros_sgd=0,
            ),
        )


def provider_for(name: str, *, environment: str) -> TutorProvider:
    if name == "disabled":
        return DisabledTutorProvider()
    if name == "synthetic" and environment == "test":
        return SyntheticTutorProvider()
    if name == "synthetic":
        raise RuntimeError("The synthetic tutor provider is allowed only in test")
    raise RuntimeError(f"Unsupported tutor provider: {name}")
