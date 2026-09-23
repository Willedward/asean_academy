import asyncio
import json
from pathlib import Path

import httpx
from question_bank.course_models import ActiveRecallSection

from learning_api.config import Settings
from learning_api.course_catalogue import public_lesson_section
from learning_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def get(path: str, *, allow_drafts: bool = True):
    application = create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=allow_drafts,
        )
    )

    async def request():
        transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path)

    return asyncio.run(request())


def test_course_map_returns_seven_explicit_content_placeholders():
    response = get("/api/v1/courses/g3-sec1-math/map")

    assert response.status_code == 200
    course = response.json()
    assert course["development_preview"] is True
    assert course["content_status"] == "draft"
    assert len(course["units"]) == 1
    assert len(course["units"][0]["lessons"]) == 7
    assert [lesson["position"] for lesson in course["units"][0]["lessons"]] == list(
        range(1, 8)
    )
    assert {lesson["learning_material_state"] for lesson in course["units"][0]["lessons"]} == {
        "pending"
    }
    assert {lesson["availability"] for lesson in course["units"][0]["lessons"]} == {
        "content_pending"
    }


def test_blank_lesson_has_objectives_but_no_invented_material():
    response = get("/api/v1/lessons/n1-lesson-01")

    assert response.status_code == 200
    lesson = response.json()
    assert lesson["title"] == "Primes and prime factorisation"
    assert lesson["objectives"]
    assert lesson["sections"] == []
    assert lesson["assets"] == []
    assert lesson["practice"] == {
        "lesson_key": "n1-lesson-01",
        "mode": "guided_practice",
        "question_count": 3,
        "available": False,
        "unavailable_reason": "content_not_reviewed",
    }
    encoded = json.dumps(lesson)
    assert "canonical_answer" not in encoded
    assert "canonical_expression" not in encoded


def test_draft_course_is_hidden_when_preview_is_disabled():
    response = get("/api/v1/courses/g3-sec1-math/map", allow_drafts=False)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "course_not_found"


def test_unknown_lesson_uses_safe_not_found_error():
    response = get("/api/v1/lessons/n1-lesson-99")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "lesson_not_found"


def test_active_recall_section_does_not_leak_answer_or_locked_feedback():
    section = ActiveRecallSection.model_validate(
        {
            "stable_key": "prime-recall",
            "position": 1,
            "type": "active_recall",
            "title": "Check your understanding",
            "prompt": [{"type": "text", "text": "Is 17 a prime number?"}],
            "response": {
                "type": "numeric",
                "comparison_mode": "exact_numeric",
                "canonical_answer": "1",
                "canonical_latex": "1",
            },
            "feedback": [{"type": "text", "text": "17 has exactly two positive factors."}],
        }
    )

    encoded = json.dumps(public_lesson_section(section))
    assert "Is 17 a prime number?" in encoded
    assert "canonical_answer" not in encoded
    assert "canonical_latex" not in encoded
    assert "exactly two positive factors" not in encoded
