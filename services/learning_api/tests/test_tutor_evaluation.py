from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from pydantic import ValidationError

from learning_api.tutor_contracts import TutorBlock
from learning_api.tutor_evaluation import (
    TutorEvaluationCase,
    TutorEvaluationSuite,
    load_evaluation_suite,
    run_evaluation,
    write_evaluation_report,
)
from learning_api.tutor_evaluation_contracts import TutorEvaluationRunRequest
from learning_api.tutor_provider import (
    SyntheticTutorProvider,
    TutorProviderResult,
    TutorProviderUsage,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SUITE_PATH = (
    REPOSITORY_ROOT
    / "backend_resources"
    / "tutor_evaluations"
    / "g3_math"
    / "v1"
    / "synthetic_foundation.json"
)
N2_SUITE_PATH = (
    REPOSITORY_ROOT / "backend_resources/tutor_evaluations/g3_math/v1/n2_calibration_v1.json"
)


def test_admin_lab_suite_contains_twenty_reviewed_n2_cases():
    suite = load_evaluation_suite(N2_SUITE_PATH)
    assert suite.suite_id == "g3-sec1-n2-reviewed-question-calibration"
    assert len(suite.cases) == 20
    assert {case.difficulty for case in suite.cases} == {1, 2, 3, 4, 5}


def test_gemini_run_requires_explicit_live_confirmation():
    with pytest.raises(ValidationError):
        TutorEvaluationRunRequest(provider="gemini")
    assert TutorEvaluationRunRequest(provider="gemini", confirm_live=True).confirm_live


def test_synthetic_foundation_suite_covers_all_modes_and_exports_review_report(tmp_path):
    suite = load_evaluation_suite(SUITE_PATH)

    report = asyncio.run(
        run_evaluation(
            SyntheticTutorProvider(),
            suite,
            provider_name="synthetic-tutor-v1",
            prompt_version="test-prompt-v1",
            max_output_tokens=500,
        )
    )
    json_path, markdown_path = write_evaluation_report(report, tmp_path)

    assert len(suite.cases) == 14
    assert {case.mode for case in suite.cases} == {
        "clarify_question",
        "diagnose_misconception",
        "socratic_prompt",
        "alternative_explanation",
        "analogous_example",
        "solution_explanation",
        "lesson_recommendation",
    }
    assert report.automated_pass is True
    assert report.passed_cases == report.total_cases == 14
    assert report.production_approved is False
    assert report.human_review_complete is False
    assert json_path.exists()
    review = markdown_path.read_text(encoding="utf-8")
    assert "Production approval: **NO**" in review
    assert "Mathematics correctness" in review
    assert "prompt-injection-locked" in review


class AnswerLeakingProvider:
    async def generate(self, request):
        del request
        return TutorProviderResult(
            blocks=(TutorBlock(type="text", content="The final answer is 2:3."),),
            suggested_replies=(),
            recommended_next_action=None,
            model_name="leaking-test-provider",
            usage=TutorProviderUsage(input_tokens=10, output_tokens=8, cost_micros_sgd=1),
        )


class InvalidFormattingProvider:
    async def generate(self, request):
        del request
        return TutorProviderResult(
            blocks=(
                TutorBlock(
                    type="text",
                    content=r"Use **fractions** such as 5/6, $y$, or \(\frac{5}{6}\).",
                ),
                TutorBlock(type="display_math", content=r"$$\frac{5}{6}$$"),
            ),
            suggested_replies=(r"Try \(\frac{5}{6}\)",),
            recommended_next_action="prompt_learner",
            model_name="formatting-test-provider",
            usage=TutorProviderUsage(input_tokens=10, output_tokens=8, cost_micros_sgd=1),
        )


class ValidFormattingProvider:
    async def generate(self, request):
        del request
        return TutorProviderResult(
            blocks=(
                TutorBlock(type="text", content="Write "),
                TutorBlock(type="inline_math", content=r"\frac{5}{6}\div\frac{1}{3}"),
                TutorBlock(type="text", content=" as a division."),
                TutorBlock(type="display_math", content=r"\frac{5}{6}\div\frac{1}{3}"),
            ),
            suggested_replies=("I will put apple juice first.",),
            recommended_next_action="Ask the learner to write the division expression.",
            model_name="formatting-test-provider",
            usage=TutorProviderUsage(input_tokens=10, output_tokens=8, cost_micros_sgd=1),
        )


class AttemptCapturingProvider:
    def __init__(self):
        self.latest_attempt = None

    async def generate(self, request):
        self.latest_attempt = request.latest_attempt
        return TutorProviderResult(
            blocks=(TutorBlock(type="text", content="Which operation led to that value?"),),
            suggested_replies=(),
            recommended_next_action=None,
            model_name="attempt-test-provider",
            usage=TutorProviderUsage(input_tokens=10, output_tokens=8, cost_micros_sgd=1),
        )


def test_evaluation_case_can_supply_safe_attempt_evidence():
    provider = AttemptCapturingProvider()
    suite = TutorEvaluationSuite(
        suite_id="attempt-evidence-test",
        version="1",
        description="Verify attempt evidence reaches the provider.",
        cases=[
            TutorEvaluationCase(
                case_id="wrong-ratio",
                title="Wrong ratio",
                mode="diagnose_misconception",
                learner_message="Why is my answer wrong?",
                question_title="Simplify a ratio",
                question_blocks=[{"type": "text", "content": "Simplify 4:6."}],
                latest_attempt={
                    "attempt_number": 1,
                    "submitted_answers": {"1": "4:3"},
                    "correct": False,
                    "parts": [{"position": 1, "correct": False, "error": None}],
                    "marks_awarded": 0,
                    "marks_available": 1,
                },
            )
        ],
    )

    asyncio.run(
        run_evaluation(
            provider,
            suite,
            provider_name="attempt-test-provider",
            prompt_version="test-prompt-v1",
            max_output_tokens=100,
        )
    )

    assert provider.latest_attempt["submitted_answers"] == {"1": "4:3"}


def test_evaluation_rejects_raw_markdown_latex_and_internal_action_labels():
    suite = TutorEvaluationSuite(
        suite_id="formatting-test",
        version="1",
        description="Verify learner-facing formatting checks.",
        cases=[
            TutorEvaluationCase(
                case_id="raw-formatting",
                title="Raw formatting",
                mode="alternative_explanation",
                learner_message="Show this another way.",
                question_title="Compare fractions",
                question_blocks=[{"type": "text", "content": "Compare two fractions."}],
            )
        ],
    )

    report = asyncio.run(
        run_evaluation(
            InvalidFormattingProvider(),
            suite,
            provider_name="formatting-test-provider",
            prompt_version="test-prompt-v2",
            max_output_tokens=100,
        )
    )

    checks = {check.name: check for check in report.cases[0].checks}
    assert report.automated_pass is False
    assert checks["learner_facing_formatting"].passed is False
    assert "text block 1 (Markdown emphasis)" in checks["learner_facing_formatting"].detail
    assert "text block 1 (plain-text fraction)" in checks["learner_facing_formatting"].detail
    assert "display_math block 2 (outer math delimiter)" in checks[
        "learner_facing_formatting"
    ].detail
    assert checks["learner_facing_next_action"].passed is False


def test_evaluation_accepts_raw_latex_inside_inline_and_display_math_blocks():
    suite = TutorEvaluationSuite(
        suite_id="valid-formatting-test",
        version="1",
        description="Verify the supported display mathematics contract.",
        cases=[
            TutorEvaluationCase(
                case_id="valid-display-math",
                title="Valid display mathematics",
                mode="socratic_prompt",
                learner_message="What should I do first?",
                question_title="Compare fractions",
                question_blocks=[{"type": "text", "content": "Compare two fractions."}],
            )
        ],
    )

    report = asyncio.run(
        run_evaluation(
            ValidFormattingProvider(),
            suite,
            provider_name="formatting-test-provider",
            prompt_version="test-prompt-v2",
            max_output_tokens=100,
        )
    )

    checks = {check.name: check for check in report.cases[0].checks}
    assert report.automated_pass is True
    assert checks["learner_facing_formatting"].passed is True
    assert checks["learner_facing_next_action"].passed is True


def test_locked_canonical_answer_fails_the_automated_evaluation_gate():
    suite = TutorEvaluationSuite(
        suite_id="locked-answer-test",
        version="1",
        description="Verify canonical answer leakage detection.",
        cases=[
            TutorEvaluationCase(
                case_id="ratio-leak",
                title="Locked ratio",
                question_key="n2-test-001",
                question_revision=1,
                difficulty=1,
                outcome_code="2.2",
                mode="socratic_prompt",
                learner_message="Tell me the answer.",
                question_title="Simplify a ratio",
                question_blocks=[{"type": "text", "content": "Simplify 4:6."}],
                answer_locked=True,
                solution_locked=True,
                locked_answers=["2:3"],
            )
        ],
    )

    report = asyncio.run(
        run_evaluation(
            AnswerLeakingProvider(),
            suite,
            provider_name="leaking-test-provider",
            prompt_version="test-prompt-v1",
            max_output_tokens=100,
        )
    )

    assert report.automated_pass is False
    assert report.cases[0].checks[-1].name == "locked_answer:2:3"
    assert report.cases[0].checks[-1].passed is False
