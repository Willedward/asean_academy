"""Invitation onboarding and current-user API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .contracts import ApiModel


class AcceptInvitationRequest(ApiModel):
    invitation_code: str = Field(min_length=16, max_length=300)
    display_name: str = Field(min_length=1, max_length=80)


class ProfileResponse(ApiModel):
    learner_id: str
    email: str
    display_name: str | None
    role: Literal["student", "content_admin", "academic_admin"]
    target_track: str | None


class EnrolmentResponse(ApiModel):
    course_key: str
    course_revision: int
    status: Literal["active", "completed", "withdrawn"]
    enrolled_at: datetime


class CurrentLearnerResponse(ApiModel):
    profile: ProfileResponse
    enrolments: list[EnrolmentResponse]


class InvitationAcceptanceResponse(CurrentLearnerResponse):
    accepted: Literal[True] = True
