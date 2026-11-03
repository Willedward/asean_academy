"""A real invited learner holds both Mathematics courses on disposable PostgreSQL."""

from __future__ import annotations

import asyncio
import os
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
import pytest
from question_bank.practice import solution_for

from learning_api.config import Settings
from learning_api.course_catalogue import CourseCatalogue
from learning_api.identity import AuthenticatedLearner, StaticTokenVerifier
from learning_api.identity_repository import invitation_digest
from learning_api.main import create_app

ROOT = Path(__file__).resolve().parents[3]
CATALOGUE = CourseCatalogue(ROOT, allow_drafts=True)
QUESTIONS = {question.stable_key: question for question in CATALOGUE.all_questions}
SEC1 = "g3-sec1-math"
SEC2 = "g3-sec2-math"


def _database_url() -> str:
    value = os.environ.get("TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set TEST_DATABASE_URL to a migrated, imported disposable database")
    return value


def _invite(connection, email: str, course_key: str) -> str:
    code = secrets.token_urlsafe(32)
    version = connection.execute(
        """
        select versions.id
        from course_versions versions
        join courses on courses.id = versions.course_id
        where courses.course_key = %s and versions.is_current
        """,
        (course_key,),
    ).fetchone()
    assert version is not None, f"Import {course_key} before running PostgreSQL tests"
    connection.execute(
        """
        insert into beta_invitations (token_sha256, email, course_version_id, expires_at)
        values (%s, %s, %s, %s)
        """,
        (invitation_digest(code), email, version[0], datetime.now(UTC) + timedelta(hours=1)),
    )
    return code


def _application(database_url: str, learners: dict[str, tuple[str, str]]):
    return create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=ROOT,
            allow_draft_content=True,
            development_learner_id=None,
            database_url=database_url,
        ),
        token_verifier=StaticTokenVerifier(
            {
                token: AuthenticatedLearner(learner_id, "authenticated", email)
                for token, (learner_id, email) in learners.items()
            }
        ),
    )


def _request(app, method: str, path: str, token: str, **kwargs):
    async def send():
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {token}"
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, headers=headers, **kwargs)

    return asyncio.run(send())


def _accept(app, token: str, code: str):
    accepted = _request(
        app,
        "POST",
        "/api/v1/onboarding/accept-invitation",
        token,
        json={"invitation_code": code, "display_name": "Two Course Learner"},
    )
    assert accepted.status_code == 200, accepted.text
    return accepted.json()


def _complete_session(app, token: str, session_id: str, prefix: str) -> None:
    attempt = 0
    while True:
        current = _request(app, "GET", f"/api/v1/practice-sessions/{session_id}/next", token)
        assert current.status_code == 200, current.text
        if current.json()["status"] == "completed":
            return
        question = current.json()["question"]
        attempt += 1
        submitted = _request(
            app,
            "POST",
            "/api/v1/attempts",
            token,
            headers={"Idempotency-Key": f"{prefix}-{attempt}"},
            json={
                "session_id": session_id,
                "question_key": question["stable_key"],
                "question_revision": question["revision"],
                "answers": {
                    str(part["position"]): part["canonical_answer"]
                    for part in solution_for(QUESTIONS[question["stable_key"]])["parts"]
                },
            },
        )
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["correct"] is True


def _create_session(app, token: str, key: str, **payload):
    return _request(
        app,
        "POST",
        "/api/v1/practice-sessions",
        token,
        headers={"Idempotency-Key": key},
        json=payload,
    )


@pytest.mark.postgres
def test_both_courses_import_and_units_may_have_several_reserve_pools():
    with psycopg.connect(_database_url()) as connection:
        rows = connection.execute(
            """
            select pools.pool_type::text, count(*)
            from unit_checkpoint_pools pools
            join unit_versions units on units.id = pools.unit_version_id
            join course_units on course_units.id = units.unit_id
            join course_versions versions on versions.id = units.course_version_id
            where course_units.unit_key = 'g3-sec2-g5' and versions.is_current
            group by pools.pool_type
            """
        ).fetchall()
        assert dict(rows) == {"unit_checkpoint": 1, "adaptive_reserve": 2}
        with pytest.raises(psycopg.errors.UniqueViolation):
            with connection.transaction():
                connection.execute(
                    """
                    insert into unit_checkpoint_pools (
                        unit_version_id, pool_key, pool_type, expected_question_count
                    )
                    select unit_version_id, 'second-checkpoint', pool_type, 1
                    from unit_checkpoint_pools
                    where pool_type = 'unit_checkpoint'
                    limit 1
                    """
                )


@pytest.mark.postgres
def test_learner_with_two_enrolments_practises_and_progresses_in_both():
    database_url = _database_url()
    learner_id, email = str(uuid4()), f"two-course-{uuid4()}@example.test"
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "insert into auth.users (id, email) values (%s, %s)", (learner_id, email)
        )
        sec1_code = _invite(connection, email, SEC1)
        sec2_code = _invite(connection, email, SEC2)
    app = _application(database_url, {"learner": (learner_id, email)})

    first = _accept(app, "learner", sec1_code)
    assert [item["course_key"] for item in first["enrolments"]] == [SEC1]
    # Before the second acceptance, Secondary 2 is refused and progress covers one course.
    refused = _request(app, "POST", "/api/v1/lessons/g5-lesson-06/start", "learner")
    assert refused.status_code == 409
    assert refused.json()["error"]["code"] == "course_revision_update_required"
    refused_session = _create_session(app, "learner", "refused", lesson_key="g5-lesson-06")
    assert refused_session.status_code == 409
    single = _request(app, "GET", "/api/v1/progress", "learner").json()
    assert [course["course_key"] for course in single["courses"]] == [SEC1]
    assert len(single["lessons"]) == 52

    second = _accept(app, "learner", sec2_code)
    assert sorted(item["course_key"] for item in second["enrolments"]) == [SEC1, SEC2]
    assert all(item["status"] == "active" for item in second["enrolments"])
    # Replaying an accepted invitation stays idempotent and adds nothing.
    assert len(_accept(app, "learner", sec2_code)["enrolments"]) == 2

    both = _request(app, "GET", "/api/v1/progress", "learner").json()
    assert [course["course_key"] for course in both["courses"]] == [SEC1, SEC2]
    assert len(both["lessons"]) == 87
    assert len(both["checkpoints"]) == 19

    # Secondary 1 beyond the first bank uses its own bank, not the first course question's.
    sec1_session = _create_session(
        app, "learner", "sec1-n2", lesson_key="n2-lesson-01", question_count=1
    )
    assert sec1_session.status_code == 201, sec1_session.text
    _complete_session(app, "learner", sec1_session.json()["session_id"], "sec1-n2")

    started = _request(app, "POST", "/api/v1/lessons/g5-lesson-06/start", "learner")
    assert started.status_code == 200, started.text
    assert started.json()["course_key"] == SEC2

    practice = _create_session(app, "learner", "sec2-g5", lesson_key="g5-lesson-06")
    assert practice.status_code == 201, practice.text
    _complete_session(app, "learner", practice.json()["session_id"], "sec2-g5")

    with psycopg.connect(database_url) as connection:
        scope, bank_key = connection.execute(
            """
            select sessions.scope, banks.bank_key
            from practice_sessions sessions
            join math_question_banks banks on banks.id = sessions.bank_id
            where sessions.id = %s
            """,
            (practice.json()["session_id"],),
        ).fetchone()
    assert scope["course_key"] == SEC2
    assert scope["course_revision"] == CATALOGUE.reports[SEC2].course.revision
    assert bank_key == "g3-sec2-g5-v1"

    checkpoint = _create_session(
        app, "learner", "sec2-g5-checkpoint", unit_key="g3-sec2-g5", mode="checkpoint"
    )
    assert checkpoint.status_code == 201, checkpoint.text
    _complete_session(app, "learner", checkpoint.json()["session_id"], "sec2-g5-checkpoint")

    progress = _request(app, "GET", "/api/v1/progress", "learner").json()
    lessons = {item["lesson_key"]: item for item in progress["lessons"]}
    assert lessons["g5-lesson-06"]["state"] == "mastered"
    assert lessons["g5-lesson-06"]["course_key"] == SEC2
    assert lessons["n2-lesson-01"]["course_key"] == SEC1
    assert lessons["n2-lesson-01"]["resolved_count"] == 1
    assert lessons["n2-lesson-01"]["state"] != "mastered"
    checkpoints = {item["unit_key"]: item for item in progress["checkpoints"]}
    assert checkpoints["g3-sec2-g5"]["state"] == "passed"
    assert checkpoints["g3-sec1-g5"]["state"] == "locked"

    for course_key, unit_key, lesson_key, state in (
        (SEC1, "g3-sec1-n2", "n2-lesson-01", lessons["n2-lesson-01"]["state"]),
        (SEC2, "g3-sec2-g5", "g5-lesson-06", "mastered"),
    ):
        course_map = _request(app, "GET", f"/api/v1/courses/{course_key}/map", "learner").json()
        unit = next(item for item in course_map["units"] if item["stable_key"] == unit_key)
        lesson = next(item for item in unit["lessons"] if item["stable_key"] == lesson_key)
        assert lesson["progress_state"] == state

    home = _request(app, "GET", "/api/v1/learning-home", "learner").json()
    assert [course["course_key"] for course in home["courses"]] == [SEC1, SEC2]
