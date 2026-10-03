"""Admin-only beta invitation and operational reporting contracts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from .contracts import ApiModel, ReleaseMetadata

InvitationStatus = Literal["active", "expired", "exhausted", "revoked"]


class CreateInvitationRequest(ApiModel):
    email: str = Field(min_length=5, max_length=320)
    course_key: str = Field(default="g3-sec1-math", min_length=1, max_length=80)
    expires_days: int = Field(default=14, ge=1, le=90)
    max_uses: int = Field(default=1, ge=1, le=100)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("Enter a valid email address.")
        return normalized

    @field_validator("course_key")
    @classmethod
    def normalize_course_key(cls, value: str) -> str:
        return value.strip()


class InvitationResponse(ApiModel):
    invitation_id: UUID
    email: str
    course_key: str
    course_revision: int
    status: InvitationStatus
    max_uses: int
    use_count: int
    expires_at: datetime
    revoked_at: datetime | None
    created_by: UUID | None
    created_at: datetime


class CreatedInvitationResponse(InvitationResponse):
    invitation_code: str = Field(min_length=16)


class InvitationListResponse(ApiModel):
    invitations: list[InvitationResponse]
    total: int


class BetaOperationsSummaryResponse(ApiModel):
    total_students: int
    active_students: int
    invitations_active: int
    invitations_expired: int
    invitations_exhausted: int
    invitations_revoked: int
    enrolments_last_7_days: int


class OperationalResourceCounts(ApiModel):
    registered_users: int
    students: int
    active_enrolments: int
    current_course_versions: int
    current_questions: int


class OperationalDatabaseStatus(ApiModel):
    state: Literal["ready"] = "ready"
    latency_ms: float = Field(ge=0)
    server_time: datetime
    resources: OperationalResourceCounts


class DeploymentStatusResponse(ApiModel):
    status: Literal["operational"] = "operational"
    checked_at: datetime
    request_id: str
    environment: str
    uptime_seconds: float = Field(ge=0)
    release: ReleaseMetadata
    database: OperationalDatabaseStatus


class AuditEventResponse(ApiModel):
    event_id: UUID
    event_type: Literal[
        "invitation_created", "invitation_revoked", "invitation_accepted",
        "role_changed", "course_revision_changed",
        "content_review_recorded", "content_publication_requested",
        "content_retirement_requested",
        "question_report_created", "question_report_status_changed",
        "account_deletion_completed",
        "tutor_evaluation_run_created", "tutor_evaluation_review_recorded",
    ]
    actor_user_id: UUID | None
    invitation_id: UUID | None
    target_user_id: UUID | None
    request_id: str
    metadata: dict[str, Any]
    created_at: datetime


class AuditEventListResponse(ApiModel):
    events: list[AuditEventResponse]


class AccountDeletionPreviewResponse(ApiModel):
    learner_id: UUID
    email: str
    display_name: str | None
    counts: dict[str, int]
    retained_records: list[str]
    preview_token: str
    expires_at: datetime
    confirmation_value: str


class ExecuteAccountDeletionRequest(ApiModel):
    preview_token: str = Field(min_length=40, max_length=4000)
    confirmation_email: str = Field(min_length=5, max_length=320)
    reason: str = Field(min_length=10, max_length=500)

    @field_validator("confirmation_email")
    @classmethod
    def normalize_confirmation_email(cls, value: str) -> str:
        return value.strip().casefold()

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 10:
            raise ValueError("reason must contain at least 10 non-whitespace characters")
        return normalized


class AccountDeletionResponse(ApiModel):
    deleted: Literal[True] = True
    target_reference: str = Field(pattern=r"^[0-9a-f]{64}$")
    completed_at: datetime
    retained_records: list[str]
