from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

import httpx

from learning_api.config import Settings
from learning_api.dependencies import admin_learner
from learning_api.identity import AuthenticatedLearner
from learning_api.main import create_app
from learning_api.tutor_contracts import AnswerLockState, TutorBlock
from learning_api.tutor_provider import TutorProviderResult, TutorProviderUsage
from learning_api.tutor_repository import (
    InMemoryTutorRepository,
    TutorGrounding,
    _safe_attempt_evidence,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def grounding(
    *, answer_locked: bool = True, incorrect_attempts: int = 0, difficulty: int = 1
) -> TutorGrounding:
    return TutorGrounding(
        session_id=str(uuid4()),
        question_title="A safe synthetic ratio question",
        question_difficulty=difficulty,
        question_blocks=({"kind": "stem", "blocks": [{"type": "text", "content": "Find the ratio."}]},),
        unlocked_hint_blocks=(),
        lesson_sections=({"section_key": "ratio", "content": {"blocks": []}},),
        unlocked_solution_blocks=(),
        latest_attempt=(
            {
                "attempt_number": 1,
                "submitted_answers": {"1": "2:6"},
                "correct": False,
                "parts": [
                    {
                        "position": 1,
                        "correct": False,
                        "error": None,
                        "marks_awarded": 0,
                        "marks_available": 1,
                    }
                ],
                "marks_awarded": 0,
                "marks_available": 1,
            }
            if incorrect_attempts
            else None
        ),
        recent_messages=(),
        answer_lock_state=AnswerLockState(
            answer_locked=answer_locked,
            solution_locked=answer_locked,
        ),
        incorrect_attempts=incorrect_attempts,
        premium_turns_this_session=0,
        leakage_answers=("42",),
        grounding_revision_ids=(str(uuid4()), str(uuid4())),
    )


def application(
    repo: InMemoryTutorRepository,
    *,
    enabled: bool = True,
    daily_messages: int = 10,
):
    app = create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            development_learner_id="development-learner",
            rate_limits_enabled=False,
            tutor_enabled=enabled,
            tutor_provider="synthetic",
            tutor_daily_message_limit=daily_messages,
        )
    )
    app.state.tutor_repository = repo
    return app


def request(app, method: str, path: str, **kwargs):
    async def send():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def create_session(app):
    return request(
        app,
        "POST",
        "/api/v1/tutor/sessions",
        json={
            "practice_session_id": str(uuid4()),
            "question_key": "n2-l1-001",
            "question_revision": 1,
        },
    )


def test_tutor_is_disabled_by_default_boundary():
    app = application(InMemoryTutorRepository(grounding()), enabled=False)

    response = create_session(app)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "tutor_disabled"
    assert response.json()["error"]["request_id"]


def test_synthetic_tutor_creates_session_and_reconciles_quota():
    repo = InMemoryTutorRepository(grounding())
    app = application(repo)
    created = create_session(app)
    session_id = created.json()["session_id"]

    response = request(
        app,
        "POST",
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={"message": "I do not know how to begin."},
    )

    assert created.status_code == 201
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["message"]["mode"] == "socratic_prompt"
    assert payload["message"]["safety_outcome"] == "accepted"
    assert payload["quota"]["daily_messages_remaining"] == 9
    assert repo.actual_requests == 1
    encoded = response.text.casefold()
    assert "provider api key" not in encoded
    assert "canonical_answer" not in encoded


class LeakingProvider:
    async def generate(self, request):
        del request
        return TutorProviderResult(
            blocks=(TutorBlock(type="text", content="The final answer is 42."),),
            suggested_replies=(),
            recommended_next_action=None,
            model_name="unsafe-test-provider",
            usage=TutorProviderUsage(input_tokens=50, output_tokens=8, cost_micros_sgd=100),
        )


class InlineMathLeakingProvider:
    async def generate(self, request):
        del request
        return TutorProviderResult(
            blocks=(TutorBlock(type="inline_math", content="42"),),
            suggested_replies=(),
            recommended_next_action=None,
            model_name="unsafe-test-provider",
            usage=TutorProviderUsage(input_tokens=50, output_tokens=8, cost_micros_sgd=100),
        )


class CapturingProvider:
    def __init__(self):
        self.request = None

    async def generate(self, request):
        self.request = request
        return TutorProviderResult(
            blocks=(TutorBlock(type="text", content="Which step produced 2:6?"),),
            suggested_replies=(),
            recommended_next_action="Check both ratio terms.",
            model_name="capturing-test-provider",
            usage=TutorProviderUsage(input_tokens=50, output_tokens=8, cost_micros_sgd=100),
        )


def test_incorrect_attempt_is_grounded_for_misconception_chat():
    repo = InMemoryTutorRepository(grounding(incorrect_attempts=1))
    app = application(repo)
    provider = CapturingProvider()
    app.state.tutor_provider = provider
    session_id = create_session(app).json()["session_id"]

    response = request(
        app,
        "POST",
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={"message": "Why is my answer wrong?"},
    )

    assert response.status_code == 200
    assert provider.request.mode == "diagnose_misconception"
    assert provider.request.latest_attempt["submitted_answers"] == {"1": "2:6"}
    assert provider.request.latest_attempt["correct"] is False


def test_attempt_grounding_excludes_canonical_answer_fields():
    evidence = _safe_attempt_evidence(
        {
            "attempt_number": 1,
            "answers": {"1": "2:6"},
            "is_correct": False,
            "marks_awarded": 0,
            "result": {
                "parts": [
                    {
                        "position": 1,
                        "correct": False,
                        "error": None,
                        "marks_awarded": 0,
                        "marks_available": 1,
                        "canonical_answer": "2:3",
                    }
                ],
                "marks_available": 1,
                "canonical_answer": "2:3",
            },
        }
    )

    assert evidence["submitted_answers"] == {"1": "2:6"}
    assert "canonical_answer" not in str(evidence)


def test_locked_answer_is_replaced_when_provider_output_leaks():
    repo = InMemoryTutorRepository(grounding(answer_locked=True))
    app = application(repo)
    app.state.tutor_provider = LeakingProvider()
    session_id = create_session(app).json()["session_id"]

    response = request(
        app,
        "POST",
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={"message": "Please tell me the answer."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"]["safety_outcome"] == "answer_leakage_blocked"
    assert "42" not in payload["message"]["blocks"][0]["content"]
    assert "cannot reveal" in payload["message"]["blocks"][0]["content"]


def test_locked_answer_is_replaced_when_inline_math_output_leaks():
    repo = InMemoryTutorRepository(grounding(answer_locked=True))
    app = application(repo)
    app.state.tutor_provider = InlineMathLeakingProvider()
    session_id = create_session(app).json()["session_id"]

    response = request(
        app,
        "POST",
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={"message": "Please tell me the answer."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"]["safety_outcome"] == "answer_leakage_blocked"
    assert "42" not in payload["message"]["blocks"][0]["content"]


def test_daily_message_hard_cap_does_not_disable_other_learning_features():
    repo = InMemoryTutorRepository(grounding())
    app = application(repo, daily_messages=1)
    session_id = create_session(app).json()["session_id"]
    first = request(
        app,
        "POST",
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={"message": "Give me one hint."},
    )
    second = request(
        app,
        "POST",
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={"message": "Give me another hint."},
    )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "tutor_quota_exceeded"
    assert "resets_at" in second.json()["error"]["details"]


def test_closed_session_rejects_new_messages():
    repo = InMemoryTutorRepository(grounding())
    app = application(repo)
    session_id = create_session(app).json()["session_id"]

    closed = request(app, "POST", f"/api/v1/tutor/sessions/{session_id}/close")
    message = request(
        app,
        "POST",
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={"message": "Can we continue?"},
    )

    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    assert message.status_code == 409
    assert message.json()["error"]["code"] == "tutor_session_closed"


def test_academic_admin_can_read_monthly_tutor_usage_while_tutor_is_disabled():
    repo = InMemoryTutorRepository(grounding())
    app = application(repo, enabled=False)
    app.dependency_overrides[admin_learner] = lambda: AuthenticatedLearner(
        learner_id=str(uuid4()),
        role="academic_admin",
        source="test",
    )

    response = request(app, "GET", "/api/v1/admin/tutor-usage?month=2026-10")

    assert response.status_code == 200
    assert response.json() == {
        "usage_month": "2026-10",
        "learners": 0,
        "actual_requests": 0,
        "failed_requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "actual_cost_micros_sgd": 0,
        "reserved_cost_micros_sgd": 0,
        "active_reservations": 0,
    }
