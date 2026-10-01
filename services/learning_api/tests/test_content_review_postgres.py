"""Integration coverage for the append-only content review workflow."""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from learning_api.admin_repository import BetaOperationsError, PostgresBetaOperationsRepository
from learning_api.content_review import (
    list_review_queue,
    record_review,
    request_lifecycle,
    reviewer_preview,
    student_preview,
    verify_release_workflow,
)
from learning_api.content_review_contracts import (
    CreateLifecycleRequest,
    RecordContentReviewRequest,
)
from learning_api.course_catalogue import CourseCatalogue
from learning_api.identity import AuthenticatedLearner

ROOT = Path(__file__).resolve().parents[3]


def _body(item: dict, dimension: str, decision: str, notes: str):
    return RecordContentReviewRequest(
        source_revision=item["revision"],
        source_content_sha256=item["source_content_sha256"],
        review_fingerprint=item["review_fingerprint"],
        dimension=dimension,
        decision=decision,
        notes=notes,
    )


def _lifecycle_body(item: dict):
    return CreateLifecycleRequest(
        source_revision=item["revision"],
        source_content_sha256=item["source_content_sha256"],
        review_fingerprint=item["review_fingerprint"],
        action="publish",
        reason="Ready for the controlled content release pipeline.",
    )


@pytest.mark.postgres
def test_reviews_are_separated_safe_append_only_and_invalidate_old_release_requests():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires a migrated and imported disposable database")

    content_admin_id, academic_admin_id = uuid4(), uuid4()
    content_email = f"editor-{content_admin_id}@example.test"
    academic_email = f"academic-{academic_admin_id}@example.test"
    content_admin = AuthenticatedLearner(
        str(content_admin_id), "content_admin", content_email
    )
    academic_admin = AuthenticatedLearner(
        str(academic_admin_id), "academic_admin", academic_email
    )
    repository = PostgresBetaOperationsRepository(url)
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)

    with psycopg.connect(url) as connection:
        connection.execute("truncate content_lifecycle_requests, content_review_records")
        for user_id, email, role in (
            (content_admin_id, content_email, "content_admin"),
            (academic_admin_id, academic_email, "academic_admin"),
        ):
            connection.execute(
                "insert into auth.users(id, email) values (%s, %s)",
                (user_id, email),
            )
            connection.execute(
                "insert into profiles(id, email, role) values (%s, %s, %s)",
                (user_id, email, role),
            )

    queue = list_review_queue(
        repository,
        catalogue,
        kind="question",
        source_status=None,
        review_state=None,
        search="n1-l1-01",
        limit=20,
        offset=0,
    )
    assert queue["total"] == 1
    item = queue["items"][0]
    assert item["review_state"] == "unreviewed"
    assert not item["can_request_publication"]

    preview = student_preview(catalogue, "question", item["stable_key"])
    serialized_preview = json.dumps(preview)
    assert "parts" in serialized_preview
    assert "canonical" not in serialized_preview
    assert "hint" not in serialized_preview
    assert "solution" not in serialized_preview

    protected_preview = reviewer_preview(catalogue, "question", "n2-l1-001")
    assert protected_preview["batch_id"] == "g3-sec1-n2-b001"
    assert "canonical_answer" in json.dumps(protected_preview)

    n2_batch = list_review_queue(
        repository,
        catalogue,
        kind="question",
        source_status=None,
        review_state=None,
        search=None,
        limit=100,
        offset=0,
        batch_id="g3-sec1-n2-b001",
    )
    assert n2_batch["total"] == 26
    assert {entry["batch_id"] for entry in n2_batch["items"]} == {
        "g3-sec1-n2-b001"
    }
    assert "g3-sec1-n2-b001" in n2_batch["batch_ids"]

    with pytest.raises(BetaOperationsError, match="academic administrator"):
        record_review(
            repository,
            catalogue,
            content_admin,
            "question",
            item["stable_key"],
            _body(item, "mathematics", "approved", "Mathematics answer is correct."),
            "review-forbidden",
        )

    record_review(
        repository,
        catalogue,
        content_admin,
        "question",
        item["stable_key"],
        _body(item, "editorial", "approved", "Language and mark allocation are clear."),
        "review-editorial",
    )
    record_review(
        repository,
        catalogue,
        academic_admin,
        "question",
        item["stable_key"],
        _body(item, "mathematics", "approved", "Worked solution and answer are correct."),
        "review-mathematics",
    )

    approved = list_review_queue(
        repository,
        catalogue,
        kind="question",
        source_status=None,
        review_state="approved",
        search=item["stable_key"],
        limit=20,
        offset=0,
    )["items"][0]
    assert approved["can_request_publication"]

    first_request = request_lifecycle(
        repository,
        catalogue,
        academic_admin,
        "question",
        item["stable_key"],
        _lifecycle_body(item),
        "publish-request-one",
    )
    assert first_request["action"] == "publish"

    record_review(
        repository,
        catalogue,
        academic_admin,
        "question",
        item["stable_key"],
        _body(
            item,
            "mathematics",
            "changes_requested",
            "Revise the final mathematical justification before release.",
        ),
        "review-changes",
    )
    changed = list_review_queue(
        repository,
        catalogue,
        kind="question",
        source_status=None,
        review_state="changes_requested",
        search=item["stable_key"],
        limit=20,
        offset=0,
    )["items"][0]
    assert changed["lifecycle_request"] is None
    assert not changed["can_request_publication"]

    record_review(
        repository,
        catalogue,
        academic_admin,
        "question",
        item["stable_key"],
        _body(item, "mathematics", "approved", "The revised reasoning is now correct."),
        "review-reapproved",
    )
    reapproved = list_review_queue(
        repository,
        catalogue,
        kind="question",
        source_status=None,
        review_state="approved",
        search=item["stable_key"],
        limit=20,
        offset=0,
    )["items"][0]
    assert reapproved["lifecycle_request"] is None
    assert reapproved["can_request_publication"]

    second_request = request_lifecycle(
        repository,
        catalogue,
        academic_admin,
        "question",
        item["stable_key"],
        _lifecycle_body(item),
        "publish-request-two",
    )
    assert second_request["lifecycle_request_id"] != first_request["lifecycle_request_id"]

    with repository._connect() as connection:
        assert verify_release_workflow(connection, catalogue) == {
            "status": "approved",
            "checked_items": 0,
        }
        assert connection.execute(
            "select count(*) from content_review_records where stable_key=%s",
            (item["stable_key"],),
        ).fetchone()["count"] == 4
        assert connection.execute(
            "select count(*) from content_lifecycle_requests where stable_key=%s",
            (item["stable_key"],),
        ).fetchone()["count"] == 2
        assert connection.execute(
            "select count(*) from beta_audit_events where event_type='content_review_recorded' and actor_user_id in (%s, %s)",
            (content_admin_id, academic_admin_id),
        ).fetchone()["count"] == 4

    with pytest.raises(psycopg.DatabaseError, match="append-only"):
        with psycopg.connect(url) as connection:
            connection.execute(
                "update content_review_records set notes='Mutation is forbidden' where stable_key=%s",
                (item["stable_key"],),
            )
