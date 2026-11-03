"""Shared fixtures for the learning API tests."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest
from question_bank.models import NumericResponse, Question

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def wrong_answer(response) -> str:
    """A well-formed answer that the checker reads and marks incorrect.

    A malformed answer such as "not an answer" is a format error, which practice does
    not count as an attempt, so tests that need an incorrect attempt must use this.
    """

    if isinstance(response, NumericResponse):
        return str(Fraction(response.canonical_answer) + 1001)
    mode = response.comparison_mode
    if mode == "prime_factorisation":
        return "3" if response.canonical_expression.strip() == "2" else "2"
    if mode == "ordered_numeric_list":
        values = json.loads(response.canonical_expression)
        return ", ".join(str(value) for value in reversed(values))
    if mode == "exact_relation":
        operator = response.checker_config["allowed_operators"][0]
        return f"1001 {operator} 1002"
    if mode == "exact_ratio":
        return ":".join(["97", "89", "83"][: response.checker_config["terms"]])
    raise AssertionError(f"No well-formed wrong answer is defined for {mode}")


@pytest.fixture(scope="session")
def authored_questions() -> dict[str, Question]:
    root = REPOSITORY_ROOT / "backend_resources/question_bank/g3_math"
    questions = (
        Question.model_validate_json(path.read_text()) for path in root.glob("**/questions/*.json")
    )
    return {question.stable_key: question for question in questions}


@pytest.fixture(scope="session")
def wrong_answers(authored_questions):
    """Build a complete, well-formed but incorrect answer set for a question key."""

    def build(question_key: str) -> dict[str, str]:
        return {
            str(part.position): wrong_answer(part.response)
            for part in authored_questions[question_key].parts
        }

    return build
