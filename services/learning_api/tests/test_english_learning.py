import asyncio
import json
from pathlib import Path

import httpx

from learning_api.config import Settings
from learning_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def application(*, allow_drafts: bool = True):
    return create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=allow_drafts,
            development_learner_id="english-development-learner",
            rate_limits_enabled=False,
        )
    )


def request(app, method: str, path: str, **kwargs):
    async def send():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def create_session(app, key: str, *, mode: str = "guided_practice"):
    return request(
        app,
        "POST",
        "/api/v1/english/practice-sessions",
        headers={"Idempotency-Key": key},
        json={"lesson_key": "e1-lesson-01", "mode": mode},
    )


def submit(app, session_id: str, question: dict, answer: str, key: str):
    return request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": key},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {"1": answer},
        },
    )


def test_draft_english_foundation_is_hidden_without_preview_flag():
    response = request(application(allow_drafts=False), "GET", "/api/v1/english/course-map")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "english_course_not_found"


def test_e1_1_course_and_lesson_are_learner_safe_in_development_preview():
    app = application()

    course = request(app, "GET", "/api/v1/english/course-map")
    lesson = request(app, "GET", "/api/v1/english/lessons/e1-lesson-01")

    assert course.status_code == 200, course.text
    assert len(course.json()["modules"]) == 10
    first = next(
        lesson
        for module in course.json()["modules"]
        for lesson in module["lessons"]
        if lesson["stable_key"] == "e1-lesson-01"
    )
    assert first == {
        "stable_key": "e1-lesson-01",
        "lesson_code": "E1.1",
        "position": 1,
        "title": "Meaning from local context",
        "outcome_code": "EV1.1",
        "outcome": (
            "Use definitions, examples, contrast, cause and tone around a word to test a "
            "possible meaning."
        ),
        "content_status": "draft",
        "authored": True,
        "available": True,
        "href": "/english/lessons/e1-lesson-01",
        "progress_state": "not_started",
        "retry_question_count": 0,
    }
    assert lesson.status_code == 200, lesson.text
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"] == {
        "lesson_key": "e1-lesson-01",
        "question_count": 6,
        "available": False,
        "development_available": True,
        "retry_question_count": 0,
    }


def test_full_e1_1_journey_marks_deterministically_and_retries_failed_exit_ticket():
    app = application()
    created = create_session(app, "e1-guided")
    replay = create_session(app, "e1-guided")

    assert created.status_code == 201, created.text
    assert created.json() == replay.json()
    assert created.json()["question_count"] == 6
    assert created.json()["development_drafts"] is True
    session_id = created.json()["session_id"]
    correct_keys = ["B", "A", "A", "A", "A"]

    for number, answer in enumerate(correct_keys, 1):
        current = request(
            app,
            "GET",
            f"/api/v1/english/practice-sessions/{session_id}/next",
        )
        assert current.status_code == 200, current.text
        question = current.json()["question"]
        encoded = json.dumps(question)
        assert "correct_key" not in encoded
        assert "correct_keys" not in encoded
        assert "canonical_answer" not in encoded
        assert "rationale" not in encoded
        answered = submit(app, session_id, question, answer, f"e1-correct-{number}")
        assert answered.status_code == 200, answered.text
        assert answered.json()["correct"] is True

    exit_ticket = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    ).json()["question"]
    assert exit_ticket["stable_key"] == "ev-l1-006"
    wrong = submit(app, session_id, exit_ticket, "B", "e1-wrong-exit")

    assert wrong.status_code == 200, wrong.text
    assert wrong.json()["correct"] is False
    assert wrong.json()["retry_queued"] is True
    assert wrong.json()["needs_error_classification"] is True
    assert wrong.json()["lesson_state"] == "practice_completed"

    classified = request(
        app,
        "POST",
        f"/api/v1/english/attempts/{wrong.json()['attempt_id']}/error-classification",
        json={"category": "missed_clue"},
    )
    assert classified.status_code == 200, classified.text
    assert classified.json()["category"] == "missed_clue"

    before_retry = request(app, "GET", "/api/v1/english/progress").json()["lessons"][0]
    assert before_retry["state"] == "practice_completed"
    assert before_retry["retry_question_count"] == 1

    retry = create_session(app, "e1-retry", mode="retry_review")
    assert retry.status_code == 201, retry.text
    assert retry.json()["question_count"] == 1
    retry_id = retry.json()["session_id"]
    retry_question = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{retry_id}/next",
    ).json()["question"]
    assert retry_question["stable_key"] == "ev-l1-006"

    corrected = submit(app, retry_id, retry_question, "A", "e1-corrected-exit")
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["correct"] is True
    assert corrected.json()["lesson_state"] == "proficient"

    after_retry = request(app, "GET", "/api/v1/english/progress").json()["lessons"][0]
    assert after_retry["state"] == "proficient"
    assert after_retry["retry_question_count"] == 0
