from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import httpx
import pytest
from question_bank.practice import solution_for
from question_bank.validation import validate_bank

from learning_api.config import Settings
from learning_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BANK_ROOT = REPOSITORY_ROOT / "backend_resources/question_bank/g3_math/secondary_1/n1/v1"
QUESTIONS = {question.stable_key: question for question in validate_bank(BANK_ROOT).questions}
LESSON_KEYS = [f"n1-lesson-{number:02d}" for number in range(1, 8)]


def application(tmp_path: Path):
    database = tmp_path / "practice.sqlite3"
    app = create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=True,
            practice_database=database,
            development_learner_id="development-learner",
        )
    )
    return app, database


def request(app, method: str, path: str, **kwargs):
    async def send():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def canonical_answers(question_key: str):
    return {
        str(part["position"]): part["canonical_answer"]
        for part in solution_for(QUESTIONS[question_key])["parts"]
    }


def create_lesson_session(app, lesson_key: str, key: str, *, mode="guided_practice", count=None):
    payload = {"lesson_key": lesson_key, "mode": mode}
    if count is not None:
        payload["question_count"] = count
    return request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        headers={"Idempotency-Key": key},
        json=payload,
    )


def complete_lesson_correctly(app, lesson_key: str, sequence: int) -> None:
    response = create_lesson_session(app, lesson_key, f"lesson-{sequence}-session")
    assert response.status_code == 201, response.text
    session_id = response.json()["session_id"]
    attempt = 0
    while True:
        current = request(app, "GET", f"/api/v1/practice-sessions/{session_id}/next")
        assert current.status_code == 200, current.text
        if current.json()["status"] == "completed":
            break
        question = current.json()["question"]
        attempt += 1
        submitted = request(
            app,
            "POST",
            "/api/v1/attempts",
            headers={"Idempotency-Key": f"lesson-{sequence}-answer-{attempt}"},
            json={
                "session_id": session_id,
                "question_key": question["stable_key"],
                "question_revision": question["revision"],
                "answers": canonical_answers(question["stable_key"]),
            },
        )
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["correct"] is True


def test_lesson_and_checkpoint_are_locked_until_prerequisites_are_proficient(tmp_path):
    app, _ = application(tmp_path)

    course = request(app, "GET", "/api/v1/courses/g3-sec1-math/map").json()
    assert course["units"][0]["lessons"][0]["unlocked"] is True
    assert course["units"][0]["lessons"][1]["unlocked"] is False
    assert course["units"][0]["checkpoint_available"] is False

    locked_lesson = create_lesson_session(app, "n1-lesson-02", "locked-lesson")
    assert locked_lesson.status_code == 409
    assert locked_lesson.json()["error"]["code"] == "lesson_locked"

    checkpoint = request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        headers={"Idempotency-Key": "locked-checkpoint"},
        json={"unit_key": "g3-sec1-n1", "mode": "checkpoint"},
    )
    assert checkpoint.status_code == 409
    assert checkpoint.json()["error"]["code"] == "checkpoint_locked"


def test_retry_review_selects_only_the_unresolved_question(tmp_path):
    app, _ = application(tmp_path)
    first = create_lesson_session(app, "n1-lesson-01", "failed-practice", count=1)
    session_id = first.json()["session_id"]
    current = request(app, "GET", f"/api/v1/practice-sessions/{session_id}/next").json()
    question = current["question"]

    for number in (1, 2):
        wrong = request(
            app,
            "POST",
            "/api/v1/attempts",
            headers={"Idempotency-Key": f"failed-answer-{number}"},
            json={
                "session_id": session_id,
                "question_key": question["stable_key"],
                "question_revision": question["revision"],
                "answers": {"1": "not an answer"},
            },
        )
        assert wrong.status_code == 200

    gave_up = request(
        app,
        "POST",
        f"/api/v1/practice-sessions/{session_id}/questions/{question['stable_key']}/give-up",
    )
    assert gave_up.status_code == 200
    request(app, "GET", f"/api/v1/practice-sessions/{session_id}/next")

    retry = create_lesson_session(
        app,
        "n1-lesson-01",
        "retry-review",
        mode="retry_review",
    )
    assert retry.status_code == 201, retry.text
    assert retry.json()["mode"] == "retry_review"
    assert retry.json()["question_count"] == 1

    retry_question = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{retry.json()['session_id']}/next",
    ).json()
    assert retry_question["question"]["stable_key"] == question["stable_key"]
    assert retry_question["selection_reason"] == "required_retry"
    assert retry_question["stage"] == "adaptive"


def test_checkpoint_is_single_attempt_and_passing_records_immutable_mastery(tmp_path):
    app, database = application(tmp_path)
    for sequence, lesson_key in enumerate(LESSON_KEYS, start=1):
        complete_lesson_correctly(app, lesson_key, sequence)

    before = request(app, "GET", "/api/v1/progress").json()
    assert all(lesson["state"] == "proficient" for lesson in before["lessons"])
    assert before["checkpoints"][0]["state"] == "available"
    assert before["checkpoints"][0]["question_count"] == 8
    assert before["checkpoints"][0]["passing_percentage"] == 70

    created = request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        headers={"Idempotency-Key": "n1-checkpoint"},
        json={"unit_key": "g3-sec1-n1", "mode": "checkpoint"},
    )
    assert created.status_code == 201, created.text
    checkpoint_id = created.json()["session_id"]
    assert created.json()["question_count"] == 8
    assert created.json()["lesson_key"] is None
    assert created.json()["unit_key"] == "g3-sec1-n1"

    first = request(app, "GET", f"/api/v1/practice-sessions/{checkpoint_id}/next").json()
    first_question = first["question"]
    hint = request(
        app,
        "POST",
        f"/api/v1/practice-sessions/{checkpoint_id}/questions/{first_question['stable_key']}/hints/1",
    )
    give_up = request(
        app,
        "POST",
        f"/api/v1/practice-sessions/{checkpoint_id}/questions/{first_question['stable_key']}/give-up",
    )
    assert hint.status_code == give_up.status_code == 403
    assert hint.json()["error"]["code"] == "checkpoint_support_locked"
    assert give_up.json()["error"]["code"] == "checkpoint_support_locked"

    wrong = request(
        app,
        "POST",
        "/api/v1/attempts",
        headers={"Idempotency-Key": "checkpoint-answer-1"},
        json={
            "session_id": checkpoint_id,
            "question_key": first_question["stable_key"],
            "question_revision": first_question["revision"],
            "answers": {"1": "not an answer"},
        },
    )
    assert wrong.status_code == 200
    assert wrong.json()["correct"] is False
    assert wrong.json()["question_finished"] is True
    assert wrong.json()["solution_available"] is False

    for number in range(2, 9):
        current = request(
            app,
            "GET",
            f"/api/v1/practice-sessions/{checkpoint_id}/next",
        ).json()
        assert current["status"] == "active"
        question = current["question"]
        correct = request(
            app,
            "POST",
            "/api/v1/attempts",
            headers={"Idempotency-Key": f"checkpoint-answer-{number}"},
            json={
                "session_id": checkpoint_id,
                "question_key": question["stable_key"],
                "question_revision": question["revision"],
                "answers": canonical_answers(question["stable_key"]),
            },
        )
        assert correct.status_code == 200, correct.text
        assert correct.json()["correct"] is True

    completed = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{checkpoint_id}/next",
    ).json()
    assert completed["status"] == "completed"
    assert completed["session"]["correct_count"] == 7
    assert completed["session"]["incorrect_count"] == 1

    progress = request(app, "GET", "/api/v1/progress").json()
    home = request(app, "GET", "/api/v1/learning-home").json()
    assert all(lesson["state"] == "mastered" for lesson in progress["lessons"])
    assert all(lesson["checkpoint_passed"] for lesson in progress["lessons"])
    assert progress["checkpoints"][0]["state"] == "passed"
    assert progress["checkpoints"][0]["last_percentage"] == 87.5
    assert home["next_action"]["type"] == "course_complete"

    with sqlite3.connect(database) as connection:
        events = connection.execute(
            """
            select event_type, count(*)
            from learner_mastery_events
            group by event_type
            order by event_type
            """
        ).fetchall()
        assert events == [
            ("checkpoint_passed", 1),
            ("lesson_mastered", 1),
            ("lesson_proficient", 7),
        ]
        with pytest.raises(sqlite3.IntegrityError, match="mastery events are immutable"):
            connection.execute(
                "update learner_mastery_events set evidence_json = '{}'"
            )


def test_failed_checkpoint_preserves_proficiency_and_allows_a_retake(tmp_path):
    app, _ = application(tmp_path)
    for sequence, lesson_key in enumerate(LESSON_KEYS, start=1):
        complete_lesson_correctly(app, lesson_key, sequence)

    created = request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        headers={"Idempotency-Key": "failed-n1-checkpoint"},
        json={"unit_key": "g3-sec1-n1", "mode": "checkpoint"},
    )
    assert created.status_code == 201, created.text
    checkpoint_id = created.json()["session_id"]

    for number in range(1, 9):
        current = request(
            app,
            "GET",
            f"/api/v1/practice-sessions/{checkpoint_id}/next",
        ).json()
        question = current["question"]
        wrong = request(
            app,
            "POST",
            "/api/v1/attempts",
            headers={"Idempotency-Key": f"failed-checkpoint-answer-{number}"},
            json={
                "session_id": checkpoint_id,
                "question_key": question["stable_key"],
                "question_revision": question["revision"],
                "answers": {"1": "not an answer"},
            },
        )
        assert wrong.status_code == 200, wrong.text
        assert wrong.json()["question_finished"] is True

    completed = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{checkpoint_id}/next",
    ).json()
    assert completed["status"] == "completed"
    assert completed["session"]["incorrect_count"] == 8

    progress = request(app, "GET", "/api/v1/progress").json()
    assert all(lesson["state"] == "proficient" for lesson in progress["lessons"])
    assert not any(lesson["checkpoint_passed"] for lesson in progress["lessons"])
    assert sum(lesson["retry_question_count"] for lesson in progress["lessons"]) == 8
    assert progress["checkpoints"][0]["state"] == "available"
    assert progress["checkpoints"][0]["last_percentage"] == 0

    home = request(app, "GET", "/api/v1/learning-home").json()
    assert home["unresolved_retry_count"] == 8
    assert home["next_action"]["type"] == "retry_practice"
    retry = create_lesson_session(
        app,
        home["next_action"]["lesson_key"],
        "checkpoint-remediation",
        mode="retry_review",
        count=1,
    )
    assert retry.status_code == 201, retry.text
    retry_question = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{retry.json()['session_id']}/next",
    ).json()
    assert retry_question["selection_reason"] == "required_retry"

    # Resolve the active remediation session before starting a checkpoint retake.
    question = retry_question["question"]
    corrected = request(
        app,
        "POST",
        "/api/v1/attempts",
        headers={"Idempotency-Key": "checkpoint-remediation-answer"},
        json={
            "session_id": retry.json()["session_id"],
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": canonical_answers(question["stable_key"]),
        },
    )
    assert corrected.status_code == 200, corrected.text
    request(app, "GET", f"/api/v1/practice-sessions/{retry.json()['session_id']}/next")

    retake = request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        headers={"Idempotency-Key": "n1-checkpoint-retake"},
        json={"unit_key": "g3-sec1-n1", "mode": "checkpoint"},
    )
    assert retake.status_code == 201, retake.text
    assert retake.json()["session_id"] != checkpoint_id
