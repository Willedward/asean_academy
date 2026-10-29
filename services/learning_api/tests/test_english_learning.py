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


def create_session(
    app,
    key: str,
    *,
    mode: str = "guided_practice",
    lesson_key: str = "e1-lesson-01",
):
    return request(
        app,
        "POST",
        "/api/v1/english/practice-sessions",
        headers={"Idempotency-Key": key},
        json={"lesson_key": lesson_key, "mode": mode},
    )


def submit(app, session_id: str, question: dict, answer: str | list[str], key: str):
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


def seed_checkpoint_prerequisites(app, *lesson_keys: str):
    request(app, "GET", "/api/v1/english/progress")
    repository = app.state.english_learning_repository
    for lesson_key in lesson_keys:
        repository.lesson_progress[("english-development-learner", lesson_key)] = {
            "lesson_key": lesson_key,
            "lesson_revision": 1,
            "state": "proficient",
            "question_count": 1,
            "resolved_count": 1,
            "correct_count": 1,
            "incorrect_count": 0,
            "retry_question_count": 0,
            "last_session_id": None,
            "updated_at": "2026-10-28T00:00:00+00:00",
        }


def seed_e1_checkpoint_prerequisites(app):
    seed_checkpoint_prerequisites(app, "e1-lesson-01", "e1-lesson-06")


def create_checkpoint(app, key: str, *, module_code: str = "E1"):
    return request(
        app,
        "POST",
        "/api/v1/english/checkpoint-sessions",
        headers={"Idempotency-Key": key},
        json={"module_code": module_code},
    )


def submit_checkpoint(app, session_id: str, question: dict, answers: dict, key: str):
    return request(
        app,
        "POST",
        "/api/v1/english/checkpoint-attempts",
        headers={"Idempotency-Key": key},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": answers,
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
    assert course.json()["exam_profile"]["profile_key"] == ("asean-english-sec1-id-reported-v1")
    assert course.json()["exam_profile"]["excluded_task_types"] == [
        "editing_section",
        "own_words_short_answer",
    ]
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
        "route_tags": ["full", "core", "sprint"],
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


def test_e1_checkpoint_is_locked_until_every_scoped_lesson_is_proficient():
    app = application()

    locked = create_checkpoint(app, "e1-checkpoint-locked")

    assert locked.status_code == 409, locked.text
    assert locked.json()["error"]["code"] == "english_checkpoint_locked"
    assert "e1-lesson-01" in locked.json()["error"]["message"]
    assert "e1-lesson-06" in locked.json()["error"]["message"]


def test_e0_checkpoint_sequences_both_outcomes_without_early_feedback():
    app = application()
    seed_checkpoint_prerequisites(app, "e0-lesson-01", "e0-lesson-02")

    created = create_checkpoint(app, "e0-checkpoint-pass", module_code="E0")
    assert created.status_code == 201, created.text
    assert created.json()["form_key"] == "english-checkpoint-e0-orientation-a-v1"
    assert created.json()["mastery_lesson_keys"] == ["e0-lesson-01", "e0-lesson-02"]
    session_id = created.json()["session_id"]

    first = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert first["stable_key"] == "ex-l1-008"
    first_attempt = submit_checkpoint(
        app,
        session_id,
        first,
        {"1": "B", "2": "C", "3": "A"},
        "e0-checkpoint-first-group",
    )
    assert first_attempt.status_code == 200, first_attempt.text
    assert first_attempt.json()["checkpoint_completed"] is False
    assert first_attempt.json()["session"]["score"] is None
    assert first_attempt.json()["session"]["resolved_count"] == 1
    assert "parts" not in first_attempt.json()

    second = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert second["stable_key"] == "ex-l2-007"
    completed = submit_checkpoint(
        app,
        session_id,
        second,
        {"1": "D", "2": "B"},
        "e0-checkpoint-second-group",
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["checkpoint_completed"] is True
    assert completed.json()["session"]["score"] == 1
    assert completed.json()["session"]["passed"] is True

    progress = request(app, "GET", "/api/v1/english/progress").json()["lessons"]
    by_key = {item["lesson_key"]: item for item in progress}
    assert by_key["e0-lesson-01"]["state"] == "mastered"
    assert by_key["e0-lesson-02"]["state"] == "mastered"


def test_failed_e0_checkpoint_retake_uses_disjoint_form_b():
    app = application()
    seed_checkpoint_prerequisites(app, "e0-lesson-01", "e0-lesson-02")

    created = create_checkpoint(app, "e0-checkpoint-fail", module_code="E0")
    session_id = created.json()["session_id"]
    first = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    submit_checkpoint(
        app,
        session_id,
        first,
        {"1": "A", "2": "A", "3": "A"},
        "e0-checkpoint-fail-first",
    )
    second = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    failed = submit_checkpoint(
        app,
        session_id,
        second,
        {"1": "A", "2": "A"},
        "e0-checkpoint-fail-second",
    )
    assert failed.status_code == 200, failed.text
    assert failed.json()["session"]["score"] == 0.2
    assert failed.json()["session"]["passed"] is False

    retake = create_checkpoint(app, "e0-checkpoint-retake", module_code="E0")
    assert retake.status_code == 201, retake.text
    assert retake.json()["form_key"] == "english-checkpoint-e0-orientation-b-v1"
    retry_id = retake.json()["session_id"]
    retry_question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{retry_id}/next"
    ).json()["question"]
    assert retry_question["stable_key"] == "ex-l1-009"
    assert retry_question["stable_key"] not in {first["stable_key"], second["stable_key"]}


def test_e2_checkpoint_passes_and_records_sprint_grammar_mastery():
    app = application()
    seed_checkpoint_prerequisites(app, "e2-lesson-02")

    created = create_checkpoint(app, "e2-checkpoint-pass", module_code="E2")
    assert created.status_code == 201, created.text
    assert created.json()["form_key"] == "english-checkpoint-e2-grammar-a-v1"
    assert created.json()["mastery_lesson_keys"] == ["e2-lesson-02"]
    session_id = created.json()["session_id"]
    question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert question["stable_key"] == "eg-l2-003"
    assert question["difficulty"] == 4
    assert "correct_key" not in json.dumps(question)

    completed = submit_checkpoint(
        app,
        session_id,
        question,
        {"1": "B", "2": "D", "3": "A", "4": "C", "5": "B"},
        "e2-checkpoint-pass-attempt",
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["checkpoint_completed"] is True
    assert completed.json()["session"]["score"] == 1
    assert completed.json()["session"]["passed"] is True
    assert "parts" not in completed.json()

    progress = request(app, "GET", "/api/v1/english/progress").json()["lessons"]
    by_key = {item["lesson_key"]: item for item in progress}
    assert by_key["e2-lesson-02"]["state"] == "mastered"


def test_failed_e2_checkpoint_retake_uses_disjoint_form_b():
    app = application()
    seed_checkpoint_prerequisites(app, "e2-lesson-02")

    created = create_checkpoint(app, "e2-checkpoint-fail", module_code="E2")
    session_id = created.json()["session_id"]
    question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    failed = submit_checkpoint(
        app,
        session_id,
        question,
        {str(position): "A" for position in range(1, 6)},
        "e2-checkpoint-fail-attempt",
    )
    assert failed.status_code == 200, failed.text
    assert failed.json()["session"]["score"] == 0.2
    assert failed.json()["session"]["passed"] is False

    retake = create_checkpoint(app, "e2-checkpoint-retake", module_code="E2")
    assert retake.status_code == 201, retake.text
    assert retake.json()["form_key"] == "english-checkpoint-e2-grammar-b-v1"
    retry_id = retake.json()["session_id"]
    retry_question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{retry_id}/next"
    ).json()["question"]
    assert retry_question["stable_key"] == "eg-l2-004"
    assert retry_question["stable_key"] != question["stable_key"]


def test_e3_checkpoint_passes_with_a_learner_safe_complete_passage():
    app = application()
    seed_checkpoint_prerequisites(app, "e3-lesson-01")

    created = create_checkpoint(app, "e3-checkpoint-pass", module_code="E3")
    assert created.status_code == 201, created.text
    assert created.json()["form_key"] == "english-checkpoint-e3-banked-cloze-a-v1"
    assert created.json()["mastery_lesson_keys"] == ["e3-lesson-01"]
    session_id = created.json()["session_id"]
    question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert question["stable_key"] == "eb-l1-006"
    assert question["difficulty"] == 4
    assert len(question["passage"]["paragraphs"]) == 3
    assert "{{1}}" in question["passage"]["paragraphs"][0]
    assert "{{5}}" in question["passage"]["paragraphs"][2]
    assert "correct_key" not in json.dumps(question)

    completed = submit_checkpoint(
        app,
        session_id,
        question,
        {"1": "B", "2": "D", "3": "A", "4": "C", "5": "E"},
        "e3-checkpoint-pass-attempt",
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["checkpoint_completed"] is True
    assert completed.json()["session"]["score"] == 1
    assert completed.json()["session"]["passed"] is True
    assert "parts" not in completed.json()

    progress = request(app, "GET", "/api/v1/english/progress").json()["lessons"]
    by_key = {item["lesson_key"]: item for item in progress}
    assert by_key["e3-lesson-01"]["state"] == "mastered"


def test_failed_e3_checkpoint_retake_uses_a_fresh_passage_on_form_b():
    app = application()
    seed_checkpoint_prerequisites(app, "e3-lesson-01")

    created = create_checkpoint(app, "e3-checkpoint-fail", module_code="E3")
    session_id = created.json()["session_id"]
    question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    failed = submit_checkpoint(
        app,
        session_id,
        question,
        {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"},
        "e3-checkpoint-fail-attempt",
    )
    assert failed.status_code == 200, failed.text
    assert failed.json()["session"]["score"] == 0.2
    assert failed.json()["session"]["passed"] is False

    retake = create_checkpoint(app, "e3-checkpoint-retake", module_code="E3")
    assert retake.status_code == 201, retake.text
    assert retake.json()["form_key"] == "english-checkpoint-e3-banked-cloze-b-v1"
    retry_id = retake.json()["session_id"]
    retry_question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{retry_id}/next"
    ).json()["question"]
    assert retry_question["stable_key"] == "eb-l1-007"
    assert retry_question["passage"]["stable_key"] == (
        "english-passage-checkpoint-missing-recipe"
    )
    assert retry_question["stable_key"] != question["stable_key"]
    assert retry_question["passage"]["stable_key"] != question["passage"]["stable_key"]


def test_e4_checkpoint_sequences_two_open_cloze_passages_without_answer_leak():
    app = application()
    seed_checkpoint_prerequisites(app, "e4-lesson-01", "e4-lesson-05")

    created = create_checkpoint(app, "e4-checkpoint-pass", module_code="E4")
    assert created.status_code == 201, created.text
    assert created.json()["form_key"] == "english-checkpoint-e4-open-cloze-a-v1"
    assert created.json()["mastery_lesson_keys"] == [
        "e4-lesson-01",
        "e4-lesson-05",
    ]
    session_id = created.json()["session_id"]

    first = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert first["stable_key"] == "eo-l1-003"
    assert first["word_bank"] is None
    assert len(first["parts"]) == 3
    assert "canonical_answer" not in json.dumps(first)
    first_attempt = submit_checkpoint(
        app,
        session_id,
        first,
        {"1": "A", "2": "who", "3": "till"},
        "e4-checkpoint-first-group",
    )
    assert first_attempt.status_code == 200, first_attempt.text
    assert first_attempt.json()["checkpoint_completed"] is False
    assert first_attempt.json()["session"]["score"] is None
    assert "parts" not in first_attempt.json()

    second = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert second["stable_key"] == "eo-l5-006"
    assert len(second["parts"]) == 2
    assert "canonical_answer" not in json.dumps(second)
    completed = submit_checkpoint(
        app,
        session_id,
        second,
        {"1": "again", "2": "unless"},
        "e4-checkpoint-second-group",
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["checkpoint_completed"] is True
    assert completed.json()["session"]["score"] == 1
    assert completed.json()["session"]["passed"] is True

    progress = request(app, "GET", "/api/v1/english/progress").json()["lessons"]
    by_key = {item["lesson_key"]: item for item in progress}
    assert by_key["e4-lesson-01"]["state"] == "mastered"
    assert by_key["e4-lesson-05"]["state"] == "mastered"


def test_failed_e4_checkpoint_retake_uses_two_disjoint_form_b_passages():
    app = application()
    seed_checkpoint_prerequisites(app, "e4-lesson-01", "e4-lesson-05")

    created = create_checkpoint(app, "e4-checkpoint-fail", module_code="E4")
    session_id = created.json()["session_id"]
    first = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    first_attempt = submit_checkpoint(
        app,
        session_id,
        first,
        {"1": "wrong", "2": "wrong", "3": "wrong"},
        "e4-checkpoint-fail-first",
    )
    assert first_attempt.status_code == 200, first_attempt.text
    assert first_attempt.json()["checkpoint_completed"] is False

    second = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    failed = submit_checkpoint(
        app,
        session_id,
        second,
        {"1": "wrong", "2": "wrong"},
        "e4-checkpoint-fail-second",
    )
    assert failed.status_code == 200, failed.text
    assert failed.json()["session"]["score"] == 0
    assert failed.json()["session"]["passed"] is False

    retake = create_checkpoint(app, "e4-checkpoint-retake", module_code="E4")
    assert retake.status_code == 201, retake.text
    assert retake.json()["form_key"] == "english-checkpoint-e4-open-cloze-b-v1"
    retry_id = retake.json()["session_id"]
    retry_question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{retry_id}/next"
    ).json()["question"]
    assert retry_question["stable_key"] == "eo-l1-004"
    assert retry_question["passage"]["stable_key"] == (
        "english-passage-checkpoint-museum-parcel"
    )
    assert retry_question["stable_key"] not in {first["stable_key"], second["stable_key"]}
    assert retry_question["passage"]["stable_key"] not in {
        first["passage"]["stable_key"],
        second["passage"]["stable_key"],
    }


def test_e5_checkpoint_delivers_a_safe_paired_passage_and_records_three_masteries():
    app = application()
    seed_checkpoint_prerequisites(
        app, "e5-lesson-02", "e5-lesson-03", "e5-lesson-07"
    )

    created = create_checkpoint(app, "e5-checkpoint-pass", module_code="E5")
    assert created.status_code == 201, created.text
    assert created.json()["form_key"] == "english-checkpoint-e5-reading-a-v1"
    assert created.json()["mastery_lesson_keys"] == [
        "e5-lesson-02",
        "e5-lesson-03",
        "e5-lesson-07",
    ]
    session_id = created.json()["session_id"]

    question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert question["stable_key"] == "er-l5-008"
    assert question["passage"]["stable_key"] == (
        "english-passage-checkpoint-rain-routes-pair"
    )
    assert len(question["parts"]) == 5
    assert "PASSAGE A" in question["passage"]["paragraphs"][0]
    assert "PASSAGE B" in question["passage"]["paragraphs"][4]
    assert "correct_key" not in json.dumps(question)
    assert "choice_rationales" not in json.dumps(question)

    completed = submit_checkpoint(
        app,
        session_id,
        question,
        {"1": "A", "2": "A", "3": "B", "4": "A", "5": "A"},
        "e5-checkpoint-pass-attempt",
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["checkpoint_completed"] is True
    assert completed.json()["session"]["score"] == 1
    assert completed.json()["session"]["passed"] is True
    assert "parts" not in completed.json()

    progress = request(app, "GET", "/api/v1/english/progress").json()["lessons"]
    by_key = {item["lesson_key"]: item for item in progress}
    assert by_key["e5-lesson-02"]["state"] == "mastered"
    assert by_key["e5-lesson-03"]["state"] == "mastered"
    assert by_key["e5-lesson-07"]["state"] == "mastered"


def test_failed_e5_checkpoint_retake_uses_a_disjoint_paired_passage():
    app = application()
    seed_checkpoint_prerequisites(
        app, "e5-lesson-02", "e5-lesson-03", "e5-lesson-07"
    )

    created = create_checkpoint(app, "e5-checkpoint-fail", module_code="E5")
    session_id = created.json()["session_id"]
    question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    failed = submit_checkpoint(
        app,
        session_id,
        question,
        {"1": "D", "2": "D", "3": "D", "4": "D", "5": "D"},
        "e5-checkpoint-fail-attempt",
    )
    assert failed.status_code == 200, failed.text
    assert failed.json()["session"]["score"] == 0
    assert failed.json()["session"]["passed"] is False

    retake = create_checkpoint(app, "e5-checkpoint-retake", module_code="E5")
    assert retake.status_code == 201, retake.text
    assert retake.json()["form_key"] == "english-checkpoint-e5-reading-b-v1"
    retry_id = retake.json()["session_id"]
    retry_question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{retry_id}/next"
    ).json()["question"]
    assert retry_question["stable_key"] == "er-l5-009"
    assert retry_question["passage"]["stable_key"] == (
        "english-passage-checkpoint-night-journeys-pair"
    )
    assert retry_question["stable_key"] != question["stable_key"]
    assert retry_question["passage"]["stable_key"] != question["passage"][
        "stable_key"
    ]


def test_e6_checkpoint_sequences_task_decoding_and_planning_without_answer_leak():
    app = application()
    seed_checkpoint_prerequisites(app, "e6-lesson-01", "e6-lesson-05")

    created = create_checkpoint(app, "e6-checkpoint-pass", module_code="E6")
    assert created.status_code == 201, created.text
    assert created.json()["form_key"] == "english-checkpoint-e6-planning-a-v1"
    assert created.json()["mastery_lesson_keys"] == [
        "e6-lesson-01",
        "e6-lesson-05",
    ]
    session_id = created.json()["session_id"]

    first = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert first["stable_key"] == "ex-l1-010"
    assert len(first["parts"]) == 3
    encoded = json.dumps(first)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    first_attempt = submit_checkpoint(
        app,
        session_id,
        first,
        {"1": "B", "2": ["A", "C", "D"], "3": "C"},
        "e6-checkpoint-first-group",
    )
    assert first_attempt.status_code == 200, first_attempt.text
    assert first_attempt.json()["checkpoint_completed"] is False
    assert first_attempt.json()["session"]["score"] is None
    assert "parts" not in first_attempt.json()

    second = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert second["stable_key"] == "ex-l5-007"
    assert len(second["parts"]) == 2
    completed = submit_checkpoint(
        app,
        session_id,
        second,
        {"1": "A", "2": "A"},
        "e6-checkpoint-second-group",
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["checkpoint_completed"] is True
    assert completed.json()["session"]["score"] == 1
    assert completed.json()["session"]["passed"] is True

    progress = request(app, "GET", "/api/v1/english/progress").json()["lessons"]
    by_key = {item["lesson_key"]: item for item in progress}
    assert by_key["e6-lesson-01"]["state"] == "mastered"
    assert by_key["e6-lesson-05"]["state"] == "mastered"


def test_failed_e6_checkpoint_retake_uses_two_disjoint_form_b_groups():
    app = application()
    seed_checkpoint_prerequisites(app, "e6-lesson-01", "e6-lesson-05")

    created = create_checkpoint(app, "e6-checkpoint-fail", module_code="E6")
    session_id = created.json()["session_id"]
    first = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    first_attempt = submit_checkpoint(
        app,
        session_id,
        first,
        {"1": "D", "2": ["B", "E"], "3": "B"},
        "e6-checkpoint-fail-first",
    )
    assert first_attempt.status_code == 200, first_attempt.text
    assert first_attempt.json()["checkpoint_completed"] is False

    second = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    failed = submit_checkpoint(
        app,
        session_id,
        second,
        {"1": "D", "2": "D"},
        "e6-checkpoint-fail-second",
    )
    assert failed.status_code == 200, failed.text
    assert failed.json()["session"]["score"] == 0
    assert failed.json()["session"]["passed"] is False

    retake = create_checkpoint(app, "e6-checkpoint-retake", module_code="E6")
    assert retake.status_code == 201, retake.text
    assert retake.json()["form_key"] == "english-checkpoint-e6-planning-b-v1"
    retry_id = retake.json()["session_id"]
    retry_first = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{retry_id}/next"
    ).json()["question"]
    assert retry_first["stable_key"] == "ex-l1-011"
    assert retry_first["stable_key"] not in {first["stable_key"], second["stable_key"]}
    retry_first_attempt = submit_checkpoint(
        app,
        retry_id,
        retry_first,
        {"1": "B", "2": "A", "3": "A"},
        "e6-checkpoint-retry-first",
    )
    assert retry_first_attempt.status_code == 200, retry_first_attempt.text
    assert retry_first_attempt.json()["checkpoint_completed"] is False

    retry_second = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{retry_id}/next"
    ).json()["question"]
    assert retry_second["stable_key"] == "ex-l5-008"
    assert retry_second["stable_key"] not in {first["stable_key"], second["stable_key"]}
    retry_completed = submit_checkpoint(
        app,
        retry_id,
        retry_second,
        {"1": "A", "2": "A"},
        "e6-checkpoint-retry-second",
    )
    assert retry_completed.status_code == 200, retry_completed.text
    assert retry_completed.json()["session"]["passed"] is True


def test_e7_checkpoint_sequences_evidence_and_relevance_without_answer_leak():
    app = application()
    seed_checkpoint_prerequisites(app, "e7-lesson-02")

    created = create_checkpoint(app, "e7-checkpoint-pass", module_code="E7")
    assert created.status_code == 201, created.text
    assert created.json()["form_key"] == "english-checkpoint-e7-development-a-v1"
    assert created.json()["mastery_lesson_keys"] == ["e7-lesson-02"]
    session_id = created.json()["session_id"]

    first = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert first["stable_key"] == "ex-l2-009"
    assert len(first["parts"]) == 3
    encoded = json.dumps(first)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    first_attempt = submit_checkpoint(
        app,
        session_id,
        first,
        {"1": "B", "2": ["A", "B"], "3": "A"},
        "e7-checkpoint-first-group",
    )
    assert first_attempt.status_code == 200, first_attempt.text
    assert first_attempt.json()["checkpoint_completed"] is False
    assert first_attempt.json()["session"]["score"] is None

    second = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    assert second["stable_key"] == "ex-l2-010"
    completed = submit_checkpoint(
        app,
        session_id,
        second,
        {"1": "C", "2": "A"},
        "e7-checkpoint-second-group",
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["checkpoint_completed"] is True
    assert completed.json()["session"]["score"] == 1
    assert completed.json()["session"]["passed"] is True

    progress = request(app, "GET", "/api/v1/english/progress").json()["lessons"]
    by_key = {item["lesson_key"]: item for item in progress}
    assert by_key["e7-lesson-02"]["state"] == "mastered"


def test_failed_e7_checkpoint_retake_uses_two_disjoint_form_b_groups():
    app = application()
    seed_checkpoint_prerequisites(app, "e7-lesson-02")

    created = create_checkpoint(app, "e7-checkpoint-fail", module_code="E7")
    session_id = created.json()["session_id"]
    first = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    first_attempt = submit_checkpoint(
        app,
        session_id,
        first,
        {"1": "D", "2": ["C", "E"], "3": "D"},
        "e7-checkpoint-fail-first",
    )
    assert first_attempt.status_code == 200, first_attempt.text
    assert first_attempt.json()["checkpoint_completed"] is False
    second = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    failed = submit_checkpoint(
        app,
        session_id,
        second,
        {"1": "D", "2": "D"},
        "e7-checkpoint-fail-second",
    )
    assert failed.status_code == 200, failed.text
    assert failed.json()["session"]["score"] == 0
    assert failed.json()["session"]["passed"] is False

    retake = create_checkpoint(app, "e7-checkpoint-retake", module_code="E7")
    assert retake.status_code == 201, retake.text
    assert retake.json()["form_key"] == "english-checkpoint-e7-development-b-v1"
    retry_id = retake.json()["session_id"]
    retry_first = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{retry_id}/next"
    ).json()["question"]
    assert retry_first["stable_key"] == "ex-l2-011"
    assert retry_first["stable_key"] not in {first["stable_key"], second["stable_key"]}
    retry_first_attempt = submit_checkpoint(
        app,
        retry_id,
        retry_first,
        {"1": "A", "2": "B", "3": "A"},
        "e7-checkpoint-retry-first",
    )
    assert retry_first_attempt.status_code == 200, retry_first_attempt.text
    assert retry_first_attempt.json()["checkpoint_completed"] is False

    retry_second = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{retry_id}/next"
    ).json()["question"]
    assert retry_second["stable_key"] == "ex-l2-012"
    assert retry_second["stable_key"] not in {first["stable_key"], second["stable_key"]}
    retry_completed = submit_checkpoint(
        app,
        retry_id,
        retry_second,
        {"1": ["A", "B"], "2": "A"},
        "e7-checkpoint-retry-second",
    )
    assert retry_completed.status_code == 200, retry_completed.text
    assert retry_completed.json()["session"]["passed"] is True


def test_e1_checkpoint_passes_without_answer_leak_and_atomically_records_mastery():
    app = application()
    seed_e1_checkpoint_prerequisites(app)

    created = create_checkpoint(app, "e1-checkpoint-pass")
    replay = create_checkpoint(app, "e1-checkpoint-pass")
    assert created.status_code == 201, created.text
    assert replay.json() == created.json()
    assert created.json()["form_key"] == "english-checkpoint-e1-vocabulary-a-v1"
    assert created.json()["mastery_lesson_keys"] == ["e1-lesson-01", "e1-lesson-06"]
    session_id = created.json()["session_id"]

    current = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    encoded = json.dumps(question)
    assert question["stable_key"] == "ev-l5-006"
    assert question["exposure_pool"] == "module_checkpoint"
    assert "correct_key" not in encoded
    assert "correct_explanation" not in encoded
    assert "rationale" not in encoded

    hint = request(
        app,
        "POST",
        f"/api/v1/english/practice-sessions/{session_id}/questions/{question['stable_key']}/hint",
    )
    assert hint.status_code == 404

    answered = submit_checkpoint(
        app,
        session_id,
        question,
        {"1": "A", "2": "A", "3": "A", "4": "A", "5": "B"},
        "e1-checkpoint-pass-attempt",
    )
    replayed = submit_checkpoint(
        app,
        session_id,
        question,
        {"1": "A", "2": "A", "3": "A", "4": "A", "5": "B"},
        "e1-checkpoint-pass-attempt",
    )
    assert answered.status_code == 200, answered.text
    assert replayed.json() == answered.json()
    assert answered.json()["checkpoint_completed"] is True
    assert answered.json()["session"]["score"] == 0.8
    assert answered.json()["session"]["passed"] is True
    assert "parts" not in answered.json()

    progress = request(app, "GET", "/api/v1/english/progress").json()["lessons"]
    by_key = {item["lesson_key"]: item for item in progress}
    assert by_key["e1-lesson-01"]["state"] == "mastered"
    assert by_key["e1-lesson-06"]["state"] == "mastered"

    repeated = create_checkpoint(app, "e1-checkpoint-after-pass")
    assert repeated.status_code == 409
    assert repeated.json()["error"]["code"] == "english_checkpoint_already_passed"


def test_failed_e1_checkpoint_preserves_proficiency_and_retake_uses_form_b():
    app = application()
    seed_e1_checkpoint_prerequisites(app)

    first = create_checkpoint(app, "e1-checkpoint-fail")
    session_id = first.json()["session_id"]
    question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    failed = submit_checkpoint(
        app,
        session_id,
        question,
        {"1": "D", "2": "D", "3": "D", "4": "D", "5": "D"},
        "e1-checkpoint-failed-attempt",
    )
    assert failed.status_code == 200, failed.text
    assert failed.json()["session"]["score"] == 0
    assert failed.json()["session"]["passed"] is False
    progress = request(app, "GET", "/api/v1/english/progress").json()["lessons"]
    assert {item["state"] for item in progress} == {"proficient"}

    retake = create_checkpoint(app, "e1-checkpoint-retake")
    assert retake.status_code == 201, retake.text
    assert retake.json()["form_key"] == "english-checkpoint-e1-vocabulary-b-v1"
    retry_id = retake.json()["session_id"]
    retry_question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{retry_id}/next"
    ).json()["question"]
    assert retry_question["stable_key"] == "ev-l5-007"
    assert retry_question["stable_key"] != question["stable_key"]

    passed = submit_checkpoint(
        app,
        retry_id,
        retry_question,
        {str(position): "A" for position in range(1, 6)},
        "e1-checkpoint-retake-attempt",
    )
    assert passed.status_code == 200, passed.text
    assert passed.json()["session"]["score"] == 1
    assert passed.json()["session"]["passed"] is True


def test_e1_checkpoint_does_not_partially_complete_if_proficiency_changes():
    app = application()
    seed_e1_checkpoint_prerequisites(app)

    created = create_checkpoint(app, "e1-checkpoint-prerequisite-race")
    session_id = created.json()["session_id"]
    question = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()["question"]
    repository = app.state.english_learning_repository
    repository.lesson_progress[("english-development-learner", "e1-lesson-06")][
        "state"
    ] = "started"

    rejected = submit_checkpoint(
        app,
        session_id,
        question,
        {str(position): "A" for position in range(1, 6)},
        "e1-checkpoint-prerequisite-race-attempt",
    )

    assert rejected.status_code == 409, rejected.text
    assert rejected.json()["error"]["code"] == "english_checkpoint_prerequisites_changed"
    session = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}"
    ).json()
    assert session["status"] == "active"
    assert session["resolved_count"] == 0
    assert session["score"] is None
    pending = request(
        app, "GET", f"/api/v1/english/checkpoint-sessions/{session_id}/next"
    ).json()
    assert pending["question"]["stable_key"] == question["stable_key"]


def test_full_e1_1_journey_marks_deterministically_and_retries_failed_exit_ticket():
    app = application()
    created = create_session(app, "e1-guided")
    replay = create_session(app, "e1-guided")

    assert created.status_code == 201, created.text
    assert created.json() == replay.json()
    assert created.json()["exam_profile_key"] == "asean-english-sec1-id-reported-v1"
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
    assert retry_question["stable_key"] == "ev-l1-007"
    assert retry_question["stable_key"] != exit_ticket["stable_key"]

    corrected = submit(app, retry_id, retry_question, "A", "e1-corrected-exit")
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["correct"] is True
    assert corrected.json()["lesson_state"] == "proficient"

    after_retry = request(app, "GET", "/api/v1/english/progress").json()["lessons"][0]
    assert after_retry["state"] == "proficient"
    assert after_retry["retry_question_count"] == 0


def test_hint_use_is_recorded_and_prevents_exit_ticket_proficiency():
    app = application()
    created = create_session(app, "e1-hint-guided")
    session_id = created.json()["session_id"]
    for number, answer in enumerate(["B", "A", "A", "A", "A"], 1):
        question = request(
            app,
            "GET",
            f"/api/v1/english/practice-sessions/{session_id}/next",
        ).json()["question"]
        answered = submit(app, session_id, question, answer, f"e1-hint-lead-{number}")
        assert answered.status_code == 200, answered.text

    exit_ticket = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    ).json()["question"]
    hint = request(
        app,
        "POST",
        f"/api/v1/english/practice-sessions/{session_id}/questions/{exit_ticket['stable_key']}/hint",
    )
    assert hint.status_code == 200, hint.text
    assert hint.json()["hint_used"] is True

    answered = submit(app, session_id, exit_ticket, "A", "e1-hinted-exit")
    assert answered.status_code == 200, answered.text
    assert answered.json()["correct"] is True
    assert answered.json()["hint_used"] is True
    assert answered.json()["threshold_met"] is False
    assert answered.json()["retry_queued"] is True
    assert answered.json()["lesson_state"] == "practice_completed"


def test_e2_1_grammar_journey_marks_boundaries_and_agreement_deterministically():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e2-lesson-01")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E2.1"
    assert lesson.json()["outcome_code"] == "EG2.1"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"] == {
        "lesson_key": "e2-lesson-01",
        "question_count": 6,
        "available": False,
        "development_available": True,
        "retry_question_count": 0,
    }

    created = create_session(app, "e2-guided", lesson_key="e2-lesson-01")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 6
    session_id = created.json()["session_id"]
    answers: list[str | list[str]] = ["B", "A", "B", "C", ["B", "A"], "A"]
    expected_types = [
        "grammar_usage",
        "editing",
        "editing",
        "grammar_usage",
        "grammar_usage",
        "editing",
    ]

    for number, (answer, expected_type) in enumerate(zip(answers, expected_types, strict=True), 1):
        current = request(
            app,
            "GET",
            f"/api/v1/english/practice-sessions/{session_id}/next",
        )
        assert current.status_code == 200, current.text
        question = current.json()["question"]
        assert question["stable_key"] == f"eg-l1-{number:03d}"
        assert question["question_type"] == expected_type
        assert question["passage"] is None
        encoded = json.dumps(question)
        assert "correct_key" not in encoded
        assert "correct_keys" not in encoded
        assert "choice_rationales" not in encoded

        answered = submit(app, session_id, question, answer, f"e2-correct-{number}")
        assert answered.status_code == 200, answered.text
        assert answered.json()["correct"] is True

    completed = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"
    assert completed.json()["session"]["correct_count"] == 6


def test_grammar_error_categories_are_accepted_for_incorrect_e2_attempts():
    app = application()
    created = create_session(app, "e2-error", lesson_key="e2-lesson-01")
    session_id = created.json()["session_id"]
    question = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    ).json()["question"]
    wrong = submit(app, session_id, question, "A", "e2-wrong")

    assert wrong.status_code == 200, wrong.text
    classified = request(
        app,
        "POST",
        f"/api/v1/english/attempts/{wrong.json()['attempt_id']}/error-classification",
        json={"category": "clause_structure"},
    )
    assert classified.status_code == 200, classified.text
    assert classified.json()["category"] == "clause_structure"


def test_e3_1_banked_cloze_exposes_one_bank_and_marks_the_whole_passage():
    app = application()
    created = request(
        app,
        "POST",
        "/api/v1/english/practice-sessions",
        headers={"Idempotency-Key": "e3-guided"},
        json={"lesson_key": "e3-lesson-01", "mode": "guided_practice"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]
    current = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]

    assert question["stable_key"] == "eb-l1-001"
    assert question["question_type"] == "banked_cloze"
    assert len(question["word_bank"]) == 12
    assert len(question["parts"]) == 8
    assert all(not part["options"] for part in question["parts"])
    assert "{{1}}" in question["passage"]["paragraphs"][0]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "choice_rationales" not in encoded

    incomplete = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e3-incomplete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {"1": "C"},
        },
    )
    assert incomplete.status_code == 400
    assert incomplete.json()["error"]["code"] == "english_answers_incomplete"

    reused = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e3-reused"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {str(index): "C" for index in range(1, 9)},
        },
    )
    assert reused.status_code == 400
    assert reused.json()["error"]["code"] == "english_banked_cloze_word_reused"

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e3-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "C",
                "2": "E",
                "3": "D",
                "4": "L",
                "5": "A",
                "6": "I",
                "7": "G",
                "8": "F",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 8


def test_exit_ticket_uses_part_score_and_accepts_exactly_seventy_five_percent():
    app = application()
    created = create_session(app, "e3-threshold", lesson_key="e3-lesson-01")
    session_id = created.json()["session_id"]
    question = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    ).json()["question"]
    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e3-threshold-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": "H",
                "3": "D",
                "4": "L",
                "5": "A",
                "6": "I",
                "7": "G",
                "8": "F",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is False
    assert completed.json()["correct_parts"] == 6
    assert completed.json()["total_parts"] == 8
    assert completed.json()["score"] == 0.75
    assert completed.json()["threshold_met"] is True
    assert completed.json()["retry_queued"] is False
    assert completed.json()["lesson_state"] == "proficient"


def test_e4_1_open_cloze_accepts_only_reviewed_words_and_marks_as_one_group():
    app = application()
    created = request(
        app,
        "POST",
        "/api/v1/english/practice-sessions",
        headers={"Idempotency-Key": "e4-guided"},
        json={"lesson_key": "e4-lesson-01", "mode": "guided_practice"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]
    current = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]

    assert question["stable_key"] == "eo-l1-001"
    assert question["question_type"] == "open_cloze"
    assert question["word_bank"] is None
    assert len(question["parts"]) == 8
    assert [part["response_type"] for part in question["parts"]] == ["short_text"] * 8
    assert "{{1}}" in question["passage"]["paragraphs"][0]
    encoded = json.dumps(question)
    assert "canonical_answer" not in encoded
    assert "accepted_alternatives" not in encoded
    assert "rationale" not in encoded

    incomplete = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e4-incomplete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {"1": "an"},
        },
    )
    assert incomplete.status_code == 400
    assert incomplete.json()["error"]["code"] == "english_answers_incomplete"

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e4-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "AN",
                "2": "it",
                "3": "had",
                "4": "with",
                "5": "though",
                "6": "which",
                "7": "till",
                "8": "they",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 8


def test_e4_2_form_cloze_marks_tense_number_comparison_and_derivation_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e4-lesson-02")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E4.2"
    assert lesson.json()["outcome_code"] == "EO4.2"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e4-2-guided", lesson_key="e4-lesson-02")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]
    current = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]

    assert question["stable_key"] == "eo-l2-001"
    assert question["question_type"] == "open_cloze"
    assert question["word_bank"] is None
    assert len(question["parts"]) == 8
    assert "{{8}}" in question["passage"]["paragraphs"][3]
    encoded = json.dumps(question)
    assert "canonical_answer" not in encoded
    assert "accepted_alternatives" not in encoded
    assert "rationale" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e4-2-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "MET",
                "2": "planters",
                "3": "checks",
                "4": "drained",
                "5": "brighter",
                "6": "growth",
                "7": "measurements",
                "8": "themselves",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 8


def test_e4_3_lexical_cloze_marks_collocations_and_reviewed_equivalents_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e4-lesson-03")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E4.3"
    assert lesson.json()["outcome_code"] == "EO4.3"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e4-3-guided", lesson_key="e4-lesson-03")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]
    current = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]

    assert question["stable_key"] == "eo-l3-001"
    assert question["question_type"] == "open_cloze"
    assert question["word_bank"] is None
    assert len(question["parts"]) == 8
    assert "{{8}}" in question["passage"]["paragraphs"][2]
    encoded = json.dumps(question)
    assert "canonical_answer" not in encoded
    assert "accepted_alternatives" not in encoded
    assert "rationale" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e4-3-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "NOTICE",
                "2": "charge",
                "3": "eye",
                "4": "stop",
                "5": "brink",
                "6": "minds",
                "7": "part",
                "8": "difference",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 8


def test_e4_4_cohesion_cloze_marks_cross_sentence_links_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e4-lesson-04")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E4.4"
    assert lesson.json()["outcome_code"] == "EO4.4"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e4-4-guided", lesson_key="e4-lesson-04")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]
    current = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]

    assert question["stable_key"] == "eo-l4-001"
    assert question["question_type"] == "open_cloze"
    assert question["word_bank"] is None
    assert len(question["parts"]) == 8
    assert "{{8}}" in question["passage"]["paragraphs"][4]
    encoded = json.dumps(question)
    assert "canonical_answer" not in encoded
    assert "accepted_alternatives" not in encoded
    assert "rationale" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e4-4-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "FARID",
                "2": "that",
                "3": "yet",
                "4": "then",
                "5": "them",
                "6": "again",
                "7": "his",
                "8": "it",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 8


def test_e4_5_timed_checkpoint_is_learner_safe_and_marks_all_evidence_types():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e4-lesson-05")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E4.5"
    assert lesson.json()["outcome_code"] == "EO4.5"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e4-5-checkpoint", lesson_key="e4-lesson-05")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]
    current = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]

    assert question["stable_key"] == "eo-l5-001"
    assert question["question_type"] == "open_cloze"
    assert question["word_bank"] is None
    assert len(question["parts"]) == 8
    assert "{{8}}" in question["passage"]["paragraphs"][3]
    encoded = json.dumps(question)
    assert "canonical_answer" not in encoded
    assert "accepted_alternatives" not in encoded
    assert "rationale" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e4-5-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "INTO",
                "2": "yet",
                "3": "with",
                "4": "loose",
                "5": "than",
                "6": "again",
                "7": "unless",
                "8": "had",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 8


def test_e5_1_reading_group_is_learner_safe_and_marks_mixed_responses():
    app = application()
    created = request(
        app,
        "POST",
        "/api/v1/english/practice-sessions",
        headers={"Idempotency-Key": "e5-guided"},
        json={"lesson_key": "e5-lesson-01", "mode": "guided_practice"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "er-l1-001"
    assert question["question_type"] == "reading_comprehension"
    assert question["word_bank"] is None
    assert len(question["passage"]["paragraphs"]) == 4
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "single_choice",
        "short_text",
        "short_text",
        "single_choice",
        "multiple_response",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "canonical_answer" not in encoded
    assert "rationale" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e5-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": "B",
                "3": "Retain.",
                "4": "the rain garden absorbed the pooled water within a few hours.",
                "5": "A",
                "6": ["D", "A"],
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e5_2_reference_chain_group_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e5-lesson-02")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E5.2"
    assert lesson.json()["outcome_code"] == "ER5.2"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e5-2-guided", lesson_key="e5-lesson-02")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "er-l2-001"
    assert question["question_type"] == "reading_comprehension"
    assert question["word_bank"] is None
    assert len(question["passage"]["paragraphs"]) == 5
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "short_text",
        "short_text",
        "single_choice",
        "single_choice",
        "multiple_response",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "canonical_answer" not in encoded
    assert "accepted_alternatives" not in encoded
    assert "rationale" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e5-2-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "A",
                "2": "The coastal ecologist.",
                "3": (
                    "The club moved half the trays to a covered walkway and left the others "
                    "beside the sports shed."
                ),
                "4": "A",
                "5": "C",
                "6": ["D", "A"],
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e5_3_context_synonym_group_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e5-lesson-03")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E5.3"
    assert lesson.json()["outcome_code"] == "ER5.3"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e5-3-guided", lesson_key="e5-lesson-03")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(
        app,
        "GET",
        f"/api/v1/english/practice-sessions/{session_id}/next",
    )
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "er-l3-001"
    assert question["question_type"] == "reading_comprehension"
    assert question["word_bank"] is None
    assert len(question["passage"]["paragraphs"]) == 5
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "short_text",
        "single_choice",
        "single_choice",
        "short_text",
        "multiple_response",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "canonical_answer" not in encoded
    assert "accepted_alternatives" not in encoded
    assert "rationale" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e5-3-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": "Cryptic.",
                "3": "A",
                "4": "C",
                "5": "CORROBORATED",
                "6": ["D", "A"],
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e5_4_stated_evidence_group_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e5-lesson-04")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E5.4"
    assert lesson.json()["outcome_code"] == "ER5.4"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e5-4-guided", lesson_key="e5-lesson-04")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "er-l4-001"
    assert question["question_type"] == "reading_comprehension"
    assert question["word_bank"] is None
    assert len(question["passage"]["paragraphs"]) == 5
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "short_text",
        "single_choice",
        "multiple_response",
        "short_text",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "canonical_answer" not in encoded
    assert "accepted_alternatives" not in encoded
    assert "rationale" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e5-4-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "A",
                "2": "1 metre above ground.",
                "3": "C",
                "4": ["D", "A"],
                "5": "Shade sails at the main gate.",
                "6": "A",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e5_5_bounded_inference_group_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e5-lesson-05")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E5.5"
    assert lesson.json()["outcome_code"] == "ER5.5"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e5-5-guided", lesson_key="e5-lesson-05")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "er-l5-001"
    assert question["question_type"] == "reading_comprehension"
    assert question["word_bank"] is None
    assert len(question["passage"]["paragraphs"]) == 5
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e5-5-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": "C",
                "3": "A",
                "4": ["D", "A"],
                "5": "C",
                "6": "A",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e5_6_purpose_tone_and_main_idea_group_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e5-lesson-06")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E5.6"
    assert lesson.json()["outcome_code"] == "ER5.6"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e5-6-guided", lesson_key="e5-lesson-06")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "er-l5-002"
    assert question["question_type"] == "reading_comprehension"
    assert question["word_bank"] is None
    assert len(question["passage"]["paragraphs"]) == 5
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e5-6-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "A",
                "2": "C",
                "3": "B",
                "4": "B",
                "5": ["C", "A"],
                "6": "D",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e5_7_two_passage_group_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e5-lesson-07")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E5.7"
    assert lesson.json()["outcome_code"] == "ER5.7"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e5-7-guided", lesson_key="e5-lesson-07")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "er-l5-003"
    assert question["question_type"] == "reading_comprehension"
    assert question["word_bank"] is None
    assert len(question["passage"]["paragraphs"]) == 7
    assert question["passage"]["paragraphs"][0].startswith("PASSAGE A")
    assert question["passage"]["paragraphs"][4].startswith("PASSAGE B")
    assert [part["response_type"] for part in question["parts"]] == ["single_choice"] * 8
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e5-7-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "A",
                "2": "B",
                "3": "B",
                "4": "A",
                "5": "B",
                "6": "B",
                "7": "A",
                "8": "C",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 8


def test_e6_1_composition_task_analysis_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e6-lesson-01")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E6.1"
    assert lesson.json()["outcome_code"] == "EW6.1"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e6-1-guided", lesson_key="e6-lesson-01")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l1-001"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e6-1-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": "C",
                "3": "B",
                "4": ["D", "A", "C"],
                "5": "D",
                "6": "B",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e6_2_idea_generation_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e6-lesson-02")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E6.2"
    assert lesson.json()["outcome_code"] == "EW6.2"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e6-2-guided", lesson_key="e6-lesson-02")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l2-001"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e6-2-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": "B",
                "3": ["C", "A", "B"],
                "4": "C",
                "5": "C",
                "6": "B",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e6_3_choose_and_order_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e6-lesson-03")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E6.3"
    assert lesson.json()["outcome_code"] == "EW6.3"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e6-3-guided", lesson_key="e6-lesson-03")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l3-001"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e6-3-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": ["C", "A"],
                "2": "A",
                "3": "C",
                "4": "B",
                "5": "B",
                "6": "A",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e6_4_controlling_focus_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e6-lesson-04")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E6.4"
    assert lesson.json()["outcome_code"] == "EW6.4"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e6-4-guided", lesson_key="e6-lesson-04")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l4-001"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e6-4-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": ["C", "A", "B"],
                "3": "A",
                "4": "A",
                "5": "C",
                "6": "A",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e6_5_five_minute_plan_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e6-lesson-05")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E6.5"
    assert lesson.json()["outcome_code"] == "EW6.5"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e6-5-guided", lesson_key="e6-lesson-05")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l5-001"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e6-5-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": ["C", "A", "B"],
                "3": "A",
                "4": "C",
                "5": "A",
                "6": "A",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e7_1_paragraph_purpose_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e7-lesson-01")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E7.1"
    assert lesson.json()["outcome_code"] == "EW7.1"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e7-1-guided", lesson_key="e7-lesson-01")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l1-002"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e7-1-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": ["C", "A", "B"],
                "3": "C",
                "4": "B",
                "5": "C",
                "6": "A",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e7_2_develop_with_specifics_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e7-lesson-02")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E7.2"
    assert lesson.json()["outcome_code"] == "EW7.2"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e7-2-guided", lesson_key="e7-lesson-02")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l2-002"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e7-2-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "C",
                "2": ["C", "A", "B"],
                "3": "B",
                "4": "A",
                "5": "C",
                "6": "A",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e7_3_cohesion_without_formula_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e7-lesson-03")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E7.3"
    assert lesson.json()["outcome_code"] == "EW7.3"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e7-3-guided", lesson_key="e7-lesson-03")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l3-002"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e7-3-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": ["C", "A", "B"],
                "3": "C",
                "4": "B",
                "5": "A",
                "6": "A",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e7_4_introductions_and_endings_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e7-lesson-04")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E7.4"
    assert lesson.json()["outcome_code"] == "EW7.4"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e7-4-guided", lesson_key="e7-lesson-04")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l4-002"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e7-4-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "C",
                "2": ["C", "A", "B"],
                "3": "D",
                "4": "B",
                "5": "D",
                "6": "B",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e7_5_read_like_a_writer_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e7-lesson-05")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E7.5"
    assert lesson.json()["outcome_code"] == "EW7.5"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e7-5-guided", lesson_key="e7-lesson-05")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l5-002"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e7-5-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": ["C", "A", "B"],
                "3": "D",
                "4": "B",
                "5": "A",
                "6": "C",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e8_1_precise_vocabulary_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e8-lesson-01")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E8.1"
    assert lesson.json()["outcome_code"] == "EW8.1"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e8-1-guided", lesson_key="e8-lesson-01")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l1-003"
    assert question["question_type"] == "editing"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e8-1-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": ["E", "A", "C"],
                "2": "B",
                "3": "C",
                "4": "A",
                "5": "B",
                "6": "C",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e8_2_sentence_variety_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e8-lesson-02")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E8.2"
    assert lesson.json()["outcome_code"] == "EW8.2"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e8-2-guided", lesson_key="e8-lesson-02")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l2-003"
    assert question["question_type"] == "editing"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e8-2-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "A",
                "2": "B",
                "3": "C",
                "4": "B",
                "5": ["F", "A", "D"],
                "6": "B",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e8_3_show_relationships_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e8-lesson-03")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E8.3"
    assert lesson.json()["outcome_code"] == "EW8.3"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e8-3-guided", lesson_key="e8-lesson-03")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l3-003"
    assert question["question_type"] == "editing"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e8-3-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "A",
                "2": "B",
                "3": "C",
                "4": ["C", "A", "B"],
                "5": "B",
                "6": "B",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e8_4_edit_by_priority_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e8-lesson-04")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E8.4"
    assert lesson.json()["outcome_code"] == "EW8.4"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e8-4-guided", lesson_key="e8-lesson-04")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l4-003"
    assert question["question_type"] == "editing"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e8-4-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "A",
                "2": "B",
                "3": "B",
                "4": "B",
                "5": ["D", "C"],
                "6": "B",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e8_5_personal_error_log_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e8-lesson-05")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E8.5"
    assert lesson.json()["outcome_code"] == "EW8.5"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e8-5-guided", lesson_key="e8-lesson-05")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l5-003"
    assert question["question_type"] == "editing"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e8-5-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": ["E", "A", "C"],
                "2": "B",
                "3": "A",
                "4": "B",
                "5": "B",
                "6": "B",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6


def test_e9_1_reflective_writing_is_learner_safe_and_marks_exactly():
    app = application()
    lesson = request(app, "GET", "/api/v1/english/lessons/e9-lesson-01")

    assert lesson.status_code == 200, lesson.text
    assert lesson.json()["lesson_code"] == "E9.1"
    assert lesson.json()["outcome_code"] == "EW9.1"
    assert len(lesson.json()["sections"]) == 7
    assert lesson.json()["practice"]["question_count"] == 1

    created = create_session(app, "e9-1-guided", lesson_key="e9-lesson-01")
    assert created.status_code == 201, created.text
    assert created.json()["question_count"] == 1
    session_id = created.json()["session_id"]

    current = request(app, "GET", f"/api/v1/english/practice-sessions/{session_id}/next")
    assert current.status_code == 200, current.text
    question = current.json()["question"]
    assert question["stable_key"] == "ex-l1-004"
    assert question["question_type"] == "composition_planning"
    assert question["passage"] is None
    assert question["word_bank"] is None
    assert [part["response_type"] for part in question["parts"]] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    encoded = json.dumps(question)
    assert "correct_key" not in encoded
    assert "correct_keys" not in encoded
    assert "choice_rationales" not in encoded
    assert "correct_explanation" not in encoded

    completed = request(
        app,
        "POST",
        "/api/v1/english/attempts",
        headers={"Idempotency-Key": "e9-1-complete"},
        json={
            "session_id": session_id,
            "question_key": question["stable_key"],
            "question_revision": question["revision"],
            "answers": {
                "1": "B",
                "2": ["C", "A", "B"],
                "3": "C",
                "4": "B",
                "5": "C",
                "6": "B",
            },
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["correct"] is True
    assert completed.json()["lesson_state"] == "proficient"
    assert [part["correct"] for part in completed.json()["parts"]] == [True] * 6
