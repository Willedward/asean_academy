from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import httpx

from learning_api.config import Settings
from learning_api.dependencies import (
    admin_analytics_repository,
    beta_operations_repository,
)
from learning_api.identity import AuthenticatedLearner, StaticTokenVerifier
from learning_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTENT_ADMIN_ID = "00000000-0000-4000-8000-000000000020"
ACADEMIC_ADMIN_ID = "00000000-0000-4000-8000-000000000021"
STUDENT_ID = "00000000-0000-4000-8000-000000000022"
NOW = datetime.now(UTC)


class FakeRoleRepository:
    def role_for(self, learner_id: str) -> str:
        return {
            CONTENT_ADMIN_ID: "content_admin",
            ACADEMIC_ADMIN_ID: "academic_admin",
        }.get(learner_id, "student")


class FakeAdminAnalyticsRepository:
    def __init__(self):
        self.changed_role = None

    @staticmethod
    def student():
        return {
            "learner_id": UUID(STUDENT_ID),
            "email": "student@example.test",
            "display_name": "Student",
            "target_track": "g3-sec1-math",
            "enrolment_status": "active",
            "course_keys": ["g3-sec1-math"],
            "enrolled_at": NOW,
            "last_activity_at": NOW,
            "lessons_started": 2,
            "lessons_proficient": 1,
            "lessons_mastered": 0,
            "practice_sessions": 3,
            "attempts": 8,
            "correct_attempts": 5,
            "accuracy_percentage": 62.5,
            "retry_question_count": 2,
        }

    def list_students(self, *, search, limit, offset):
        assert search in {None, "Student"}
        return {
            "students": [self.student()],
            "total": 1,
            "limit": limit,
            "offset": offset,
        }

    def student_detail(self, learner_id):
        assert learner_id == UUID(STUDENT_ID)
        return {
            "student": self.student(),
            "lessons": [
                {
                    "lesson_key": "n1-primes",
                    "lesson_title": "Primes and prime factorisation",
                    "state": "proficient",
                    "question_count": 3,
                    "resolved_count": 3,
                    "correct_count": 3,
                    "gave_up_count": 0,
                    "eventual_correct_percentage": 100,
                    "checkpoint_passed": False,
                    "started_at": NOW,
                    "updated_at": NOW,
                    "completed_at": NOW,
                }
            ],
            "difficulty_performance": [
                {
                    "difficulty": 1,
                    "attempts": 5,
                    "correct_attempts": 4,
                    "accuracy_percentage": 80,
                }
            ],
        }

    def overview(self):
        return {
            "total_students": 12,
            "active_enrolments": 9,
            "active_students_last_7_days": 6,
            "active_students_last_30_days": 9,
            "lessons_started": 25,
            "lessons_mastered": 8,
            "practice_sessions": 31,
            "completed_practice_sessions": 27,
            "attempts": 120,
            "correct_attempts": 84,
            "overall_accuracy_percentage": 70,
            "hint_reveals": 30,
            "give_ups": 4,
            "students_with_retries": 5,
            "checkpoint_attempts": 3,
            "checkpoint_passes": 2,
        }

    def question_analytics(self, *, difficulty, outcome, limit, offset):
        assert difficulty in {None, 1}
        assert outcome is None
        return {
            "questions": [
                {
                    "question_key": "n1-l1-01",
                    "title": "Prime recognition",
                    "difficulty": 1,
                    "outcome_code": "1.1",
                    "attempt_count": 10,
                    "unique_students": 5,
                    "correct_attempts": 7,
                    "accuracy_percentage": 70,
                    "hint_reveals": 3,
                    "give_up_count": 1,
                    "queued_for_retry_students": 2,
                }
            ],
            "total": 1,
            "limit": limit,
            "offset": offset,
        }

    def change_role(self, administrator, learner_id, role, request_id):
        assert administrator.learner_id == ACADEMIC_ADMIN_ID
        assert request_id
        self.changed_role = (learner_id, role)
        return {
            "learner_id": learner_id,
            "email": "student@example.test",
            "display_name": "Student",
            "role": role,
            "updated_at": NOW,
        }


def application():
    analytics = FakeAdminAnalyticsRepository()
    app = create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=REPOSITORY_ROOT,
            allow_draft_content=True,
            development_learner_id=None,
        ),
        token_verifier=StaticTokenVerifier(
            {
                "content-admin-token": AuthenticatedLearner(
                    CONTENT_ADMIN_ID, "authenticated", "content@example.test"
                ),
                "academic-admin-token": AuthenticatedLearner(
                    ACADEMIC_ADMIN_ID, "authenticated", "academic@example.test"
                ),
                "student-token": AuthenticatedLearner(
                    STUDENT_ID, "authenticated", "student@example.test"
                ),
            }
        ),
    )
    app.dependency_overrides[beta_operations_repository] = FakeRoleRepository
    app.dependency_overrides[admin_analytics_repository] = lambda: analytics
    return app, analytics


def request(app, method: str, path: str, token: str, **kwargs):
    async def send():
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {token}"
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, headers=headers, **kwargs)

    return asyncio.run(send())


def test_student_cannot_access_admin_analytics():
    app, _ = application()
    response = request(app, "GET", "/api/v1/admin/students", "student-token")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "administrator_required"


def test_content_admin_can_read_student_and_aggregate_analytics():
    app, _ = application()
    students = request(
        app,
        "GET",
        "/api/v1/admin/students?search=Student",
        "content-admin-token",
    )
    detail = request(
        app,
        "GET",
        f"/api/v1/admin/students/{STUDENT_ID}",
        "content-admin-token",
    )
    overview = request(
        app,
        "GET",
        "/api/v1/admin/analytics/overview",
        "content-admin-token",
    )
    questions = request(
        app,
        "GET",
        "/api/v1/admin/analytics/questions?difficulty=1",
        "content-admin-token",
    )

    assert students.status_code == 200
    assert students.json()["students"][0]["email"] == "student@example.test"
    assert detail.status_code == 200
    assert detail.json()["lessons"][0]["state"] == "proficient"
    assert overview.status_code == 200
    assert overview.json()["overall_accuracy_percentage"] == 70
    assert questions.status_code == 200
    assert questions.json()["questions"][0]["question_key"] == "n1-l1-01"
    assert "answers" not in questions.text


def test_only_academic_admin_can_change_roles():
    app, analytics = application()
    denied = request(
        app,
        "PATCH",
        f"/api/v1/admin/users/{STUDENT_ID}/role",
        "content-admin-token",
        json={"role": "content_admin"},
    )
    allowed = request(
        app,
        "PATCH",
        f"/api/v1/admin/users/{STUDENT_ID}/role",
        "academic-admin-token",
        headers={"X-Request-ID": "role-change-test"},
        json={"role": "content_admin"},
    )

    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "academic_administrator_required"
    assert allowed.status_code == 200
    assert allowed.json()["role"] == "content_admin"
    assert analytics.changed_role == (UUID(STUDENT_ID), "content_admin")


def test_question_analytics_filters_are_bounded():
    app, _ = application()
    response = request(
        app,
        "GET",
        "/api/v1/admin/analytics/questions?difficulty=4",
        "academic-admin-token",
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
