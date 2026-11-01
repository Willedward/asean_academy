import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from learning_api.english_essay_calibration import (
    CALIBRATION_POLICY_VERSION,
    CalibrationPackage,
    evaluate_calibration,
)
from learning_api.english_essay_calibration_repository import (
    InMemoryEnglishEssayCalibrationRepository,
)
from learning_api.english_essay_provider_feedback import (
    PROVIDER_FEEDBACK_DISCLAIMER,
    PROVIDER_FEEDBACK_SCHEMA_VERSION,
)

RUBRIC_KEY = "english-essay-rubric-instructional-v1"
CRITERIA = [
    {"criterion_key": "task_fulfilment", "title": "Task fulfilment and focus"},
    {"criterion_key": "organisation_cohesion", "title": "Organisation and cohesion"},
    {"criterion_key": "development_evidence", "title": "Development and evidence"},
    {"criterion_key": "language_control", "title": "Language control and precision"},
]
CASE_TAGS = [
    ["off_topic"],
    ["memorised"],
    ["very_short"],
    ["error_heavy"],
    ["prompt_injection"],
    ["typical"],
    ["typical"],
    ["typical"],
    ["typical"],
    ["typical"],
    ["typical"],
    ["typical"],
]


def _feedback(body: str, level: int = 3):
    quote = body.split(". ", 1)[0] + "."
    return {
        "schema_version": PROVIDER_FEEDBACK_SCHEMA_VERSION,
        "rubric_key": RUBRIC_KEY,
        "rubric_revision": 1,
        "preparation_estimate": "developing",
        "criterion_feedback": [
            {
                "criterion_key": criterion["criterion_key"],
                "criterion_title": criterion["title"],
                "preparation_level": level,
                "evidence_spans": [
                    {"quote": quote, "start": 0, "end": len(quote)}
                ],
                "what_works": "The quoted detail gives a specific starting point.",
                "next_step": "Explain the consequence and connect it to the main idea.",
            }
            for criterion in CRITERIA
        ],
        "overall_summary": "The response has a relevant example and needs deeper explanation.",
        "strengths": ["A specific school experience anchors the response."],
        "priorities": [
            "Explain why the experience mattered.",
            "Connect the example to the central insight.",
        ],
        "revision_task": "Add two sentences explaining the consequence of the experience.",
        "transfer_goal": "Connect each future example explicitly to the main insight.",
        "learner_disclaimer": PROVIDER_FEEDBACK_DISCLAIMER,
    }


def _package_dict():
    anchors = []
    runs = []
    for index, tags in enumerate(CASE_TAGS, start=1):
        key = f"anchor-case-{index:02d}"
        body = (
            f"I learned to organise project {index} at school. "
            "The experience taught me to listen before assigning each role."
        )
        anchors.append(
            {
                "anchor_key": key,
                "submission_body": body,
                "case_tags": tags,
                "prompt_key": "english-essay-prompt-school-learning-transfer-v1",
                "prompt_revision": 1,
                "rubric_key": RUBRIC_KEY,
                "rubric_revision": 1,
                "rubric_criteria": CRITERIA,
                "educator_levels": {
                    criterion["criterion_key"]: 3 for criterion in CRITERIA
                },
            }
        )
        recognised = [tag for tag in tags if tag in {"off_topic", "memorised"}]
        for run_number in (1, 2):
            runs.append(
                {
                    "anchor_key": key,
                    "run_number": run_number,
                    "provider_output": _feedback(body),
                    "actual_cost_micros_sgd": 400_000,
                    "latency_ms": 8_000,
                    "human_observation": {
                        "instructional_usefulness": "useful",
                        "age_appropriate_tone": True,
                        "safety_passed": True,
                        "false_claim_count": 0,
                        "recognised_case_tags": recognised,
                    },
                }
            )
    return {
        "policy_version": CALIBRATION_POLICY_VERSION,
        "provider_name": "disabled-candidate-provider",
        "model_name": "disabled-candidate-model",
        "provider_policy_version": "english-essay-feedback-policy-v1",
        "educator_reference": "educator-ref-private-001",
        "thresholds": {},
        "anchors": anchors,
        "candidate_runs": runs,
    }


def test_bounded_calibration_passes_and_returns_only_privacy_safe_aggregates():
    package = CalibrationPackage.model_validate(_package_dict())
    report = evaluate_calibration(package)

    assert report.passed is True
    assert report.failure_reasons == []
    assert report.anchor_count == 12
    assert report.run_count == 24
    assert report.schema_valid_rate == 1
    assert report.evidence_fidelity_rate == 1
    assert report.band_within_one_rate == 1
    assert report.repeat_stability_passed is True
    assert report.case_recognition_rate == 1
    assert report.contains_private_essay_text is False
    assert report.live_provider_released is False
    assert "I learned" not in report.model_dump_json()


def test_gate_fails_closed_for_bad_evidence_instability_safety_and_ceiling_breaches():
    source = _package_dict()
    first = source["candidate_runs"][0]
    first["provider_output"]["criterion_feedback"][0]["evidence_spans"][0][
        "quote"
    ] = "This was not in the essay."
    first["human_observation"]["safety_passed"] = False
    first["human_observation"]["instructional_usefulness"] = "not_useful"
    first["human_observation"]["false_claim_count"] = 1
    first["actual_cost_micros_sgd"] = 1_000_001
    first["latency_ms"] = 20_001
    second = source["candidate_runs"][1]
    second["provider_output"] = _feedback(source["anchors"][0]["submission_body"], level=5)
    second["latency_ms"] = 20_001

    report = evaluate_calibration(CalibrationPackage.model_validate(source))

    assert report.passed is False
    assert "evidence_fidelity_failed" in report.failure_reasons
    assert "repeat_stability_failed" in report.failure_reasons
    assert "false_claim_gate_failed" in report.failure_reasons
    assert "safety_gate_failed" in report.failure_reasons
    assert "cost_ceiling_failed" in report.failure_reasons
    assert "latency_ceiling_failed" in report.failure_reasons


def test_required_edge_cases_and_exact_repeat_coverage_are_mandatory():
    source = _package_dict()
    source["anchors"][0]["case_tags"] = ["typical"]
    source["candidate_runs"][0]["run_number"] = 2

    report = evaluate_calibration(CalibrationPackage.model_validate(source))

    assert report.passed is False
    assert "required_case_coverage_missing" in report.failure_reasons
    assert "duplicate_candidate_run" in report.failure_reasons
    assert "candidate_run_coverage_incomplete" in report.failure_reasons


def test_anchor_and_candidate_hashes_change_when_private_evidence_changes():
    original = _package_dict()
    original_report = evaluate_calibration(CalibrationPackage.model_validate(original))

    changed_anchor = deepcopy(original)
    changed_anchor["anchors"][5]["submission_body"] += " I revised the plan afterwards."
    changed_anchor["candidate_runs"][10]["provider_output"] = _feedback(
        changed_anchor["anchors"][5]["submission_body"]
    )
    changed_anchor["candidate_runs"][11]["provider_output"] = _feedback(
        changed_anchor["anchors"][5]["submission_body"]
    )
    changed_anchor_report = evaluate_calibration(
        CalibrationPackage.model_validate(changed_anchor)
    )
    assert changed_anchor_report.anchor_set_sha256 != original_report.anchor_set_sha256

    changed_candidate = deepcopy(original)
    changed_candidate["candidate_runs"][3]["latency_ms"] += 1
    changed_candidate_report = evaluate_calibration(
        CalibrationPackage.model_validate(changed_candidate)
    )
    assert (
        changed_candidate_report.candidate_set_sha256
        != original_report.candidate_set_sha256
    )


def test_source_controlled_policy_matches_the_fail_closed_evaluator():
    repository_root = Path(__file__).resolve().parents[3]
    policy = json.loads(
        (
            repository_root
            / "backend_resources/english/v1/calibration/english-essay-calibration-policy-v1.json"
        ).read_text(encoding="utf-8")
    )
    package = CalibrationPackage.model_validate(_package_dict())
    thresholds = package.thresholds.model_dump(mode="json")
    minimum_anchors = thresholds.pop("minimum_anchors")
    maximum_anchors = thresholds.pop("maximum_anchors")
    runs_per_anchor = thresholds.pop("runs_per_anchor")

    assert policy["policy_version"] == package.policy_version
    assert policy["release_thresholds"] == thresholds
    assert policy["private_inputs"]["minimum_anchors"] == minimum_anchors
    assert policy["private_inputs"]["maximum_anchors"] == maximum_anchors
    assert policy["private_inputs"]["runs_per_anchor"] == runs_per_anchor
    assert policy["release_effect"]["live_provider_released"] is False


def test_gate_repository_is_idempotent_and_never_treats_a_failed_report_as_passed():
    repository = InMemoryEnglishEssayCalibrationRepository()
    passing = evaluate_calibration(CalibrationPackage.model_validate(_package_dict()))
    stored = repository.record(passing)
    repeated = repository.record(passing)

    assert repeated["gate_report_id"] == stored["gate_report_id"]
    assert repository.latest_passed(
        passing.provider_name, passing.model_name, passing.provider_policy_version
    )["candidate_set_sha256"] == passing.candidate_set_sha256

    failing_source = _package_dict()
    for run in failing_source["candidate_runs"][:3]:
        run["human_observation"]["instructional_usefulness"] = "not_useful"
    failing_source["model_name"] = "failed-candidate-model"
    failing = evaluate_calibration(
        CalibrationPackage.model_validate(failing_source)
    )
    assert failing.passed is False
    repository.record(failing)
    assert repository.latest_passed(
        failing.provider_name, failing.model_name, failing.provider_policy_version
    ) is None


def test_offline_cli_emits_only_the_privacy_safe_report(tmp_path):
    repository_root = Path(__file__).resolve().parents[3]
    source = tmp_path / "private-package.json"
    output = tmp_path / "safe-report.json"
    source.write_text(json.dumps(_package_dict()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(
                repository_root
                / "services/learning_api/scripts/evaluate_english_essay_calibration.py"
            ),
            str(source),
            "--output",
            str(output),
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    rendered = output.read_text(encoding="utf-8")
    assert '"passed": true' in rendered
    assert "I learned to organise" not in rendered
