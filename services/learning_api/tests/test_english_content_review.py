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
        ("english_lesson", "e4-lesson-01"),
        ("english_lesson", "e4-lesson-02"),
        ("english_lesson", "e4-lesson-03"),
        ("english_lesson", "e4-lesson-04"),
        ("english_lesson", "e4-lesson-05"),
        ("english_lesson", "e5-lesson-01"),
        ("english_lesson", "e5-lesson-02"),
        ("english_lesson", "e5-lesson-03"),
        ("english_lesson", "e5-lesson-04"),
        ("english_lesson", "e5-lesson-05"),
        ("english_lesson", "e5-lesson-06"),
        ("english_passage", "english-passage-afternoon-broadcast"),
        ("english_passage", "english-passage-courtyard-rain-garden"),
        ("english_passage", "english-passage-neighbourhood-garden"),
        ("english_passage", "english-passage-workshop-box"),
        ("english_passage", "english-passage-rooftop-garden-record"),
        ("english_passage", "english-passage-rehearsal-rescue"),
        ("english_passage", "english-passage-repair-cafe-record"),
        ("english_passage", "english-passage-hillside-water-survey"),
        ("english_passage", "english-passage-mangrove-nursery-experiment"),
        ("english_passage", "english-passage-river-town-radio-archive"),
        ("english_passage", "english-passage-cooler-school-route"),
        ("english_passage", "english-passage-container-return-experiment"),
        ("english_passage", "english-passage-library-quiet-hour"),
        ("english_question", "eb-l1-001"),
        ("english_question", "eo-l1-001"),
        ("english_question", "eo-l2-001"),
        ("english_question", "eo-l3-001"),
        ("english_question", "eo-l4-001"),
        ("english_question", "eo-l5-001"),
        ("english_question", "er-l1-001"),
        ("english_question", "er-l2-001"),
        ("english_question", "er-l3-001"),
        ("english_question", "er-l4-001"),
        ("english_question", "er-l5-001"),
        ("english_question", "er-l5-002"),
        ("english_question", "ev-l1-001"),
    }
    question = next(item for item in english_items if item.stable_key == "ev-l1-001")
    assert question.batch_id == "english-ev-b001"
    assert question.unit_key == "english-e1"
    banked = next(item for item in english_items if item.stable_key == "eb-l1-001")
    assert banked.batch_id == "english-eb-b001"
    assert banked.unit_key == "english-e3"
    open_cloze = next(item for item in english_items if item.stable_key == "eo-l1-001")
    assert open_cloze.batch_id == "english-eo-b001"
    assert open_cloze.unit_key == "english-e4"
    form_cloze = next(item for item in english_items if item.stable_key == "eo-l2-001")
    assert form_cloze.batch_id == "english-eo-b002"
    assert form_cloze.unit_key == "english-e4"
    lexical_cloze = next(item for item in english_items if item.stable_key == "eo-l3-001")
    assert lexical_cloze.batch_id == "english-eo-b003"
    assert lexical_cloze.unit_key == "english-e4"
    cohesion_cloze = next(item for item in english_items if item.stable_key == "eo-l4-001")
    assert cohesion_cloze.batch_id == "english-eo-b004"
    assert cohesion_cloze.unit_key == "english-e4"
    timed_cloze = next(item for item in english_items if item.stable_key == "eo-l5-001")
    assert timed_cloze.batch_id == "english-eo-b005"
    assert timed_cloze.unit_key == "english-e4"
    reading = next(item for item in english_items if item.stable_key == "er-l1-001")
    assert reading.batch_id == "english-er-b001"
    assert reading.unit_key == "english-e5"
    reference = next(item for item in english_items if item.stable_key == "er-l2-001")
    assert reference.batch_id == "english-er-b002"
    assert reference.unit_key == "english-e5"
    contextual = next(item for item in english_items if item.stable_key == "er-l3-001")
    assert contextual.batch_id == "english-er-b003"
    assert contextual.unit_key == "english-e5"
    stated = next(item for item in english_items if item.stable_key == "er-l4-001")
    assert stated.batch_id == "english-er-b004"
    assert stated.unit_key == "english-e5"
    inferred = next(item for item in english_items if item.stable_key == "er-l5-001")
    assert inferred.batch_id == "english-er-b005"
    assert inferred.unit_key == "english-e5"
    purpose_tone = next(item for item in english_items if item.stable_key == "er-l5-002")
    assert purpose_tone.batch_id == "english-er-b006"
    assert purpose_tone.unit_key == "english-e5"


def test_english_reviewer_preview_contains_answers_but_student_preview_does_not(catalogue):
    protected = reviewer_preview(catalogue, "english_question", "ev-l1-001")
    public = student_preview(catalogue, "english_question", "ev-l1-001")

    assert protected["batch_id"] == "english-ev-b001"
    assert protected["review_content"]["parts"][0]["response"]["correct_key"] == "B"
    assert "correct_key" not in str(public["public_content"])
    assert "choice_rationales" not in str(public["public_content"])
    assert "correct_explanation" not in str(public["public_content"])
    assert public["public_content"]["parts"][0]["response"]["options"]

    protected_open = reviewer_preview(catalogue, "english_question", "eo-l1-001")
    public_open = student_preview(catalogue, "english_question", "eo-l1-001")
    assert protected_open["review_content"]["parts"][0]["response"][
        "canonical_answer"
    ] == "an"
    assert "canonical_answer" not in str(public_open["public_content"])
    assert "accepted_alternatives" not in str(public_open["public_content"])
    assert "rationale" not in str(public_open["public_content"])

    protected_form = reviewer_preview(catalogue, "english_question", "eo-l2-001")
    public_form = student_preview(catalogue, "english_question", "eo-l2-001")
    assert protected_form["review_content"]["parts"][0]["response"][
        "canonical_answer"
    ] == "met"
    assert "canonical_answer" not in str(public_form["public_content"])
    assert "rationale" not in str(public_form["public_content"])

    protected_lexical = reviewer_preview(catalogue, "english_question", "eo-l3-001")
    public_lexical = student_preview(catalogue, "english_question", "eo-l3-001")
    assert protected_lexical["review_content"]["parts"][0]["response"][
        "canonical_answer"
    ] == "notice"
    assert "canonical_answer" not in str(public_lexical["public_content"])
    assert "accepted_alternatives" not in str(public_lexical["public_content"])

    protected_cohesion = reviewer_preview(catalogue, "english_question", "eo-l4-001")
    public_cohesion = student_preview(catalogue, "english_question", "eo-l4-001")
    assert protected_cohesion["review_content"]["parts"][0]["response"][
        "canonical_answer"
    ] == "Farid"
    assert "canonical_answer" not in str(public_cohesion["public_content"])
    assert "accepted_alternatives" not in str(public_cohesion["public_content"])

    protected_timed = reviewer_preview(catalogue, "english_question", "eo-l5-001")
    public_timed = student_preview(catalogue, "english_question", "eo-l5-001")
    assert protected_timed["review_content"]["parts"][0]["response"][
        "canonical_answer"
    ] == "into"
    assert "canonical_answer" not in str(public_timed["public_content"])
    assert "accepted_alternatives" not in str(public_timed["public_content"])

    protected_reference = reviewer_preview(catalogue, "english_question", "er-l2-001")
    public_reference = student_preview(catalogue, "english_question", "er-l2-001")
    assert protected_reference["review_content"]["parts"][1]["response"][
        "canonical_answer"
    ] == "Dr Arun"
    assert "canonical_answer" not in str(public_reference["public_content"])
    assert "choice_rationales" not in str(public_reference["public_content"])

    protected_contextual = reviewer_preview(catalogue, "english_question", "er-l3-001")
    public_contextual = student_preview(catalogue, "english_question", "er-l3-001")
    assert protected_contextual["review_content"]["parts"][1]["response"][
        "canonical_answer"
    ] == "cryptic"
    assert protected_contextual["review_content"]["parts"][4]["response"][
        "canonical_answer"
    ] == "corroborated"
    assert "canonical_answer" not in str(public_contextual["public_content"])
    assert "choice_rationales" not in str(public_contextual["public_content"])

    protected_stated = reviewer_preview(catalogue, "english_question", "er-l4-001")
    public_stated = student_preview(catalogue, "english_question", "er-l4-001")
    assert protected_stated["review_content"]["parts"][0]["response"]["correct_key"] == "A"
    assert protected_stated["review_content"]["parts"][1]["response"][
        "canonical_answer"
    ] == "one metre above the ground"
    assert protected_stated["review_content"]["parts"][3]["response"]["correct_keys"] == [
        "A",
        "D",
    ]
    assert protected_stated["review_content"]["parts"][4]["response"][
        "canonical_answer"
    ] == "a six-week trial of shade sails at the main gate"
    assert protected_stated["review_content"]["parts"][5]["response"]["correct_key"] == "A"
    assert "correct_key" not in str(public_stated["public_content"])
    assert "correct_keys" not in str(public_stated["public_content"])
    assert "canonical_answer" not in str(public_stated["public_content"])
    assert "choice_rationales" not in str(public_stated["public_content"])
    assert "rationale" not in str(public_stated["public_content"])

    protected_inferred = reviewer_preview(catalogue, "english_question", "er-l5-001")
    public_inferred = student_preview(catalogue, "english_question", "er-l5-001")
    assert protected_inferred["review_content"]["parts"][0]["response"]["correct_key"] == "B"
    assert protected_inferred["review_content"]["parts"][1]["response"]["correct_key"] == "C"
    assert protected_inferred["review_content"]["parts"][2]["response"]["correct_key"] == "A"
    assert protected_inferred["review_content"]["parts"][3]["response"]["correct_keys"] == [
        "A",
        "D",
    ]
    assert protected_inferred["review_content"]["parts"][4]["response"]["correct_key"] == "C"
    assert protected_inferred["review_content"]["parts"][5]["response"]["correct_key"] == "A"
    assert "correct_key" not in str(public_inferred["public_content"])
    assert "correct_keys" not in str(public_inferred["public_content"])
    assert "choice_rationales" not in str(public_inferred["public_content"])
    assert "correct_explanation" not in str(public_inferred["public_content"])

    protected_purpose = reviewer_preview(catalogue, "english_question", "er-l5-002")
    public_purpose = student_preview(catalogue, "english_question", "er-l5-002")
    assert protected_purpose["review_content"]["parts"][0]["response"]["correct_key"] == "A"
    assert protected_purpose["review_content"]["parts"][1]["response"]["correct_key"] == "C"
    assert protected_purpose["review_content"]["parts"][2]["response"]["correct_key"] == "B"
    assert protected_purpose["review_content"]["parts"][3]["response"]["correct_key"] == "B"
    assert protected_purpose["review_content"]["parts"][4]["response"]["correct_keys"] == [
        "A",
        "C",
    ]
    assert protected_purpose["review_content"]["parts"][5]["response"]["correct_key"] == "D"
    assert "correct_key" not in str(public_purpose["public_content"])
    assert "correct_keys" not in str(public_purpose["public_content"])
    assert "choice_rationales" not in str(public_purpose["public_content"])
    assert "correct_explanation" not in str(public_purpose["public_content"])


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
