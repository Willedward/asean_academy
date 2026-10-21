import json

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from question_bank.english_authoring import (
    claim_english_batch,
    detect_english_duplicates,
    export_english_reviewer_batch,
    release_english_batch,
    validate_english_authoring,
)
from question_bank.english_checking import check_english_answer, normalise_text
from question_bank.english_models import (
    EnglishObjectiveQuestion,
    ShortTextResponse,
    TextNormalisation,
)
from question_bank.english_repository import english_question_content_hash
from question_bank.english_validation import validate_english_foundation


@pytest.fixture(scope="session")
def english_root(repository_root):
    return repository_root / "backend_resources/english/v1"


def test_english_foundation_has_complete_curriculum_and_valid_pilot(english_root):
    report = validate_english_foundation(english_root)

    assert report.valid
    assert len(report.catalogue.modules) == 10
    assert sum(len(module.lessons) for module in report.catalogue.modules) == 51
    assert len(report.lessons) == 4
    assert len(report.passages) == 3
    assert len(report.questions) == 14
    assert not report.issues


def test_every_english_source_matches_its_generated_schema(repository_root, english_root):
    schema_root = repository_root / "backend_resources/english/schema"
    cases = [
        (schema_root / "catalogue-v1.schema.json", [english_root / "catalogue.json"]),
        (schema_root / "source-inventory-v1.schema.json", [english_root / "sources.json"]),
        (schema_root / "passage-v1.schema.json", list((english_root / "passages").glob("*.json"))),
        (schema_root / "lesson-v1.schema.json", list((english_root / "lessons").glob("*.json"))),
        (
            schema_root / "bank-manifest-v1.schema.json",
            list((english_root / "banks").glob("*.json")),
        ),
        (
            schema_root / "objective-question-v1.schema.json",
            list((english_root / "questions").glob("*.json")),
        ),
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


def test_e3_banked_cloze_has_one_shared_bank_and_exact_marking(english_root):
    payload = json.loads((english_root / "questions/eb-l1-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "banked_cloze"
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 8
    assert len(question.parts[0].response.options) == 12
    assert all(
        part.response.options == question.parts[0].response.options for part in question.parts
    )
    assert [part.response.correct_key for part in question.parts] == [
        "C",
        "E",
        "D",
        "L",
        "A",
        "I",
        "G",
        "F",
    ]
    assert check_english_answer(question.parts[0].response, "C")["correct"]
    assert not check_english_answer(question.parts[0].response, "A")["correct"]


def test_e5_reading_group_mixes_comprehension_responses_and_marks_exactly(english_root):
    payload = json.loads((english_root / "questions/er-l1-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "reading_comprehension"
    assert question.feedback_timing == "after_group"
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "single_choice",
        "short_text",
        "short_text",
        "single_choice",
        "multiple_response",
    ]
    assert check_english_answer(question.parts[2].response, "Retain.")["correct"]
    assert check_english_answer(
        question.parts[3].response,
        "The rain garden absorbed the pooled water within a few hours.",
    )["correct"]
    assert check_english_answer(question.parts[5].response, ["D", "A"])["correct"]
    assert not check_english_answer(question.parts[5].response, ["A", "B"])["correct"]


def test_e2_grammar_pilot_covers_boundaries_and_agreement_exactly(english_root):
    keys = [f"eg-l1-{number:03d}" for number in range(1, 7)]
    questions = [
        EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/{key}.json").read_text()
        )
        for key in keys
    ]

    assert [question.exposure_pool for question in questions] == [
        "guided_practice",
        "guided_practice",
        "independent_practice",
        "independent_practice",
        "independent_practice",
        "exit_ticket",
    ]
    assert [question.question_type for question in questions] == [
        "grammar_usage",
        "editing",
        "editing",
        "grammar_usage",
        "grammar_usage",
        "editing",
    ]
    assert check_english_answer(questions[0].parts[0].response, "B")["correct"]
    assert check_english_answer(questions[4].parts[0].response, ["B", "A"])["correct"]
    assert not check_english_answer(questions[4].parts[0].response, ["A"])["correct"]
    assert check_english_answer(questions[5].parts[0].response, "A")["correct"]


def test_draft_pilot_is_not_publishable_before_human_review(english_root):
    report = validate_english_foundation(english_root, publish=True)

    assert not report.valid
    codes = {issue.code for issue in report.errors}
    assert codes == {
        "bank_review_required",
        "lesson_review_required",
        "question_review_required",
    }


def test_english_pilot_has_one_complete_reviewable_batch(english_root):
    report = validate_english_authoring(english_root)

    assert report.valid
    assert [batch.batch_id for batch in report.batches] == [
        "english-eb-b001",
        "english-eg-b001",
        "english-er-b001",
        "english-ev-b001",
    ]
    assert len(report.questions) == 14
    assert not report.duplicates


def test_english_duplicate_scan_catches_exact_and_template_variants(english_root):
    payload = json.loads((english_root / "questions/ev-l1-001.json").read_text())
    first = EnglishObjectiveQuestion.model_validate(payload)
    exact = first.model_copy(update={"stable_key": "ev-l1-900"})
    variant_payload = first.model_dump(mode="json")
    variant_payload["stable_key"] = "ev-l1-901"
    variant_payload["parts"][0]["prompt"] = variant_payload["parts"][0]["prompt"].replace(
        "everyone", "all six hikers"
    )
    variant = EnglishObjectiveQuestion.model_validate(variant_payload)

    exact_matches = detect_english_duplicates([first, exact])
    assert exact_matches[0].kind == "exact_prompt"
    assert detect_english_duplicates([first, variant], near_threshold=0.8)


def test_english_reviewer_export_and_claims_are_reviewable(english_root, tmp_path):
    batch = english_root / "authoring/batches/english-ev-b001.json"
    output = tmp_path / "review"
    result = export_english_reviewer_batch(english_root, batch, output)

    assert result["question_count"] == 6
    assert {path.name for path in output.iterdir()} == {
        "index.html",
        "review.csv",
        "review.md",
    }
    assert "English decision: `pending`" in (output / "review.md").read_text()
    assert "Approved answer" not in (output / "index.html").read_text()
    assert "<strong>Answer:</strong>" in (output / "index.html").read_text()

    claims = tmp_path / "claims.json"
    claims.write_text('{"schema_version":"1.0.0","claims":[]}\n')
    claimed = claim_english_batch(
        claims,
        english_root,
        batch_id="english-ev-b001",
        owner="william",
        branch="content/english-ev-b001",
    )
    assert claimed["status"] == "claimed"
    with pytest.raises(ValueError, match="already claimed"):
        claim_english_batch(
            claims,
            english_root,
            batch_id="english-ev-b001",
            owner="friend",
            branch="content/friend-english",
        )
    released = release_english_batch(claims, batch_id="english-ev-b001", owner="william")
    assert released["status"] == "released"


def test_banked_cloze_reviewer_export_includes_passage_and_one_shared_bank(english_root, tmp_path):
    batch = english_root / "authoring/batches/english-eb-b001.json"
    output = tmp_path / "banked-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "The afternoon broadcast" in page
    assert "Shared word bank" in page
    assert page.count("<strong>C.</strong> deserted") == 1
    assert "{{1}}" in page


def test_reading_reviewer_export_includes_complete_passage_and_answers(english_root, tmp_path):
    batch = english_root / "authoring/batches/english-er-b001.json"
    output = tmp_path / "reading-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "A second life for the school courtyard" in page
    assert "Then a strong storm filled the shallow beds" in page
    assert "retain" in page
    assert "the soil absorbed the pooled water within a few hours" in page


def test_english_question_hash_excludes_review_workflow_metadata(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ev-l1-001.json").read_text()
    )
    reviewed = question.model_copy(update={"status": "reviewed"})

    assert english_question_content_hash(reviewed) == english_question_content_hash(question)
