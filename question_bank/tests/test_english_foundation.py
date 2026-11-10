import json
import shutil

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from question_bank.english_authoring import (
    claim_english_batch,
    detect_english_duplicates,
    export_english_reviewer_batch,
    export_english_route_reviewer_packet,
    release_english_batch,
    validate_english_authoring,
)
from question_bank.english_checking import check_english_answer, normalise_text
from question_bank.english_models import (
    EnglishAssessmentForm,
    EnglishCurriculumCatalogue,
    EnglishEssayPrompt,
    EnglishEssayRubric,
    EnglishObjectiveQuestion,
    ShortTextResponse,
    TextNormalisation,
)
from question_bank.english_quality import BASELINE_PATH, english_quality_findings
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
    assert len(report.lessons) == 51
    assert len(report.passages) == 78
    assert len(report.questions) == 214
    assert report.exam_profile is not None
    assert report.exam_profile.profile_key == "asean-english-sec3-id-reported-v1"
    assert set(report.exam_profile.excluded_task_types) == {
        "editing_section",
        "own_words_short_answer",
    }
    assert len(report.forms) == 25
    assert len(report.essay_rubrics) == 1
    assert len(report.essay_prompts) == 1
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
        "full": 51,
        "core": 32,
        "sprint": 16,
    }
    assert summary["route_exit_ticket_lesson_counts"] == {
        "full": 51,
        "core": 32,
        "sprint": 16,
    }
    assert summary["route_parallel_retry_lesson_counts"] == {
        "full": 28,
        "core": 23,
        "sprint": 16,
    }
    assert summary["route_unauthored_lesson_codes"]["sprint"] == []
    assert not report.issues


def test_protected_english_forms_pin_matched_disjoint_sixty_minute_blueprints(english_root):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    passages = {passage.stable_key: passage for passage in report.passages}
    expected = {
        "baseline": (
            ["ev-l5-201", "eb-l5-201", "eo-l5-201", "er-l5-201", "er-l5-204"],
            "baseline_diagnostic",
        ),
        "endline": (
            ["ev-l5-202", "eb-l5-202", "eo-l5-202", "er-l5-202", "er-l5-205"],
            "endline_diagnostic",
        ),
        "endline_reserve": (
            ["ev-l5-203", "eb-l5-203", "eo-l5-203", "er-l5-203", "er-l5-206"],
            "protected_reserve",
        ),
    }
    selected_keys = set()

    measurement_forms = [
        form for form in report.forms if form.form_type not in {"checkpoint", "mock"}
    ]
    assert len(measurement_forms) == 3
    for form in measurement_forms:
        question_keys, exposure_pool = expected[form.form_type]
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert form.question_keys == question_keys
        assert sum(len(question.parts) for question in selected) == 43
        assert form.task_part_distribution == {
            "vocabulary_in_context": 15,
            "banked_cloze": 8,
            "open_cloze": 8,
            "reading_comprehension": 12,
        }
        actual_distribution = {
            task_type: sum(
                len(question.parts)
                for question in selected
                if question.question_type == task_type
            )
            for task_type in form.task_part_distribution
        }
        assert actual_distribution == form.task_part_distribution
        reading = [
            question for question in selected if question.question_type == "reading_comprehension"
        ]
        assert {passages[question.passage_ref.stable_key].text_type for question in reading} == {
            "informational",
            "narrative",
        }
        assert {question.exposure_pool for question in selected} == {exposure_pool}
        assert selected_keys.isdisjoint(form.question_keys)
        selected_keys.update(form.question_keys)

    assert len(selected_keys) == 15


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


def test_e1_2_word_family_filters_by_slot_form_and_complete_sentence(english_root):
    questions = [
        EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/ev-l2-00{number}.json").read_text()
        )
        for number in range(1, 8)
    ]

    assert {question.outcome_code for question in questions} == {"EV1.2"}
    assert {question.question_type for question in questions} == {
        "vocabulary_in_context"
    }
    assert [question.exposure_pool for question in questions] == [
        "guided_practice",
        "guided_practice",
        "independent_practice",
        "independent_practice",
        "independent_practice",
        "exit_ticket",
        "retry_review",
    ]
    assert [len(question.parts) for question in questions] == [1] * 7
    for question, answer in zip(
        questions,
        ["B", "B", "B", "C", "C", "B", "C"],
        strict=True,
    ):
        assert check_english_answer(question.parts[0].response, answer)["correct"]
    assert not check_english_answer(questions[5].parts[0].response, "C")["correct"]
    assert questions[6].parallel_form_of == questions[5].stable_key
    assert questions[6].parts[0].prompt != questions[5].parts[0].prompt


def test_e1_4_synonym_precision_preserves_core_degree_and_attitude(english_root):
    questions = [
        EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/ev-l4-00{number}.json").read_text()
        )
        for number in range(1, 8)
    ]

    assert {question.outcome_code for question in questions} == {"EV1.4"}
    assert {question.question_type for question in questions} == {
        "vocabulary_in_context"
    }
    assert [question.exposure_pool for question in questions] == [
        "guided_practice",
        "guided_practice",
        "independent_practice",
        "independent_practice",
        "independent_practice",
        "exit_ticket",
        "retry_review",
    ]
    assert [len(question.parts) for question in questions] == [1] * 7
    for question, answer in zip(
        questions,
        ["B", "C", "A", "B", "D", "B", "C"],
        strict=True,
    ):
        assert check_english_answer(question.parts[0].response, answer)["correct"]
    assert not check_english_answer(questions[5].parts[0].response, "A")["correct"]
    assert questions[6].parallel_form_of == questions[5].stable_key
    assert questions[6].parts[0].prompt != questions[5].parts[0].prompt


def test_e1_5_collocation_and_register_checks_partnership_and_audience(english_root):
    questions = [
        EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/ev-l5-{number:03d}.json").read_text()
        )
        for number in range(8, 15)
    ]

    assert {question.outcome_code for question in questions} == {"EV1.5"}
    assert {question.question_type for question in questions} == {
        "vocabulary_in_context"
    }
    assert [question.exposure_pool for question in questions] == [
        "guided_practice",
        "guided_practice",
        "independent_practice",
        "independent_practice",
        "independent_practice",
        "exit_ticket",
        "retry_review",
    ]
    assert [len(question.parts) for question in questions] == [1] * 7
    for question, answer in zip(
        questions,
        ["C", "B", "D", "C", "C", "D", "A"],
        strict=True,
    ):
        assert check_english_answer(question.parts[0].response, answer)["correct"]
    assert not check_english_answer(questions[5].parts[0].response, "A")["correct"]
    assert questions[6].parallel_form_of == questions[5].stable_key
    assert questions[6].parts[0].prompt != questions[5].parts[0].prompt


def test_e2_3_tense_and_aspect_uses_timeline_evidence_and_fresh_retry(english_root):
    questions = [
        EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/eg-l3-{number:03d}.json").read_text()
        )
        for number in range(1, 8)
    ]

    assert {question.outcome_code for question in questions} == {"EG2.3"}
    assert {question.question_type for question in questions} == {"grammar_usage"}
    assert [question.exposure_pool for question in questions] == [
        "guided_practice",
        "guided_practice",
        "independent_practice",
        "independent_practice",
        "independent_practice",
        "exit_ticket",
        "retry_review",
    ]
    assert [len(question.parts) for question in questions] == [1] * 7
    for question, answer in zip(
        questions,
        ["B", "D", "A", "C", "B", "D", "A"],
        strict=True,
    ):
        assert check_english_answer(question.parts[0].response, answer)["correct"]
    assert not check_english_answer(questions[5].parts[0].response, "A")["correct"]
    assert questions[6].parallel_form_of == questions[5].stable_key
    assert questions[6].parts[0].prompt != questions[5].parts[0].prompt


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


def test_e8_checkpoint_forms_prioritise_composition_revision_without_new_task_type(
    english_root,
):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    forms = sorted(
        (
            form
            for form in report.forms
            if form.form_type == "checkpoint" and form.module_code == "E8"
        ),
        key=lambda form: form.form_key,
    )
    assert [form.form_key for form in forms] == [
        "english-checkpoint-e8-revision-a-v1",
        "english-checkpoint-e8-revision-b-v1",
    ]
    assert forms[0].paired_form_key == forms[1].form_key
    assert forms[1].paired_form_key == forms[0].form_key
    assert forms[0].mastery_lesson_keys == forms[1].mastery_lesson_keys == [
        "e8-lesson-04"
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
        assert {question.outcome_code for question in selected} == {"EW8.4"}
        assert {question.difficulty for question in selected} == {4}
        assert sum(len(question.parts) for question in selected) == 5
        assert {question.exposure_pool for question in selected} == {
            "module_checkpoint"
        }


def test_e9_checkpoint_forms_protect_full_simulation_readiness_without_being_mocks(
    english_root,
):
    report = validate_english_foundation(english_root)
    questions = {question.stable_key: question for question in report.questions}
    forms = sorted(
        (
            form
            for form in report.forms
            if form.form_type == "checkpoint" and form.module_code == "E9"
        ),
        key=lambda form: form.form_key,
    )
    assert [form.form_key for form in forms] == [
        "english-checkpoint-e9-simulation-a-v1",
        "english-checkpoint-e9-simulation-b-v1",
    ]
    assert forms[0].paired_form_key == forms[1].form_key
    assert forms[1].paired_form_key == forms[0].form_key
    assert forms[0].mastery_lesson_keys == forms[1].mastery_lesson_keys == [
        "e9-lesson-05"
    ]
    assert forms[0].task_part_distribution == forms[1].task_part_distribution == {
        "exam_strategy": 5
    }
    assert set(forms[0].question_keys).isdisjoint(forms[1].question_keys)
    for form in forms:
        selected = [questions[key] for key in form.question_keys]
        assert form.status == "draft"
        assert form.form_type == "checkpoint"
        assert form.protected
        assert not form.tutoring_enabled
        assert form.feedback_timing == "after_form"
        assert {question.outcome_code for question in selected} == {"EW9.5"}
        assert {question.difficulty for question in selected} == {5}
        assert sum(len(question.parts) for question in selected) == 5
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


def test_e9_narrative_builds_an_earned_bounded_change(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l2-013.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW9.2"
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
    assert check_english_answer(question.parts[2].response, "B")["correct"]
    assert check_english_answer(question.parts[3].response, "D")["correct"]
    assert check_english_answer(question.parts[4].response, "B")["correct"]
    assert check_english_answer(question.parts[5].response, "A")["correct"]


def test_e9_opinion_builds_a_qualified_evidence_bounded_position(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l3-004.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW9.3"
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


def test_e9_compression_preserves_a_complete_independent_process(english_root):
    question = EnglishObjectiveQuestion.model_validate_json(
        (english_root / "questions/ex-l4-007.json").read_text()
    )

    assert question.question_type == "composition_planning"
    assert question.outcome_code == "EW9.4"
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
        (
            schema_root / "essay-rubric-v1.schema.json",
            list((english_root / "rubrics").glob("*.json")),
        ),
        (
            schema_root / "essay-prompt-v1.schema.json",
            list((english_root / "prompts").glob("*.json")),
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


def test_essay_prompt_pins_an_instructional_non_official_rubric(english_root):
    rubric = EnglishEssayRubric.model_validate(
        json.loads(
            (
                english_root
                / "rubrics/english-essay-rubric-instructional-v1-v2.json"
            ).read_text()
        )
    )
    prompt = EnglishEssayPrompt.model_validate(
        json.loads(
            (
                english_root
                / "prompts/english-essay-prompt-school-learning-transfer-v1-v2.json"
            ).read_text()
        )
    )

    assert rubric.official_score_claim is False
    assert [criterion.criterion_key for criterion in rubric.criteria] == [
        "task_fulfilment",
        "organisation_cohesion",
        "development_evidence",
        "language_control",
    ]
    assert sum(criterion.weight_percent for criterion in rubric.criteria) == 100
    assert all([band.level for band in criterion.bands] == [1, 2, 3, 4, 5] for criterion in rubric.criteria)
    assert (prompt.rubric_key, prompt.rubric_revision) == (
        rubric.stable_key,
        rubric.revision,
    )
    assert prompt.time_limit_minutes == 30
    assert prompt.time_limit_evidence == "candidate_reported"
    assert prompt.word_count_guidance == 300
    assert prompt.word_count_status == "guidance"


def test_essay_contracts_reject_official_claims_and_invalid_weights(english_root):
    payload = json.loads(
        (
            english_root / "rubrics/english-essay-rubric-instructional-v1-v2.json"
        ).read_text()
    )
    payload["official_score_claim"] = True
    with pytest.raises(ValidationError):
        EnglishEssayRubric.model_validate(payload)

    payload["official_score_claim"] = False
    payload["criteria"][0]["weight_percent"] = 20
    with pytest.raises(ValidationError, match="total 100 percent"):
        EnglishEssayRubric.model_validate(payload)


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
    assert check_english_answer(question.parts[1].response, "control")["correct"]
    assert not check_english_answer(question.parts[1].response, "notice")["correct"]


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
        "single_choice",
        "single_choice",
        "multiple_response",
    ]
    assert check_english_answer(question.parts[2].response, "Retain.")["correct"]
    assert check_english_answer(question.parts[3].response, "B")["correct"]
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
        "single_choice",
        "single_choice",
        "single_choice",
        "multiple_response",
    ]
    assert check_english_answer(question.parts[0].response, "A")["correct"]
    assert check_english_answer(question.parts[1].response, "The coastal ecologist.")["correct"]
    assert check_english_answer(question.parts[2].response, "A")["correct"]
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
        "er-l5-008": ["A", "C", "B", "C", "A"],
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


def test_e8_checkpoint_groups_mark_revision_priority_exactly(english_root):
    expected = {
        "ex-l4-005": ["A", "B", "C", "A", "D"],
        "ex-l4-006": ["B", "A", "C", "B", "A"],
    }
    for question_key, answers in expected.items():
        question = EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/{question_key}.json").read_text()
        )
        assert question.question_type == "composition_planning"
        assert question.exposure_pool == "module_checkpoint"
        assert question.feedback_timing == "after_group"
        assert question.outcome_code == "EW8.4"
        assert [
            check_english_answer(part.response, answer)["correct"]
            for part, answer in zip(question.parts, answers, strict=True)
        ] == [True] * 5
        assert "composition self-editing" in question.instructions


def test_e9_checkpoint_groups_mark_simulation_protocol_exactly(english_root):
    expected = {
        "ex-l5-009": ["B", "B", "B", "B", "C"],
        "ex-l5-010": ["A", "B", "B", "C", "B"],
    }
    for question_key, answers in expected.items():
        question = EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/{question_key}.json").read_text()
        )
        assert question.question_type == "exam_strategy"
        assert question.exposure_pool == "module_checkpoint"
        assert question.feedback_timing == "after_group"
        assert question.outcome_code == "EW9.5"
        assert [
            check_english_answer(part.response, answer)["correct"]
            for part, answer in zip(question.parts, answers, strict=True)
        ] == [True] * 5
        assert "not the full mock" in question.instructions


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
        "essay_prompt_review_required",
        "essay_rubric_review_required",
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
        "english-eb-b008",
        "english-eb-b009",
        "english-eb-b010",
        "english-eb-b011",
        "english-eb-b012",
        "english-eb-b013",
        "english-eb-b014",
            "english-eb-b015",
        "english-eg-b001",
        "english-eg-b002",
            "english-eg-b003",
            "english-eg-b004",
            "english-eg-b005",
            "english-eg-b006",
            "english-eg-b007",
            "english-eg-b008",
            "english-eg-b009",
            "english-eg-b010",
            "english-eg-b011",
            "english-eg-b012",
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
        "english-eo-b012",
            "english-eo-b013",
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
        "english-er-b014",
            "english-er-b015",
        "english-ev-b001",
        "english-ev-b002",
        "english-ev-b003",
        "english-ev-b004",
        "english-ev-b005",
        "english-ev-b006",
        "english-ev-b007",
        "english-ev-b008",
        "english-ev-b009",
        "english-ev-b010",
        "english-ev-b011",
        "english-ev-b012",
        "english-ev-b013",
        "english-ev-b014",
        "english-ev-b015",
        "english-ev-b016",
        "english-ev-b017",
            "english-ev-b018",
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
        "english-ex-b031",
        "english-ex-b032",
        "english-ex-b033",
        "english-ex-b034",
        "english-ex-b035",
        "english-ex-b036",
        "english-ex-b037",
        "english-ex-b038",
        "english-ex-b039",
    ]
    assert len(report.questions) == 214
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


def test_word_family_reviewer_export_contains_complete_form_evidence(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ev-b009.json"
    output = tmp_path / "word-family-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 6
    assert page.count("<strong>Answer:</strong>") == 6
    assert "must ___ its measurements" in page
    assert "The modal frame ‘must verify’ requires the base form" in page
    assert "provisional means temporary or awaiting confirmation" in page


def test_synonym_precision_reviewer_export_contains_degree_and_attitude_evidence(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ev-b011.json"
    output = tmp_path / "synonym-precision-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 6
    assert page.count("<strong>Answer:</strong>") == 6
    assert "comfortable to touch" in page
    assert "confident core meaning and the respectful attitude" in page
    assert "responsible attitude of the account" in page


def test_collocation_register_reviewer_export_contains_partnership_and_audience_evidence(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ev-b013.json"
    output = tmp_path / "collocation-register-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 6
    assert page.count("<strong>Answer:</strong>") == 6
    assert "standard word partnership" in page
    assert "appropriately neutral-formal for an office email" in page
    assert "matches the personal audience" in page
    assert "Raise serious concerns" in page


def test_tense_aspect_reviewer_export_contains_anchor_order_and_viewpoint_evidence(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-eg-b005.json"
    output = tmp_path / "tense-aspect-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 6
    assert page.count("<strong>Answer:</strong>") == 6
    assert "in progress at the moment the power failed" in page
    assert "past-to-present period" in page
    assert "rehearsal began before Maya arrived" in page


def test_sprint_route_reviewer_export_pins_complete_review_evidence(
    english_root, tmp_path
):
    output = tmp_path / "sprint-review"
    result = export_english_route_reviewer_packet(english_root, output)

    assert result["packet_key"] == "english-sprint-route-v3b-review"
    assert result["lesson_count"] == 16
    assert result["checkpoint_form_count"] == 20
    assert result["parallel_retry_count"] == 16
    assert result["question_count"] == 65
    assert result["review_item_count"] == 121
    assert {path.name for path in output.iterdir()} == {
        "index.html",
        "manifest.json",
        "review.csv",
        "review.md",
    }

    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["route"] == "sprint"
    assert manifest["parallel_retry_count"] == 16
    assert [lesson["lesson_code"] for lesson in manifest["lessons"]] == [
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
    assert {
        form["module_code"] for form in manifest["checkpoint_forms"]
    } == {f"E{index}" for index in range(10)}
    assert all(len(item["fingerprint"]) == 64 for item in manifest["lessons"])
    assert all(
        len(item["fingerprint"]) == 64 for item in manifest["checkpoint_forms"]
    )
    assert all(len(item["fingerprint"]) == 64 for item in manifest["questions"])
    assert all(len(item["fingerprint"]) == 64 for item in manifest["passages"])

    page = (output / "index.html").read_text()
    assert "PROTECTED REVIEWER EVIDENCE · DRAFT ONLY" in page
    assert "E9 full-simulation readiness checkpoint form A" in page
    assert "<strong>Answer:</strong>" in page
    assert "Option rationales" in page
    second = export_english_route_reviewer_packet(
        english_root, tmp_path / "sprint-review-copy"
    )
    assert second["preview_sha256"] == result["preview_sha256"]


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
    assert "the soil absorbing the pooled water quickly" in page


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
    assert "paragraph-by-paragraph summary" in page


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


def test_narrative_writing_reviewer_export_contains_complete_change_route(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b035.json"
    output = tmp_path / "narrative-writing-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "three empty display boards" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "preparation and agency" in page
    assert "human, specific and imperfect" in page


def test_opinion_writing_reviewer_export_contains_qualified_reasoning_route(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b036.json"
    output = tmp_path / "opinion-writing-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "Do not treat the fictional record as real-world research" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "unsupported universal result" in page
    assert "rather than an exaggerated or trivial alternative" in page


def test_compression_reviewer_export_contains_bounded_transfer_route(
    english_root, tmp_path
):
    batch = english_root / "authoring/batches/english-ex-b037.json"
    output = tmp_path / "compression-review"

    result = export_english_reviewer_batch(english_root, batch, output)
    page = (output / "index.html").read_text()

    assert result["question_count"] == 1
    assert "Nara has not yet attempted the 30-minute independent run" in page
    assert page.count("<strong>Answer:</strong>") == 6
    assert "<strong>Answer:</strong> A, B, C" in page
    assert "Bounded compression uses one stage to diagnose" in page
    assert "does not justify a high-stakes judgement" in page


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


def _quality_question(english_root, key):
    return EnglishObjectiveQuestion.model_validate_json(
        (english_root / f"questions/{key}.json").read_text()
    )


def test_quality_rules_flag_answer_cues_in_new_content(english_root):
    question = _quality_question(english_root, "ev-l5-003").model_copy(deep=True)
    question.title = "Baseline word: reluctant"
    codes = {finding.code for finding in english_quality_findings([question], [], [])}
    assert "title_names_answer" in codes

    cloze = _quality_question(english_root, "eo-l5-003").model_copy(deep=True)
    assert not english_quality_findings([cloze], [], [])
    cloze.parts[0].prompt = "Gap 1: enter the article before the noun."
    assert {finding.code for finding in english_quality_findings([cloze], [], [])} == {
        "open_cloze_prompt_not_neutral"
    }


def test_quality_rules_flag_a_key_much_longer_than_every_other_option(english_root):
    question = _quality_question(english_root, "ev-l5-004").model_copy(deep=True)
    assert not [
        finding
        for finding in english_quality_findings([question], [], [])
        if finding.code == "key_uniquely_longest"
    ]
    question.parts[0].response.options[0].text = "extremely hard-working and steady over a long time"
    assert "ev-l5-004#1" in {
        finding.location
        for finding in english_quality_findings([question], [], [])
        if finding.code == "key_uniquely_longest"
    }


def _bank_in_gap_order(question):
    """Rebuild a banked cloze so gap 1 uses bank word A, gap 2 uses B and so on."""

    payload = question.model_dump(mode="json")
    bank = {option["key"]: option["text"] for option in payload["parts"][0]["response"]["options"]}
    keyed = [part["response"]["correct_key"] for part in payload["parts"]]
    order = keyed + [key for key in bank if key not in keyed]
    new_key = {old: chr(ord("A") + index) for index, old in enumerate(order)}
    for part in payload["parts"]:
        response = part["response"]
        response["options"] = [{"key": new_key[old], "text": bank[old]} for old in order]
        response["correct_key"] = new_key[response["correct_key"]]
        response["choice_rationales"] = {
            new_key[old]: text for old, text in response["choice_rationales"].items()
        }
    return EnglishObjectiveQuestion.model_validate(payload)


def test_quality_rules_flag_banked_cloze_keys_in_bank_order(english_root):
    for key in ("eb-l1-003", "eb-l5-201", "eb-l2-002"):
        question = _quality_question(english_root, key)
        codes = {finding.code for finding in english_quality_findings([question], [], [])}
        assert "banked_cloze_keys_follow_bank_order" not in codes
        ordered = _bank_in_gap_order(question)
        assert "".join(part.response.correct_key for part in ordered.parts).startswith("ABC")
        assert key in {
            finding.location
            for finding in english_quality_findings([ordered], [], [])
            if finding.code == "banked_cloze_keys_follow_bank_order"
        }


def test_every_banked_cloze_bank_hides_the_gap_order(english_root):
    questions = [
        _quality_question(english_root, path.stem)
        for path in sorted((english_root / "questions").glob("eb-*.json"))
    ]
    assert len(questions) == 33
    assert not [
        finding
        for finding in english_quality_findings(questions, [], [])
        if finding.code == "banked_cloze_keys_follow_bank_order"
    ]


def test_quality_rules_flag_a_target_word_missing_from_its_sentence(english_root):
    question = _quality_question(english_root, "ev-l5-201").model_copy(deep=True)
    assert not english_quality_findings([question], [], [])
    question.parts[0].prompt = (
        "Before spending the entire grant, the committee kept a reserve for unexpected "
        "repairs. What does “prudent” most nearly mean?"
    )
    assert {
        finding.location
        for finding in english_quality_findings([question], [], [])
        if finding.code == "target_word_missing_from_context"
    } == {"ev-l5-201#1"}

    passages = validate_english_foundation(english_root).passages
    reading = _quality_question(english_root, "er-l5-005").model_copy(deep=True)
    part = next(part for part in reading.parts if "What does" in part.prompt)
    assert "target_word_missing_from_context" not in {
        finding.code for finding in english_quality_findings([reading], [], [], passages)
    }
    part.prompt = "What does “judicious” mean in paragraph 2?"
    assert "target_word_missing_from_context" in {
        finding.code for finding in english_quality_findings([reading], [], [], passages)
    }
    # Without passages, passage-based parts cannot be checked and are skipped.
    assert "target_word_missing_from_context" not in {
        finding.code for finding in english_quality_findings([reading], [], [])
    }


def test_every_vocabulary_target_appears_in_its_context(english_root):
    foundation = validate_english_foundation(english_root)
    assert not [
        finding
        for finding in english_quality_findings(
            foundation.questions, [], [], foundation.passages
        )
        if finding.code == "target_word_missing_from_context"
    ]


def test_quality_baseline_rejects_new_findings_and_stale_entries(english_root, tmp_path):
    copy = tmp_path / "english"
    shutil.copytree(english_root, copy)
    assert validate_english_authoring(copy).valid
    path = copy / "questions/eo-l5-003.json"
    payload = json.loads(path.read_text())
    payload["parts"][0]["prompt"] = "Gap 1: enter the article before the noun."
    path.write_text(json.dumps(payload, ensure_ascii=False))
    assert "open_cloze_prompt_not_neutral" in {
        issue.code for issue in validate_english_authoring(copy).errors
    }

    path.write_text((english_root / "questions/eo-l5-003.json").read_text())
    baseline = copy / BASELINE_PATH
    data = json.loads(baseline.read_text())
    data["accepted_findings"].append("title_names_answer|eo-l5-003")
    baseline.write_text(json.dumps(data))
    assert "stale_quality_baseline" in {
        issue.code for issue in validate_english_authoring(copy).errors
    }


def test_e2_6_logical_connections_passes_quality_rules_and_uses_a_fresh_retry(english_root):
    questions = [
        EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/eg-l5-{number}.json").read_text()
        )
        for number in range(101, 108)
    ]

    assert {question.outcome_code for question in questions} == {"EG2.6"}
    assert [question.exposure_pool for question in questions] == [
        "guided_practice",
        "guided_practice",
        "independent_practice",
        "independent_practice",
        "independent_practice",
        "exit_ticket",
        "retry_review",
    ]
    for question, answer in zip(questions, ["C", "A", "D", "B", "C", "A", "D"], strict=True):
        assert check_english_answer(question.parts[0].response, answer)["correct"]
    assert questions[6].parallel_form_of == questions[5].stable_key
    assert not english_quality_findings(questions, [], [])


def test_e3_2_grammar_filter_passes_quality_rules_and_each_bank_has_spare_words(english_root):
    questions = [
        EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/eb-l2-{number:03d}.json").read_text()
        )
        for number in range(1, 8)
    ]

    assert {question.outcome_code for question in questions} == {"EB3.2"}
    assert {question.question_type for question in questions} == {"banked_cloze"}
    assert [len(question.parts) for question in questions] == [4, 4, 5, 5, 5, 8, 8]
    for question in questions:
        assert len(question.parts[0].response.options) > len(question.parts)
    assert questions[6].parallel_form_of == questions[5].stable_key
    assert questions[6].passage_ref.stable_key != questions[5].passage_ref.stable_key
    assert not english_quality_findings(questions, [], [])


def test_e3_4_solve_globally_passes_quality_rules_and_uses_a_fresh_retry(english_root):
    questions = [
        EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/eb-l4-{number:03d}.json").read_text()
        )
        for number in range(1, 8)
    ]

    assert {question.outcome_code for question in questions} == {"EB3.4"}
    assert [len(question.parts) for question in questions] == [4, 4, 5, 5, 5, 8, 8]
    assert questions[6].parallel_form_of == questions[5].stable_key
    assert questions[6].passage_ref.stable_key != questions[5].passage_ref.stable_key
    assert not english_quality_findings(questions, [], [])


@pytest.mark.parametrize(
    ("first_key", "outcome"),
    [
        ("eg-l4-001", "EG2.4"),
        ("eg-l5-001", "EG2.5"),
        ("ev-l3-001", "EV1.3"),
        ("ex-l1-201", "EX0.3"),
        ("eb-l3-001", "EB3.3"),
    ],
)
def test_full_route_lessons_pass_quality_rules_and_use_a_fresh_retry(
    english_root, first_key, outcome
):
    prefix, start = first_key.rsplit("-", 1)
    questions = [
        EnglishObjectiveQuestion.model_validate_json(
            (english_root / f"questions/{prefix}-{int(start) + offset:03d}.json").read_text()
        )
        for offset in range(7)
    ]

    assert {question.outcome_code for question in questions} == {outcome}
    assert questions[5].exposure_pool == "exit_ticket"
    assert questions[6].parallel_form_of == questions[5].stable_key
    assert not english_quality_findings(questions, [], [])


def test_full_mocks_follow_the_reported_paper_and_share_no_questions(english_root):
    forms = [
        EnglishAssessmentForm.model_validate_json(
            (english_root / f"forms/english-mock-sec3-{form}-v1.json").read_text()
        )
        for form in "ab"
    ]

    assert not set(forms[0].question_keys) & set(forms[1].question_keys)
    for form in forms:
        questions = [
            EnglishObjectiveQuestion.model_validate_json(
                (english_root / f"questions/{key}.json").read_text()
            )
            for key in form.question_keys
        ]
        assert {question.exposure_pool for question in questions} == {"full_mock"}
        assert [question.question_type for question in questions] == [
            "vocabulary_in_context",
            "banked_cloze",
            "open_cloze",
            "reading_comprehension",
            "reading_comprehension",
        ]
        assert sum(len(question.parts) for question in questions) == 38
        assert not english_quality_findings(questions, [], [form])


def test_runtime_validation_skips_the_slow_content_checks(english_root, monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("The API must not run content checks while serving requests")

    monkeypatch.setattr("question_bank.english_authoring.detect_english_duplicates", fail)
    monkeypatch.setattr("question_bank.english_authoring._check_quality", fail)

    assert validate_english_authoring(english_root, content_checks=False).valid

