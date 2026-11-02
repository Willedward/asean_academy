"""Opt-in release-gate checks against a migrated disposable PostgreSQL database."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import psycopg
import pytest

from learning_api.account_deletion_repository import PostgresAccountDeletionRepository
from learning_api.english_essay_calibration import (
    CALIBRATION_EVALUATOR_VERSION,
    CALIBRATION_POLICY_VERSION,
    CalibrationGateReport,
    CalibrationThresholds,
)
from learning_api.english_essay_release import (
    CalibrationEvidenceResponse,
    ConsentDecisionRequest,
    ConsentDecisionResponse,
    EssayFeedbackReleaseEvidenceResponse,
    PrivacyReviewRequest,
    PrivacyReviewResponse,
    ReleaseDecisionResponse,
)
from learning_api.english_essay_release_repository import PostgresEnglishEssayReleaseRepository


def _report(suffix: str) -> CalibrationGateReport:
    return CalibrationGateReport(
        policy_version=CALIBRATION_POLICY_VERSION,
        evaluator_version=CALIBRATION_EVALUATOR_VERSION,
        provider_name=f"postgres-release-provider-{suffix}",
        model_name="postgres-release-model",
        provider_policy_version="english-essay-feedback-policy-v1",
        educator_reference=f"educator-ref-{suffix}",
        anchor_set_sha256="a" * 64,
        candidate_set_sha256="b" * 64,
        anchor_count=12,
        run_count=24,
        schema_valid_rate=1,
        evidence_fidelity_rate=1,
        band_within_one_rate=1,
        repeat_stability_passed=True,
        instructional_usefulness_rate=1,
        age_appropriate_tone_rate=1,
        case_recognition_rate=1,
        false_claim_count=0,
        safety_failure_count=0,
        maximum_run_cost_micros_sgd=400_000,
        p95_latency_ms=8_000,
        thresholds=CalibrationThresholds(),
        failure_reasons=[],
        passed=True,
    )


@pytest.mark.postgres
def test_postgres_release_gate_is_append_only_fail_closed_and_consent_bounded():
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to a migrated disposable database")
    administrator, student = uuid4(), uuid4()
    suffix = uuid4().hex[:12]
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "insert into auth.users(id,email) values (%s,%s),(%s,%s)",
            (
                administrator,
                f"admin-{suffix}@example.test",
                student,
                f"student-{suffix}@example.test",
            ),
        )
        connection.execute(
            "insert into profiles(id,email,role) values (%s,%s,'academic_admin'),(%s,%s,'student')",
            (
                administrator,
                f"admin-{suffix}@example.test",
                student,
                f"student-{suffix}@example.test",
            ),
        )

    repository = PostgresEnglishEssayReleaseRepository(database_url)
    report = _report(suffix)
    calibration = repository.record_calibration(report, str(administrator), f"calibration-{suffix}")
    CalibrationEvidenceResponse.model_validate(calibration)
    assert (
        repository.evidence(
            report.provider_name,
            report.model_name,
            report.provider_policy_version,
            environment_enabled=True,
        )["state"]
        == "blocked_privacy_review_missing"
    )

    privacy = repository.record_privacy_review(
        PrivacyReviewRequest(
            calibration_gate_report_id=UUID(calibration["gate_report_id"]),
            guardian_consent_process_verified=True,
            consent_policy_version="english-essay-consent-v1",
            retention_policy_version="english-essay-retention-v1",
            retention_days=90,
            deletion_workflow_verified=True,
            raw_essay_logging_excluded=True,
            provider_agreement_reference=f"provider-agreement-ref-{suffix}",
            regional_privacy_review_reference=f"privacy-review-ref-{suffix}",
            provider_data_region="Singapore",
            provider_retention_days=0,
            subprocessors_reviewed=True,
            automated_safety_classification_verified=True,
            safeguarding_contact_reference=f"safeguarding-ref-{suffix}",
            review_notes="Private evidence is retained outside the application database.",
        ),
        str(administrator),
        f"privacy-{suffix}",
    )
    PrivacyReviewResponse.model_validate(privacy)
    repeated_privacy = repository.record_privacy_review(
        PrivacyReviewRequest.model_validate(
            {
                key: value
                for key, value in privacy.items()
                if key in PrivacyReviewRequest.model_fields
            }
        ),
        str(administrator),
        f"privacy-{suffix}",
    )
    assert repeated_privacy["privacy_review_id"] == privacy["privacy_review_id"]
    decision = repository.record_release_decision(
        calibration_gate_report_id=UUID(calibration["gate_report_id"]),
        privacy_review_id=UUID(privacy["privacy_review_id"]),
        action="released",
        reason="The bounded calibration and privacy controls passed.",
        actor_user_id=str(administrator),
        request_id=f"release-{suffix}",
    )
    ReleaseDecisionResponse.model_validate(decision)
    assert (
        repository.evidence(
            report.provider_name,
            report.model_name,
            report.provider_policy_version,
            environment_enabled=False,
        )["state"]
        == "disabled_by_environment"
    )
    assert (
        repository.evidence(
            report.provider_name,
            report.model_name,
            report.provider_policy_version,
            environment_enabled=True,
        )["state"]
        == "released"
    )

    consent = repository.record_consent(
        student,
        ConsentDecisionRequest(
            action="granted",
            consent_policy_version="english-essay-consent-v1",
            guardian_reference_sha256="c" * 64,
            expires_at=datetime.now(UTC) + timedelta(days=30),
            reason="Guardian consent was verified through the private academy workflow.",
        ),
        str(administrator),
        f"consent-{suffix}",
    )
    ConsentDecisionResponse.model_validate(consent)
    assert repository.has_active_consent(str(student), "english-essay-consent-v1")
    deletion_preview = PostgresAccountDeletionRepository(
        database_url, "release-gate-test-secret-at-least-32-characters"
    ).preview(student)
    assert deletion_preview["counts"]["english_essay_processing_consent_events"] == 1
    EssayFeedbackReleaseEvidenceResponse.model_validate(
        repository.evidence(
            report.provider_name,
            report.model_name,
            report.provider_policy_version,
            environment_enabled=True,
        )
    )

    with psycopg.connect(database_url) as connection:
        with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
            with connection.transaction():
                connection.execute(
                    "update english_essay_feedback_release_events set reason='This decision cannot be changed after insertion.' where id=%s",
                    (decision["release_event_id"],),
                )
        grants = connection.execute(
            """select table_name,grantee,privilege_type from information_schema.role_table_grants
                where table_schema='public'
                  and table_name in ('english_essay_feedback_privacy_reviews','english_essay_feedback_release_events','english_essay_processing_consent_events')
                  and grantee in ('anon','authenticated')"""
        ).fetchall()
        assert grants == []
