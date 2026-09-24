import asyncio
import json
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


def application(tmp_path: Path, *, allow_drafts: bool = True):
    return create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=allow_drafts,
            practice_database=tmp_path / "practice.sqlite3",
        )
    )


def request(app, method: str, path: str, **kwargs):
    async def send():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def create_session(app, key: str = "create-lesson-01"):
    return request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        headers={"Idempotency-Key": key},
        json={"lesson_key": "n1-lesson-01", "mode": "guided_practice"},
    )


def canonical_answers(question):
    return {
        str(part["position"]): part["canonical_answer"]
        for part in solution_for(question)["parts"]
    }


def test_session_creation_is_idempotent_and_resumable(tmp_path):
    app = application(tmp_path)

    first = create_session(app)
    replay = create_session(app)

    assert first.status_code == 201
    assert replay.status_code == 201
    assert first.json() == replay.json()
    assert first.json()["question_count"] == 3
    assert first.json()["development_drafts"] is True

    current = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{first.json()['session_id']}/next",
    )
    refreshed = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{first.json()['session_id']}/next",
    )

    assert current.status_code == 200
    assert current.json() == refreshed.json()
    assert current.json()["question"]["stable_key"] == "n1-l1-01"
    assert current.json()["stage"] == "guided"
    encoded = json.dumps(current.json())
    assert "canonical_answer" not in encoded
    assert "canonical_expression" not in encoded
    assert '"solution"' not in encoded


def test_lesson_practice_uses_only_configured_pool_in_order(tmp_path):
    app = application(tmp_path)
    session = create_session(app, "ordered-pool").json()
    questions = {
        question.stable_key: question
        for question in validate_bank(BANK_ROOT).questions
    }
    observed = []

    for number in range(1, 4):
        current = request(
            app,
            "GET",
            f"/api/v1/practice-sessions/{session['session_id']}/next",
        ).json()
        key = current["question"]["stable_key"]
        observed.append((key, current["stage"]))
        response = request(
            app,
            "POST",
            "/api/v1/attempts",
            headers={"Idempotency-Key": f"correct-{number}"},
            json={
                "session_id": session["session_id"],
                "question_key": key,
                "question_revision": current["question"]["revision"],
                "answers": canonical_answers(questions[key]),
            },
        )
        assert response.status_code == 200
        assert response.json()["correct"] is True

    completed = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{session['session_id']}/next",
    )
    assert completed.json()["status"] == "completed"
    assert observed == [
        ("n1-l1-01", "guided"),
        ("n1-l2-03", "independent"),
        ("n1-l3-02", "challenge"),
    ]


def test_wrong_answers_unlock_hints_and_authored_solution(tmp_path):
    app = application(tmp_path)
    session = create_session(app, "support-flow").json()
    current = request(
        app,
        "GET",
        f"/api/v1/practice-sessions/{session['session_id']}/next",
    ).json()
    key = current["question"]["stable_key"]

    second_hint_first = request(
        app,
        "POST",
        f"/api/v1/practice-sessions/{session['session_id']}/questions/{key}/hints/2",
    )
    assert second_hint_first.status_code == 409
    assert second_hint_first.json()["error"]["code"] == "hint_order"

    first_hint = request(
        app,
        "POST",
        f"/api/v1/practice-sessions/{session['session_id']}/questions/{key}/hints/1",
    )
    assert first_hint.status_code == 200
    assert first_hint.json()["parts"][0]["content"]

    for attempt in (1, 2):
        result = request(
            app,
            "POST",
            "/api/v1/attempts",
            headers={"Idempotency-Key": f"wrong-{attempt}"},
            json={
                "session_id": session["session_id"],
                "question_key": key,
                "question_revision": current["question"]["revision"],
                "answers": {"1": "not an answer"},
            },
        )
        assert result.status_code == 200
        assert result.json()["correct"] is False

    assert result.json()["solution_available"] is True
    solution = request(
        app,
        "POST",
        f"/api/v1/practice-sessions/{session['session_id']}/questions/{key}/give-up",
    )
    assert solution.status_code == 200
    assert solution.json()["status"] == "gave_up"
    assert solution.json()["solution"]["parts"][0]["canonical_answer"]
    assert solution.json()["solution"]["parts"][0]["steps"]


def test_draft_practice_fails_closed_outside_preview(tmp_path):
    app = application(tmp_path, allow_drafts=False)

    response = create_session(app, "production-like")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "course_not_found"
