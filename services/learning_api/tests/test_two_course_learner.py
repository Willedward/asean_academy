"""One local learner uses Secondary 1 and Secondary 2 Mathematics together."""

import asyncio
from pathlib import Path

import httpx
import pytest
from question_bank.practice import solution_for

from learning_api.config import Settings
from learning_api.course_catalogue import CourseCatalogue
from learning_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CATALOGUE = CourseCatalogue(REPOSITORY_ROOT, allow_drafts=True)
QUESTIONS = {question.stable_key: question for question in CATALOGUE.all_questions}
SEC1 = "g3-sec1-math"
SEC2 = "g3-sec2-math"


def application(tmp_path: Path):
    return create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=True,
            practice_database=tmp_path / "practice.sqlite3",
            development_learner_id="development-learner",
        )
    )


def request(app, method: str, path: str, **kwargs):
    async def send():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def answers(question_key: str) -> dict[str, str]:
    return {
        str(part["position"]): part["canonical_answer"]
        for part in solution_for(QUESTIONS[question_key])["parts"]
    }


def create_session(app, key: str, **payload):
    return request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        headers={"Idempotency-Key": key},
        json=payload,
    )


def answer_every_question(app, session_id: str, prefix: str) -> None:
    attempt = 0
    while True:
        current = request(app, "GET", f"/api/v1/practice-sessions/{session_id}/next")
        assert current.status_code == 200, current.text
        if current.json()["status"] == "completed":
            return
        question = current.json()["question"]
        attempt += 1
        submitted = request(
            app,
            "POST",
            "/api/v1/attempts",
            headers={"Idempotency-Key": f"{prefix}-{attempt}"},
            json={
                "session_id": session_id,
                "question_key": question["stable_key"],
                "question_revision": question["revision"],
                "answers": answers(question["stable_key"]),
            },
        )
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["correct"] is True


def lesson_progress(app, lesson_key: str) -> dict:
    lessons = request(app, "GET", "/api/v1/progress").json()["lessons"]
    return next(item for item in lessons if item["lesson_key"] == lesson_key)


def test_catalogue_resolves_every_lesson_unit_and_question_to_its_own_course():
    assert set(CATALOGUE.reports) == {SEC1, SEC2}
    assert len(CATALOGUE.all_questions) == len(QUESTIONS) == 1976
    assert CATALOGUE.report_for_lesson("n2-lesson-01").course.stable_key == SEC1
    assert CATALOGUE.report_for_lesson("n2-lesson-04").course.stable_key == SEC2
    assert CATALOGUE.report_for_unit("g3-sec1-n2").course.stable_key == SEC1
    assert CATALOGUE.report_for_unit("g3-sec2-n2").course.stable_key == SEC2
    assert CATALOGUE.report_for_lesson("missing-lesson") is None
    assert CATALOGUE.report_for_unit("missing-unit") is None
    # The release gate stays single-course until its own two-course work.
    assert len(CATALOGUE.questions) == 1040


def test_all_87_lesson_keys_pass_the_progress_path_patterns(tmp_path):
    app = application(tmp_path)
    lessons = [
        lesson for report in CATALOGUE.reports.values() for lesson in report.lessons
    ]
    assert len(lessons) == 87
    for lesson in lessons:
        section = request(app, "GET", f"/api/v1/lessons/{lesson.stable_key}/section-progress")
        started = request(app, "POST", f"/api/v1/lessons/{lesson.stable_key}/start")
        expected = 409 if lesson.prerequisite_lessons else 200
        assert section.status_code == expected, (lesson.stable_key, section.text)
        assert started.status_code == expected, (lesson.stable_key, started.text)


def test_sec2_lesson_start_and_sections_record_progress(tmp_path):
    app = application(tmp_path)
    started = request(app, "POST", "/api/v1/lessons/g2-lesson-01/start")
    assert started.status_code == 200, started.text
    assert started.json()["course_key"] == SEC2
    assert started.json()["state"] == "in_progress"

    section = next(
        item
        for item in request(app, "GET", "/api/v1/lessons/g2-lesson-01").json()["sections"]
        if item["type"] != "active_recall"
    )
    completed = request(
        app,
        "PUT",
        f"/api/v1/lessons/g2-lesson-01/sections/{section['stable_key']}/completion",
        json={"completed": True},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["completed_section_keys"] == [section["stable_key"]]


def test_sec2_practice_records_proficiency_against_the_owning_course(tmp_path):
    app = application(tmp_path)
    created = create_session(app, "sec2-practice", lesson_key="g5-lesson-06")
    assert created.status_code == 201, created.text
    session_id = created.json()["session_id"]
    assert created.json()["question_count"] == 20

    answer_every_question(app, session_id, "sec2-practice-answer")

    lesson = lesson_progress(app, "g5-lesson-06")
    assert lesson["course_key"] == SEC2
    assert lesson["state"] == "proficient"
    assert lesson["resolved_count"] == 20
    # Secondary 1 evidence is untouched, including its same-coded G5 unit.
    assert lesson_progress(app, "g5-lesson-01")["state"] == "not_started"


def test_sec2_checkpoint_is_locked_then_records_mastery(tmp_path):
    app = application(tmp_path)
    locked = create_session(app, "g5-locked", unit_key="g3-sec2-g5", mode="checkpoint")
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "checkpoint_locked"

    created = create_session(app, "g5-practice", lesson_key="g5-lesson-06")
    answer_every_question(app, created.json()["session_id"], "g5-practice-answer")

    course_map = request(app, "GET", f"/api/v1/courses/{SEC2}/map").json()
    unit = next(item for item in course_map["units"] if item["stable_key"] == "g3-sec2-g5")
    assert unit["checkpoint_available"] is True
    assert unit["lessons"][0]["progress_state"] == "proficient"

    checkpoint = create_session(app, "g5-checkpoint", unit_key="g3-sec2-g5", mode="checkpoint")
    assert checkpoint.status_code == 201, checkpoint.text
    assert checkpoint.json()["question_count"] == unit["checkpoint_question_count"]
    answer_every_question(app, checkpoint.json()["session_id"], "g5-checkpoint-answer")

    progress = request(app, "GET", "/api/v1/progress").json()
    status = next(item for item in progress["checkpoints"] if item["unit_key"] == "g3-sec2-g5")
    assert status["course_key"] == SEC2
    assert status["state"] == "passed"
    assert lesson_progress(app, "g5-lesson-06")["state"] == "mastered"
    sec1_g5 = next(item for item in progress["checkpoints"] if item["unit_key"] == "g3-sec1-g5")
    assert sec1_g5["state"] == "locked"


def test_progress_and_home_cover_both_courses_in_level_order(tmp_path):
    app = application(tmp_path)
    progress = request(app, "GET", "/api/v1/progress").json()
    assert progress["course_key"] == SEC1
    assert [course["course_key"] for course in progress["courses"]] == [SEC1, SEC2]
    assert [course["course_revision"] for course in progress["courses"]] == [
        CATALOGUE.reports[SEC1].course.revision,
        CATALOGUE.reports[SEC2].course.revision,
    ]
    assert len(progress["lessons"]) == 87
    assert len(progress["checkpoints"]) == 19
    course_order = [lesson["course_key"] for lesson in progress["lessons"]]
    assert course_order == sorted(course_order)

    created = create_session(app, "home-sec2", lesson_key="g2-lesson-01")
    assert created.status_code == 201, created.text
    home = request(app, "GET", "/api/v1/learning-home").json()
    assert [course["course_key"] for course in home["courses"]] == [SEC1, SEC2]
    assert home["next_action"]["type"] == "resume_practice"
    assert home["next_action"]["lesson_key"] == "g2-lesson-01"
    assert home["next_action"]["session_id"] == created.json()["session_id"]


@pytest.mark.parametrize("course_key", [SEC1, SEC2])
def test_course_map_applies_progress_for_each_course(tmp_path, course_key):
    app = application(tmp_path)
    report = CATALOGUE.reports[course_key]
    lesson_key = report.course.units[0].lessons[0].stable_key
    assert request(app, "POST", f"/api/v1/lessons/{lesson_key}/start").status_code == 200

    course_map = request(app, "GET", f"/api/v1/courses/{course_key}/map").json()
    first = course_map["units"][0]["lessons"][0]
    assert first["stable_key"] == lesson_key
    assert first["progress_state"] == "in_progress"
