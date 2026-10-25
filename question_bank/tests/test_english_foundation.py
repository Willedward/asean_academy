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
    assert len(report.lessons) == 16
    assert len(report.passages) == 14
    assert len(report.questions) == 26
    assert not report.issues


def test_e6_task_analysis_preserves_every_prompt_requirement(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l1-001.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW6.1"
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "B")["correct"]
    assert check_english_answer(question.parts[3].response, ["D", "A", "C"])["correct"]
    assert not check_english_answer(question.parts[3].response, ["A", "C"])["correct"]


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


def test_e4_open_cloze_uses_exact_reviewed_words_and_delayed_feedback(english_root):
    payload = json.loads((english_root / "questions/eo-l1-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "open_cloze"
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 8
    assert all(part.response.type == "short_text" for part in question.parts)
    assert [part.response.canonical_answer for part in question.parts] == [
        "an",
        "it",
        "had",
        "with",
        "although",
        "which",
        "until",
        "they",
    ]
    assert check_english_answer(question.parts[0].response, "AN")["correct"]
    assert check_english_answer(question.parts[4].response, "though")["correct"]
    assert check_english_answer(question.parts[6].response, "till")["correct"]
    assert not check_english_answer(question.parts[5].response, "that")["correct"]


def test_e4_form_and_agreement_cloze_covers_controlled_transformations(english_root):
    payload = json.loads((english_root / "questions/eo-l2-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "open_cloze"
    assert question.feedback_timing == "after_group"
    assert question.outcome_code == "EO4.2"
    assert [part.response.canonical_answer for part in question.parts] == [
        "met",
        "planters",
        "checks",
        "drained",
        "brighter",
        "growth",
        "measurements",
        "themselves",
    ]
    assert all(part.response.type == "short_text" for part in question.parts)
    assert check_english_answer(question.parts[0].response, "MET")["correct"]
    assert check_english_answer(question.parts[6].response, "measurements")["correct"]
    assert not check_english_answer(question.parts[6].response, "measures")["correct"]


def test_e4_lexical_cloze_uses_collocations_and_reviewed_equivalents(english_root):
    payload = json.loads((english_root / "questions/eo-l3-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "open_cloze"
    assert question.feedback_timing == "after_group"
    assert question.outcome_code == "EO4.3"
    assert question.difficulty == 4
    assert [part.response.canonical_answer for part in question.parts] == [
        "notice",
        "charge",
        "eye",
        "halt",
        "verge",
        "minds",
        "role",
        "difference",
    ]
    assert check_english_answer(question.parts[3].response, "STOP")["correct"]
    assert check_english_answer(question.parts[4].response, "brink")["correct"]
    assert check_english_answer(question.parts[6].response, "part")["correct"]
    assert not check_english_answer(question.parts[1].response, "control")["correct"]


def test_e4_cohesion_cloze_requires_cross_sentence_links(english_root):
    payload = json.loads((english_root / "questions/eo-l4-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "open_cloze"
    assert question.feedback_timing == "after_group"
    assert question.outcome_code == "EO4.4"
    assert question.difficulty == 4
    assert [part.response.canonical_answer for part in question.parts] == [
        "Farid",
        "This",
        "However",
        "then",
        "them",
        "again",
        "his",
        "it",
    ]
    assert check_english_answer(question.parts[1].response, "THAT")["correct"]
    assert check_english_answer(question.parts[2].response, "yet")["correct"]
    assert check_english_answer(question.parts[2].response, "instead")["correct"]
    assert not check_english_answer(question.parts[4].response, "they")["correct"]


def test_e4_timed_checkpoint_integrates_all_open_cloze_evidence(english_root):
    payload = json.loads((english_root / "questions/eo-l5-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "open_cloze"
    assert question.feedback_timing == "after_group"
    assert question.exposure_pool == "exit_ticket"
    assert question.outcome_code == "EO4.5"
    assert question.difficulty == 5
    assert [part.response.canonical_answer for part in question.parts] == [
        "into",
        "but",
        "with",
        "loose",
        "than",
        "again",
        "unless",
        "had",
    ]
    assert check_english_answer(question.parts[1].response, "YET")["correct"]
    assert check_english_answer(question.parts[6].response, "unless")["correct"]
    assert not check_english_answer(question.parts[6].response, "if")["correct"]


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


def test_e5_reference_chain_group_resolves_people_events_and_labels_exactly(english_root):
    payload = json.loads((english_root / "questions/er-l2-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "reading_comprehension"
    assert question.feedback_timing == "after_group"
    assert question.outcome_code == "ER5.2"
    assert question.difficulty == 3
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "short_text",
        "short_text",
        "single_choice",
        "single_choice",
        "multiple_response",
    ]
    assert check_english_answer(question.parts[0].response, "A")["correct"]
    assert check_english_answer(question.parts[1].response, "The coastal ecologist.")["correct"]
    assert check_english_answer(
        question.parts[2].response,
        "The club moved half the trays to a covered walkway and left the others beside the sports shed.",
    )["correct"]
    assert check_english_answer(question.parts[5].response, ["D", "A"])["correct"]
    assert not check_english_answer(question.parts[4].response, "A")["correct"]


def test_e5_context_synonym_group_preserves_meaning_and_word_class(english_root):
    payload = json.loads((english_root / "questions/er-l3-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "reading_comprehension"
    assert question.feedback_timing == "after_group"
    assert question.outcome_code == "ER5.3"
    assert question.difficulty == 4
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "short_text",
        "single_choice",
        "single_choice",
        "short_text",
        "multiple_response",
    ]
    assert check_english_answer(question.parts[0].response, "B")["correct"]
    assert check_english_answer(question.parts[1].response, "Cryptic.")["correct"]
    assert check_english_answer(question.parts[2].response, "A")["correct"]
    assert check_english_answer(question.parts[4].response, "CORROBORATED")["correct"]
    assert check_english_answer(question.parts[5].response, ["D", "A"])["correct"]
    assert not check_english_answer(question.parts[5].response, ["A", "E"])["correct"]


def test_e5_stated_evidence_group_locates_and_preserves_explicit_details(english_root):
    payload = json.loads((english_root / "questions/er-l4-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "reading_comprehension"
    assert question.feedback_timing == "after_group"
    assert question.outcome_code == "ER5.4"
    assert question.difficulty == 4
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "short_text",
        "single_choice",
        "multiple_response",
        "short_text",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "A")["correct"]
    assert check_english_answer(question.parts[1].response, "1 metre above ground.")["correct"]
    assert check_english_answer(question.parts[2].response, "C")["correct"]
    assert check_english_answer(question.parts[3].response, ["D", "A"])["correct"]
    assert check_english_answer(
        question.parts[4].response, "Shade sails at the main gate."
    )["correct"]
    assert check_english_answer(question.parts[5].response, "A")["correct"]
    assert not check_english_answer(question.parts[5].response, "B")["correct"]


def test_e5_bounded_inference_group_preserves_scope_and_uncertainty(english_root):
    payload = json.loads((english_root / "questions/er-l5-001.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "reading_comprehension"
    assert question.feedback_timing == "after_group"
    assert question.outcome_code == "ER5.5"
    assert question.difficulty == 4
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "B")["correct"]
    assert check_english_answer(question.parts[1].response, "C")["correct"]
    assert check_english_answer(question.parts[2].response, "A")["correct"]
    assert check_english_answer(question.parts[3].response, ["D", "A"])["correct"]
    assert check_english_answer(question.parts[4].response, "C")["correct"]
    assert check_english_answer(question.parts[5].response, "A")["correct"]
    assert not check_english_answer(question.parts[0].response, "A")["correct"]


def test_e5_purpose_tone_and_main_idea_group_marks_distinct_reading_tasks(english_root):
    payload = json.loads((english_root / "questions/er-l5-002.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "reading_comprehension"
    assert question.feedback_timing == "after_group"
    assert question.outcome_code == "ER5.6"
    assert question.difficulty == 4
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "A")["correct"]
    assert check_english_answer(question.parts[1].response, "C")["correct"]
    assert check_english_answer(question.parts[2].response, "B")["correct"]
    assert check_english_answer(question.parts[3].response, "B")["correct"]
    assert check_english_answer(question.parts[4].response, ["C", "A"])["correct"]
    assert check_english_answer(question.parts[5].response, "D")["correct"]
    assert not check_english_answer(question.parts[0].response, "C")["correct"]


def test_e5_two_passage_group_integrates_reading_skills_and_exact_marking(english_root):
    payload = json.loads((english_root / "questions/er-l5-003.json").read_text())
    question = EnglishObjectiveQuestion.model_validate(payload)

    assert question.question_type == "reading_comprehension"
    assert question.feedback_timing == "after_group"
    assert question.outcome_code == "ER5.7"
    assert question.difficulty == 5
    assert len(question.parts) == 8
    assert all(part.response.type == "single_choice" for part in question.parts)
    assert [
        check_english_answer(part.response, answer)["correct"]
        for part, answer in zip(
            question.parts, ["A", "B", "B", "A", "B", "B", "A", "C"], strict=True
        )
    ] == [True] * 8
    assert not check_english_answer(question.parts[7].response, "A")["correct"]


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
        "english-eo-b001",
        "english-eo-b002",
        "english-eo-b003",
        "english-eo-b004",
        "english-eo-b005",
        "english-er-b001",
        "english-er-b002",
        "english-er-b003",
        "english-er-b004",
        "english-er-b005",
        "english-er-b006",
        "english-er-b007",
        "english-ev-b001",
        "english-ex-b001",
    ]
    assert len(report.questions) == 26
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


def test_open_cloze_reviewer_export_includes_passage_and_approved_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-eo-b001.json"
    output = tmp_path / "open-cloze-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "The workshop box" in page
    assert "Shared word bank" not in page
    assert "{{1}}" in page
    assert "<strong>Answer:</strong> although" in page
    assert "<strong>Answer:</strong> until" in page


def test_form_cloze_reviewer_export_includes_anchor_transformations(english_root, tmp_path):
    batch = english_root / "authoring/batches/english-eo-b002.json"
    output = tmp_path / "form-cloze-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "The rooftop garden record" in page
    assert "{{8}}" in page
    assert "<strong>Answer:</strong> brighter" in page
    assert "<strong>Answer:</strong> measurements" in page


def test_lexical_cloze_reviewer_export_includes_collocations_and_alternatives(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-eo-b003.json"
    output = tmp_path / "lexical-cloze-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "The rehearsal rescue" in page
    assert "{{8}}" in page
    assert "<strong>Answer:</strong> notice" in page
    assert "<strong>Answer:</strong> difference" in page
    assert "brink" in page


def test_cohesion_cloze_reviewer_export_includes_cross_sentence_evidence(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-eo-b004.json"
    output = tmp_path / "cohesion-cloze-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "The repair café record" in page
    assert "{{8}}" in page
    assert "<strong>Answer:</strong> Farid" in page
    assert "<strong>Answer:</strong> again" in page
    assert "Instead" in page


def test_timed_cloze_reviewer_export_includes_checkpoint_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-eo-b005.json"
    output = tmp_path / "timed-cloze-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "The hillside water survey" in page
    assert "{{8}}" in page
    assert "<strong>Answer:</strong> into" in page
    assert "<strong>Answer:</strong> unless" in page
    assert "yet" in page


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


def test_context_synonym_reviewer_export_includes_passage_pin_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-er-b003.json"
    output = tmp_path / "context-synonym-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "Voices from the river town" in page
    assert "Some labels were cryptic" in page
    assert "<strong>Answer:</strong> B" in page
    assert "<strong>Answer:</strong> cryptic" in page
    assert "<strong>Answer:</strong> corroborated" in page
    assert "<strong>Answer:</strong> A, D" in page


def test_stated_evidence_reviewer_export_includes_passage_pin_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-er-b004.json"
    output = tmp_path / "stated-evidence-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "A cooler route to school" in page
    assert "wet surfaces become temporarily cooler" in page
    assert "<strong>Answer:</strong> A" in page
    assert "<strong>Answer:</strong> one metre above the ground" in page
    assert "<strong>Answer:</strong> C" in page
    assert "<strong>Answer:</strong> A, D" in page
    assert "a six-week trial of shade sails at the main gate" in page


def test_bounded_inference_reviewer_export_includes_passage_pin_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-er-b005.json"
    output = tmp_path / "bounded-inference-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "The container return experiment" in page
    assert "Because both changes were introduced together" in page
    assert "<strong>Answer:</strong> B" in page
    assert "<strong>Answer:</strong> C" in page
    assert "<strong>Answer:</strong> A" in page
    assert "<strong>Answer:</strong> A, D" in page
    assert "Compare waste per visitor or per meal sold" in page


def test_purpose_tone_reviewer_export_includes_passage_pin_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-er-b006.json"
    output = tmp_path / "purpose-tone-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "The library&#x27;s quiet first hour" in page
    assert "Those figures are encouraging" in page
    assert "<strong>Answer:</strong> A" in page
    assert "<strong>Answer:</strong> C" in page
    assert "<strong>Answer:</strong> B" in page
    assert "<strong>Answer:</strong> A, C" in page
    assert "states the next evidence to collect" in page


def test_two_passage_reviewer_export_includes_both_texts_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-er-b007.json"
    output = tmp_path / "two-passage-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "PASSAGE A — A map made of sound" in page
    assert "PASSAGE B — The bell at dusk" in page
    assert page.count("<strong>Answer:</strong>") == 8
    assert "<strong>Answer:</strong> A" in page
    assert "<strong>Answer:</strong> B" in page
    assert "<strong>Answer:</strong> C" in page
    assert "one source of evidence" in page
    assert "people, surroundings and shared responses" in page


def test_composition_planning_reviewer_export_contains_prompt_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b001.json"
    output = tmp_path / "composition-planning-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "The ASEAN Youth Learning Blog" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> B" in page
    assert "<strong>Answer:</strong> A, C, D" in page
    assert "real past experience or a credible future scenario" in page


def test_reference_chain_reviewer_export_includes_passage_and_full_referents(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-er-b002.json"
    output = tmp_path / "reference-chain-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "The mangrove nursery experiment" in page
    assert "a later storm damaged very few of them" in page
    assert "Dr Arun" in page
    assert "moving half the trays to a covered walkway" in page
    assert "A, D" in page


def test_english_question_hash_excludes_review_workflow_metadata(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ev-l1-001.json").read_text()
    )
    reviewed = question.model_copy(update={"status": "reviewed"})

    assert english_question_content_hash(reviewed) == english_question_content_hash(question)
