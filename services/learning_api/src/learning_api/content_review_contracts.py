"""Administrator contracts for review decisions and release requests."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from .contracts import ApiModel

ContentKind = Literal["course", "lesson", "question", "tutor_grounding"]
ReviewDimension = Literal["mathematics", "editorial"]
ReviewDecision = Literal["approved", "changes_requested"]
LifecycleAction = Literal["publish", "retire"]
ReviewState = Literal[
    "unreviewed",
    "partially_approved",
    "approved",
    "changes_requested",
    "publication_requested",
    "retirement_requested",
    "published",
    "retired",
]


class ContentReviewSummary(ApiModel):
    dimension: ReviewDimension
    decision: ReviewDecision
    reviewer_id: UUID
    reviewer_email: str
    reviewer_role: str
    notes: str
    created_at: datetime


class ContentLifecycleSummary(ApiModel):
    lifecycle_request_id: UUID
    action: LifecycleAction
    requested_by: UUID
    requester_email: str
    reason: str
    created_at: datetime


class ContentReviewItemResponse(ApiModel):
    content_kind: ContentKind
    stable_key: str
    revision: int
    source_content_sha256: str
    review_fingerprint: str
    title: str
    source_status: Literal["draft", "reviewed", "published", "retired"]
    difficulty: int | None = Field(default=None, ge=1, le=5)
    outcome_code: str | None = None
    position: int | None = Field(default=None, ge=1)
    batch_id: str | None = Field(default=None, pattern=r"^[a-z0-9-]+$")
    review_state: ReviewState
    mathematics_review: ContentReviewSummary | None
    editorial_review: ContentReviewSummary | None
    lifecycle_request: ContentLifecycleSummary | None
    blockers: list[str]
    can_request_publication: bool
    can_request_retirement: bool


class ContentReviewQueueResponse(ApiModel):
    items: list[ContentReviewItemResponse]
    batch_ids: list[str]
    total: int
    limit: int
    offset: int


class RecordContentReviewRequest(ApiModel):
    source_revision: int = Field(ge=1)
    source_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    dimension: ReviewDimension
    decision: ReviewDecision
    notes: str = Field(min_length=10, max_length=2000)


class ContentReviewRecordResponse(ContentReviewSummary):
    record_id: UUID
    content_kind: ContentKind
    stable_key: str
    source_revision: int
    source_content_sha256: str
    review_fingerprint: str


class CreateLifecycleRequest(ApiModel):
    source_revision: int = Field(ge=1)
    source_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    action: LifecycleAction
    reason: str = Field(min_length=10, max_length=2000)


class ContentLifecycleRequestResponse(ContentLifecycleSummary):
    content_kind: ContentKind
    stable_key: str
    source_revision: int
    source_content_sha256: str
    review_fingerprint: str
    release_instruction: str


class ContentStudentPreviewResponse(ApiModel):
    content_kind: ContentKind
    stable_key: str
    revision: int
    review_fingerprint: str
    public_content: dict[str, Any]


class ContentReviewerPreviewResponse(ApiModel):
    content_kind: ContentKind
    stable_key: str
    revision: int
    review_fingerprint: str
    batch_id: str | None = None
    review_content: dict[str, Any]
