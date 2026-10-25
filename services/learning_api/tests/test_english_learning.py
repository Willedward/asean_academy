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
