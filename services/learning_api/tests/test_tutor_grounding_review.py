"""Source and safety coverage for administrator tutor-grounding review."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from learning_api.admin_repository import BetaOperationsError
from learning_api.content_review import (
    catalogue_review_items,
    request_lifecycle,
    review_fingerprint,
    reviewer_preview,
    student_preview,
)
from learning_api.content_review_contracts import CreateLifecycleRequest
from learning_api.course_catalogue import CourseCatalogue

ROOT = Path(__file__).resolve().parents[3]
GROUNDING_KEY = "g3-sec1-n2-tutor-grounding-v1"
GROUNDING_PATH = (
    ROOT / "backend_resources/tutor_evaluations/g3_math/v1/n2_grounding_draft.json"
)


def test_n2_tutor_grounding_is_a_hash_bound_protected_review_item():
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)
    item = next(
        item
        for item in catalogue_review_items(catalogue)
        if item.stable_key == GROUNDING_KEY
    )

    assert item.kind == "tutor_grounding"
    assert item.revision == 1
    assert item.source_status == "draft"
    assert item.outcome_code == "N2"
    assert len(item.source_hash) == 64
    assert len(item.fingerprint) == 64

    preview = reviewer_preview(catalogue, item.kind, item.stable_key)
    assert preview["content_kind"] == "tutor_grounding"
    assert preview["review_content"]["scope"].startswith("Secondary 1")
    assert set(preview["review_content"]["sections_by_outcome"]) == {
        "2.1",
        "2.2",
        "2.3",
    }


def test_tutor_grounding_has_no_student_preview_or_publication_lifecycle():
    catalogue = CourseCatalogue(ROOT, allow_drafts=True)
    item = next(
        item
        for item in catalogue_review_items(catalogue)
        if item.stable_key == GROUNDING_KEY
    )

    with pytest.raises(BetaOperationsError, match="protected reviewer preview"):
        student_preview(catalogue, item.kind, item.stable_key)

    body = CreateLifecycleRequest(
        source_revision=item.revision,
        source_content_sha256=item.source_hash,
        review_fingerprint=item.fingerprint,
        action="publish",
        reason="This deliberately verifies the lifecycle safety boundary.",
    )
    with pytest.raises(BetaOperationsError, match="unlocks evaluation"):
        request_lifecycle(
            object(),
            catalogue,
            object(),
            item.kind,
            item.stable_key,
            body,
            "grounding-lifecycle-test",
        )


def test_grounding_review_metadata_does_not_invalidate_approved_mathematics():
    draft = json.loads(GROUNDING_PATH.read_text(encoding="utf-8"))
    reviewed = copy.deepcopy(draft)
    reviewed["status"] = "reviewed"
    reviewed["review"] = {
        "mathematics": "approved",
        "editorial": "approved",
        "reviewed_by": ["reviewer@example.test"],
        "reviewed_at": "2026-10-03T12:00:00+08:00",
        "notes": "Recorded through the append-only administrator workflow.",
    }

    assert review_fingerprint(draft) == review_fingerprint(reviewed)

    corrected = copy.deepcopy(reviewed)
    corrected["sections_by_outcome"]["2.1"][0]["content"]["blocks"][0][
        "text"
    ] += " Material mathematical change."
    assert review_fingerprint(draft) != review_fingerprint(corrected)
