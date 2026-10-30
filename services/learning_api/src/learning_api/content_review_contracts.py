"""Administrator contracts for review decisions and release requests."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from .contracts import ApiModel

ContentKind = Literal[
    "course",
    "lesson",
    "question",
    "english_lesson",
    "english_checkpoint_form",
    "english_passage",
    "english_question",
    "tutor_grounding",
]
ReviewDimension = Literal["mathematics", "english", "editorial"]
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
    unit_key: str | None = Field(default=None, pattern=r"^[a-z0-9-]+$")
    route_keys: list[str] = Field(default_factory=list)
    review_state: ReviewState
    mathematics_review: ContentReviewSummary | None
    english_review: ContentReviewSummary | None
    editorial_review: ContentReviewSummary | None
    lifecycle_request: ContentLifecycleSummary | None
    blockers: list[str]
    can_request_publication: bool
    can_request_retirement: bool


class ContentReviewQueueResponse(ApiModel):
    items: list[ContentReviewItemResponse]
    batch_ids: list[str]
    unit_keys: list[str]
    route_keys: list[str]
    total: int
    limit: int
    offset: int


class RouteReleaseRevision(ApiModel):
    content_kind: ContentKind
    stable_key: str
    revision: int = Field(ge=1)
    source_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_status: Literal["draft", "reviewed", "published", "retired"]
    english_review: ContentReviewSummary
    editorial_review: ContentReviewSummary
    lifecycle_request: ContentLifecycleSummary | None


class RouteReleaseBlocker(ApiModel):
    content_kind: ContentKind
    stable_key: str
    revision: int = Field(ge=1)
    review_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    reasons: list[str] = Field(min_length=1)


class RouteReleaseManifestResponse(ApiModel):
    route_key: str = Field(pattern=r"^[a-z0-9-]+$")
    status: Literal["review_pending", "publication_pending", "ready"]
    release_ready: bool
    expected_item_count: int = Field(ge=1)
    item_counts: dict[str, int]
    approved_revision_count: int = Field(ge=0)
    published_revision_count: int = Field(ge=0)
    publication_request_count: int = Field(ge=0)
    blocked_item_count: int = Field(ge=0)
    route_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    release_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    approved_revisions: list[RouteReleaseRevision]
    blockers: list[RouteReleaseBlocker]


class RecordContentReviewRequest(ApiModel):
    source_revision: int = Field(ge=1)
    source_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    dimension: ReviewDimension
    decision: ReviewDecision
    notes: str = Field(min_length=10, max_length=2000)


class BulkContentReviewTarget(ApiModel):
    content_kind: ContentKind
    stable_key: str = Field(min_length=1, max_length=160)
    source_revision: int = Field(ge=1)
    source_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class BulkContentReviewPreviewRequest(ApiModel):
    scope: Literal["batch", "unit", "route"]
    scope_key: str = Field(pattern=r"^[a-z0-9-]+$")
    targets: list[BulkContentReviewTarget] = Field(min_length=1, max_length=250)


class BulkContentReviewRequest(BulkContentReviewPreviewRequest):
    dimension: ReviewDimension
    decision: ReviewDecision
    notes: str = Field(min_length=10, max_length=2000)
    confirmed: Literal[True]


class ContentReviewRecordResponse(ContentReviewSummary):
    record_id: UUID
    content_kind: ContentKind
    stable_key: str
    source_revision: int
    source_content_sha256: str
    review_fingerprint: str


class BulkContentReviewResponse(ApiModel):
    scope: Literal["batch", "unit", "route"]
    scope_key: str
    recorded_count: int = Field(ge=1, le=250)
    records: list[ContentReviewRecordResponse]


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


class BulkContentReviewerPreviewResponse(ApiModel):
    scope: Literal["batch", "unit", "route"]
    scope_key: str
    items: list[ContentReviewerPreviewResponse]
