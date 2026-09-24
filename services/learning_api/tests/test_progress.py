import asyncio
from pathlib import Path

import httpx
from question_bank.practice import solution_for
from question_bank.validation import validate_bank

from learning_api.config import Settings
from learning_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BANK_ROOT = (
    REPOSITORY_ROOT
    / "backend_resources/question_bank/g3_math/secondary_1/n1/v1"
)


def application(tmp_path: Path, *, learner_id: str | None = "development-learner"):
    return create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=True,
            practice_database=tmp_path / "practice.sqlite3",
            development_learner_id=learner_id,
        )
    )


def request(app, method: str, path: str, **kwargs):
    async def send():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def create_session(app, key: str, question_count: int | None = None):
    payload = {"lesson_key": "n1-lesson-01", "mode": "guided_practice"}
    if question_count is not None:
        payload["question_count"] = question_count
    return request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        headers={"Idempotency-Key": key},
        json=payload,
    )


def canonical_answers(question):
    return {
        str(part["position"]): part["canonical_answer"]
        for part in solution_for(question)["parts"]
    }


def answer_current_correctly(app, session_id: str, key: str, questions):
    current = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{session_id}/next",
    ).json()
    question_key = current["question"]["stable_key"]
    response = request(
        app,
        "POST",
        "/api/v1/attempts",
        headers={"Idempotency-Key": key},
        json={
            "session_id": session_id,
            "question_key": question_key,
            "question_revision": current["question"]["revision"],
            "answers": canonical_answers(questions[question_key]),
        },
    )
    assert response.status_code == 200
    assert response.json()["correct"] is True


def test_learning_home_resumes_active_practice(tmp_path):
    app = application(tmp_path)

    initial = request(app, "GET", "/api/v1/learning-home")
    assert initial.status_code == 200
    assert initial.json()["next_action"]["type"] == "start_lesson"

    session = create_session(app, "resume-progress").json()
    home = request(app, "GET", "/api/v1/learning-home")
    course = request(app, "GET", "/api/v1/courses/g3-sec1-math/map").json()

    assert home.json()["next_action"] == {
        "type": "resume_practice",
        "title": "Resume Primes and prime factorisation",
        "description": "Continue question 1 of 3.",
        "href": f"/practice/{session['session_id']}",
        "lesson_key": "n1-lesson-01",
        "session_id": session["session_id"],
    }
    assert course["units"][0]["lessons"][0]["progress_state"] == "in_progress"

    replay = create_session(app, "different-click").json()
    assert replay["session_id"] == session["session_id"]


def test_successful_practice_records_proficiency_and_next_lesson(tmp_path):
    app = application(tmp_path)
    session = create_session(app, "proficiency-session").json()
    questions = {
        question.stable_key: question
        for question in validate_bank(BANK_ROOT).questions
    }

    for number in range(1, 4):
        answer_current_correctly(
            app,
            session["session_id"],
            f"proficiency-answer-{number}",
            questions,
        )

    completed = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{session['session_id']}/next",
    )
    assert completed.json()["status"] == "completed"

    progress = request(app, "GET", "/api/v1/progress").json()
    lesson = progress["lessons"][0]
    home = request(app, "GET", "/api/v1/learning-home").json()

    assert lesson["state"] == "proficient"
    assert lesson["eventual_correct_percentage"] == 100
    assert lesson["checkpoint_passed"] is False
    assert progress["checkpoint_required_for_mastery"] is True
    assert home["next_action"]["type"] == "content_pending"
    assert home["next_action"]["lesson_key"] == "n1-lesson-02"


def test_give_up_requires_retry_and_retry_can_reach_proficiency(tmp_path):
    app = application(tmp_path)
    session = create_session(app, "give-up-session", question_count=1).json()
    current = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{session['session_id']}/next",
    ).json()
    question = current["question"]

    for number in (1, 2):
        request(
            app,
            "POST",
            "/api/v1/attempts",
            headers={"Idempotency-Key": f"give-up-wrong-{number}"},
            json={
                "session_id": session["session_id"],
                "question_key": question["stable_key"],
                "question_revision": question["revision"],
                "answers": {"1": "wrong"},
            },
        )
    request(
        app,
        "POST",
        (
            f"/api/v1/practice-sessions/{session['session_id']}"
            f"/questions/{question['stable_key']}/give-up"
        ),
    )
    request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{session['session_id']}/next",
    )

    failed = request(app, "GET", "/api/v1/progress").json()["lessons"][0]
    home = request(app, "GET", "/api/v1/learning-home").json()
    assert failed["state"] == "practice_completed"
    assert failed["gave_up_count"] == 1
    assert home["next_action"]["type"] == "retry_practice"

    retry = create_session(app, "retry-session", question_count=1).json()
    questions = {
        item.stable_key: item for item in validate_bank(BANK_ROOT).questions
    }
    answer_current_correctly(
        app,
        retry["session_id"],
        "retry-correct",
        questions,
    )
    request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{retry['session_id']}/next",
    )

    improved = request(app, "GET", "/api/v1/progress").json()["lessons"][0]
    assert improved["state"] == "proficient"
    assert improved["gave_up_count"] == 0


def test_progress_fails_closed_without_a_learner_identity(tmp_path):
    app = application(tmp_path, learner_id=None)

    response = request(app, "GET", "/api/v1/progress")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"
