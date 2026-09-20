import json
import random

import pytest

from question_bank.models import AlgebraicResponse, NumericResponse
from question_bank.practice import PracticeEngine, PracticeError
from question_bank.validation import validate_bank


@pytest.fixture
def engine(tmp_path, bank_root):
    questions = validate_bank(bank_root).questions
    return PracticeEngine(
        tmp_path / "practice.sqlite3",
        questions,
        allow_drafts=True,
        rng=random.Random(7),
    )


def canonical_answers(question):
    answers = {}
    for part in question.parts:
        if isinstance(part.response, NumericResponse):
            value = part.response.canonical_answer
        elif isinstance(part.response, AlgebraicResponse):
            value = part.response.canonical_expression
        answers[str(part.position)] = value
    return answers


def test_public_question_hides_answers_and_solution(engine):
    session = engine.create_session(question_count=1)
    current = engine.next_question(session["session_id"])
    encoded = json.dumps(current["question"])

    assert "canonical_answer" not in encoded
    assert "canonical_expression" not in encoded
    assert '"solution"' not in encoded
    assert current["question"]["revision"] == 1
    assert current["session"]["development_drafts"] is True


def test_correct_attempt_finishes_question_and_is_idempotent(engine):
    session = engine.create_session(question_count=1)
    current = engine.next_question(session["session_id"])
    question = engine.questions[current["question"]["stable_key"]]
    payload = {
        "session_id": session["session_id"],
        "stable_key": question.stable_key,
        "revision": question.revision,
        "answers": canonical_answers(question),
        "idempotency_key": "attempt-one",
    }

    first = engine.submit_attempt(**payload)
    replay = engine.submit_attempt(**payload)

    assert first == replay
    assert first["correct"] is True
    assert first["marks_awarded"] == question.total_marks
    assert engine.next_question(session["session_id"])["status"] == "completed"


def test_two_incorrect_attempts_unlock_give_up(engine):
    session = engine.create_session(question_count=1)
    current = engine.next_question(session["session_id"])
    question = current["question"]

    for number in (1, 2):
        result = engine.submit_attempt(
            session_id=session["session_id"],
            stable_key=question["stable_key"],
            revision=question["revision"],
            answers={str(part["position"]): "not-an-answer" for part in question["parts"]},
            idempotency_key=f"wrong-{number}",
        )

    assert result["solution_available"] is True
    revealed = engine.give_up(session["session_id"], question["stable_key"])
    assert revealed["solution"]["parts"][0]["canonical_answer"]
    assert engine.next_question(session["session_id"])["status"] == "completed"


def test_solution_is_locked_before_two_incorrect_attempts(engine):
    session = engine.create_session(question_count=1)
    current = engine.next_question(session["session_id"])
    with pytest.raises(PracticeError, match="two incorrect") as raised:
        engine.give_up(session["session_id"], current["question"]["stable_key"])
    assert raised.value.status == 403


def test_hints_are_revealed_in_order(engine):
    session = engine.create_session(question_count=1)
    current = engine.next_question(session["session_id"])
    key = current["question"]["stable_key"]

    with pytest.raises(PracticeError, match="hint 1"):
        engine.reveal_hint(session["session_id"], key, 2)
    first = engine.reveal_hint(session["session_id"], key, 1)
    second = engine.reveal_hint(session["session_id"], key, 2)

    assert first["stage"] == 1
    assert second["stage"] == 2


def test_queued_retry_is_selected_in_a_new_session(engine):
    first_session = engine.create_session(question_count=1)
    current = engine.next_question(first_session["session_id"])
    question = current["question"]
    engine.submit_attempt(
        session_id=first_session["session_id"],
        stable_key=question["stable_key"],
        revision=question["revision"],
        answers={str(part["position"]): "wrong" for part in question["parts"]},
        idempotency_key="queue-it",
    )

    second_session = engine.create_session(question_count=1)
    retry = engine.next_question(second_session["session_id"])

    assert retry["question"]["stable_key"] == question["stable_key"]
    assert retry["selection_reason"] == "required_retry"
