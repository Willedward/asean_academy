import json

from jsonschema import Draft202012Validator

from question_bank.models import Question
from question_bank.validation import validate_bank


def test_five_question_pilot_is_a_valid_draft(bank_root):
    report = validate_bank(bank_root)

    assert report.valid
    assert len(report.questions) == 5
    assert {question.difficulty for question in report.questions} == {1, 2, 3}
    assert all(issue.severity == "warning" for issue in report.issues)
    assert {issue.code for issue in report.issues} == {
        "difficulty_distribution",
        "outcome_distribution",
    }


def test_incomplete_draft_cannot_be_published(bank_root):
    report = validate_bank(bank_root, publish=True)

    assert not report.valid
    assert any(issue.code == "difficulty_distribution" for issue in report.errors)
    assert any(issue.code == "review_required" for issue in report.errors)


def test_every_pilot_question_matches_the_source_contract(bank_root):
    schema_path = bank_root.parents[3] / "schema" / "question-v1.schema.json"
    schema = json.loads(schema_path.read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for path in sorted((bank_root / "questions").glob("*.json")):
        payload = json.loads(path.read_text())
        assert not list(validator.iter_errors(payload))
        question = Question.model_validate(payload)
        assert question.stable_key == path.stem
        assert sum(part.marks for part in question.parts) == question.total_marks
        assert all([hint.stage for hint in part.hints] == [1, 2] for part in question.parts)


def test_blueprint_totals_remain_consistent(bank_root):
    blueprint = json.loads((bank_root / "blueprint.json").read_text())
    totals = {
        str(level): sum(
            row["difficulty_counts"][str(level)] for row in blueprint["outcome_distribution"]
        )
        for level in (1, 2, 3)
    }

    assert totals == blueprint["difficulty_distribution"] == {"1": 15, "2": 15, "3": 10}
    assert sum(row["total"] for row in blueprint["outcome_distribution"]) == 40
