import json

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from question_bank.english_checking import check_english_answer, normalise_text
from question_bank.english_models import (
    EnglishObjectiveQuestion,
    ShortTextResponse,
    TextNormalisation,
)
from question_bank.english_validation import validate_english_foundation


@pytest.fixture(scope="session")
def english_root(repository_root):
    return repository_root / "backend_resources/english/v1"


def test_english_foundation_has_complete_curriculum_and_valid_pilot(english_root):
    report = validate_english_foundation(english_root)

    assert report.valid
    assert len(report.catalogue.modules) == 10
    assert sum(len(module.lessons) for module in report.catalogue.modules) == 51
    assert len(report.lessons) == 1
    assert len(report.questions) == 6
    assert not report.issues


def test_every_english_source_matches_its_generated_schema(repository_root, english_root):
    schema_root = repository_root / "backend_resources/english/schema"
    cases = [
        (schema_root / "catalogue-v1.schema.json", [english_root / "catalogue.json"]),
        (schema_root / "source-inventory-v1.schema.json", [english_root / "sources.json"]),
        (schema_root / "passage-v1.schema.json", list((english_root / "passages").glob("*.json"))),
        (schema_root / "lesson-v1.schema.json", list((english_root / "lessons").glob("*.json"))),
        (schema_root / "bank-manifest-v1.schema.json", list((english_root / "banks").glob("*.json"))),
        (schema_root / "objective-question-v1.schema.json", list((english_root / "questions").glob("*.json"))),
    ]
    for schema_path, sources in cases:
        schema = json.loads(schema_path.read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        for source in sources:
            assert not list(validator.iter_errors(json.loads(source.read_text())))


def test_choice_marking_is_exact_and_does_not_call_a_model(english_root):
    payload = json.loads((english_root / "questions/ev-l1-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)
    response = question.parts[0].response

    assert check_english_answer(response, " b ") == {"correct": True, "error": None}
    assert check_english_answer(response, "A") == {"correct": False, "error": None}
    assert check_english_answer(response, "Z")["error"]


def test_short_text_only_accepts_reviewed_alternatives_after_safe_normalisation():
    spec = ShortTextResponse(
        type="short_text",
        canonical_answer="the community garden",
        accepted_alternatives=["community garden"],
        normalisation=TextNormalisation(strip_terminal_punctuation=True),
        rationale="Both approved forms identify the same explicit referent.",
    )

    assert normalise_text("  The   COMMUNITY garden. ", spec.normalisation) == (
        "the community garden"
    )
    assert check_english_answer(spec, "The community garden.")["correct"]
    assert not check_english_answer(spec, "the garden project")["correct"]


def test_passage_groups_cannot_reveal_feedback_one_item_at_a_time(english_root):
    payload = json.loads((english_root / "questions/ev-l1-001.json").read_text())
    payload["question_type"] = "reading_comprehension"
    payload["feedback_timing"] = "after_item"
    payload["passage_ref"] = {
        "stable_key": "english-passage-neighbourhood-garden",
        "revision": 1,
        "content_sha256": "0" * 64,
    }

    with pytest.raises(ValidationError, match="complete group"):
        EnglishObjectiveQuestion.model_validate(payload)


def test_draft_pilot_is_not_publishable_before_human_review(english_root):
    report = validate_english_foundation(english_root, publish=True)

    assert not report.valid
    codes = {issue.code for issue in report.errors}
    assert codes == {
        "bank_review_required",
        "lesson_review_required",
        "question_review_required",
    }
