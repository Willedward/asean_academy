"""Admin-only beta invitation and operational reporting contracts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from .contracts import ApiModel

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


class AuditEventResponse(ApiModel):
    event_id: UUID
    event_type: Literal[
        "invitation_created", "invitation_revoked", "invitation_accepted"
    ]
    actor_user_id: UUID | None
    invitation_id: UUID | None
    target_user_id: UUID | None
    request_id: str
    metadata: dict[str, Any]
    created_at: datetime


class AuditEventListResponse(ApiModel):
    events: list[AuditEventResponse]
