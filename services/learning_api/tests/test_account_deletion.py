from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx

from learning_api.config import Settings
from learning_api.dependencies import (
    account_deletion_repository,
    beta_operations_repository,
)
from learning_api.identity import AuthenticatedLearner, StaticTokenVerifier
from learning_api.main import create_app

ROOT = Path(__file__).resolve().parents[3]
ACADEMIC_ID = "00000000-0000-4000-8000-000000000091"
CONTENT_ID = "00000000-0000-4000-8000-000000000092"
STUDENT_ID = UUID("00000000-0000-4000-8000-000000000093")


class Roles:
    def role_for(self, learner_id: str) -> str:
        return {
            ACADEMIC_ID: "academic_admin",
            CONTENT_ID: "content_admin",
            str(STUDENT_ID): "student",
        }[learner_id]


class Deletions:
    def __init__(self):
        self.executed = False

    def preview(self, learner_id):
        assert learner_id == STUDENT_ID
        return {
            "learner_id": learner_id,
            "email": "student@example.test",
            "display_name": "Student",
            "counts": {"attempts": 4, "question_reports": 1},
            "retained_records": ["pseudonymous deletion record"],
            "preview_token": "x" * 80,
            "expires_at": datetime.now(UTC) + timedelta(minutes=15),
            "confirmation_value": "student@example.test",
        }

    def execute(
        self,
        administrator,
        learner_id,
        *,
        preview_token,
        confirmation_email,
        reason,
        request_id,
    ):
        assert administrator.learner_id == ACADEMIC_ID
        assert learner_id == STUDENT_ID
        assert preview_token == "x" * 80
        assert confirmation_email == "student@example.test"
        assert len(reason) >= 10
        assert request_id
        self.executed = True
        return {
            "deleted": True,
            "target_reference": "a" * 64,
            "completed_at": datetime.now(UTC),
            "retained_records": ["pseudonymous deletion record"],
        }


def application():
    deletions = Deletions()
    app = create_app(
        Settings(
            environment="test",
            cors_origins=("http://localhost:3000",),
            log_level="INFO",
            repository_root=ROOT,
            allow_draft_content=True,
            development_learner_id=None,
        ),
        token_verifier=StaticTokenVerifier(
            {
                "academic": AuthenticatedLearner(ACADEMIC_ID, "authenticated"),
                "content": AuthenticatedLearner(CONTENT_ID, "authenticated"),
                "student": AuthenticatedLearner(str(STUDENT_ID), "authenticated"),
            }
        ),
    )
    app.dependency_overrides[beta_operations_repository] = Roles
    app.dependency_overrides[account_deletion_repository] = lambda: deletions
    return app, deletions


def request(app, method: str, path: str, token: str, **kwargs):
    async def send():
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {token}"
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, headers=headers, **kwargs)

    return asyncio.run(send())


def test_only_academic_admin_can_preview_and_execute_student_deletion():
    app, deletions = application()
    path = f"/api/v1/admin/students/{STUDENT_ID}/deletion/preview"

    assert request(app, "POST", path, "student").status_code == 403
    denied = request(app, "POST", path, "content")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "academic_administrator_required"

    preview = request(app, "POST", path, "academic")
    assert preview.status_code == 200
    assert preview.json()["confirmation_value"] == "student@example.test"
    assert preview.json()["counts"]["attempts"] == 4

    executed = request(
        app,
        "POST",
        f"/api/v1/admin/students/{STUDENT_ID}/deletion/execute",
        "academic",
        json={
            "preview_token": "x" * 80,
            "confirmation_email": "STUDENT@example.test",
            "reason": "Learner requested account deletion.",
        },
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["deleted"] is True
    assert deletions.executed

