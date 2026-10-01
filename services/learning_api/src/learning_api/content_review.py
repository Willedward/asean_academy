"""Review workflow over the immutable Git-authored course catalogue."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from psycopg.types.json import Jsonb
from question_bank.course_repository import course_content_hash, lesson_content_hash
from question_bank.practice import public_question
from question_bank.repository import content_hash

from .admin_repository import BetaOperationsError
from .course_catalogue import CourseCatalogue, public_lesson_section


@dataclass(frozen=True, slots=True)
class CatalogueReviewItem:
    kind: str
    stable_key: str
    revision: int
    source_hash: str
    fingerprint: str
    title: str
    source_status: str
    model: Any
    difficulty: int | None = None
    outcome_code: str | None = None
    position: int | None = None
    batch_id: str | None = None


def _without_workflow_metadata(value):
    if isinstance(value, list):
        return [_without_workflow_metadata(item) for item in value]
    if not isinstance(value, dict):
        return value
    ignored = {"revision", "status", "reviewed_at", "reviewed_by", "review_notes"}
    return {
        key: _without_workflow_metadata(item)
        for key, item in value.items()
        if key not in ignored
    }


def review_fingerprint(*models: Any) -> str:
    payload = [
        _without_workflow_metadata(model.model_dump(mode="json"))
        for model in models
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def catalogue_review_items(catalogue: CourseCatalogue) -> list[CatalogueReviewItem]:
    report = catalogue.report
    course = report.course
    items = [
        CatalogueReviewItem(
            "course",
            course.stable_key,
            course.revision,
            course_content_hash(course, report.lessons, report.pools),
            review_fingerprint(course, report.pools),
            course.title,
            course.status,
            course,
        )
    ]
    items.extend(
        CatalogueReviewItem(
            "lesson",
            lesson.stable_key,
            lesson.revision,
            lesson_content_hash(lesson),
            review_fingerprint(lesson),
            lesson.title,
            lesson.status,
            lesson,
            position=lesson.position,
        )
        for lesson in report.lessons
    )
    items.extend(
        CatalogueReviewItem(
            "question",
            question.stable_key,
            question.revision,
            content_hash(question),
            review_fingerprint(question),
            question.title,
            question.status,
            question,
            difficulty=question.difficulty,
            outcome_code=question.primary_outcome,
            batch_id=catalogue.review_question_batches.get(question.stable_key),
        )
        for question in catalogue.review_questions
    )
    return items


def _item(catalogue: CourseCatalogue, kind: str, stable_key: str) -> CatalogueReviewItem:
    match = next(
        (
            item
            for item in catalogue_review_items(catalogue)
            if item.kind == kind and item.stable_key == stable_key
        ),
        None,
    )
    if match is None:
        raise BetaOperationsError("content_not_found", "The content item was not found.", 404)
    return match


def _assert_expected(item: CatalogueReviewItem, body) -> None:
    if (
        body.source_revision != item.revision
        or body.source_content_sha256 != item.source_hash
        or body.review_fingerprint != item.fingerprint
    ):
        raise BetaOperationsError(
            "content_review_stale",
            "The content changed after this page loaded. Refresh before reviewing it.",
            409,
        )


def _snapshot(connection) -> tuple[dict, dict]:
    reviews = connection.execute(
        """
        select distinct on (records.item_kind, records.stable_key,
                            records.review_fingerprint, records.dimension)
               records.item_kind, records.stable_key, records.review_fingerprint,
               records.dimension, records.decision, records.reviewer_id,
               profiles.email as reviewer_email, profiles.role::text as reviewer_role,
               records.notes, records.created_at
        from content_review_records records
        join profiles on profiles.id = records.reviewer_id
        order by records.item_kind, records.stable_key, records.review_fingerprint,
                 records.dimension, records.created_at desc, records.id desc
        """
    ).fetchall()
    lifecycle = connection.execute(
        """
        select distinct on (requests.item_kind, requests.stable_key,
                            requests.review_fingerprint)
               requests.id as lifecycle_request_id, requests.item_kind,
               requests.stable_key, requests.review_fingerprint, requests.action,
               requests.requested_by, profiles.email as requester_email,
               requests.reason, requests.created_at
        from content_lifecycle_requests requests
        join profiles on profiles.id = requests.requested_by
        order by requests.item_kind, requests.stable_key, requests.review_fingerprint,
                 requests.created_at desc, requests.id desc
        """
    ).fetchall()
    return (
        {
            (row["item_kind"], row["stable_key"], row["review_fingerprint"], row["dimension"]): dict(row)
            for row in reviews
        },
        {
            (row["item_kind"], row["stable_key"], row["review_fingerprint"]): dict(row)
            for row in lifecycle
        },
    )


def _review_summary(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {
        key: row[key]
        for key in (
            "dimension",
            "decision",
            "reviewer_id",
            "reviewer_email",
            "reviewer_role",
            "notes",
            "created_at",
        )
    }


def _lifecycle_summary(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {
        key: row[key]
        for key in (
            "lifecycle_request_id",
            "action",
            "requested_by",
            "requester_email",
            "reason",
            "created_at",
        )
    }


def _serialize_item(item: CatalogueReviewItem, reviews: dict, lifecycle: dict) -> dict:
    base = (item.kind, item.stable_key, item.fingerprint)
    mathematics = reviews.get((*base, "mathematics"))
    editorial = reviews.get((*base, "editorial"))
    latest_request = lifecycle.get(base)
    decisions = [row["decision"] for row in (mathematics, editorial) if row]
    all_approved = len(decisions) == 2 and all(value == "approved" for value in decisions)
    active_request = latest_request
    if latest_request and latest_request["action"] == "publish":
        if not all_approved:
            active_request = None
        else:
            latest_review_at = max(
                row["created_at"] for row in (mathematics, editorial) if row is not None
            )
            if latest_request["created_at"] < latest_review_at:
                active_request = None
    blockers = []
    if mathematics is None or mathematics["decision"] != "approved":
        blockers.append("Mathematics approval is required.")
    if editorial is None or editorial["decision"] != "approved":
        blockers.append("Editorial approval is required.")
    if item.kind == "lesson" and not item.model.sections:
        blockers.append("The lesson has no learning sections.")
    if item.source_status == "retired":
        blockers.append("Retired content cannot be published again without a new revision.")

    if item.source_status == "retired":
        state = "retired"
    elif item.source_status == "published" and active_request and active_request["action"] == "retire":
        state = "retirement_requested"
    elif item.source_status == "published":
        state = "published"
    elif active_request and active_request["action"] == "publish":
        state = "publication_requested"
    elif "changes_requested" in decisions:
        state = "changes_requested"
    elif len(decisions) == 2 and all(value == "approved" for value in decisions):
        state = "approved"
    elif decisions:
        state = "partially_approved"
    else:
        state = "unreviewed"

    return {
        "content_kind": item.kind,
        "stable_key": item.stable_key,
        "revision": item.revision,
        "source_content_sha256": item.source_hash,
        "review_fingerprint": item.fingerprint,
        "title": item.title,
        "source_status": item.source_status,
        "difficulty": item.difficulty,
        "outcome_code": item.outcome_code,
        "position": item.position,
        "batch_id": item.batch_id,
        "review_state": state,
        "mathematics_review": _review_summary(mathematics),
        "editorial_review": _review_summary(editorial),
        "lifecycle_request": _lifecycle_summary(active_request),
        "blockers": blockers,
        "can_request_publication": not blockers
        and item.source_status not in {"published", "retired"}
        and not (active_request and active_request["action"] == "publish"),
        "can_request_retirement": item.source_status == "published"
        and not (active_request and active_request["action"] == "retire"),
    }


def list_review_queue(
    repository,
    catalogue: CourseCatalogue,
    *,
    kind: str | None,
    source_status: str | None,
    review_state: str | None,
    search: str | None,
    limit: int,
    offset: int,
    batch_id: str | None = None,
) -> dict:
    with repository._connect() as connection:
        reviews, lifecycle = _snapshot(connection)
    items = [
        _serialize_item(item, reviews, lifecycle)
        for item in catalogue_review_items(catalogue)
    ]
    batch_ids = sorted(
        {item["batch_id"] for item in items if item["batch_id"] is not None}
    )
    if kind:
        items = [item for item in items if item["content_kind"] == kind]
    if source_status:
        items = [item for item in items if item["source_status"] == source_status]
    if review_state:
        items = [item for item in items if item["review_state"] == review_state]
    if batch_id:
        items = [item for item in items if item["batch_id"] == batch_id]
    if search:
        query = search.strip().casefold()
        items = [
            item
            for item in items
            if query in item["stable_key"].casefold() or query in item["title"].casefold()
        ]
    items.sort(key=lambda item: ({"course": 0, "lesson": 1, "question": 2}[item["content_kind"]], item["position"] or 0, item["stable_key"]))
    return {
        "items": items[offset : offset + limit],
        "batch_ids": batch_ids,
        "total": len(items),
        "limit": limit,
        "offset": offset,
    }


def student_preview(catalogue: CourseCatalogue, kind: str, stable_key: str) -> dict:
    item = _item(catalogue, kind, stable_key)
    if kind == "question":
        content = public_question(item.model)
    elif kind == "lesson":
        lesson = item.model
        content = {
            "stable_key": lesson.stable_key,
            "revision": lesson.revision,
            "title": lesson.title,
            "summary": lesson.summary,
            "objectives": lesson.objectives,
            "estimated_minutes": lesson.estimated_minutes,
            "sections": [public_lesson_section(section) for section in lesson.sections],
            "assets": [asset.model_dump(mode="json") for asset in lesson.assets],
        }
    else:
        course = item.model
        content = {
            "stable_key": course.stable_key,
            "revision": course.revision,
            "title": course.title,
            "description": course.description,
            "school_level": course.school_level,
            "subject": course.subject,
            "units": [unit.model_dump(mode="json") for unit in course.units],
        }
    return {
        "content_kind": item.kind,
        "stable_key": item.stable_key,
        "revision": item.revision,
        "review_fingerprint": item.fingerprint,
        "public_content": content,
    }


def reviewer_preview(catalogue: CourseCatalogue, kind: str, stable_key: str) -> dict:
    """Return protected authoring content, including answers and feedback."""
    item = _item(catalogue, kind, stable_key)
    return {
        "content_kind": item.kind,
        "stable_key": item.stable_key,
        "revision": item.revision,
        "review_fingerprint": item.fingerprint,
        "batch_id": item.batch_id,
        "review_content": item.model.model_dump(mode="json"),
    }


def record_review(repository, catalogue, administrator, kind, stable_key, body, request_id):
    item = _item(catalogue, kind, stable_key)
    _assert_expected(item, body)
    if body.dimension == "mathematics" and administrator.role != "academic_admin":
        raise BetaOperationsError(
            "academic_review_required",
            "Only an academic administrator can record Mathematics review.",
            403,
        )
    with repository._connect() as connection:
        connection.execute(
            "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (f"content:{kind}:{stable_key}",),
        )
        row = connection.execute(
            """
            insert into content_review_records (
                item_kind, stable_key, source_revision, source_content_sha256,
                review_fingerprint, dimension, decision, reviewer_id, notes, request_id
            ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            returning id as record_id, item_kind as content_kind, stable_key,
                      source_revision, source_content_sha256, review_fingerprint,
                      dimension, decision, reviewer_id, notes, created_at
            """,
            (
                kind,
                stable_key,
                item.revision,
                item.source_hash,
                item.fingerprint,
                body.dimension,
                body.decision,
                administrator.learner_id,
                body.notes.strip(),
                request_id,
            ),
        ).fetchone()
        connection.execute(
            """
            insert into beta_audit_events(event_type, actor_user_id, request_id, metadata)
            values ('content_review_recorded', %s, %s, %s)
            """,
            (
                administrator.learner_id,
                request_id,
                Jsonb({
                    "content_kind": kind,
                    "stable_key": stable_key,
                    "source_revision": item.revision,
                    "review_fingerprint": item.fingerprint,
                    "dimension": body.dimension,
                    "decision": body.decision,
                }),
            ),
        )
        profile = connection.execute(
            "select email, role::text as role from profiles where id=%s",
            (administrator.learner_id,),
        ).fetchone()
    return {
        **dict(row),
        "reviewer_email": profile["email"],
        "reviewer_role": profile["role"],
    }


def request_lifecycle(repository, catalogue, administrator, kind, stable_key, body, request_id):
    item = _item(catalogue, kind, stable_key)
    _assert_expected(item, body)
    with repository._connect() as connection:
        connection.execute(
            "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (f"content:{kind}:{stable_key}",),
        )
        reviews, lifecycle = _snapshot(connection)
        serialized = _serialize_item(item, reviews, lifecycle)
        if body.action == "publish" and not serialized["can_request_publication"]:
            raise BetaOperationsError(
                "content_publication_blocked",
                " ".join(serialized["blockers"]) or "Publication was already requested.",
                409,
            )
        if body.action == "retire" and not serialized["can_request_retirement"]:
            raise BetaOperationsError(
                "content_retirement_blocked",
                "Only published content without a pending retirement request can be retired.",
                409,
            )
        row = connection.execute(
            """
            insert into content_lifecycle_requests (
                item_kind, stable_key, source_revision, source_content_sha256,
                review_fingerprint, action, requested_by, reason, request_id
            ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            returning id as lifecycle_request_id, item_kind as content_kind,
                      stable_key, source_revision, source_content_sha256,
                      review_fingerprint, action, requested_by, reason, created_at
            """,
            (
                kind,
                stable_key,
                item.revision,
                item.source_hash,
                item.fingerprint,
                body.action,
                administrator.learner_id,
                body.reason.strip(),
                request_id,
            ),
        ).fetchone()
        event_type = (
            "content_publication_requested"
            if body.action == "publish"
            else "content_retirement_requested"
        )
        connection.execute(
            """
            insert into beta_audit_events(event_type, actor_user_id, request_id, metadata)
            values (%s, %s, %s, %s)
            """,
            (
                event_type,
                administrator.learner_id,
                request_id,
                Jsonb({
                    "content_kind": kind,
                    "stable_key": stable_key,
                    "source_revision": item.revision,
                    "review_fingerprint": item.fingerprint,
                    "action": body.action,
                }),
            ),
        )
        profile = connection.execute(
            "select email from profiles where id=%s", (administrator.learner_id,)
        ).fetchone()
    instruction = (
        "Create a new reviewed/published Git revision with unchanged reviewed content, then run the release gate and importer."
        if body.action == "publish"
        else "Create a new retired Git revision, then run the release gate and importer. Historical attempts remain pinned."
    )
    return {
        **dict(row),
        "requester_email": profile["email"],
        "release_instruction": instruction,
    }


def verify_release_workflow(connection, catalogue: CourseCatalogue) -> dict:
    reviews, lifecycle = _snapshot(connection)
    failures = []
    checked = 0
    for item in catalogue_review_items(catalogue):
        if item.source_status == "draft":
            continue
        checked += 1
        serialized = _serialize_item(item, reviews, lifecycle)
        if serialized["mathematics_review"] is None or serialized["mathematics_review"]["decision"] != "approved":
            failures.append(f"{item.kind}:{item.stable_key} lacks Mathematics approval")
        if serialized["editorial_review"] is None or serialized["editorial_review"]["decision"] != "approved":
            failures.append(f"{item.kind}:{item.stable_key} lacks editorial approval")
        if item.source_status in {"published", "retired"}:
            required_action = "retire" if item.source_status == "retired" else "publish"
            request = serialized["lifecycle_request"]
            if request is None or request["action"] != required_action:
                failures.append(f"{item.kind}:{item.stable_key} lacks a {required_action} request")
    if failures:
        raise BetaOperationsError(
            "content_release_unapproved",
            "Release workflow failed: " + "; ".join(failures[:10]),
            409,
        )
    return {"status": "approved", "checked_items": checked}
