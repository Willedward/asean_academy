from __future__ import annotations

import asyncio
from pathlib import Path

from learning_api.tutor_evaluation import (
    load_evaluation_suite,
    run_evaluation,
    write_evaluation_report,
)
from learning_api.tutor_provider import SyntheticTutorProvider

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SUITE_PATH = (
    REPOSITORY_ROOT
    / "backend_resources"
    / "tutor_evaluations"
    / "g3_math"
    / "v1"
    / "synthetic_foundation.json"
)


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
