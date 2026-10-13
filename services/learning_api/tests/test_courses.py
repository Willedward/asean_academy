import asyncio
import json
from pathlib import Path

import httpx
from question_bank.course_models import ActiveRecallSection

from learning_api.config import Settings
from learning_api.course_catalogue import CourseCatalogue, public_lesson_section
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
            development_learner_id="development-learner",
        )
    )

    async def request():
        transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path)

    return asyncio.run(request())


def test_course_map_returns_complete_secondary_1_content_units():
    response = get("/api/v1/courses/g3-sec1-math/map")

    assert response.status_code == 200
    course = response.json()
    assert course["development_preview"] is True
    assert course["content_status"] == "draft"
    assert len(course["units"]) == 10
    assert len(course["units"][0]["lessons"]) == 7
    assert len(course["units"][1]["lessons"]) == 3
    assert len(course["units"][2]["lessons"]) == 6
    assert len(course["units"][3]["lessons"]) == 3
    assert len(course["units"][4]["lessons"]) == 8
    assert len(course["units"][5]["lessons"]) == 5
    assert len(course["units"][6]["lessons"]) == 4
    assert len(course["units"][7]["lessons"]) == 7
    assert len(course["units"][8]["lessons"]) == 5
    assert len(course["units"][9]["lessons"]) == 4
    assert [lesson["position"] for lesson in course["units"][0]["lessons"]] == list(range(1, 8))
    assert {lesson["learning_material_state"] for lesson in course["units"][0]["lessons"]} == {
        "pending"
    }
    assert {lesson["availability"] for lesson in course["units"][0]["lessons"]} == {
        "content_pending"
    }


def test_draft_lesson_returns_authored_sections_without_private_recall_answer():
    response = get("/api/v1/lessons/n1-lesson-01")

    assert response.status_code == 200
    lesson = response.json()
    assert lesson["revision"] == 2
    assert lesson["title"] == "Primes and prime factorisation"
    assert lesson["objectives"]
    assert [section["type"] for section in lesson["sections"]] == [
        "explanation",
        "worked_example",
        "explanation",
        "worked_example",
        "active_recall",
        "explanation",
        "summary",
    ]
    assert lesson["sections"][4]["response_type"] == "algebraic_expression"
    assert lesson["assets"] == []
    assert lesson["learning_material_state"] == "pending"
    assert lesson["practice"] == {
        "lesson_key": "n1-lesson-01",
        "mode": "guided_practice",
        "question_count": 3,
        "available": False,
        "development_available": True,
        "unavailable_reason": "content_not_reviewed",
    }
    encoded = json.dumps(lesson)
    assert "canonical_answer" not in encoded
    assert "canonical_expression" not in encoded
    assert "Correct. Repeated division" not in encoded


def test_n2_lesson_is_available_as_a_complete_reviewed_preview():
    response = get("/api/v1/lessons/n2-lesson-01")

    assert response.status_code == 200
    lesson = response.json()
    assert lesson["title"] == "Ratios involving rational numbers"
    assert [section["type"] for section in lesson["sections"]] == [
        "explanation",
        "explanation",
        "worked_example",
        "worked_example",
        "active_recall",
        "summary",
    ]
    assert lesson["practice"]["question_count"] == 20
    assert lesson["practice"]["development_available"] is True
    encoded = json.dumps(lesson)
    assert "canonical_expression" not in encoded
    assert "Convert 1.5 kg to 1500 g" not in encoded


def test_unpublished_course_is_hidden_when_preview_is_disabled():
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


def test_course_registry_exposes_complete_planned_scope():
    response = get("/api/v1/courses")

    assert response.status_code == 200
    registry = response.json()
    assert registry["course_count"] == 2
    assert registry["topic_group_count"] == 19
    assert registry["lesson_count"] == registry["outcome_count"] == 87
    secondary_one, secondary_two = registry["courses"]
    assert secondary_one["stable_key"] == "g3-sec1-math"
    assert len(secondary_one["units"]) == 10
    assert secondary_one["available"] is True
    assert secondary_one["units"][0]["topic_code"] == "N1"
    assert secondary_one["units"][0]["available"] is True
    assert secondary_one["units"][1]["available"] is True
    assert secondary_two["stable_key"] == "g3-sec2-math"
    assert len(secondary_two["units"]) == 9
    assert secondary_two["available"] is True
    assert secondary_two["units"][4]["topic_code"] == "G2"
    assert secondary_two["units"][4]["available"] is True
    assert all(lesson["available"] is True for lesson in secondary_two["units"][4]["lessons"])


def test_secondary_2_g2_course_and_lesson_are_available_in_draft_preview():
    course_response = get("/api/v1/courses/g3-sec2-math/map")

    assert course_response.status_code == 200
    course = course_response.json()
    assert course["school_level"] == "secondary_2"
    assert course["content_status"] == "draft"
    assert len(course["units"]) == 1
    assert course["units"][0]["stable_key"] == "g3-sec2-g2"
    assert len(course["units"][0]["lessons"]) == 5

    lesson_response = get("/api/v1/lessons/g2-lesson-01")
    assert lesson_response.status_code == 200
    lesson = lesson_response.json()
    assert lesson["course_key"] == "g3-sec2-math"
    assert lesson["unit_key"] == "g3-sec2-g2"
    assert lesson["practice"]["question_count"] == 15
    assert lesson["practice"]["development_available"] is True


def test_validated_geometry_assets_are_served_for_lessons_and_questions():
    lesson_response = get("/api/v1/content-assets/lesson/g2-lesson-01/g2-lesson-01-diagram")
    assert lesson_response.status_code == 200
    assert lesson_response.headers["content-type"].startswith("image/svg+xml")
    assert b"Congruent figures" in lesson_response.content

    question_response = get("/api/v1/content-assets/question/g2-l1-501/g2-l1-501-diagram")
    assert question_response.status_code == 200
    assert question_response.headers["content-type"].startswith("image/svg+xml")
    assert b"Matching triangular tiles" in question_response.content

    missing_response = get("/api/v1/content-assets/question/g2-l1-501/not-a-real-diagram")
    assert missing_response.status_code == 404


def test_draft_registry_entries_are_not_available_without_preview():
    response = get("/api/v1/courses", allow_drafts=False)

    assert response.status_code == 200
    assert all(course["available"] is False for course in response.json()["courses"])


def test_review_catalogue_exposes_all_authored_questions_and_batch_membership():
    catalogue = CourseCatalogue(REPOSITORY_ROOT, allow_drafts=True)
    authored_paths = list(
        (REPOSITORY_ROOT / "backend_resources/question_bank/g3_math").glob("**/questions/*.json")
    )

    assert len(catalogue.questions) == 976
    assert len(catalogue.review_questions) == len(authored_paths)
    assert catalogue.review_question_batches["n2-l1-001"] == "g3-sec1-n2-b001"
    assert catalogue.review_question_batches["n2-l1-007"] == "g3-sec1-n2-b002"
    assert catalogue.review_question_batches["n3-l1-001"] == "g3-sec1-n3-b001"
    assert catalogue.review_question_batches["n6-l1-001"] == "g3-sec1-n6-b001"
    assert catalogue.review_question_batches["n7-l1-001"] == "g3-sec1-n7-b001"
    assert catalogue.review_question_batches["g1-l1-001"] == "g3-sec1-g1-b001"
    assert catalogue.review_question_batches["s1-l1-001"] == "g3-sec1-s1-b001"
    assert catalogue.review_question_batches["g2-l1-501"] == "g3-sec2-g2-b001"
    assert "n1-l1-01" not in catalogue.review_question_batches
