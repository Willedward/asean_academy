import json
import shutil

import pytest
from pydantic import ValidationError

from question_bank.catalogue import load_catalogue
from question_bank.course_models import Course
from question_bank.models import Question
from question_bank.validation import validate_bank, validate_catalogue


def test_versioned_syllabus_records_confirmed_subset(repository_root):
    path = repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json"
    catalogue = load_catalogue(path)

    assert catalogue.status == "active"
    assert len(catalogue.topics) == catalogue.expected_topic_count == 13
    assert catalogue.topic_group_count == catalogue.expected_topic_group_count == 19
    assert sum(len(topic.outcomes) for topic in catalogue.topics) == 87
    assert catalogue.topic("N1").outcome_codes("secondary_1") == {
        "1.1",
        "1.2",
        "1.3",
        "1.4",
        "1.5",
        "1.6",
        "1.7",
    }
    assert catalogue.topic("N2").outcome_codes("secondary_2") == {"2.4", "2.5"}


def test_generic_question_contract_accepts_another_confirmed_topic(bank_root):
    source = json.loads(next((bank_root / "questions").glob("*.json")).read_text())
    source.update(
        stable_key=f"n2-l{source['difficulty']}-001",
        bank_key="g3-sec1-n2-v1",
        topic_code="N2",
        primary_outcome="2.1",
        calculator_allowed=False,
    )
    for part in source["parts"]:
        part["primary_outcome"] = "2.1"
        part["secondary_outcomes"] = []

    question = Question.model_validate(source)

    assert question.topic_code == "N2"
    assert question.school_level == "secondary_1"
    assert question.calculator_allowed is False


@pytest.mark.parametrize("difficulty", [4, 5])
def test_question_contract_accepts_extended_difficulty_levels(bank_root, difficulty):
    source = json.loads(next((bank_root / "questions").glob("*.json")).read_text())
    source.update(
        stable_key=f"n2-l{difficulty}-001",
        bank_key="g3-sec1-n2-v1",
        topic_code="N2",
        primary_outcome="2.1",
        difficulty=difficulty,
    )
    for part in source["parts"]:
        part["primary_outcome"] = "2.1"
        part["secondary_outcomes"] = []

    assert Question.model_validate(source).difficulty == difficulty


def test_question_contract_rejects_difficulty_above_five(bank_root):
    source = json.loads(next((bank_root / "questions").glob("*.json")).read_text())
    source.update(stable_key="n1-l6-001", difficulty=6)

    with pytest.raises(ValidationError):
        Question.model_validate(source)


def test_bank_validator_rejects_outcome_outside_catalogue(
    repository_root, bank_root, tmp_path
):
    resources = tmp_path / "backend_resources"
    target = resources / "question_bank/g3_math/secondary_1/n1/v1"
    shutil.copytree(bank_root, target)
    shutil.copytree(
        repository_root / "backend_resources/question_bank/schema",
        resources / "question_bank/schema",
    )
    question_path = next((target / "questions").glob("*.json"))
    payload = json.loads(question_path.read_text())
    payload["primary_outcome"] = "9.9"
    payload["parts"][0]["primary_outcome"] = "9.9"
    question_path.write_text(json.dumps(payload))

    report = validate_bank(
        target,
        catalogue_path=repository_root
        / "backend_resources/syllabi/g3_math/v1/catalogue.json",
    )

    assert not report.valid
    assert "unknown_question_outcome" in {issue.code for issue in report.errors}


def test_catalogue_validation_reports_remaining_scope(repository_root):
    report = validate_catalogue(
        repository_root / "backend_resources/question_bank/g3_math",
        repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json",
    )

    assert report.valid
    assert report.as_dict()["known_topic_count"] == 13
    assert report.as_dict()["unconfirmed_topic_count"] == 0
    assert report.as_dict()["known_topic_group_count"] == 19
    assert report.as_dict()["unconfirmed_topic_group_count"] == 0
    assert report.as_dict()["blueprinted_topic_level_count"] == 19
    assert report.as_dict()["authored_topic_level_count"] == 1
    assert {issue.code for issue in report.warnings} == {
        "difficulty_distribution",
        "outcome_distribution",
    }

    publish_report = validate_catalogue(
        repository_root / "backend_resources/question_bank/g3_math",
        repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        publish=True,
    )
    assert not publish_report.valid
    assert "incomplete_syllabus_catalogue" not in {
        issue.code for issue in publish_report.errors
    }
    assert "bank_review_required" in {
        issue.code for issue in publish_report.errors
    }


def test_course_contract_accepts_multiple_topic_units(repository_root):
    path = repository_root / "backend_resources/courses/g3_math/secondary_1/n1/v1/course.json"
    payload = json.loads(path.read_text())
    second = json.loads(json.dumps(payload["units"][0]))
    second.update(
        stable_key="g3-sec1-n2",
        position=2,
        topic_code="N2",
        title="Ratio and proportion",
    )
    for position, lesson in enumerate(second["lessons"], start=1):
        lesson["stable_key"] = f"n2-lesson-{position:02d}"
        lesson["outcomes"] = ["2.1"]
    payload["units"].append(second)

    course = Course.model_validate(payload)

    assert [unit.topic_code for unit in course.units] == ["N1", "N2"]
