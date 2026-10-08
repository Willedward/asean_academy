"""Deterministic, auditable model routing for grounded tutor turns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .tutor_contracts import TutorMode

TutorModelTier = Literal["economy", "premium"]


@dataclass(frozen=True, slots=True)
class TutorModelTarget:
    tier: TutorModelTier
    provider_name: str
    model_name: str
    max_output_tokens: int
    input_cost_per_million_micros_sgd: int
    output_cost_per_million_micros_sgd: int

    def __post_init__(self) -> None:
        if not self.provider_name.strip() or not self.model_name.strip():
            raise ValueError("Tutor model targets require provider and model names")
        if self.max_output_tokens <= 0:
            raise ValueError("Tutor model output limits must be positive")
        if (
            self.input_cost_per_million_micros_sgd < 0
            or self.output_cost_per_million_micros_sgd < 0
        ):
            raise ValueError("Tutor model prices must not be negative")

    def maximum_cost_micros_sgd(self, max_input_tokens: int) -> int:
        if max_input_tokens <= 0:
            raise ValueError("Tutor model input limits must be positive")
        return _token_cost(
            max_input_tokens, self.input_cost_per_million_micros_sgd
        ) + _token_cost(
            self.max_output_tokens, self.output_cost_per_million_micros_sgd
        )


@dataclass(frozen=True, slots=True)
class TutorRoutingPolicy:
    version: str
    economy: TutorModelTarget
    premium: TutorModelTarget | None = None
    premium_threshold: int = 5
    max_premium_turns_per_session: int = 3

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("Tutor routing policy versions must not be empty")
        if self.economy.tier != "economy":
            raise ValueError("The economy target must use the economy tier")
        if self.premium is not None and self.premium.tier != "premium":
            raise ValueError("The premium target must use the premium tier")
        if self.premium_threshold <= 0 or self.max_premium_turns_per_session <= 0:
            raise ValueError("Tutor premium thresholds and limits must be positive")


@dataclass(frozen=True, slots=True)
class TutorRoutingContext:
    question_difficulty: int
    mode: TutorMode
    incorrect_attempts: int
    repeated_confusion_count: int
    premium_turns_this_session: int


@dataclass(frozen=True, slots=True)
class TutorRouteDecision:
    policy_version: str
    tier: TutorModelTier
    provider_name: str
    model_name: str
    mode: TutorMode
    question_difficulty: int
    score: int
    reason_codes: tuple[str, ...]
    max_output_tokens: int
    input_cost_per_million_micros_sgd: int
    output_cost_per_million_micros_sgd: int

    def maximum_cost_micros_sgd(self, max_input_tokens: int) -> int:
        return _token_cost(
            max_input_tokens, self.input_cost_per_million_micros_sgd
        ) + _token_cost(
            self.max_output_tokens, self.output_cost_per_million_micros_sgd
        )


MODE_WEIGHTS: dict[TutorMode, int] = {
    "clarify_question": 0,
    "socratic_prompt": 0,
    "lesson_recommendation": 0,
    "diagnose_misconception": 1,
    "analogous_example": 1,
    "alternative_explanation": 2,
    "solution_explanation": 2,
}

_CONFUSION_PHRASES = (
    "don't understand",
    "dont understand",
    "do not understand",
    "don't get",
    "dont get",
    "still confused",
    "still don't",
    "still dont",
    "another way",
    "different way",
    "explain differently",
)


def repeated_confusion_count(current_message: str, recent_messages: tuple[dict, ...]) -> int:
    """Count bounded learner confusion signals without an additional model call."""

    messages = [current_message]
    messages.extend(
        _message_text(item)
        for item in recent_messages
        if str(item.get("role", "")).casefold() == "student"
    )
    return sum(_has_confusion_signal(message) for message in messages if message)


class TutorModelRouter:
    def __init__(self, policy: TutorRoutingPolicy):
        self.policy = policy

    def decide(self, context: TutorRoutingContext) -> TutorRouteDecision:
        if not 1 <= context.question_difficulty <= 5:
            raise ValueError("Tutor question difficulty must be between 1 and 5")
        if context.incorrect_attempts < 0 or context.repeated_confusion_count < 0:
            raise ValueError("Tutor routing counters must not be negative")

        reasons: list[str] = [f"difficulty_{context.question_difficulty}"]
        score = context.question_difficulty - 1

        mode_weight = MODE_WEIGHTS[context.mode]
        score += mode_weight
        if mode_weight:
            reasons.append(f"mode_{context.mode}")

        if context.incorrect_attempts >= 3:
            score += 2
            reasons.append("three_or_more_incorrect_attempts")
        elif context.incorrect_attempts >= 2:
            score += 1
            reasons.append("multiple_incorrect_attempts")

        if context.repeated_confusion_count >= 2:
            score += 2
            reasons.append("repeated_confusion")
        elif context.repeated_confusion_count == 1:
            score += 1
            reasons.append("learner_confusion")

        premium_requested = score >= self.policy.premium_threshold
        if (
            context.question_difficulty == 5
            and context.mode
            in {
                "diagnose_misconception",
                "alternative_explanation",
                "analogous_example",
                "solution_explanation",
            }
        ):
            premium_requested = True
            reasons.append("level_5_complex_mode")

        target = self.policy.economy
        if premium_requested and self.policy.premium is None:
            reasons.append("premium_not_configured")
        elif (
            premium_requested
            and context.premium_turns_this_session
            >= self.policy.max_premium_turns_per_session
        ):
            reasons.append("premium_session_cap")
        elif premium_requested:
            target = self.policy.premium or self.policy.economy
            reasons.append("premium_threshold_reached")
        else:
            reasons.append("economy_sufficient")

        return TutorRouteDecision(
            policy_version=self.policy.version,
            tier=target.tier,
            provider_name=target.provider_name,
            model_name=target.model_name,
            mode=context.mode,
            question_difficulty=context.question_difficulty,
            score=score,
            reason_codes=tuple(dict.fromkeys(reasons)),
            max_output_tokens=target.max_output_tokens,
            input_cost_per_million_micros_sgd=(
                target.input_cost_per_million_micros_sgd
            ),
            output_cost_per_million_micros_sgd=(
                target.output_cost_per_million_micros_sgd
            ),
        )


def _message_text(message: dict) -> str:
    content = message.get("content", {})
    blocks = content.get("blocks", []) if isinstance(content, dict) else []
    return " ".join(
        str(block.get("content", ""))
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "text"
    )


def _has_confusion_signal(message: str) -> bool:
    normalized = message.casefold()
    return any(phrase in normalized for phrase in _CONFUSION_PHRASES)


def _token_cost(tokens: int, per_million_micros_sgd: int) -> int:
    if tokens == 0 or per_million_micros_sgd == 0:
        return 0
    return (tokens * per_million_micros_sgd + 999_999) // 1_000_000
