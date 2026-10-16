import json
import shutil

import pytest
from pydantic import ValidationError

import question_bank.authoring_runner as authoring_runner
import question_bank.collaboration as collaboration
from question_bank.authoring import QuestionBatchManifest, load_manifest, validate_batch
from question_bank.authoring_runner import create_authoring_work_order, next_authoring_batch
from question_bank.collaboration import check_pull_request
from question_bank.diagnostic_authoring import plan_diagnostic_authoring_banks
from question_bank.diagnostic_plan import DiagnosticPlan


def _paths(repository_root):
    return {
        "banks": repository_root / "backend_resources/question_bank/g3_math",
        "plan": repository_root
        / "backend_resources/diagnostics/g3_math/secondary_1_2/v1/plan.json",
        "syllabus": repository_root
        / "backend_resources/syllabi/g3_math/v1/catalogue.json",
        "house_rules": repository_root
        / "backend_resources/question_bank/authoring/house-rules-v2.json",
    }


def test_tracked_diagnostic_banks_match_all_reserved_plan_slots(repository_root):
    paths = _paths(repository_root)
    plan = DiagnosticPlan.model_validate_json(paths["plan"].read_text())
    expected = {
        slot.bank_key: [
            item.stable_key
            for form in plan.forms
            for item in form.items
            if item.bank_key == slot.bank_key
        ]
        for form in plan.forms
        for slot in form.items
    }

    manifests = {}
    for path in sorted(paths["banks"].glob("**/v2/batches/*.json")):
        manifest = load_manifest(path)
        manifests[manifest.bank_key] = manifest
        assert manifest.bank_role == "diagnostic"
        assert manifest.expected_question_count == 4
        assert manifest.question_keys == expected[manifest.bank_key]
        assert validate_batch(
            path,
            repository_root=repository_root,
            syllabus_path=paths["syllabus"],
        ).valid

    assert len(manifests) == len(expected) == 19
    assert sum(len(manifest.question_keys) for manifest in manifests.values()) == 76


def test_diagnostic_bank_planner_is_idempotent(repository_root):
    paths = _paths(repository_root)
    result = plan_diagnostic_authoring_banks(
        paths["plan"],
        paths["banks"],
        repository_root,
        paths["syllabus"],
        paths["house_rules"],
    )

    assert result["created_blueprints"] == []
    assert result["created_manifests"] == []
    assert len(result["preserved_blueprints"]) == 19
    assert len(result["preserved_manifests"]) == 19
    assert result["question_slots"] == 76


def test_diagnostic_work_order_preserves_form_usage(
    repository_root, tmp_path, monkeypatch
):
    paths = _paths(repository_root)
    manifest = (
        paths["banks"]
        / "secondary_1/n1/v2/batches/g3-sec1-n1-diagnostic-b001.json"
    )
    output = tmp_path / "work-order"

    original_validate_batch = authoring_runner.validate_batch

    def validate_as_planned(path, **kwargs):
        report = original_validate_batch(path, **kwargs)
        if path == manifest and report.manifest is not None:
            report.manifest = report.manifest.model_copy(update={"status": "planned"})
        return report

    monkeypatch.setattr(authoring_runner, "validate_batch", validate_as_planned)

    create_authoring_work_order(
        manifest,
        output,
        repository_root=repository_root,
        syllabus_path=paths["syllabus"],
    )
    payload = json.loads((output / "work-order.json").read_text())

    assert payload["bank_role"] == "diagnostic"
    assert payload["expected_question_count"] == 4
    assert payload["generation_contract"]["learning_question_reuse_allowed"] is False
    assert [slot["diagnostic_usage"]["purpose"] for slot in payload["slots"]] == [
        "baseline",
        "baseline",
        "endline",
        "endline",
    ]
    prompt = (output / "prompt.md").read_text()
    assert "comparable difficulty" in prompt
    assert "Do not reuse any learning question" in prompt


def test_next_batch_can_select_only_diagnostic_work(
    repository_root, tmp_path, monkeypatch
):
    paths = _paths(repository_root)
    claims = tmp_path / "claims.json"
    claims.write_text('{"schema_version":"1.0.0","claims":[]}\n')

    original_load_manifest = authoring_runner.load_manifest

    def load_with_n1_planned(path):
        manifest = original_load_manifest(path)
        if manifest.batch_id == "g3-sec1-n1-diagnostic-b001":
            return manifest.model_copy(update={"status": "planned"})
        return manifest

    monkeypatch.setattr(authoring_runner, "load_manifest", load_with_n1_planned)

    result = next_authoring_batch(
        paths["banks"],
        claims,
        owner="Willedward",
        syllabus_path=paths["syllabus"],
        bank_role="diagnostic",
    )

    assert result["status"] == "ready"
    assert result["bank_role"] == "diagnostic"
    assert result["batch_id"] == "g3-sec1-n1-diagnostic-b001"
    assert result["remaining_unclaimed_planned_batches"] >= 1


def test_four_question_exception_cannot_weaken_learning_batches(repository_root):
    paths = _paths(repository_root)
    source = paths["banks"] / (
        "secondary_1/n1/v2/batches/g3-sec1-n1-diagnostic-b001.json"
    )
    payload = json.loads(source.read_text())

    learning = dict(payload)
    learning["batch_id"] = "g3-sec1-n1-b999"
    learning["bank_key"] = "g3-sec1-n1-v1"
    learning["bank_role"] = "learning"
    with pytest.raises(ValidationError, match="20–30"):
        QuestionBatchManifest.model_validate(learning)

    oversized = dict(payload)
    oversized["expected_question_count"] = 5
    with pytest.raises(ValidationError, match="exactly four"):
        QuestionBatchManifest.model_validate(oversized)


def test_validator_rejects_diagnostic_keys_that_drift_from_plan(
    repository_root, tmp_path
):
    paths = _paths(repository_root)
    source_bank = paths["banks"] / "secondary_1/n1/v2"
    target_bank = tmp_path / "secondary_1/n1/v2"
    shutil.copytree(source_bank, target_bank)
    manifest_path = next((target_bank / "batches").glob("*.json"))
    payload = json.loads(manifest_path.read_text())
    payload["question_keys"][0] = "n1-l2-999"
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n")

    report = validate_batch(
        manifest_path,
        repository_root=repository_root,
        syllabus_path=paths["syllabus"],
    )

    assert not report.valid
    assert "diagnostic_plan_question_keys" in {issue.code for issue in report.errors}


def test_planning_pull_request_can_add_multiple_empty_diagnostic_batches(
    repository_root, tmp_path, monkeypatch
):
    paths = _paths(repository_root)
    claims = tmp_path / "claims.json"
    claims.write_text('{"schema_version":"1.0.0","claims":[]}\n')
    planned_batch_ids = {
        "g3-sec1-n1-diagnostic-b001",
        "g3-sec1-n2-diagnostic-b001",
    }
    original_load_manifest = collaboration.load_manifest

    def load_selected_as_planned(path):
        manifest = original_load_manifest(path)
        if manifest.batch_id in planned_batch_ids:
            return manifest.model_copy(update={"status": "planned"})
        return manifest

    monkeypatch.setattr(collaboration, "load_manifest", load_selected_as_planned)
    changed = [
        (
            paths["banks"]
            / "secondary_1/n1/v2/batches/g3-sec1-n1-diagnostic-b001.json"
        ).relative_to(repository_root).as_posix(),
        (
            paths["banks"]
            / "secondary_1/n2/v2/batches/g3-sec1-n2-diagnostic-b001.json"
        ).relative_to(repository_root).as_posix(),
    ]

    report = check_pull_request(
        changed_files=changed,
        head_branch="feature/diagnostic-four-question-authoring",
        repository_root=repository_root,
        bank_root=paths["banks"],
        syllabus_path=paths["syllabus"],
        registry_path=claims,
        output=tmp_path / "review",
    )

    assert report.valid
    assert report.changed_batches == [
        "g3-sec1-n1-diagnostic-b001",
        "g3-sec1-n2-diagnostic-b001",
    ]
    assert report.exported_batches == []
