from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx

from learning_api.admin_contracts import CreateInvitationRequest
from learning_api.config import Settings
from learning_api.dependencies import beta_operations_repository
from learning_api.identity import AuthenticatedLearner, StaticTokenVerifier
from learning_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ADMIN_ID = "00000000-0000-4000-8000-000000000010"
STUDENT_ID = "00000000-0000-4000-8000-000000000011"
INVITATION_ID = UUID("00000000-0000-4000-8000-000000000012")
EVENT_ID = UUID("00000000-0000-4000-8000-000000000013")


class FakeBetaOperationsRepository:
    def __init__(self):
        self.invitation = {
            "invitation_id": INVITATION_ID,
            "email": "student@example.test",
            "course_key": "g3-sec1-math",
            "course_revision": 1,
            "status": "active",
            "max_uses": 1,
            "use_count": 0,
            "expires_at": datetime.now(UTC) + timedelta(days=14),
            "revoked_at": None,
            "created_by": UUID(ADMIN_ID),
            "created_at": datetime.now(UTC),
        }
        self.created_with: CreateInvitationRequest | None = None

    def role_for(self, learner_id: str) -> str:
        return "content_admin" if learner_id == ADMIN_ID else "student"

    def create_invitation(self, administrator, body, request_id):
        assert administrator.learner_id == ADMIN_ID
        assert request_id
        self.created_with = body
        return {**self.invitation, "email": body.email, "invitation_code": "raw-code-visible-once"}

    def list_invitations(self, *, status, limit, offset):
        assert limit <= 200
        assert offset >= 0
        invitations = [self.invitation]
        if status and status != self.invitation["status"]:
            invitations = []
        return {"invitations": invitations, "total": len(invitations)}

    def revoke_invitation(self, administrator, invitation_id, request_id):
        assert administrator.learner_id == ADMIN_ID
        assert invitation_id == INVITATION_ID
        assert request_id
        self.invitation = {
            **self.invitation,
            "status": "revoked",
            "revoked_at": datetime.now(UTC),
        }
        return self.invitation

    def summary(self):
        return {
            "total_students": 12,
            "active_students": 9,
            "invitations_active": 2,
            "invitations_expired": 1,
            "invitations_exhausted": 3,
            "invitations_revoked": 1,
            "enrolments_last_7_days": 4,
        }

    def audit_events(self, *, limit):
        assert limit <= 200
        return {
            "events": [
                {
                    "event_id": EVENT_ID,
                    "event_type": "invitation_created",
                    "actor_user_id": UUID(ADMIN_ID),
                    "invitation_id": INVITATION_ID,
                    "target_user_id": None,
                    "request_id": "request-123",
                    "metadata": {"course_key": "g3-sec1-math"},
                    "created_at": datetime.now(UTC),
                }
            ]
        }


def application():
    repository = FakeBetaOperationsRepository()
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
                "admin-token": AuthenticatedLearner(
                    ADMIN_ID, "authenticated", "admin@example.test"
                ),
                "student-token": AuthenticatedLearner(
                    STUDENT_ID, "authenticated", "student@example.test"
                ),
            }
        ),
    )
    app.dependency_overrides[beta_operations_repository] = lambda: repository
    return app, repository


def request(app, method: str, path: str, token: str | None = None, **kwargs):
    async def send():
        headers = dict(kwargs.pop("headers", {}))
        if token:
            headers["Authorization"] = f"Bearer {token}"
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, headers=headers, **kwargs)

    return asyncio.run(send())


def test_admin_routes_require_database_backed_admin_role():
    app, _ = application()

    missing = request(app, "GET", "/api/v1/admin/invitations")
    student = request(app, "GET", "/api/v1/admin/invitations", "student-token")
    administrator = request(app, "GET", "/api/v1/admin/invitations", "admin-token")

    assert missing.status_code == 401
    assert student.status_code == 403
    assert student.json()["error"]["code"] == "administrator_required"
    assert administrator.status_code == 200
    assert administrator.json()["total"] == 1
    assert "invitation_code" not in administrator.text


def test_admin_can_create_and_revoke_invitation_with_raw_code_returned_once():
    app, repository = application()

    created = request(
        app,
        "POST",
        "/api/v1/admin/invitations",
        "admin-token",
        json={
            "email": "  New.Student@Example.Test ",
            "course_key": "g3-sec1-math",
            "expires_days": 10,
            "max_uses": 1,
        },
    )

    assert created.status_code == 201, created.text
    assert created.json()["email"] == "new.student@example.test"
    assert created.json()["invitation_code"] == "raw-code-visible-once"
    assert repository.created_with is not None
    assert repository.created_with.email == "new.student@example.test"

    revoked = request(
        app,
        "POST",
        f"/api/v1/admin/invitations/{INVITATION_ID}/revoke",
        "admin-token",
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert "invitation_code" not in revoked.text


def test_admin_summary_and_audit_are_privacy_minimal():
    app, _ = application()

    summary = request(app, "GET", "/api/v1/admin/operations/summary", "admin-token")
    events = request(app, "GET", "/api/v1/admin/audit-events", "admin-token")

    assert summary.status_code == 200
    assert summary.json()["active_students"] == 9
    assert events.status_code == 200
    assert events.json()["events"][0]["request_id"] == "request-123"
    assert "raw-code" not in events.text


def test_admin_invitation_contract_rejects_invalid_email():
    app, _ = application()
    response = request(
        app,
        "POST",
        "/api/v1/admin/invitations",
        "admin-token",
        json={"email": "not-an-email"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
