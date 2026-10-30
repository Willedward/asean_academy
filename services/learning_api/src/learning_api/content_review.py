"""Review workflow over the immutable Git-authored course catalogue."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb
from question_bank.course_repository import course_content_hash, lesson_content_hash
from question_bank.english_authoring import (
    english_review_fingerprint,
    english_route_review_selection,
)
from question_bank.english_models import (
    EnglishAssessmentForm,
    EnglishLesson,
    EnglishObjectiveQuestion,
    EnglishPassage,
)
from question_bank.practice import public_question
from question_bank.repository import content_hash

from .admin_repository import BetaOperationsError
from .course_catalogue import CourseCatalogue, public_lesson_section

TUTOR_GROUNDING_ROOT = Path("backend_resources/tutor_evaluations")
ENGLISH_SPRINT_ROUTE_KEY = "english-sprint-route-v3b-review"
ENGLISH_SPRINT_EXPECTED_COUNTS = {
    "english_lesson": 16,
    "english_checkpoint_form": 20,
    "english_question": 65,
    "english_passage": 20,
}


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
    unit_key: str | None = None
    route_keys: tuple[str, ...] = ()


def _without_workflow_metadata(value):
    if isinstance(value, list):
        return [_without_workflow_metadata(item) for item in value]
    if not isinstance(value, dict):
        return value
    ignored = {
        "revision",
        "status",
        "review",
        "reviewed_at",
        "reviewed_by",
        "review_notes",
    }
    return {
        key: _without_workflow_metadata(item)
        for key, item in value.items()
        if key not in ignored
    }


def review_fingerprint(*models: Any) -> str:
    payload = [
        _without_workflow_metadata(
            model.model_dump(mode="json") if hasattr(model, "model_dump") else model
        )
        for model in models
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _english_source_hash(model: Any) -> str:
    payload = model.model_dump(mode="json")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _english_review_items(catalogue: CourseCatalogue) -> list[CatalogueReviewItem]:
    report = catalogue.english_review_report
    batch_by_question = catalogue.english_review_question_batches
    sprint = english_route_review_selection(report, route="sprint")
    sprint_lesson_keys = {lesson.stable_key for lesson in sprint.lessons}
    sprint_question_keys = {question.stable_key for question in sprint.questions}
    sprint_passage_keys = {passage.stable_key for passage in sprint.passages}
    sprint_route = (ENGLISH_SPRINT_ROUTE_KEY,)
    items = []
    for lesson in report.lessons:
        module_code = lesson.lesson_code.split(".", 1)[0].lower()
        items.append(
            CatalogueReviewItem(
                kind="english_lesson",
                stable_key=lesson.stable_key,
                revision=lesson.revision,
                source_hash=_english_source_hash(lesson),
                fingerprint=english_review_fingerprint(lesson),
                title=lesson.title,
                source_status=lesson.status,
                model=lesson,
                position=int(lesson.lesson_code.split(".", 1)[1]),
                unit_key=f"english-{module_code}",
                route_keys=(sprint_route if lesson.stable_key in sprint_lesson_keys else ()),
            )
        )
    for form in sprint.forms:
        items.append(
            CatalogueReviewItem(
                kind="english_checkpoint_form",
                stable_key=form.form_key,
                revision=form.revision,
                source_hash=_english_source_hash(form),
                fingerprint=english_review_fingerprint(form),
                title=form.title,
                source_status=form.status,
                model=form,
                unit_key=f"english-{form.module_code.lower()}",
                route_keys=sprint_route,
            )
        )
    for question in report.questions:
        batch_id = batch_by_question.get(question.stable_key)
        module_number = re.search(r"[0-9]+", question.outcome_code)
        unit_key = f"english-e{module_number.group(0)}" if module_number else "english"
        items.append(
            CatalogueReviewItem(
                kind="english_question",
                stable_key=question.stable_key,
                revision=question.revision,
                source_hash=_english_source_hash(question),
                fingerprint=english_review_fingerprint(question),
                title=question.title,
                source_status=question.status,
                model=question,
                difficulty=question.difficulty,
                outcome_code=question.outcome_code,
                batch_id=batch_id,
                unit_key=unit_key,
                route_keys=(
                    sprint_route if question.stable_key in sprint_question_keys else ()
                ),
            )
        )
    passage_batches: dict[str, set[str]] = {}
    for question in report.questions:
        if question.passage_ref is None:
            continue
        passage_batches.setdefault(question.passage_ref.stable_key, set()).add(
            batch_by_question.get(question.stable_key, "")
        )
    for passage in report.passages:
        batches = {value for value in passage_batches.get(passage.stable_key, set()) if value}
        items.append(
            CatalogueReviewItem(
                kind="english_passage",
                stable_key=passage.stable_key,
                revision=passage.revision,
                source_hash=_english_source_hash(passage),
                fingerprint=english_review_fingerprint(passage),
                title=passage.title,
                source_status=passage.status,
                model=passage,
                batch_id=next(iter(batches)) if len(batches) == 1 else None,
                unit_key="english-passages",
                route_keys=(
                    sprint_route if passage.stable_key in sprint_passage_keys else ()
                ),
            )
        )
    return items


def catalogue_review_items(catalogue: CourseCatalogue) -> list[CatalogueReviewItem]:
    items = []
    for report in catalogue.reports.values():
        course = report.course
        items.append(
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
        )
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
                unit_key=lesson.unit_key,
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
            unit_key=(
                f"g3-sec{question.school_level[-1]}-{question.topic_code.lower()}"
            ),
        )
        for question in catalogue.review_questions
    )
    items.extend(_tutor_grounding_review_items(catalogue.repository_root))
    items.extend(_english_review_items(catalogue))
    return items


def _tutor_grounding_review_items(repository_root: Path) -> list[CatalogueReviewItem]:
    root = repository_root / TUTOR_GROUNDING_ROOT
    items: list[CatalogueReviewItem] = []
    for path in sorted(root.glob("**/*grounding*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        required = {
            "grounding_id",
            "revision",
            "status",
            "title",
            "topic_code",
            "scope",
            "source_references",
            "sections_by_outcome",
        }
        missing = sorted(required - payload.keys())
        if missing:
            raise BetaOperationsError(
                "tutor_grounding_invalid",
                f"Tutor grounding {path.name} is missing: {', '.join(missing)}.",
                503,
            )
        revision = payload["revision"]
        if not isinstance(revision, int) or revision < 1:
            raise BetaOperationsError(
                "tutor_grounding_invalid",
                f"Tutor grounding {path.name} must have a positive integer revision.",
                503,
            )
        source_status = {
            "draft_for_review": "draft",
            "reviewed": "reviewed",
            "published": "published",
            "retired": "retired",
        }.get(payload["status"])
        if source_status is None:
            raise BetaOperationsError(
                "tutor_grounding_invalid",
                f"Tutor grounding {path.name} has an unsupported status.",
                503,
            )
        items.append(
            CatalogueReviewItem(
                kind="tutor_grounding",
                stable_key=str(payload["grounding_id"]),
                revision=revision,
                source_hash=hashlib.sha256(path.read_bytes()).hexdigest(),
                fingerprint=review_fingerprint(payload),
                title=str(payload["title"]),
                source_status=source_status,
                model=payload,
                outcome_code=str(payload["topic_code"]),
            )
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
    english = reviews.get((*base, "english"))
    editorial = reviews.get((*base, "editorial"))
    latest_request = lifecycle.get(base)
    subject_dimension = "english" if item.kind.startswith("english_") else "mathematics"
    subject_review = english if subject_dimension == "english" else mathematics
    decisions = [row["decision"] for row in (subject_review, editorial) if row]
    all_approved = len(decisions) == 2 and all(value == "approved" for value in decisions)
    active_request = latest_request
    if latest_request and latest_request["action"] == "publish":
        if not all_approved:
            active_request = None
        else:
            latest_review_at = max(
                row["created_at"] for row in (subject_review, editorial) if row is not None
            )
            if latest_request["created_at"] < latest_review_at:
                active_request = None
    blockers = []
    if subject_review is None or subject_review["decision"] != "approved":
        subject_label = "English" if subject_dimension == "english" else "Mathematics"
        blockers.append(f"{subject_label} approval is required.")
    if editorial is None or editorial["decision"] != "approved":
        blockers.append("Editorial approval is required.")
    if item.kind in {"lesson", "english_lesson"} and not item.model.sections:
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
        "unit_key": item.unit_key,
        "route_keys": list(item.route_keys),
        "review_state": state,
        "mathematics_review": _review_summary(mathematics),
        "english_review": _review_summary(english),
        "editorial_review": _review_summary(editorial),
        "lifecycle_request": _lifecycle_summary(active_request),
        "blockers": blockers,
        "can_request_publication": item.kind != "tutor_grounding"
        and not blockers
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
    unit_key: str | None = None,
    route_key: str | None = None,
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
    unit_keys = sorted(
        {item["unit_key"] for item in items if item["unit_key"] is not None}
    )
    route_keys = sorted({key for item in items for key in item["route_keys"]})
    if kind:
        items = [item for item in items if item["content_kind"] == kind]
    if source_status:
        items = [item for item in items if item["source_status"] == source_status]
    if review_state:
        items = [item for item in items if item["review_state"] == review_state]
    if batch_id:
        items = [item for item in items if item["batch_id"] == batch_id]
    if unit_key:
        items = [item for item in items if item["unit_key"] == unit_key]
    if route_key:
        items = [item for item in items if route_key in item["route_keys"]]
    if search:
        query = search.strip().casefold()
        items = [
            item
            for item in items
            if query in item["stable_key"].casefold() or query in item["title"].casefold()
        ]
    priority = {
        "course": 0,
        "lesson": 1,
        "question": 2,
        "english_lesson": 3,
        "english_checkpoint_form": 4,
        "english_passage": 5,
        "english_question": 6,
        "tutor_grounding": 7,
    }
    items.sort(
        key=lambda item: (
            priority[item["content_kind"]],
            item["position"] or 0,
            item["stable_key"],
        )
    )
    return {
        "items": items[offset : offset + limit],
        "batch_ids": batch_ids,
        "unit_keys": unit_keys,
        "route_keys": route_keys,
        "total": len(items),
        "limit": limit,
        "offset": offset,
    }


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_route_release_manifest(
    catalogue: CourseCatalogue,
    reviews: dict,
    lifecycle: dict,
    *,
    route_key: str,
) -> dict:
    """Build fail-closed release evidence for one fixed review route.

    The release list contains only revisions with both required human approvals.
    Learner release remains blocked until every pinned item is also published and
    retains an active publication request for the same review fingerprint.
    """
    if route_key != ENGLISH_SPRINT_ROUTE_KEY:
        raise BetaOperationsError(
            "content_release_route_not_found",
            "The requested content release route was not found.",
            404,
        )
    items = sorted(
        (
            item
            for item in catalogue_review_items(catalogue)
            if route_key in item.route_keys
        ),
        key=lambda item: (item.kind, item.stable_key),
    )
    item_counts = {
        kind: sum(item.kind == kind for item in items)
        for kind in ENGLISH_SPRINT_EXPECTED_COUNTS
    }
    if item_counts != ENGLISH_SPRINT_EXPECTED_COUNTS:
        raise BetaOperationsError(
            "content_release_route_drift",
            "The deployed English Sprint route no longer matches its fixed release scope.",
            503,
        )

    route_rows = [
        {
            "content_kind": item.kind,
            "stable_key": item.stable_key,
            "revision": item.revision,
            "source_content_sha256": item.source_hash,
            "review_fingerprint": item.fingerprint,
        }
        for item in items
    ]
    approved_revisions = []
    blockers = []
    published_revision_count = 0
    publication_request_count = 0
    for item in items:
        serialized = _serialize_item(item, reviews, lifecycle)
        english_review = serialized["english_review"]
        editorial_review = serialized["editorial_review"]
        reasons = []
        if english_review is None:
            reasons.append("english_approval_missing")
        elif english_review["decision"] != "approved":
            reasons.append("english_changes_requested")
        if editorial_review is None:
            reasons.append("editorial_approval_missing")
        elif editorial_review["decision"] != "approved":
            reasons.append("editorial_changes_requested")

        review_approved = not any(
            reason.startswith(("english_", "editorial_")) for reason in reasons
        )
        if review_approved:
            approved_revisions.append(
                {
                    "content_kind": item.kind,
                    "stable_key": item.stable_key,
                    "revision": item.revision,
                    "source_content_sha256": item.source_hash,
                    "review_fingerprint": item.fingerprint,
                    "source_status": item.source_status,
                    "english_review": english_review,
                    "editorial_review": editorial_review,
                    "lifecycle_request": serialized["lifecycle_request"],
                }
            )

        if item.source_status == "published":
            published_revision_count += 1
        else:
            reasons.append("source_not_published")
        request = serialized["lifecycle_request"]
        if request is not None and request["action"] == "publish":
            publication_request_count += 1
        else:
            reasons.append("publication_request_missing")
        if reasons:
            blockers.append(
                {
                    "content_kind": item.kind,
                    "stable_key": item.stable_key,
                    "revision": item.revision,
                    "review_fingerprint": item.fingerprint,
                    "reasons": reasons,
                }
            )

    expected_item_count = sum(ENGLISH_SPRINT_EXPECTED_COUNTS.values())
    approved_revision_count = len(approved_revisions)
    release_ready = not blockers and approved_revision_count == expected_item_count
    if approved_revision_count < expected_item_count:
        status = "review_pending"
    elif release_ready:
        status = "ready"
    else:
        status = "publication_pending"
    approval_rows = [
        {
            "content_kind": row["content_kind"],
            "stable_key": row["stable_key"],
            "revision": row["revision"],
            "source_content_sha256": row["source_content_sha256"],
            "review_fingerprint": row["review_fingerprint"],
            "english_reviewer_id": row["english_review"]["reviewer_id"],
            "english_reviewed_at": row["english_review"]["created_at"],
            "editorial_reviewer_id": row["editorial_review"]["reviewer_id"],
            "editorial_reviewed_at": row["editorial_review"]["created_at"],
        }
        for row in approved_revisions
    ]
    return {
        "route_key": route_key,
        "status": status,
        "release_ready": release_ready,
        "expected_item_count": expected_item_count,
        "item_counts": item_counts,
        "approved_revision_count": approved_revision_count,
        "published_revision_count": published_revision_count,
        "publication_request_count": publication_request_count,
        "blocked_item_count": len(blockers),
        "route_fingerprint": _canonical_sha256(route_rows),
        "release_manifest_sha256": _canonical_sha256(approval_rows),
        "approved_revisions": approved_revisions,
        "blockers": blockers,
    }


def route_release_manifest(repository, catalogue: CourseCatalogue, *, route_key: str) -> dict:
    with repository._connect() as connection:
        reviews, lifecycle = _snapshot(connection)
    return build_route_release_manifest(
        catalogue,
        reviews,
        lifecycle,
        route_key=route_key,
    )


def student_preview(catalogue: CourseCatalogue, kind: str, stable_key: str) -> dict:
    item = _item(catalogue, kind, stable_key)
    if kind == "tutor_grounding":
        raise BetaOperationsError(
            "tutor_grounding_has_no_student_preview",
            "Tutor calibration grounding is available only in the protected reviewer preview.",
            409,
        )
    if kind == "english_question":
        question: EnglishObjectiveQuestion = item.model
        parts = []
        for part in question.parts:
            response = part.response
            public_response = {"type": response.type}
            if response.type in {"single_choice", "multiple_response"}:
                public_response["options"] = [
                    option.model_dump(mode="json") for option in response.options
                ]
            parts.append(
                {
                    "position": part.position,
                    "prompt": part.prompt,
                    "response": public_response,
                }
            )
        content = {
            "stable_key": question.stable_key,
            "revision": question.revision,
            "title": question.title,
            "difficulty": question.difficulty,
            "question_type": question.question_type,
            "instructions": question.instructions,
            "parts": parts,
        }
    elif kind == "english_lesson":
        lesson: EnglishLesson = item.model
        content = {
            "stable_key": lesson.stable_key,
            "revision": lesson.revision,
            "lesson_code": lesson.lesson_code,
            "title": lesson.title,
            "summary": lesson.summary,
            "estimated_minutes": lesson.estimated_minutes,
            "sections": [
                {
                    "position": section.position,
                    "section_type": section.section_type,
                    "title": section.title,
                    "content": section.content,
                    "question_keys": section.question_keys,
                }
                for section in lesson.sections
            ],
        }
    elif kind == "english_checkpoint_form":
        form: EnglishAssessmentForm = item.model
        content = {
            "form_key": form.form_key,
            "revision": form.revision,
            "form_type": form.form_type,
            "title": form.title,
            "expected_scored_part_count": form.expected_scored_part_count,
            "task_part_distribution": form.task_part_distribution,
            "paired_form_key": form.paired_form_key,
            "module_code": form.module_code,
            "mastery_lesson_keys": form.mastery_lesson_keys,
        }
    elif kind == "english_passage":
        passage: EnglishPassage = item.model
        content = {
            "stable_key": passage.stable_key,
            "revision": passage.revision,
            "title": passage.title,
            "text_type": passage.text_type,
            "paragraphs": passage.paragraphs,
            "attribution": passage.attribution,
        }
    elif kind == "question":
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
    elif kind == "course":
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
    else:
        raise BetaOperationsError(
            "content_preview_unavailable",
            "This content item does not have a learner preview.",
            409,
        )
    return {
        "content_kind": item.kind,
        "stable_key": item.stable_key,
        "revision": item.revision,
        "review_fingerprint": item.fingerprint,
        "public_content": content,
    }


def _reviewer_preview_item(item: CatalogueReviewItem) -> dict:
    return {
        "content_kind": item.kind,
        "stable_key": item.stable_key,
        "revision": item.revision,
        "review_fingerprint": item.fingerprint,
        "batch_id": item.batch_id,
        "review_content": (
            item.model.model_dump(mode="json")
            if hasattr(item.model, "model_dump")
            else item.model
        ),
    }


def reviewer_preview(catalogue: CourseCatalogue, kind: str, stable_key: str) -> dict:
    """Return protected authoring content, including answers and feedback."""
    return _reviewer_preview_item(_item(catalogue, kind, stable_key))


def _bulk_targets(catalogue: CourseCatalogue, body) -> list[CatalogueReviewItem]:
    available = {
        (item.kind, item.stable_key): item for item in catalogue_review_items(catalogue)
    }
    identities = [(target.content_kind, target.stable_key) for target in body.targets]
    if len(identities) != len(set(identities)):
        raise BetaOperationsError(
            "bulk_review_duplicate_target",
            "Each content item may appear only once in a bulk review session.",
            422,
        )
    items = []
    for target in body.targets:
        item = available.get((target.content_kind, target.stable_key))
        if item is None:
            raise BetaOperationsError(
                "content_not_found", "A selected content item was not found.", 404
            )
        _assert_expected(item, target)
        if body.scope == "batch":
            in_scope = item.batch_id == body.scope_key
        elif body.scope == "unit":
            in_scope = item.unit_key == body.scope_key
        else:
            in_scope = body.scope_key in item.route_keys
        if not in_scope:
            raise BetaOperationsError(
                "bulk_review_scope_mismatch",
                "Every selected item must belong to the requested batch, unit or route.",
                422,
            )
        items.append(item)
    return sorted(items, key=lambda item: (item.kind, item.stable_key))


def bulk_reviewer_preview(catalogue: CourseCatalogue, body) -> dict:
    items = _bulk_targets(catalogue, body)
    return {
        "scope": body.scope,
        "scope_key": body.scope_key,
        "items": [_reviewer_preview_item(item) for item in items],
    }


def _assert_review_dimension(item, administrator, dimension):
    required = "english" if item.kind.startswith("english_") else "mathematics"
    if dimension != "editorial" and dimension != required:
        label = "English" if required == "english" else "Mathematics"
        raise BetaOperationsError(
            "content_review_dimension_mismatch",
            f"This item requires {label} or editorial review.",
            422,
        )
    if dimension == required and administrator.role != "academic_admin":
        label = "English" if required == "english" else "Mathematics"
        raise BetaOperationsError(
            "academic_review_required",
            f"Only an academic administrator can record {label} review.",
            403,
        )


def record_bulk_reviews(repository, catalogue, administrator, body, request_id):
    items = _bulk_targets(catalogue, body)
    for item in items:
        _assert_review_dimension(item, administrator, body.dimension)
    with repository._connect() as connection:
        for item in items:
            connection.execute(
                "select pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (f"content:{item.kind}:{item.stable_key}",),
            )
        profile = connection.execute(
            "select email, role::text as role from profiles where id=%s",
            (administrator.learner_id,),
        ).fetchone()
        records = []
        for item in items:
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
                    item.kind,
                    item.stable_key,
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
                    Jsonb(
                        {
                            "content_kind": item.kind,
                            "stable_key": item.stable_key,
                            "source_revision": item.revision,
                            "review_fingerprint": item.fingerprint,
                            "dimension": body.dimension,
                            "decision": body.decision,
                            "bulk_scope": body.scope,
                            "bulk_scope_key": body.scope_key,
                            "bulk_size": len(items),
                        }
                    ),
                ),
            )
            records.append(
                {
                    **dict(row),
                    "reviewer_email": profile["email"],
                    "reviewer_role": profile["role"],
                }
            )
    return {
        "scope": body.scope,
        "scope_key": body.scope_key,
        "recorded_count": len(records),
        "records": records,
    }


def record_review(repository, catalogue, administrator, kind, stable_key, body, request_id):
    item = _item(catalogue, kind, stable_key)
    _assert_expected(item, body)
    _assert_review_dimension(item, administrator, body.dimension)
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
    if kind == "tutor_grounding":
        raise BetaOperationsError(
            "tutor_grounding_lifecycle_not_applicable",
            "Tutor grounding approval unlocks evaluation; it is not a student publication request.",
            409,
        )
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
        subject = "english" if item.kind.startswith("english_") else "mathematics"
        subject_review = serialized[f"{subject}_review"]
        if subject_review is None or subject_review["decision"] != "approved":
            failures.append(
                f"{item.kind}:{item.stable_key} lacks {subject.title()} approval"
            )
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
