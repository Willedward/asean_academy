import json

from question_bank.catalogue import load_catalogue
from question_bank.diagnostic_plan import (
    build_diagnostic_plan,
    validate_diagnostic_plan,
    write_diagnostic_plan,
)


def test_tracked_full_syllabus_diagnostic_plan_is_deterministic(repository_root):
    syllabus_path = repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json"
    plan_path = (
        repository_root
        / "backend_resources/diagnostics/g3_math/secondary_1_2/v1/plan.json"
    )
    plan, issues = validate_diagnostic_plan(plan_path, syllabus_path)

    assert plan is not None
    assert not issues
    assert plan == build_diagnostic_plan(load_catalogue(syllabus_path))
    assert len(plan.forms) == 2
    assert sum(len(form.items) for form in plan.forms) == 76


def test_forms_are_disjoint_matched_and_cover_every_topic_group(repository_root):
    plan_path = (
        repository_root
        / "backend_resources/diagnostics/g3_math/secondary_1_2/v1/plan.json"
    )
    payload = json.loads(plan_path.read_text())
    baseline, endline = payload["forms"]

    assert baseline["purpose"] == "baseline"
    assert endline["purpose"] == "endline"
    assert not (
        {item["stable_key"] for item in baseline["items"]}
        & {item["stable_key"] for item in endline["items"]}
    )
    for form in (baseline, endline):
        groups = {item["topic_group_key"] for item in form["items"]}
        assert len(groups) == 19
        assert all(
            sum(item["topic_group_key"] == group for item in form["items"]) == 2
            for group in groups
        )
    for group in {item["topic_group_key"] for item in baseline["items"]}:
        baseline_levels = sorted(
            item["difficulty"]
            for item in baseline["items"]
            if item["topic_group_key"] == group
        )
        endline_levels = sorted(
            item["difficulty"]
            for item in endline["items"]
            if item["topic_group_key"] == group
        )
        assert baseline_levels == endline_levels


def test_validator_rejects_an_outcome_outside_its_topic_group(repository_root, tmp_path):
    source = (
        repository_root
        / "backend_resources/diagnostics/g3_math/secondary_1_2/v1/plan.json"
    )
    payload = json.loads(source.read_text())
    payload["forms"][0]["items"][0]["outcome_code"] = "99.99"
    changed = tmp_path / "plan.json"
    changed.write_text(json.dumps(payload))

    plan, issues = validate_diagnostic_plan(
        changed,
        repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json",
    )

    assert plan is not None
    assert {issue.code for issue in issues} == {"unknown_diagnostic_outcome"}


def test_writer_creates_the_same_plan(repository_root, tmp_path):
    output = tmp_path / "plan.json"
    tracked = (
        repository_root
        / "backend_resources/diagnostics/g3_math/secondary_1_2/v1/plan.json"
    )
    plan = write_diagnostic_plan(
        repository_root / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        output,
    )

    assert json.loads(output.read_text()) == plan.model_dump(mode="json")
    assert output.read_bytes() == tracked.read_bytes()
