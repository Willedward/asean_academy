import hashlib
import json
import shutil

from jsonschema import Draft202012Validator

from question_bank.geometry_validation import revisioned_asset_path_issues
from question_bank.models import Question
from question_bank.validation import validate_bank


def test_authored_n1_pilot_is_a_valid_partial_draft(bank_root):
    report = validate_bank(bank_root)

    assert report.valid
    assert len(report.questions) == 62
    assert {question.difficulty for question in report.questions} == {1, 2, 3, 4, 5}
    assert not report.errors
    assert {issue.code for issue in report.warnings} == {
        "difficulty_distribution",
        "outcome_distribution",
    }


def test_unreviewed_draft_cannot_be_published(bank_root):
    report = validate_bank(bank_root, publish=True)

    assert not report.valid
    assert len([issue for issue in report.errors if issue.code == "review_required"]) == 62


def test_changed_assets_use_a_revisioned_storage_path():
    assert revisioned_asset_path_issues("assets/angle.svg", 2) == []
    assert revisioned_asset_path_issues("assets/angle-r3.svg", 3) == []
    assert revisioned_asset_path_issues("assets/angle.svg", 3) == [
        (
            "asset_revision_path",
            "Revision 3 assets require an -r3 filename before the extension.",
        )
    ]


def test_every_question_matches_the_source_contract(bank_root):
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
        for level in (1, 2, 3, 4, 5)
    }

    assert totals == blueprint["difficulty_distribution"] == {
        "1": 21,
        "2": 31,
        "3": 31,
        "4": 16,
        "5": 5,
    }
    assert sum(row["total"] for row in blueprint["outcome_distribution"]) == 104


def test_question_angle_diagram_rays_must_match_the_declared_classification(
    repository_root, tmp_path
):
    source = (
        repository_root
        / "backend_resources/question_bank/g3_math/secondary_1/g1/v1"
    )
    bank_root = tmp_path / "question_bank/g3_math/secondary_1/g1/v1"
    shutil.copytree(source, bank_root)
    shutil.copytree(
        repository_root / "backend_resources/question_bank/schema",
        tmp_path / "question_bank/schema",
    )
    question_path = bank_root / "questions/g1-l1-001.json"
    question = json.loads(question_path.read_text())
    asset = question["assets"][0]
    svg_path = bank_root / asset["path"]
    svg = svg_path.read_text().replace(
        '<line x1="520" y1="230" x2="628.25" y2="292.5"/>',
        '<line x1="520" y1="230" x2="628.25" y2="167.5"/>',
        1,
    )
    svg_path.write_text(svg)
    asset["sha256"] = hashlib.sha256(svg_path.read_bytes()).hexdigest()
    question_path.write_text(json.dumps(question))

    report = validate_bank(
        bank_root,
        catalogue_path=repository_root
        / "backend_resources/syllabi/g3_math/v1/catalogue.json",
    )

    assert not report.valid
    assert "geometry_angle_measure" in {issue.code for issue in report.errors}
