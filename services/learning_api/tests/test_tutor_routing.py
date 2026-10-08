import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from learning_api.config import Settings
from learning_api.dependencies import tutor_service
from learning_api.identity import AuthenticatedLearner
from learning_api.tutor_contracts import AnswerLockState, TutorBlock
from learning_api.tutor_provider import TutorProviderResult, TutorProviderUsage
from learning_api.tutor_repository import (
    InMemoryTutorRepository,
    TutorError,
    TutorGrounding,
    TutorLimits,
    UsageActual,
    UsageReservationQuote,
    decode_tutor_route_cursor,
    encode_tutor_route_cursor,
)
from learning_api.tutor_routing import (
    TutorModelRouter,
    TutorModelTarget,
    TutorRoutePlan,
    TutorRoutingContext,
    TutorRoutingPolicy,
    configured_routing_mode,
    repeated_confusion_count,
    resolve_routing_mode,
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


def test_shadow_plan_recommends_premium_but_executes_economy():
    plan = router().plan(
        context(question_difficulty=5, mode="solution_explanation"),
        "shadow",
    )

    assert plan.routing_mode == "shadow"
    assert plan.recommendation.tier == "premium"
    assert plan.recommendation.provider_name == "openai"
    assert plan.execution.tier == "economy"
    assert plan.execution.provider_name == "gemini"


def test_routing_cohort_is_resolved_from_the_database_role():
    assert (
        configured_routing_mode(live_enabled=False, shadow_enabled=True) == "shadow"
    )
    assert resolve_routing_mode("shadow", "admins", "academic_admin") == "shadow"
    assert resolve_routing_mode("shadow", "admins", "content_admin") == "off"
    assert resolve_routing_mode("shadow", "admins", "student") == "off"
    assert resolve_routing_mode("shadow", "admins", None) == "off"
    assert resolve_routing_mode("shadow", "all", "student") == "shadow"
    assert resolve_routing_mode("shadow", "off", "academic_admin") == "off"
    assert resolve_routing_mode("off", "all", "academic_admin") == "off"


def test_tutor_service_dependency_uses_the_database_role_for_admin_cohort():
    settings = Settings(
        environment="test",
        cors_origins=("http://localhost:3000",),
        log_level="INFO",
        rate_limits_enabled=False,
        tutor_enabled=True,
        tutor_provider="synthetic",
        tutor_hybrid_routing_shadow_enabled=True,
        tutor_routing_cohort="admins",
        tutor_premium_provider="openai",
    )

    def service_for(database_role: str) -> TutorService:
        repository = InMemoryTutorRepository(
            TutorGrounding(
                session_id=str(uuid4()),
                question_title="Role gate",
                question_difficulty=1,
                question_blocks=(),
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
                leakage_answers=(),
                grounding_revision_ids=(),
            )
        )
        role_repository = SimpleNamespace(
            role_for=lambda learner_id: database_role
        )
        state = SimpleNamespace(
            settings=settings,
            tutor_repository=repository,
            tutor_provider=CapturingProvider(),
            tutor_premium_provider=None,
            beta_operations_repository=role_repository,
        )
        request = SimpleNamespace(app=SimpleNamespace(state=state))
        learner = AuthenticatedLearner(
            learner_id=str(uuid4()),
            role="student",
            source="test",
        )
        return tutor_service(request, learner)

    assert service_for("academic_admin").routing_mode == "shadow"
    assert service_for("content_admin").routing_mode == "off"
    assert service_for("student").routing_mode == "off"


def test_tutor_route_cursor_is_opaque_stable_and_rejects_invalid_input():
    created_at = datetime(2026, 10, 9, 12, 30, tzinfo=UTC)
    decision_id = str(uuid4())

    cursor = encode_tutor_route_cursor(created_at, decision_id)
    decoded = decode_tutor_route_cursor(cursor)

    assert decoded.created_at == created_at
    assert decoded.decision_id == decision_id
    assert decision_id not in cursor
    with pytest.raises(TutorError, match="cursor is invalid") as caught:
        decode_tutor_route_cursor("not-a-cursor")
    assert caught.value.code == "invalid_tutor_routing_cursor"
    assert caught.value.status == 422


def test_routing_evidence_pages_are_stable_filtered_and_content_free():
    session_id = str(uuid4())
    repository = InMemoryTutorRepository(
        TutorGrounding(
            session_id=session_id,
            question_title="Evidence pagination",
            question_difficulty=1,
            question_blocks=(),
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
            leakage_answers=(),
            grounding_revision_ids=(),
        )
    )
    repository.create_session(
        "learner-1",
        practice_session_id=str(uuid4()),
        question_key="n2-l1-001",
        question_revision=1,
        model_policy_version="test-policy-v1",
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
    decision = router().decide(context())
    plan = TutorRoutePlan("off", decision, decision)
    reservations = []
    for index in range(2):
        reservation = repository.reserve(
            "learner-1",
            session_id,
            limits,
            request_id=f"evidence-{index}",
            quote=UsageReservationQuote(5_000, 500, 3_520),
            routing=plan,
        )
        repository.reconcile(
            reservation,
            UsageActual(input_tokens=100, output_tokens=50, cost_micros_sgd=199),
            limits,
            request_id=f"evidence-{index}",
        )
        repository.append_message(
            session_id,
            role="assistant",
            mode="socratic_prompt",
            content={"blocks": [{"type": "text", "content": "Private response"}]},
            provider_name="gemini",
            model_name="gemini-flash",
            model_tier="economy",
            route_decision_id=reservation.route_decision_id,
            latency_ms=125,
        )
        reservations.append(reservation)
    month = reservations[0].usage_month

    first = repository.admin_route_decisions(
        month,
        limit=1,
        routing_mode="off",
        recommended_tier="economy",
        executed_tier="economy",
        reservation_status="reconciled",
    )
    second = repository.admin_route_decisions(
        month,
        limit=1,
        cursor=first["next_cursor"],
        reason_code="economy_sufficient",
    )

    assert len(first["items"]) == 1
    assert first["next_cursor"]
    assert len(second["items"]) == 1
    assert second["next_cursor"] is None
    assert first["items"][0]["decision_id"] != second["items"][0]["decision_id"]
    assert first["items"][0]["projected_recommended_cost_micros_sgd"] == 199
    assert first["items"][0]["latency_ms"] == 125
    assert "learner_id" not in first["items"][0]
    assert "blocks" not in first["items"][0]


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


def test_shadow_service_never_calls_or_reserves_the_premium_provider():
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
        routing_mode="shadow",
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

    asyncio.run(
        service.send_message(
            session_id,
            "I still don't understand. Explain this a different way.",
            request_id="shadow-request-1",
        )
    )

    assert economy_provider.request.max_output_tokens == 500
    assert premium_provider.request is None
    assert repository.last_route_plan.routing_mode == "shadow"
    assert repository.last_route_plan.recommendation.tier == "premium"
    assert repository.last_routing.tier == "economy"
    assert repository.last_quote.max_cost_micros_sgd == 3_520
    usage = repository.admin_usage(repository.reservations[next(iter(repository.reservations))].usage_month)
    assert usage["shadow_route_decisions"] == 1
    assert usage["shadow_premium_executions"] == 0
    assert usage["recommended_premium_routes"] == 1
    assert usage["executed_premium_routes"] == 0


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
                routing=TutorRoutePlan("live", routing, routing),
            )
