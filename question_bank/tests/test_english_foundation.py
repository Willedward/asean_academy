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
    EnglishCurriculumCatalogue,
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
    assert len(report.lessons) == 36
    assert len(report.passages) == 37
    assert len(report.questions) == 98
    assert report.exam_profile is not None
    assert report.exam_profile.profile_key == "asean-english-sec1-id-reported-v1"
    assert set(report.exam_profile.excluded_task_types) == {
        "editing_section",
        "own_words_short_answer",
    }
    assert len(report.forms) == 19
    assert {form.status for form in report.forms} == {"draft"}
    assert report.catalogue.route_lesson_codes("core") == [
        "E0.1",
        "E0.2",
        "E1.1",
        "E1.2",
        "E1.4",
        "E1.5",
        "E1.6",
        "E2.1",
        "E2.2",
        "E2.3",
        "E2.6",
        "E3.1",
        "E3.2",
        "E3.4",
        "E4.1",
        "E4.2",
        "E4.4",
        "E4.5",
        "E5.1",
        "E5.2",
        "E5.3",
        "E5.5",
        "E5.6",
        "E5.7",
        "E6.1",
        "E6.2",
        "E6.5",
        "E7.1",
        "E7.2",
        "E8.4",
        "E9.1",
        "E9.5",
    ]
    assert report.catalogue.route_lesson_codes("sprint") == [
        "E0.1",
        "E0.2",
        "E1.1",
        "E1.6",
        "E2.2",
        "E3.1",
        "E4.1",
        "E4.5",
        "E5.2",
        "E5.3",
        "E5.7",
        "E6.1",
        "E6.5",
        "E7.2",
        "E8.4",
        "E9.5",
    ]
    summary = report.as_dict()
    assert summary["route_lesson_counts"] == {"full": 51, "core": 32, "sprint": 16}
    assert summary["route_authored_lesson_counts"] == {
        "full": 36,
        "core": 25,
        "sprint": 16,
    }
    assert summary["route_exit_ticket_lesson_counts"] == {
        "full": 36,
        "core": 25,
        "sprint": 16,
    }
    assert summary["route_parallel_retry_lesson_counts"] == {
        "full": 16,
        "core": 16,
        "sprint": 16,
    }
    assert summary["route_unauthored_lesson_codes"]["sprint"] == []
    assert not report.issues


def test_protected_english_forms_pin_matched_disjoint_twenty_part_blueprints(english_root):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    expected = {
        "baseline": (
            ["ev-l5-003", "eb-l1-003", "eo-l5-003", "er-l5-005"],
            "baseline_diagnostic",
        ),
        "endline": (
            ["ev-l5-004", "eb-l1-004", "eo-l5-004", "er-l5-006"],
            "endline_diagnostic",
        ),
        "endline_reserve": (
            ["ev-l5-005", "eb-l1-005", "eo-l5-005", "er-l5-007"],
            "protected_reserve",
        ),
    }
    selected_keys = set()

    measurement_forms = [form for form in report.forms if form.form_type != "checkpoint"]
    assert len(measurement_forms) == 3
    for form in measurement_forms:
        question_keys, exposure_pool = expected[form.form_type]
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert form.question_keys == question_keys
        assert sum(len(question.parts) for question in selected) == 20
        assert {
            question.question_type: len(question.parts) for question in selected
        } == form.task_part_distribution
        assert {question.exposure_pool for question in selected} == {exposure_pool}
        assert selected_keys.isdisjoint(form.question_keys)
        selected_keys.update(form.question_keys)

    assert len(selected_keys) == 12


def test_e1_checkpoint_forms_have_reciprocal_disjoint_mastery_scope(english_root):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    forms = sorted(
        (
            form
            for form in report.forms
            if form.form_type == "checkpoint" and form.module_code == "E1"
        ),
        key=lambda form: form.form_key,
    )

    assert [form.form_key for form in forms] == [
        "english-checkpoint-e1-vocabulary-a-v1",
        "english-checkpoint-e1-vocabulary-b-v1",
    ]
    assert forms[0].paired_form_key == forms[1].form_key
    assert forms[1].paired_form_key == forms[0].form_key
    assert forms[0].module_code == forms[1].module_code == "E1"
    assert forms[0].mastery_lesson_keys == forms[1].mastery_lesson_keys == [
        "e1-lesson-01",
        "e1-lesson-06",
    ]
    assert forms[0].task_part_distribution == forms[1].task_part_distribution == {
        "vocabulary_in_context": 5
    }
    assert set(forms[0].question_keys).isdisjoint(forms[1].question_keys)
    for form in forms:
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert sum(len(question.parts) for question in selected) == 5
        assert {question.exposure_pool for question in selected} == {
            "module_checkpoint"
        }


def test_e0_checkpoint_forms_sample_both_orientation_outcomes(english_root):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    forms = sorted(
        (
            form
            for form in report.forms
            if form.form_type == "checkpoint" and form.module_code == "E0"
        ),
        key=lambda form: form.form_key,
    )

    assert [form.form_key for form in forms] == [
        "english-checkpoint-e0-orientation-a-v1",
        "english-checkpoint-e0-orientation-b-v1",
    ]
    assert forms[0].paired_form_key == forms[1].form_key
    assert forms[1].paired_form_key == forms[0].form_key
    assert forms[0].mastery_lesson_keys == forms[1].mastery_lesson_keys == [
        "e0-lesson-01",
        "e0-lesson-02",
    ]
    assert forms[0].task_part_distribution == forms[1].task_part_distribution == {
        "exam_strategy": 5
    }
    assert set(forms[0].question_keys).isdisjoint(forms[1].question_keys)
    for form in forms:
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert [question.outcome_code for question in selected] == ["EX0.1", "EX0.2"]
        assert [len(question.parts) for question in selected] == [3, 2]
        assert sum(len(question.parts) for question in selected) == 5
        assert {question.exposure_pool for question in selected} == {
            "module_checkpoint"
        }


def test_e2_checkpoint_forms_are_disjoint_and_scope_sprint_grammar(english_root):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    forms = sorted(
        (
            form
            for form in report.forms
            if form.form_type == "checkpoint" and form.module_code == "E2"
        ),
        key=lambda form: form.form_key,
    )

    assert [form.form_key for form in forms] == [
        "english-checkpoint-e2-grammar-a-v1",
        "english-checkpoint-e2-grammar-b-v1",
    ]
    assert forms[0].paired_form_key == forms[1].form_key
    assert forms[1].paired_form_key == forms[0].form_key
    assert forms[0].mastery_lesson_keys == forms[1].mastery_lesson_keys == [
        "e2-lesson-02"
    ]
    assert forms[0].task_part_distribution == forms[1].task_part_distribution == {
        "grammar_usage": 5
    }
    assert set(forms[0].question_keys).isdisjoint(forms[1].question_keys)
    for form in forms:
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert {question.outcome_code for question in selected} == {"EG2.2"}
        assert sum(len(question.parts) for question in selected) == 5
        assert {question.exposure_pool for question in selected} == {
            "module_checkpoint"
        }


def test_e3_checkpoint_forms_are_disjoint_complete_banked_cloze_passages(english_root):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    forms = sorted(
        (
            form
            for form in report.forms
            if form.form_type == "checkpoint" and form.module_code == "E3"
        ),
        key=lambda form: form.form_key,
    )

    assert [form.form_key for form in forms] == [
        "english-checkpoint-e3-banked-cloze-a-v1",
        "english-checkpoint-e3-banked-cloze-b-v1",
    ]
    assert forms[0].paired_form_key == forms[1].form_key
    assert forms[1].paired_form_key == forms[0].form_key
    assert forms[0].mastery_lesson_keys == forms[1].mastery_lesson_keys == [
        "e3-lesson-01"
    ]
    assert forms[0].task_part_distribution == forms[1].task_part_distribution == {
        "banked_cloze": 5
    }
    assert set(forms[0].question_keys).isdisjoint(forms[1].question_keys)
    for form in forms:
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert {question.outcome_code for question in selected} == {"EB3.1"}
        assert {question.difficulty for question in selected} == {4}
        assert all(question.passage_ref is not None for question in selected)
        assert sum(len(question.parts) for question in selected) == 5
        assert {question.exposure_pool for question in selected} == {
            "module_checkpoint"
        }


def test_e4_checkpoint_forms_cover_function_words_and_timed_open_cloze(english_root):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    forms = sorted(
        (
            form
            for form in report.forms
            if form.form_type == "checkpoint" and form.module_code == "E4"
        ),
        key=lambda form: form.form_key,
    )

    assert [form.form_key for form in forms] == [
        "english-checkpoint-e4-open-cloze-a-v1",
        "english-checkpoint-e4-open-cloze-b-v1",
    ]
    assert forms[0].paired_form_key == forms[1].form_key
    assert forms[1].paired_form_key == forms[0].form_key
    assert forms[0].mastery_lesson_keys == forms[1].mastery_lesson_keys == [
        "e4-lesson-01",
        "e4-lesson-05",
    ]
    assert forms[0].task_part_distribution == forms[1].task_part_distribution == {
        "open_cloze": 5
    }
    assert set(forms[0].question_keys).isdisjoint(forms[1].question_keys)
    for form in forms:
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert [question.outcome_code for question in selected] == ["EO4.1", "EO4.5"]
        assert [question.difficulty for question in selected] == [4, 5]
        assert [len(question.parts) for question in selected] == [3, 2]
        assert all(question.passage_ref is not None for question in selected)
        assert {question.exposure_pool for question in selected} == {
            "module_checkpoint"
        }


def test_e5_checkpoint_forms_use_fresh_paired_passages_and_scope_sprint_reading(
    english_root,
):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    forms = sorted(
        (
            form
            for form in report.forms
            if form.form_type == "checkpoint" and form.module_code == "E5"
        ),
        key=lambda form: form.form_key,
    )

    assert [form.form_key for form in forms] == [
        "english-checkpoint-e5-reading-a-v1",
        "english-checkpoint-e5-reading-b-v1",
    ]
    assert forms[0].paired_form_key == forms[1].form_key
    assert forms[1].paired_form_key == forms[0].form_key
    assert forms[0].mastery_lesson_keys == forms[1].mastery_lesson_keys == [
        "e5-lesson-02",
        "e5-lesson-03",
        "e5-lesson-07",
    ]
    assert forms[0].task_part_distribution == forms[1].task_part_distribution == {
        "reading_comprehension": 5
    }
    assert set(forms[0].question_keys).isdisjoint(forms[1].question_keys)
    passage_keys = set()
    for form in forms:
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert {question.outcome_code for question in selected} == {"ER5.7"}
        assert {question.difficulty for question in selected} == {4}
        assert all(question.passage_ref is not None for question in selected)
        assert sum(len(question.parts) for question in selected) == 5
        assert {question.exposure_pool for question in selected} == {
            "module_checkpoint"
        }
        passage_keys.update(
            question.passage_ref.stable_key for question in selected if question.passage_ref
        )

    assert passage_keys == {
        "english-passage-checkpoint-rain-routes-pair",
        "english-passage-checkpoint-night-journeys-pair",
    }


def test_e6_checkpoint_forms_decode_and_plan_two_original_composition_prompts(
    english_root,
):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    forms = sorted(
        (
            form
            for form in report.forms
            if form.form_type == "checkpoint" and form.module_code == "E6"
        ),
        key=lambda form: form.form_key,
    )

    assert [form.form_key for form in forms] == [
        "english-checkpoint-e6-planning-a-v1",
        "english-checkpoint-e6-planning-b-v1",
    ]
    assert forms[0].paired_form_key == forms[1].form_key
    assert forms[1].paired_form_key == forms[0].form_key
    assert forms[0].mastery_lesson_keys == forms[1].mastery_lesson_keys == [
        "e6-lesson-01",
        "e6-lesson-05",
    ]
    assert forms[0].task_part_distribution == forms[1].task_part_distribution == {
        "composition_planning": 5
    }
    assert set(forms[0].question_keys).isdisjoint(forms[1].question_keys)
    for form in forms:
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert [question.outcome_code for question in selected] == ["EW6.1", "EW6.5"]
        assert [question.difficulty for question in selected] == [4, 4]
        assert [len(question.parts) for question in selected] == [3, 2]
        assert {question.exposure_pool for question in selected} == {
            "module_checkpoint"
        }


def test_e7_checkpoint_forms_develop_relevant_honest_evidence_chains(english_root):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    forms = sorted(
        (
            form
            for form in report.forms
            if form.form_type == "checkpoint" and form.module_code == "E7"
        ),
        key=lambda form: form.form_key,
    )

    assert [form.form_key for form in forms] == [
        "english-checkpoint-e7-development-a-v1",
        "english-checkpoint-e7-development-b-v1",
    ]
    assert forms[0].paired_form_key == forms[1].form_key
    assert forms[1].paired_form_key == forms[0].form_key
    assert forms[0].mastery_lesson_keys == forms[1].mastery_lesson_keys == [
        "e7-lesson-02"
    ]
    assert forms[0].task_part_distribution == forms[1].task_part_distribution == {
        "composition_planning": 5
    }
    assert set(forms[0].question_keys).isdisjoint(forms[1].question_keys)
    for form in forms:
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert {question.outcome_code for question in selected} == {"EW7.2"}
        assert {question.difficulty for question in selected} == {4}
        assert [len(question.parts) for question in selected] == [3, 2]
        assert {question.exposure_pool for question in selected} == {
            "module_checkpoint"
        }


def test_v3b_sprint_lessons_have_five_decision_exit_and_parallel_forms(english_root):
    report = validate_english_foundation(english_root)
    lessons = {lesson.lesson_code: lesson for lesson in report.lessons}
    questions = {question.stable_key: question for question in report.questions}
    pairs = {
        "E0.1": ("ex-l1-005", "ex-l1-006", "exam_strategy"),
        "E0.2": ("ex-l2-004", "ex-l2-005", "exam_strategy"),
        "E1.6": ("ev-l5-001", "ev-l5-002", "vocabulary_in_context"),
        "E2.2": ("eg-l2-001", "eg-l2-002", "grammar_usage"),
        "E9.5": ("ex-l5-004", "ex-l5-005", "exam_strategy"),
    }
    for lesson_code, (exit_key, retry_key, question_type) in pairs.items():
        lesson = lessons[lesson_code]
        exit_question = questions[exit_key]
        retry_question = questions[retry_key]
        assert lesson.sections[-1].question_keys == [exit_key]
        assert exit_question.exposure_pool == "exit_ticket"
        assert exit_question.question_type == question_type
        assert exit_question.feedback_timing == "after_group"
        assert len(exit_question.parts) == 5
        assert retry_question.exposure_pool == "retry_review"
        assert retry_question.parallel_form_of == exit_key
        assert retry_question.outcome_code == exit_question.outcome_code
        assert retry_question.question_type == exit_question.question_type
        assert len(retry_question.parts) == 5
        assert {part.prompt for part in retry_question.parts}.isdisjoint(
            part.prompt for part in exit_question.parts
        )


def test_english_routes_reject_sprint_lessons_outside_core(english_root):
    payload = json.loads((english_root / "catalogue.json").read_text())
    e1_3 = next(
        lesson
        for module in payload["modules"]
        for lesson in module["lessons"]
        if lesson["lesson_code"] == "E1.3"
    )
    e1_3["route_tags"] = ["full", "sprint"]

    with pytest.raises(ValidationError, match="Sprint lesson must also belong to the Core"):
        EnglishCurriculumCatalogue.model_validate(payload)


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


def test_e6_idea_generation_is_relevant_specific_and_honest(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l2-001.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW6.2"
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "B")["correct"]
    assert check_english_answer(question.parts[2].response, ["C", "A", "B"])["correct"]
    assert check_english_answer(question.parts[4].response, "C")["correct"]
    assert not check_english_answer(question.parts[4].response, "A")["correct"]


def test_e6_selection_preserves_one_focus_and_reader_need_order(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l3-001.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW6.3"
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, ["C", "A"])["correct"]
    assert not check_english_answer(question.parts[0].response, ["A", "B"])["correct"]
    assert check_english_answer(question.parts[3].response, "B")["correct"]
    assert check_english_answer(question.parts[5].response, "A")["correct"]


def test_e6_controlling_focus_unites_paragraph_jobs_without_overclaim(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l4-001.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW6.4"
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "B")["correct"]
    assert check_english_answer(question.parts[1].response, ["C", "A", "B"])["correct"]
    assert not check_english_answer(question.parts[1].response, ["A", "B", "D"])["correct"]
    assert check_english_answer(question.parts[4].response, "C")["correct"]
    assert check_english_answer(question.parts[5].response, "A")["correct"]


def test_e6_five_minute_plan_builds_and_audits_a_complete_route(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l5-001.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW6.5"
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "B")["correct"]
    assert check_english_answer(question.parts[1].response, ["C", "A", "B"])["correct"]
    assert not check_english_answer(question.parts[1].response, ["A", "B", "D"])[
        "correct"
    ]
    assert check_english_answer(question.parts[3].response, "C")["correct"]
    assert check_english_answer(question.parts[5].response, "A")["correct"]


def test_e7_paragraph_purpose_controls_evidence_boundaries_and_progression(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l1-002.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW7.1"
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "B")["correct"]
    assert check_english_answer(question.parts[1].response, ["C", "A", "B"])["correct"]
    assert not check_english_answer(question.parts[1].response, ["A", "B", "D"])[
        "correct"
    ]
    assert check_english_answer(question.parts[2].response, "C")["correct"]
    assert check_english_answer(question.parts[4].response, "C")["correct"]
    assert check_english_answer(question.parts[5].response, "A")["correct"]


def test_e7_specifics_connect_action_consequence_and_significance(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l2-002.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW7.2"
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "C")["correct"]
    assert check_english_answer(question.parts[1].response, ["C", "A", "B"])["correct"]
    assert not check_english_answer(question.parts[1].response, ["A", "B", "E"])[
        "correct"
    ]
    assert check_english_answer(question.parts[2].response, "B")["correct"]
    assert check_english_answer(question.parts[4].response, "C")["correct"]
    assert check_english_answer(question.parts[5].response, "A")["correct"]


def test_e7_cohesion_uses_reference_sequence_and_selective_transitions(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l3-002.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW7.3"
    assert question.difficulty == 4
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "B")["correct"]
    assert check_english_answer(question.parts[1].response, ["C", "A", "B"])[
        "correct"
    ]
    assert not check_english_answer(question.parts[1].response, ["A", "D", "E"])[
        "correct"
    ]
    assert check_english_answer(question.parts[2].response, "C")["correct"]
    assert check_english_answer(question.parts[3].response, "B")["correct"]
    assert check_english_answer(question.parts[4].response, "A")["correct"]
    assert check_english_answer(question.parts[5].response, "A")["correct"]


def test_e7_introductions_and_endings_frame_and_resolve_the_response(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l4-002.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW7.4"
    assert question.difficulty == 4
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "C")["correct"]
    assert check_english_answer(question.parts[1].response, ["C", "A", "B"])[
        "correct"
    ]
    assert not check_english_answer(question.parts[1].response, ["A", "D", "E"])[
        "correct"
    ]
    assert check_english_answer(question.parts[2].response, "D")["correct"]
    assert check_english_answer(question.parts[3].response, "B")["correct"]
    assert check_english_answer(question.parts[4].response, "D")["correct"]
    assert check_english_answer(question.parts[5].response, "B")["correct"]


def test_e7_read_like_a_writer_transfers_structure_without_surface_copying(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l5-002.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW7.5"
    assert question.difficulty == 4
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "B")["correct"]
    assert check_english_answer(question.parts[1].response, ["C", "A", "B"])[
        "correct"
    ]
    assert not check_english_answer(question.parts[1].response, ["A", "D", "E"])[
        "correct"
    ]
    assert check_english_answer(question.parts[2].response, "D")["correct"]
    assert check_english_answer(question.parts[3].response, "B")["correct"]
    assert check_english_answer(question.parts[4].response, "A")["correct"]
    assert check_english_answer(question.parts[5].response, "C")["correct"]


def test_e8_precise_vocabulary_aligns_wording_with_meaning_and_evidence(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l1-003.json").read_text()
    )

    assert question.question_type == "editing"
    assert question.outcome_code == "EW8.1"
    assert question.difficulty == 4
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, ["E", "A", "C"])[
        "correct"
    ]
    assert not check_english_answer(question.parts[0].response, ["A", "B", "C"])[
        "correct"
    ]
    assert check_english_answer(question.parts[1].response, "B")["correct"]
    assert check_english_answer(question.parts[2].response, "C")["correct"]
    assert check_english_answer(question.parts[3].response, "A")["correct"]
    assert check_english_answer(question.parts[4].response, "B")["correct"]
    assert check_english_answer(question.parts[5].response, "C")["correct"]


def test_e8_sentence_variety_preserves_boundaries_agreement_and_reference(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l2-003.json").read_text()
    )

    assert question.question_type == "editing"
    assert question.outcome_code == "EW8.2"
    assert question.difficulty == 4
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "A")["correct"]
    assert check_english_answer(question.parts[1].response, "B")["correct"]
    assert check_english_answer(question.parts[2].response, "C")["correct"]
    assert check_english_answer(question.parts[3].response, "B")["correct"]
    assert check_english_answer(question.parts[4].response, ["F", "A", "D"])[
        "correct"
    ]
    assert not check_english_answer(question.parts[4].response, ["A", "C", "D"])[
        "correct"
    ]
    assert check_english_answer(question.parts[5].response, "B")["correct"]


def test_e8_relationships_match_connectors_to_evidence_and_scope(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l3-003.json").read_text()
    )

    assert question.question_type == "editing"
    assert question.outcome_code == "EW8.3"
    assert question.difficulty == 4
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
    assert check_english_answer(question.parts[0].response, "A")["correct"]
    assert check_english_answer(question.parts[1].response, "B")["correct"]
    assert check_english_answer(question.parts[2].response, "C")["correct"]
    assert check_english_answer(question.parts[3].response, ["C", "A", "B"])[
        "correct"
    ]
    assert not check_english_answer(question.parts[3].response, ["A", "B", "D"])[
        "correct"
    ]
    assert check_english_answer(question.parts[4].response, "B")["correct"]
    assert check_english_answer(question.parts[5].response, "B")["correct"]


def test_e8_editing_priority_protects_task_before_surface_corrections(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l4-003.json").read_text()
    )

    assert question.question_type == "editing"
    assert question.outcome_code == "EW8.4"
    assert question.difficulty == 4
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "A")["correct"]
    assert check_english_answer(question.parts[1].response, "B")["correct"]
    assert check_english_answer(question.parts[2].response, "B")["correct"]
    assert check_english_answer(question.parts[3].response, "B")["correct"]
    assert check_english_answer(question.parts[4].response, ["D", "C"])[
        "correct"
    ]
    assert not check_english_answer(question.parts[4].response, ["A", "C"])[
        "correct"
    ]
    assert check_english_answer(question.parts[5].response, "B")["correct"]


def test_e8_personal_error_log_selects_recurring_actionable_patterns(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l5-003.json").read_text()
    )

    assert question.question_type == "editing"
    assert question.outcome_code == "EW8.5"
    assert question.difficulty == 4
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, ["E", "A", "C"])[
        "correct"
    ]
    assert not check_english_answer(question.parts[0].response, ["A", "C", "D"])[
        "correct"
    ]
    assert check_english_answer(question.parts[1].response, "B")["correct"]
    assert check_english_answer(question.parts[2].response, "A")["correct"]
    assert check_english_answer(question.parts[3].response, "B")["correct"]
    assert check_english_answer(question.parts[4].response, "B")["correct"]
    assert check_english_answer(question.parts[5].response, "B")["correct"]


def test_e9_reflection_connects_experience_insight_and_transfer(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l1-004.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW9.1"
    assert question.difficulty == 4
    assert question.feedback_timing == "after_group"
    assert len(question.parts) == 6
    assert [part.response.type for part in question.parts] == [
        "single_choice",
        "multiple_response",
        "single_choice",
        "single_choice",
        "single_choice",
        "single_choice",
    ]
    assert check_english_answer(question.parts[0].response, "B")["correct"]
    assert check_english_answer(question.parts[1].response, ["C", "A", "B"])[
        "correct"
    ]
    assert not check_english_answer(question.parts[1].response, ["A", "B", "D"])[
        "correct"
    ]
    assert check_english_answer(question.parts[2].response, "C")["correct"]
    assert check_english_answer(question.parts[3].response, "B")["correct"]
    assert check_english_answer(question.parts[4].response, "C")["correct"]
    assert check_english_answer(question.parts[5].response, "B")["correct"]


def test_every_english_source_matches_its_generated_schema(repository_root, english_root):
    schema_root = repository_root / "backend_resources/english/schema"
    cases = [
        (schema_root / "catalogue-v1.schema.json", [english_root / "catalogue.json"]),
        (schema_root / "source-inventory-v1.schema.json", [english_root / "sources.json"]),
        (
            schema_root / "exam-profile-v1.schema.json",
            list((english_root / "exam_profiles").glob("*.json")),
        ),
        (
            schema_root / "assessment-form-v1.schema.json",
            list((english_root / "forms").glob("*.json")),
        ),
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


def test_e5_checkpoint_pairs_mark_reference_context_and_comparison_exactly(english_root):
    expected = {
        "er-l5-008": ["A", "A", "B", "A", "A"],
        "er-l5-009": ["B", "A", "C", "A", "A"],
    }

    for question_key, answers in expected.items():
        question = EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/{question_key}.json").read_text()
        )
        assert question.question_type == "reading_comprehension"
        assert question.exposure_pool == "module_checkpoint"
        assert question.feedback_timing == "after_group"
        assert question.outcome_code == "ER5.7"
        assert len(question.parts) == 5
        assert all(part.response.type == "single_choice" for part in question.parts)
        assert [
            check_english_answer(part.response, answer)["correct"]
            for part, answer in zip(question.parts, answers, strict=True)
        ] == [True] * 5

    form_b = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/er-l5-009.json").read_text()
    )
    assert form_b.passage_ref.stable_key == (
        "english-passage-checkpoint-night-journeys-pair"
    )
    assert not check_english_answer(form_b.parts[4].response, "B")["correct"]


def test_e6_checkpoint_groups_mark_task_decoding_and_planning_exactly(english_root):
    expected = {
        "ex-l1-010": ["B", ["A", "C", "D"], "C"],
        "ex-l5-007": ["A", "A"],
        "ex-l1-011": ["B", "A", "A"],
        "ex-l5-008": ["A", "A"],
    }

    for question_key, answers in expected.items():
        question = EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/{question_key}.json").read_text()
        )
        assert question.question_type == "composition_planning"
        assert question.exposure_pool == "module_checkpoint"
        assert question.feedback_timing == "after_group"
        assert question.outcome_code in {"EW6.1", "EW6.5"}
        assert [
            check_english_answer(part.response, answer)["correct"]
            for part, answer in zip(question.parts, answers, strict=True)
        ] == [True] * len(answers)

    form_a = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l1-010.json").read_text()
    )
    assert form_a.parts[1].response.type == "multiple_response"
    assert not check_english_answer(form_a.parts[1].response, ["A", "C"])["correct"]


def test_e7_checkpoint_groups_mark_evidence_and_relevance_exactly(english_root):
    expected = {
        "ex-l2-009": ["B", ["A", "B"], "A"],
        "ex-l2-010": ["C", "A"],
        "ex-l2-011": ["A", "B", "A"],
        "ex-l2-012": [["A", "B"], "A"],
    }

    for question_key, answers in expected.items():
        question = EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/{question_key}.json").read_text()
        )
        assert question.question_type == "composition_planning"
        assert question.exposure_pool == "module_checkpoint"
        assert question.feedback_timing == "after_group"
        assert question.outcome_code == "EW7.2"
        assert [
            check_english_answer(part.response, answer)["correct"]
            for part, answer in zip(question.parts, answers, strict=True)
        ] == [True] * len(answers)

    form_b = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l2-012.json").read_text()
    )
    assert form_b.parts[0].response.type == "multiple_response"
    assert not check_english_answer(form_b.parts[0].response, ["A"])["correct"]


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


def test_english_pilot_has_complete_reviewable_batches(english_root):
    report = validate_english_authoring(english_root)

    assert report.valid
    assert [batch.batch_id for batch in report.batches] == [
        "english-eb-b001",
        "english-eb-b002",
        "english-eb-b003",
        "english-eb-b004",
        "english-eb-b005",
        "english-eb-b006",
        "english-eb-b007",
        "english-eg-b001",
        "english-eg-b002",
            "english-eg-b003",
            "english-eg-b004",
        "english-eo-b001",
        "english-eo-b002",
        "english-eo-b003",
        "english-eo-b004",
        "english-eo-b005",
        "english-eo-b006",
        "english-eo-b007",
        "english-eo-b008",
        "english-eo-b009",
        "english-eo-b010",
        "english-eo-b011",
        "english-er-b001",
        "english-er-b002",
        "english-er-b003",
        "english-er-b004",
        "english-er-b005",
        "english-er-b006",
        "english-er-b007",
        "english-er-b008",
        "english-er-b009",
        "english-er-b010",
        "english-er-b011",
        "english-er-b012",
        "english-er-b013",
        "english-ev-b001",
        "english-ev-b002",
        "english-ev-b003",
        "english-ev-b004",
        "english-ev-b005",
        "english-ev-b006",
        "english-ev-b007",
        "english-ev-b008",
        "english-ex-b001",
        "english-ex-b002",
        "english-ex-b003",
        "english-ex-b004",
        "english-ex-b005",
        "english-ex-b006",
        "english-ex-b007",
        "english-ex-b008",
        "english-ex-b009",
        "english-ex-b010",
        "english-ex-b011",
        "english-ex-b012",
        "english-ex-b013",
        "english-ex-b014",
        "english-ex-b015",
        "english-ex-b016",
        "english-ex-b017",
        "english-ex-b018",
        "english-ex-b019",
        "english-ex-b020",
        "english-ex-b021",
        "english-ex-b022",
        "english-ex-b023",
        "english-ex-b024",
        "english-ex-b025",
        "english-ex-b026",
        "english-ex-b027",
        "english-ex-b028",
        "english-ex-b029",
        "english-ex-b030",
    ]
    assert len(report.questions) == 98
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


def test_idea_generation_reviewer_export_contains_contract_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b002.json"
    output = tmp_path / "idea-generation-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "Continue from this task contract" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "credible future use" in page


def test_choose_and_order_reviewer_export_contains_sequence_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b003.json"
    output = tmp_path / "choose-order-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "breaking a large problem into smaller parts" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, C" in page
    assert "Method, plan, complication and reflection" in page


def test_controlling_focus_reviewer_export_contains_focus_map_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b004.json"
    output = tmp_path / "controlling-focus-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "breaking a large task into smaller parts" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "one claim, two non-overlapping contributions" in page


def test_five_minute_plan_reviewer_export_contains_route_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b005.json"
    output = tmp_path / "five-minute-plan-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "five-minute routine is a practice target" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "task and focus through two developing body jobs" in page


def test_paragraph_purpose_reviewer_export_contains_boundaries_and_all_answers(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b006.json"
    output = tmp_path / "paragraph-purpose-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "Body paragraph one explains" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "initial-planning job" in page
    assert "reverse outline" in page


def test_develop_with_specifics_reviewer_export_contains_evidence_chain(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b007.json"
    output = tmp_path / "develop-specifics-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "without presenting invented precision as fact" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "unsupported exact statistics weaken credibility" in page
    assert "observable consequence to significance" in page


def test_cohesion_reviewer_export_contains_reference_and_logical_chains(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b008.json"
    output = tmp_path / "cohesion-without-formula-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "Improve cohesion in the charity-sale composition" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "sequence moves from rain to the resulting risk" in page
    assert "cause-and-response chain" in page


def test_introductions_and_endings_reviewer_export_contains_framing_and_closure(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b009.json"
    output = tmp_path / "introductions-and-endings-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "Improve the introduction and ending of the charity-sale composition" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "provides immediate orientation and a focused route" in page
    assert "creates closure by moving from a genuine opening question" in page


def test_read_like_a_writer_reviewer_export_contains_model_and_transfer(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b010.json"
    output = tmp_path / "read-like-a-writer-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "At first, the repair-café volunteers" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "records sentence functions and relationships" in page
    assert "fully grounded in the food-waste context" in page


def test_precise_vocabulary_reviewer_export_contains_notes_and_evidence_limits(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b011.json"
    output = tmp_path / "precise-vocabulary-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "returned books were sometimes left unsorted" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, C, E" in page
    assert "Controlled repetition supports cohesion" in page
    assert "the intended register and the evidence available" in page


def test_sentence_variety_reviewer_export_contains_control_checks(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b012.json"
    output = tmp_path / "sentence-variety-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "the front room faced a bus stop" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, D, F" in page
    assert "subject–verb agreement" in page
    assert "sentence structures change because the relationships" in page


def test_show_relationships_reviewer_export_contains_evidence_limits(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b013.json"
    output = tmp_path / "show-relationships-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "the longest queues formed during the first ten minutes" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "population, setting and period" in page
    assert "connectors must serve the evidence" in page


def test_edit_by_priority_reviewer_export_contains_the_full_editing_ladder(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b014.json"
    output = tmp_path / "edit-by-priority-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "eight basil seedlings in identical pots were wilting" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> C, D" in page
    assert "task, organisation and evidence-scope repairs come earlier" in page
    assert "task, organisation, development, sentence control and conventions" in page


def test_personal_error_log_reviewer_export_contains_patterns_and_retest_plan(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b015.json"
    output = tmp_path / "personal-error-log-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "eight dated review entries" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, C, E" in page
    assert "complete clauses with only a comma" in page
    assert "requires successful transfer before retirement" in page


def test_reflective_writing_reviewer_export_contains_complete_transfer_chain(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b016.json"
    output = tmp_path / "reflective-writing-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "all eight basil seedlings" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "experience–insight–transfer chain" in page
    assert "balances enough experience to support the insight" in page


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
