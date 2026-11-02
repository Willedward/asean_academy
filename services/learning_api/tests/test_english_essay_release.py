from datetime import UTC, datetime, timedelta
from uuid import UUID

from learning_api.english_essay_calibration import (
    CALIBRATION_EVALUATOR_VERSION,
    CALIBRATION_POLICY_VERSION,
    CalibrationGateReport,
    CalibrationThresholds,
)
from learning_api.english_essay_release import (
    ConsentDecisionRequest,
    PrivacyReviewRequest,
)
from learning_api.english_essay_release_repository import (
    InMemoryEnglishEssayReleaseRepository,
)

ADMIN_ID = "00000000-0000-4000-8000-000000000010"
STUDENT_ID = UUID("00000000-0000-4000-8000-000000000011")


def report(*, passed: bool = True, candidate_hash: str = "b" * 64):
    failures = [] if passed else ["safety_gate_failed"]
    return CalibrationGateReport(
        policy_version=CALIBRATION_POLICY_VERSION,
        evaluator_version=CALIBRATION_EVALUATOR_VERSION,
        provider_name="candidate-provider",
        model_name="candidate-model",
        provider_policy_version="english-essay-feedback-policy-v1",
        educator_reference="educator-ref-private-001",
        anchor_set_sha256="a" * 64,
        candidate_set_sha256=candidate_hash,
        anchor_count=12,
        run_count=24,
        schema_valid_rate=1.0,
        evidence_fidelity_rate=1.0,
        band_within_one_rate=1.0,
        repeat_stability_passed=True,
        instructional_usefulness_rate=1.0,
        age_appropriate_tone_rate=1.0,
        case_recognition_rate=1.0,
        false_claim_count=0,
        safety_failure_count=0 if passed else 1,
        maximum_run_cost_micros_sgd=400_000,
        p95_latency_ms=8_000,
        thresholds=CalibrationThresholds(),
        failure_reasons=failures,
        passed=passed,
    )


def privacy(gate_report_id: str, *, passed: bool = True):
    return PrivacyReviewRequest(
        calibration_gate_report_id=UUID(gate_report_id),
        guardian_consent_process_verified=passed,
        consent_policy_version="english-essay-consent-v1",
        retention_policy_version="english-essay-retention-v1",
        retention_days=90,
        deletion_workflow_verified=passed,
        raw_essay_logging_excluded=passed,
        provider_agreement_reference="provider-agreement-ref-private-001",
        regional_privacy_review_reference="privacy-review-ref-private-001",
        provider_data_region="Singapore",
        provider_retention_days=0,
        subprocessors_reviewed=passed,
        automated_safety_classification_verified=passed,
        safeguarding_contact_reference="safeguarding-ref-private-001",
        review_notes="Private review evidence is held outside the application.",
    )


def evidence(repository, *, enabled=False):
    return repository.evidence(
        "candidate-provider",
        "candidate-model",
        "english-essay-feedback-policy-v1",
        environment_enabled=enabled,
    )


def test_release_requires_current_calibration_privacy_decision_and_environment():
    repository = InMemoryEnglishEssayReleaseRepository()
    assert evidence(repository)["state"] == "blocked_no_calibration"

    calibration = repository.record_calibration(report(), ADMIN_ID, "request-calibration")
    assert evidence(repository)["state"] == "blocked_privacy_review_missing"

    review = repository.record_privacy_review(
        privacy(calibration["gate_report_id"]), ADMIN_ID, "request-privacy"
    )
    repeated_review = repository.record_privacy_review(
        privacy(calibration["gate_report_id"]), ADMIN_ID, "request-privacy"
    )
    assert repeated_review["privacy_review_id"] == review["privacy_review_id"]
    assert evidence(repository)["state"] == "ready_for_release"

    released = repository.record_release_decision(
        calibration_gate_report_id=UUID(calibration["gate_report_id"]),
        privacy_review_id=UUID(review["privacy_review_id"]),
        action="released",
        reason="The bounded evidence and privacy review have passed.",
        actor_user_id=ADMIN_ID,
        request_id="request-release",
    )
    repeated_release = repository.record_release_decision(
        calibration_gate_report_id=UUID(calibration["gate_report_id"]),
        privacy_review_id=UUID(review["privacy_review_id"]),
        action="released",
        reason="The bounded evidence and privacy review have passed.",
        actor_user_id=ADMIN_ID,
        request_id="request-release",
    )
    assert repeated_release["release_event_id"] == released["release_event_id"]
    assert evidence(repository)["state"] == "disabled_by_environment"
    assert evidence(repository, enabled=True)["live_provider_available"] is True

    repository.record_release_decision(
        calibration_gate_report_id=UUID(calibration["gate_report_id"]),
        privacy_review_id=UUID(review["privacy_review_id"]),
        action="suspended",
        reason="Provider processing is suspended pending a new review.",
        actor_user_id=ADMIN_ID,
        request_id="request-suspend",
    )
    assert evidence(repository, enabled=True)["state"] == "suspended"


def test_newer_failed_evidence_invalidates_an_older_release():
    repository = InMemoryEnglishEssayReleaseRepository()
    calibration = repository.record_calibration(report(), ADMIN_ID, "request-calibration")
    review = repository.record_privacy_review(
        privacy(calibration["gate_report_id"]), ADMIN_ID, "request-privacy"
    )
    repository.record_release_decision(
        calibration_gate_report_id=UUID(calibration["gate_report_id"]),
        privacy_review_id=UUID(review["privacy_review_id"]),
        action="released",
        reason="All release controls passed the bounded review.",
        actor_user_id=ADMIN_ID,
        request_id="request-release",
    )
    assert evidence(repository, enabled=True)["state"] == "released"

    repository.record_calibration(
        report(passed=False, candidate_hash="c" * 64), ADMIN_ID, "request-failed"
    )
    assert evidence(repository, enabled=True)["state"] == "blocked_calibration_failed"
    assert evidence(repository, enabled=True)["live_provider_available"] is False


def test_latest_consent_event_must_be_unexpired_grant_for_exact_policy():
    repository = InMemoryEnglishEssayReleaseRepository()
    grant = ConsentDecisionRequest(
        action="granted",
        consent_policy_version="english-essay-consent-v1",
        guardian_reference_sha256="d" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=30),
        reason="Guardian consent was verified through the private academy process.",
    )
    consent = repository.record_consent(STUDENT_ID, grant, ADMIN_ID, "request-consent")
    repeated = repository.record_consent(STUDENT_ID, grant, ADMIN_ID, "request-consent")
    assert repeated["consent_event_id"] == consent["consent_event_id"]
    assert repository.has_active_consent(str(STUDENT_ID), "english-essay-consent-v1")
    assert not repository.has_active_consent(str(STUDENT_ID), "english-essay-consent-v2")

    revoke = ConsentDecisionRequest(
        action="revoked",
        consent_policy_version="english-essay-consent-v1",
        reason="The guardian withdrew consent through the academy process.",
    )
    repository.record_consent(STUDENT_ID, revoke, ADMIN_ID, "request-revoke")
    assert not repository.has_active_consent(str(STUDENT_ID), "english-essay-consent-v1")
