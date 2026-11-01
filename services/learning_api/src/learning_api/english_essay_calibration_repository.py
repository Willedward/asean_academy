"""Persistence for privacy-safe English essay calibration gate reports."""

from __future__ import annotations

from threading import Lock
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .english_essay_calibration import CalibrationGateReport


class InMemoryEnglishEssayCalibrationRepository:
    def __init__(self):
        self.reports: list[dict] = []
        self._lock = Lock()

    def record(self, report: CalibrationGateReport) -> dict:
        payload = report.model_dump(mode="json")
        with self._lock:
            existing = next(
                (
                    item
                    for item in self.reports
                    if item["provider_name"] == report.provider_name
                    and item["model_name"] == report.model_name
                    and item["provider_policy_version"]
                    == report.provider_policy_version
                    and item["candidate_set_sha256"] == report.candidate_set_sha256
                ),
                None,
            )
            if existing:
                return dict(existing)
            stored = {"gate_report_id": str(uuid4()), **payload}
            self.reports.append(stored)
            return dict(stored)

    def latest_passed(
        self, provider_name: str, model_name: str, provider_policy_version: str
    ) -> dict | None:
        with self._lock:
            row = next(
                (
                    item
                    for item in reversed(self.reports)
                    if item["provider_name"] == provider_name
                    and item["model_name"] == model_name
                    and item["provider_policy_version"] == provider_policy_version
                    and item["passed"]
                ),
                None,
            )
            return dict(row) if row else None


class PostgresEnglishEssayCalibrationRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def record(self, report: CalibrationGateReport) -> dict:
        payload = report.model_dump(mode="json")
        with self._connect() as connection, connection.transaction():
            row = connection.execute(
                """
                insert into english_essay_calibration_gate_reports(
                    policy_version, evaluator_version, provider_name, model_name,
                    provider_policy_version, educator_reference, anchor_set_sha256,
                    candidate_set_sha256, anchor_count, run_count, schema_valid_rate,
                    evidence_fidelity_rate, band_within_one_rate,
                    repeat_stability_passed, instructional_usefulness_rate,
                    age_appropriate_tone_rate, case_recognition_rate, false_claim_count,
                    safety_failure_count, maximum_run_cost_micros_sgd, p95_latency_ms,
                    thresholds, failure_reasons, passed,
                    contains_private_essay_text, live_provider_released
                ) values (
                    %(policy_version)s, %(evaluator_version)s, %(provider_name)s,
                    %(model_name)s, %(provider_policy_version)s, %(educator_reference)s,
                    %(anchor_set_sha256)s, %(candidate_set_sha256)s, %(anchor_count)s,
                    %(run_count)s, %(schema_valid_rate)s, %(evidence_fidelity_rate)s,
                    %(band_within_one_rate)s, %(repeat_stability_passed)s,
                    %(instructional_usefulness_rate)s, %(age_appropriate_tone_rate)s,
                    %(case_recognition_rate)s, %(false_claim_count)s,
                    %(safety_failure_count)s, %(maximum_run_cost_micros_sgd)s,
                    %(p95_latency_ms)s, %(thresholds)s, %(failure_reasons)s, %(passed)s,
                    %(contains_private_essay_text)s, %(live_provider_released)s
                )
                on conflict (
                    provider_name, model_name, provider_policy_version, candidate_set_sha256
                ) do nothing
                returning id::text as gate_report_id, *
                """,
                {
                    **payload,
                    "thresholds": Jsonb(payload["thresholds"]),
                    "failure_reasons": Jsonb(payload["failure_reasons"]),
                },
            ).fetchone()
            if row is None:
                row = connection.execute(
                    """
                    select id::text as gate_report_id, *
                      from english_essay_calibration_gate_reports
                     where provider_name=%s and model_name=%s
                       and provider_policy_version=%s and candidate_set_sha256=%s
                    """,
                    (
                        report.provider_name,
                        report.model_name,
                        report.provider_policy_version,
                        report.candidate_set_sha256,
                    ),
                ).fetchone()
            return dict(row)

    def latest_passed(
        self, provider_name: str, model_name: str, provider_policy_version: str
    ) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                select id::text as gate_report_id, *
                  from english_essay_calibration_gate_reports
                 where provider_name=%s and model_name=%s
                   and provider_policy_version=%s and passed
                 order by created_at desc, id desc
                 limit 1
                """,
                (provider_name, model_name, provider_policy_version),
            ).fetchone()
            return dict(row) if row else None
