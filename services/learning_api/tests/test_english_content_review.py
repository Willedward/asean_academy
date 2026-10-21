from pathlib import Path

import pytest

from learning_api.admin_repository import BetaOperationsError
from learning_api.content_review import (
    _assert_review_dimension,
    _serialize_item,
    catalogue_review_items,
    reviewer_preview,
    student_preview,
)
from learning_api.course_catalogue import CourseCatalogue
from learning_api.identity import AuthenticatedLearner

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def catalogue():
    return CourseCatalogue(REPOSITORY_ROOT, allow_drafts=True)


def test_english_lessons_passages_and_questions_enter_admin_review(catalogue):
    items = catalogue_review_items(catalogue)
    english_items = [item for item in items if item.kind.startswith("english_")]

    assert {(item.kind, item.stable_key) for item in english_items} >= {
        ("english_lesson", "e1-lesson-01"),
        ("english_lesson", "e3-lesson-01"),
        ("english_lesson", "e5-lesson-01"),
        ("english_passage", "english-passage-afternoon-broadcast"),
        ("english_passage", "english-passage-courtyard-rain-garden"),
        ("english_passage", "english-passage-neighbourhood-garden"),
        ("english_question", "eb-l1-001"),
        ("english_question", "er-l1-001"),
        ("english_question", "ev-l1-001"),
    }
    question = next(item for item in english_items if item.stable_key == "ev-l1-001")
    assert question.batch_id == "english-ev-b001"
    assert question.unit_key == "english-e1"
    banked = next(item for item in english_items if item.stable_key == "eb-l1-001")
    assert banked.batch_id == "english-eb-b001"
    assert banked.unit_key == "english-e3"
    reading = next(item for item in english_items if item.stable_key == "er-l1-001")
    assert reading.batch_id == "english-er-b001"
    assert reading.unit_key == "english-e5"


def test_english_reviewer_preview_contains_answers_but_student_preview_does_not(catalogue):
    protected = reviewer_preview(catalogue, "english_question", "ev-l1-001")
    public = student_preview(catalogue, "english_question", "ev-l1-001")

    assert protected["batch_id"] == "english-ev-b001"
    assert protected["review_content"]["parts"][0]["response"]["correct_key"] == "B"
    assert "correct_key" not in str(public["public_content"])
    assert "choice_rationales" not in str(public["public_content"])
    assert "correct_explanation" not in str(public["public_content"])
    assert public["public_content"]["parts"][0]["response"]["options"]


def test_english_review_requires_english_and_editorial_dimensions(catalogue):
    item = next(
        item
        for item in catalogue_review_items(catalogue)
        if item.kind == "english_question" and item.stable_key == "ev-l1-001"
    )
    academic = AuthenticatedLearner("admin", "academic_admin", "admin@example.test")
    content_admin = AuthenticatedLearner("editor", "content_admin", "editor@example.test")

    _assert_review_dimension(item, academic, "english")
    _assert_review_dimension(item, content_admin, "editorial")
    with pytest.raises(BetaOperationsError, match="English or editorial"):
        _assert_review_dimension(item, academic, "mathematics")
    with pytest.raises(BetaOperationsError, match="academic administrator"):
        _assert_review_dimension(item, content_admin, "english")


def test_english_queue_uses_english_approval_as_its_subject_gate(catalogue):
    item = next(item for item in catalogue_review_items(catalogue) if item.kind == "english_lesson")
    empty = _serialize_item(item, {}, {})

    assert empty["mathematics_review"] is None
    assert empty["english_review"] is None
    assert empty["blockers"] == [
        "English approval is required.",
        "Editorial approval is required.",
    ]
