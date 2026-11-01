"""Opt-in calibration persistence checks against a migrated disposable PostgreSQL DB."""

from __future__ import annotations

import os

import psycopg
import pytest

from learning_api.english_essay_calibration import (
    CALIBRATION_EVALUATOR_VERSION,
    CALIBRATION_POLICY_VERSION,
    CalibrationGateReport,
    CalibrationThresholds,
)
from learning_api.english_essay_calibration_repository import (
    PostgresEnglishEssayCalibrationRepository,
)


@pytest.mark.postgres
def test_calibration_gate_report_is_private_idempotent_and_immutable():
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to a migrated disposable database")

    report = CalibrationGateReport(
        policy_version=CALIBRATION_POLICY_VERSION,
        evaluator_version=CALIBRATION_EVALUATOR_VERSION,
        provider_name="postgres-calibration-provider",
        model_name="postgres-calibration-model",
        provider_policy_version="postgres-calibration-policy-v1",
        educator_reference="educator-ref-postgres-private",
        anchor_set_sha256="a" * 64,
        candidate_set_sha256="b" * 64,
        anchor_count=12,
        run_count=24,
        schema_valid_rate=1,
        evidence_fidelity_rate=1,
        band_within_one_rate=0.9,
        repeat_stability_passed=True,
        instructional_usefulness_rate=0.9,
        age_appropriate_tone_rate=1,
        case_recognition_rate=1,
        false_claim_count=0,
        safety_failure_count=0,
        maximum_run_cost_micros_sgd=1_000_000,
        p95_latency_ms=20_000,
        thresholds=CalibrationThresholds(),
        failure_reasons=[],
        passed=True,
    )
    repository = PostgresEnglishEssayCalibrationRepository(database_url)
    stored = repository.record(report)
    repeated = repository.record(report)
    assert repeated["gate_report_id"] == stored["gate_report_id"]
    assert repository.latest_passed(
        report.provider_name, report.model_name, report.provider_policy_version
    )["gate_report_id"] == stored["gate_report_id"]

    with psycopg.connect(database_url) as connection:
        with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
            with connection.transaction():
                connection.execute(
                    "update english_essay_calibration_gate_reports set passed=false where id=%s",
                    (stored["gate_report_id"],),
                )
        grants = connection.execute(
            """
            select grantee, privilege_type
              from information_schema.role_table_grants
             where table_schema='public'
               and table_name='english_essay_calibration_gate_reports'
               and grantee in ('anon', 'authenticated')
            """
        ).fetchall()
        assert grants == []
