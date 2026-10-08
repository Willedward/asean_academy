import asyncio
from uuid import uuid4

import pytest

from learning_api.tutor_contracts import AnswerLockState, TutorBlock
from learning_api.tutor_provider import TutorProviderResult, TutorProviderUsage
from learning_api.tutor_repository import (
    InMemoryTutorRepository,
    TutorError,
    TutorGrounding,
    TutorLimits,
    UsageReservationQuote,
)
from learning_api.tutor_routing import (
    TutorModelRouter,
    TutorModelTarget,
    TutorRoutingContext,
    TutorRoutingPolicy,
    repeated_confusion_count,
)
from learning_api.tutor_service import TutorService


def router(*, max_premium_turns: int = 3) -> TutorModelRouter:
    return TutorModelRouter(
        TutorRoutingPolicy(
            version="test-policy-v1",
            economy=TutorModelTarget(
                tier="economy",
                provider_name="gemini",
                model_name="gemini-flash",
                max_output_tokens=500,
                input_cost_per_million_micros_sgd=384_000,
                output_cost_per_million_micros_sgd=3_200_000,
            ),
            premium=TutorModelTarget(
                tier="premium",
                provider_name="openai",
                model_name="gpt-4o-2024-11-20",
                max_output_tokens=700,
                input_cost_per_million_micros_sgd=3_200_000,
                output_cost_per_million_micros_sgd=12_800_000,
            ),
            premium_threshold=5,
            max_premium_turns_per_session=max_premium_turns,
        )
    )


def context(**overrides) -> TutorRoutingContext:
    values = {
        "question_difficulty": 1,
        "mode": "socratic_prompt",
        "incorrect_attempts": 0,
        "repeated_confusion_count": 0,
        "premium_turns_this_session": 0,
    }
    values.update(overrides)
    return TutorRoutingContext(**values)


def test_easy_first_hint_stays_on_economy_model():
    decision = router().decide(context())

    assert decision.tier == "economy"
    assert decision.provider_name == "gemini"
    assert decision.score == 0
    assert "economy_sufficient" in decision.reason_codes


def test_difficult_solution_explanation_uses_premium_model():
    decision = router().decide(
        context(question_difficulty=5, mode="solution_explanation")
    )

    assert decision.tier == "premium"
    assert decision.provider_name == "openai"
    assert "level_5_complex_mode" in decision.reason_codes
    assert "premium_threshold_reached" in decision.reason_codes


def test_repeated_confusion_and_attempts_can_escalate_a_mid_level_question():
    decision = router().decide(
        context(
            question_difficulty=2,
            mode="alternative_explanation",
            incorrect_attempts=2,
            repeated_confusion_count=1,
        )
    )

    assert decision.score == 5
    assert decision.tier == "premium"
    assert decision.reason_codes == (
        "difficulty_2",
        "mode_alternative_explanation",
        "multiple_incorrect_attempts",
        "learner_confusion",
        "premium_threshold_reached",
    )


def test_premium_session_cap_routes_back_to_economy():
    decision = router(max_premium_turns=1).decide(
        context(
            question_difficulty=5,
            mode="alternative_explanation",
            premium_turns_this_session=1,
        )
    )

    assert decision.tier == "economy"
    assert "premium_session_cap" in decision.reason_codes


def test_cost_reservation_uses_selected_model_price_and_token_ceiling():
    decision = router().decide(
        context(question_difficulty=5, mode="solution_explanation")
    )

    assert decision.maximum_cost_micros_sgd(max_input_tokens=2_500) == 16_960


def test_confusion_signals_are_derived_without_an_llm_call():
    recent_messages = (
        {
            "role": "student",
            "content": {
                "blocks": [
                    {"type": "text", "content": "I still don't understand this."}
                ]
            },
        },
        {"role": "assistant", "model_tier": "premium", "content": {"blocks": []}},
    )

    assert repeated_confusion_count("Can you explain differently?", recent_messages) == 2


class CapturingProvider:
    def __init__(self):
        self.request = None

    async def generate(self, request):
        self.request = request
        return TutorProviderResult(
            blocks=(TutorBlock(type="text", content="Try representing it another way."),),
            suggested_replies=(),
            recommended_next_action="Draw one matching representation.",
            model_name="capturing-provider",
            usage=TutorProviderUsage(
                input_tokens=50,
                output_tokens=8,
                cost_micros_sgd=100,
            ),
        )


def test_service_calls_premium_provider_and_reserves_its_cost_boundary():
    session_id = str(uuid4())
    repository = InMemoryTutorRepository(
        TutorGrounding(
            session_id=session_id,
            question_title="A difficult ratio question",
            question_difficulty=5,
            question_blocks=({"type": "text", "content": "Compare the ratios."},),
            unlocked_hint_blocks=(),
            lesson_sections=(),
            unlocked_solution_blocks=(),
            latest_attempt=None,
            recent_messages=(),
            answer_lock_state=AnswerLockState(
                answer_locked=True,
                solution_locked=True,
            ),
            incorrect_attempts=0,
            premium_turns_this_session=0,
            leakage_answers=("42",),
            grounding_revision_ids=(str(uuid4()),),
        )
    )
    economy_provider = CapturingProvider()
    premium_provider = CapturingProvider()
    service = TutorService(
        repository,
        economy_provider,
        router(),
        "learner-1",
        premium_provider=premium_provider,
        limits=TutorLimits(
            daily_messages=10,
            daily_tokens=20_000,
            monthly_cost_micros_sgd=7_000_000,
            academy_monthly_cost_micros_sgd=7_000_000_000,
            max_input_tokens=5_000,
            max_output_tokens=1_000,
            max_turn_cost_micros_sgd=250_000,
        ),
        model_policy_version="test-policy-v1",
        prompt_version="test-prompt-v1",
    )
    service.create_session(
        practice_session_id=str(uuid4()),
        question_key="n2-l5-001",
        question_revision=1,
    )

    response = asyncio.run(
        service.send_message(
            session_id,
            "I still don't understand. Explain this a different way.",
            request_id="request-1",
        )
    )

    assert economy_provider.request is None
    assert premium_provider.request.mode == "alternative_explanation"
    assert premium_provider.request.max_output_tokens == 700
    assert repository.last_routing.tier == "premium"
    assert repository.last_routing.provider_name == "openai"
    assert repository.last_quote.max_cost_micros_sgd == 24_960
    assert repository.messages[session_id][-1]["model_tier"] == "premium"
    assert "model_tier" not in response["message"]


def test_repository_rejects_a_quote_that_understates_the_route_cost():
    session_id = str(uuid4())
    repository = InMemoryTutorRepository(
        TutorGrounding(
            session_id=session_id,
            question_title="A ratio question",
            question_difficulty=5,
            question_blocks=({"type": "text", "content": "Compare the ratios."},),
            unlocked_hint_blocks=(),
            lesson_sections=(),
            unlocked_solution_blocks=(),
            latest_attempt=None,
            recent_messages=(),
            answer_lock_state=AnswerLockState(
                answer_locked=True,
                solution_locked=True,
            ),
            incorrect_attempts=0,
            premium_turns_this_session=0,
            leakage_answers=("42",),
            grounding_revision_ids=(str(uuid4()),),
        )
    )
    repository.create_session(
        "learner-1",
        practice_session_id=str(uuid4()),
        question_key="n2-l5-001",
        question_revision=1,
        model_policy_version="test-policy-v1",
    )
    routing = router().decide(
        context(question_difficulty=5, mode="solution_explanation")
    )
    limits = TutorLimits(
        daily_messages=10,
        daily_tokens=20_000,
        monthly_cost_micros_sgd=7_000_000,
        academy_monthly_cost_micros_sgd=7_000_000_000,
        max_input_tokens=5_000,
        max_output_tokens=1_000,
        max_turn_cost_micros_sgd=250_000,
    )

    with pytest.raises(TutorError, match="boundaries do not match"):
        repository.reserve(
            "learner-1",
            session_id,
            limits,
            request_id="request-1",
            quote=UsageReservationQuote(
                max_input_tokens=5_000,
                max_output_tokens=700,
                max_cost_micros_sgd=1,
            ),
            routing=routing,
        )
