import json
import random
import sqlite3
from fractions import Fraction

import pytest

from question_bank import practice
from question_bank.models import AlgebraicResponse, NumericResponse, Question
from question_bank.practice import (
    MAX_UNCOUNTED_FORMAT_ERRORS,
    PracticeEngine,
    PracticeError,
    solution_for,
)
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


def wrong_answer(response):
    """A well-formed answer that the checker reads and marks incorrect."""

    if isinstance(response, NumericResponse):
        return str(Fraction(response.canonical_answer) + 1001)
    mode = response.comparison_mode
    if mode == "prime_factorisation":
        return "3" if response.canonical_expression.strip() == "2" else "2"
    if mode == "ordered_numeric_list":
        values = json.loads(response.canonical_expression)
        return ", ".join(str(value) for value in reversed(values))
    if mode == "exact_relation":
        return f"1001 {response.checker_config['allowed_operators'][0]} 1002"
    if mode == "exact_ratio":
        return ":".join(["97", "89", "83"][: response.checker_config["terms"]])
    raise AssertionError(f"No well-formed wrong answer is defined for {mode}")


def wrong_answers(engine, question_key):
    return {
        str(part.position): wrong_answer(part.response)
        for part in engine.questions[question_key].parts
    }


def readable_answers(engine, question_key):
    return {
        str(part["position"]): part["canonical_answer"]
        for part in solution_for(engine.questions[question_key])["parts"]
    }


def recorded_state(engine, session_id, question_key):
    with sqlite3.connect(engine.database) as connection:
        attempts = connection.execute(
            "select count(*) from attempts where session_id = ? and question_key = ?",
            (session_id, question_key),
        ).fetchone()[0]
        assignment = connection.execute(
            """
            select status, incorrect_attempts from session_questions
            where session_id = ? and question_key = ?
            """,
            (session_id, question_key),
        ).fetchone()
        progress = connection.execute(
            "select attempts_total, incorrect_total from question_progress where question_key = ?",
            (question_key,),
        ).fetchone()
    return attempts, tuple(assignment), progress


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
            answers=wrong_answers(engine, question["stable_key"]),
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
        answers=wrong_answers(engine, question["stable_key"]),
        idempotency_key="queue-it",
    )

    second_session = engine.create_session(question_count=1)
    retry = engine.next_question(second_session["session_id"])

    assert retry["question"]["stable_key"] == question["stable_key"]
    assert retry["selection_reason"] == "required_retry"


def test_configured_pool_is_ordered_and_creation_is_idempotent(engine):
    first = engine.create_session(
        question_count=2,
        ordered_question_keys=["n1-l1-01", "n1-l2-03"],
        context={
            "lesson_key": "n1-lesson-01",
            "mode": "guided_practice",
            "stages": {"n1-l1-01": "guided", "n1-l2-03": "independent"},
        },
        idempotency_key="lesson-start",
    )
    replay = engine.create_session(
        question_count=2,
        ordered_question_keys=["n1-l1-01", "n1-l2-03"],
        context={"lesson_key": "changed-but-replayed"},
        idempotency_key="lesson-start",
    )

    assert replay == first
    current = engine.next_question(first["session_id"])
    assert current["question"]["stable_key"] == "n1-l1-01"
    assert current["stage"] == "guided"
    assert current["session"]["lesson_key"] == "n1-lesson-01"


def test_session_can_select_level_four_and_five_questions(tmp_path, bank_root):
    source = validate_bank(bank_root).questions[0].model_dump(mode="json")
    questions = []
    for difficulty in (4, 5):
        payload = json.loads(json.dumps(source))
        payload.update(stable_key=f"n1-l{difficulty}-099", difficulty=difficulty)
        questions.append(Question.model_validate(payload))

    extended_engine = PracticeEngine(
        tmp_path / "extended-practice.sqlite3",
        questions,
        allow_drafts=True,
        rng=random.Random(7),
    )
    selected = set()
    for difficulty in (4, 5):
        session = extended_engine.create_session(question_count=1, difficulties=[difficulty])
        current = extended_engine.next_question(session["session_id"])
        selected.add(current["question"]["stable_key"])

    assert selected == {"n1-l4-099", "n1-l5-099"}


def test_session_rejects_difficulty_above_five(engine):
    with pytest.raises(PracticeError, match="levels 1 through 5"):
        engine.create_session(question_count=1, difficulties=[6])


def test_wrong_answer_helper_is_readable_and_incorrect(engine):
    from question_bank.checking import check_answer

    for question in engine.questions.values():
        for part in question.parts:
            result = check_answer(part.response, wrong_answer(part.response))
            assert result == {"correct": False, "error": None}, (question.stable_key, result)


def test_format_error_is_not_an_attempt(engine):
    session = engine.create_session(question_count=1)
    session_id = session["session_id"]
    question = engine.next_question(session_id)["question"]
    key = question["stable_key"]
    garbled = {str(part["position"]): "not an answer" for part in question["parts"]}

    for number in range(1, 4):
        result = engine.submit_attempt(
            session_id=session_id,
            stable_key=key,
            revision=question["revision"],
            answers=garbled,
            idempotency_key=f"garbled-{number}",
        )
        assert result["format_error"] is True
        assert result["correct"] is False
        assert result["attempt_number"] == 0
        assert result["question_finished"] is False
        assert result["solution_available"] is False
        assert all(part["error"] for part in result["parts"])

    assert recorded_state(engine, session_id, key) == (0, ("pending", 0), None)
    with pytest.raises(PracticeError, match="two incorrect"):
        engine.give_up(session_id, key)
    assert engine.next_question(session_id)["question"]["stable_key"] == key

    for number in (1, 2):
        counted = engine.submit_attempt(
            session_id=session_id,
            stable_key=key,
            revision=question["revision"],
            answers=wrong_answers(engine, key),
            idempotency_key=f"counted-{number}",
        )
        assert counted["format_error"] is False
        assert counted["attempt_number"] == number
    assert counted["solution_available"] is True
    assert recorded_state(engine, session_id, key) == (2, ("pending", 2), (2, 2))


def test_format_error_reveals_nothing_about_the_other_parts(engine):
    key = next(
        question.stable_key
        for question in engine.questions.values()
        if len(question.parts) > 1
    )
    session = engine.create_session(question_count=1, ordered_question_keys=[key])
    question = engine.next_question(session["session_id"])["question"]
    answers = readable_answers(engine, key)
    answers["2"] = "not an answer"

    result = engine.submit_attempt(
        session_id=session["session_id"],
        stable_key=key,
        revision=question["revision"],
        answers=answers,
        idempotency_key="probe",
    )

    assert result["format_error"] is True
    assert result["marks_awarded"] == 0
    assert [part["correct"] for part in result["parts"]] == [False] * len(question["parts"])
    assert [part["marks_awarded"] for part in result["parts"]] == [0] * len(question["parts"])
    assert result["parts"][0]["error"] is None
    assert result["parts"][1]["error"]


def test_format_error_replays_and_does_not_consume_its_key(engine):
    session = engine.create_session(question_count=1)
    session_id = session["session_id"]
    question = engine.next_question(session_id)["question"]
    key = question["stable_key"]
    request = {
        "session_id": session_id,
        "stable_key": key,
        "revision": question["revision"],
        "idempotency_key": "same-key",
    }

    first = engine.submit_attempt(answers={"1": ""}, **request)
    replay = engine.submit_attempt(answers={"1": ""}, **request)
    assert first == replay
    assert first["format_error"] is True
    assert recorded_state(engine, session_id, key)[0] == 0

    corrected = engine.submit_attempt(answers=readable_answers(engine, key), **request)
    assert corrected["format_error"] is False
    assert corrected["correct"] is True
    assert engine.submit_attempt(answers=readable_answers(engine, key), **request) == corrected
    assert recorded_state(engine, session_id, key)[0] == 1


def test_checkpoint_format_error_keeps_the_question_open(engine):
    key = next(iter(engine.questions))
    session = engine.create_session(
        question_count=1,
        ordered_question_keys=[key],
        context={"mode": "checkpoint"},
    )
    session_id = session["session_id"]
    question = engine.next_question(session_id)["question"]

    garbled = engine.submit_attempt(
        session_id=session_id,
        stable_key=key,
        revision=question["revision"],
        answers={str(part["position"]): "?" for part in question["parts"]},
        idempotency_key="checkpoint-garbled",
    )
    assert garbled["format_error"] is True
    assert garbled["question_finished"] is False
    assert garbled["solution_available"] is False
    assert recorded_state(engine, session_id, key) == (0, ("pending", 0), None)
    still_open = engine.next_question(session_id)
    assert still_open["status"] != "completed"
    assert still_open["question"]["stable_key"] == key

    wrong = engine.submit_attempt(
        session_id=session_id,
        stable_key=key,
        revision=question["revision"],
        answers=wrong_answers(engine, key),
        idempotency_key="checkpoint-wrong",
    )
    assert wrong["format_error"] is False
    assert wrong["question_finished"] is True
    completed = engine.next_question(session_id)
    assert completed["status"] == "completed"
    assert completed["session"]["incorrect_count"] == 1


def test_configuration_error_is_handled_as_a_format_error(engine, monkeypatch):
    message = "This question's answer cannot be checked automatically. Please report it."
    monkeypatch.setattr(
        practice, "check_answer", lambda response, answer: {"correct": False, "error": message}
    )
    session = engine.create_session(question_count=1)
    session_id = session["session_id"]
    question = engine.next_question(session_id)["question"]
    key = question["stable_key"]

    result = engine.submit_attempt(
        session_id=session_id,
        stable_key=key,
        revision=question["revision"],
        answers=readable_answers(engine, key),
        idempotency_key="unconfigured",
    )

    assert result["format_error"] is True
    assert {part["error"] for part in result["parts"]} == {message}
    assert result["question_finished"] is False
    assert recorded_state(engine, session_id, key) == (0, ("pending", 0), None)


def submit_garbled(engine, session_id, question, label, count):
    return [
        engine.submit_attempt(
            session_id=session_id,
            stable_key=question["stable_key"],
            revision=question["revision"],
            answers={str(part["position"]): "?" for part in question["parts"]},
            idempotency_key=f"{label}-{number}",
        )
        for number in range(count)
    ]


def test_repeated_format_errors_cannot_trap_a_learner_in_a_checkpoint(engine):
    key = next(iter(engine.questions))
    session = engine.create_session(
        question_count=1,
        ordered_question_keys=[key],
        context={"mode": "checkpoint"},
    )
    session_id = session["session_id"]
    question = engine.next_question(session_id)["question"]

    uncounted = submit_garbled(engine, session_id, question, "stuck", MAX_UNCOUNTED_FORMAT_ERRORS)
    assert all(result["format_error"] for result in uncounted)
    assert recorded_state(engine, session_id, key)[:2] == (0, ("pending", 0))

    counted = submit_garbled(engine, session_id, question, "counted", 1)[0]
    assert counted["format_error"] is False
    assert counted["correct"] is False
    assert counted["attempt_number"] == 1
    assert counted["question_finished"] is True
    assert engine.next_question(session_id)["status"] == "completed"


def test_counted_attempt_resets_the_format_error_allowance(engine):
    session = engine.create_session(question_count=1)
    session_id = session["session_id"]
    question = engine.next_question(session_id)["question"]
    key = question["stable_key"]

    submit_garbled(engine, session_id, question, "before", MAX_UNCOUNTED_FORMAT_ERRORS)
    engine.submit_attempt(
        session_id=session_id,
        stable_key=key,
        revision=question["revision"],
        answers=wrong_answers(engine, key),
        idempotency_key="readable-wrong",
    )

    after = submit_garbled(engine, session_id, question, "after", MAX_UNCOUNTED_FORMAT_ERRORS)
    assert all(result["format_error"] for result in after)
    assert recorded_state(engine, session_id, key)[:2] == (1, ("pending", 1))

    counted = submit_garbled(engine, session_id, question, "last", 1)[0]
    assert counted["format_error"] is False
    assert counted["solution_available"] is True
    assert engine.give_up(session_id, key)["status"] == "gave_up"


def test_existing_local_database_gains_the_format_error_column(engine):
    with sqlite3.connect(engine.database) as connection:
        connection.execute("alter table session_questions drop column uncounted_format_errors")

    engine._initialize()

    with sqlite3.connect(engine.database) as connection:
        columns = {row[1] for row in connection.execute("pragma table_info(session_questions)")}
    assert "uncounted_format_errors" in columns
