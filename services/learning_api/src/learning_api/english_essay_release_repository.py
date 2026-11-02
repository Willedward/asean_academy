"""Append-only persistence and evaluation for live essay-feedback release evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .english_essay_calibration import CalibrationGateReport
from .english_essay_release import ConsentDecisionRequest, PrivacyReviewRequest


class EnglishEssayReleaseError(ValueError):
    def __init__(self, code: str, message: str, status: int = 409):
        super().__init__(message)
        self.code = code
        self.status = status


def _public_row(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "id"}


def _state(
    calibration: dict | None,
    privacy_review: dict | None,
    release_decision: dict | None,
    *,
    environment_enabled: bool,
) -> tuple[str, list[str]]:
    if calibration is None:
        return "blocked_no_calibration", ["A calibration report is required."]
    if not calibration["passed"]:
        return "blocked_calibration_failed", ["The latest calibration report failed."]
    if privacy_review is None:
        return "blocked_privacy_review_missing", ["A privacy and safeguarding review is required."]
    if not privacy_review["passed"]:
        return "blocked_privacy_review_failed", [
            "The latest privacy and safeguarding review failed."
        ]
    if release_decision is None:
        return "ready_for_release", [
            "An academic administrator must explicitly release the provider."
        ]
    if release_decision["action"] == "suspended":
        return "suspended", ["The latest administrator decision suspended live feedback."]
    if not environment_enabled:
        return "disabled_by_environment", ["The deployment environment switch is disabled."]
    return "released", []


def _evidence(
    *,
    provider_name: str,
    model_name: str,
    provider_policy_version: str,
    environment_enabled: bool,
    calibration: dict | None,
    privacy_review: dict | None,
    release_decision: dict | None,
) -> dict:
    state, blockers = _state(
        calibration,
        privacy_review,
        release_decision,
        environment_enabled=environment_enabled,
    )
    return {
        "state": state,
        "environment_enabled": environment_enabled,
        "live_provider_available": state == "released",
        "provider_name": provider_name,
        "model_name": model_name,
        "provider_policy_version": provider_policy_version,
        "blockers": blockers,
        "calibration": calibration,
        "privacy_review": privacy_review,
        "release_decision": release_decision,
    }


class InMemoryEnglishEssayReleaseRepository:
    def __init__(self):
        self.calibrations: list[dict] = []
        self.privacy_reviews: list[dict] = []
        self.release_decisions: list[dict] = []
        self.consent_events: list[dict] = []
        self._lock = Lock()

    def record_calibration(
        self, report: CalibrationGateReport, actor_user_id: str, request_id: str
    ) -> dict:
        del actor_user_id, request_id
        payload = report.model_dump(mode="json")
        with self._lock:
            existing = next(
                (
                    row
                    for row in self.calibrations
                    if row["provider_name"] == report.provider_name
                    and row["model_name"] == report.model_name
                    and row["provider_policy_version"] == report.provider_policy_version
                    and row["candidate_set_sha256"] == report.candidate_set_sha256
                ),
                None,
            )
            if existing:
                return dict(existing)
            row = {"gate_report_id": str(uuid4()), **payload, "created_at": datetime.now(UTC)}
            self.calibrations.append(row)
            return _public_row(dict(row))

    def record_privacy_review(
        self, body: PrivacyReviewRequest, actor_user_id: str, request_id: str
    ) -> dict:
        with self._lock:
            existing = next(
                (row for row in self.privacy_reviews if row["request_id"] == request_id), None
            )
            if existing:
                return dict(existing)
            if not any(
                row["gate_report_id"] == str(body.calibration_gate_report_id)
                for row in self.calibrations
            ):
                raise EnglishEssayReleaseError(
                    "calibration_report_not_found", "The calibration report was not found.", 404
                )
            payload = body.model_dump(mode="json")
            row = {
                "privacy_review_id": str(uuid4()),
                **payload,
                "reviewer_user_id": actor_user_id,
                "request_id": request_id,
                "passed": all(
                    (
                        body.guardian_consent_process_verified,
                        body.deletion_workflow_verified,
                        body.raw_essay_logging_excluded,
                        body.subprocessors_reviewed,
                        body.automated_safety_classification_verified,
                    )
                ),
                "created_at": datetime.now(UTC),
            }
            self.privacy_reviews.append(row)
            return _public_row(dict(row))

    def record_release_decision(
        self,
        *,
        calibration_gate_report_id: UUID,
        privacy_review_id: UUID,
        action: str,
        reason: str,
        actor_user_id: str,
        request_id: str,
    ) -> dict:
        with self._lock:
            existing = next(
                (row for row in self.release_decisions if row["request_id"] == request_id), None
            )
            if existing:
                return dict(existing)
            calibration = next(
                (
                    row
                    for row in self.calibrations
                    if row["gate_report_id"] == str(calibration_gate_report_id)
                ),
                None,
            )
            review = next(
                (
                    row
                    for row in self.privacy_reviews
                    if row["privacy_review_id"] == str(privacy_review_id)
                ),
                None,
            )
            if (
                calibration is None
                or review is None
                or review["calibration_gate_report_id"] != str(calibration_gate_report_id)
            ):
                raise EnglishEssayReleaseError(
                    "release_evidence_mismatch", "The release evidence does not match."
                )
            if action == "released" and (not calibration["passed"] or not review["passed"]):
                raise EnglishEssayReleaseError(
                    "release_gate_failed",
                    "Live feedback cannot be released while evidence is failing.",
                )
            row = {
                "release_event_id": str(uuid4()),
                "calibration_gate_report_id": str(calibration_gate_report_id),
                "privacy_review_id": str(privacy_review_id),
                "actor_user_id": actor_user_id,
                "action": action,
                "reason": reason,
                "request_id": request_id,
                "created_at": datetime.now(UTC),
            }
            self.release_decisions.append(row)
            return _public_row(dict(row))

    def record_consent(
        self, student_id: UUID, body: ConsentDecisionRequest, actor_user_id: str, request_id: str
    ) -> dict:
        with self._lock:
            existing = next(
                (row for row in self.consent_events if row["request_id"] == request_id), None
            )
            if existing:
                return dict(existing)
        payload = body.model_dump(mode="python")
        row = {
            "consent_event_id": str(uuid4()),
            "student_id": str(student_id),
            **payload,
            "actor_user_id": actor_user_id,
            "request_id": request_id,
            "created_at": datetime.now(UTC),
        }
        with self._lock:
            self.consent_events.append(row)
        return dict(row)

    def evidence(
        self,
        provider_name: str,
        model_name: str,
        provider_policy_version: str,
        *,
        environment_enabled: bool,
    ) -> dict:
        with self._lock:
            calibration = next(
                (
                    row
                    for row in reversed(self.calibrations)
                    if row["provider_name"] == provider_name
                    and row["model_name"] == model_name
                    and row["provider_policy_version"] == provider_policy_version
                ),
                None,
            )
            review = next(
                (
                    row
                    for row in reversed(self.privacy_reviews)
                    if calibration
                    and row["calibration_gate_report_id"] == calibration["gate_report_id"]
                ),
                None,
            )
            decision = next(
                (
                    row
                    for row in reversed(self.release_decisions)
                    if review
                    and row["calibration_gate_report_id"] == calibration["gate_report_id"]
                    and row["privacy_review_id"] == review["privacy_review_id"]
                ),
                None,
            )
            return _evidence(
                provider_name=provider_name,
                model_name=model_name,
                provider_policy_version=provider_policy_version,
                environment_enabled=environment_enabled,
                calibration=dict(calibration) if calibration else None,
                privacy_review=dict(review) if review else None,
                release_decision=dict(decision) if decision else None,
            )

    def has_active_consent(
        self, student_id: str, consent_policy_version: str, *, at: datetime | None = None
    ) -> bool:
        now = at or datetime.now(UTC)
        with self._lock:
            latest = next(
                (
                    row
                    for row in reversed(self.consent_events)
                    if row["student_id"] == student_id
                    and row["consent_policy_version"] == consent_policy_version
                ),
                None,
            )
            return bool(
                latest
                and latest["action"] == "granted"
                and latest["expires_at"]
                and latest["expires_at"] > now
            )


class PostgresEnglishEssayReleaseRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def record_calibration(
        self, report: CalibrationGateReport, actor_user_id: str, request_id: str
    ) -> dict:
        payload = report.model_dump(mode="json")
        with self._connect() as connection, connection.transaction():
            row = connection.execute(
                """
                insert into english_essay_calibration_gate_reports(
                    policy_version,evaluator_version,provider_name,model_name,provider_policy_version,
                    educator_reference,anchor_set_sha256,candidate_set_sha256,anchor_count,run_count,
                    schema_valid_rate,evidence_fidelity_rate,band_within_one_rate,repeat_stability_passed,
                    instructional_usefulness_rate,age_appropriate_tone_rate,case_recognition_rate,
                    false_claim_count,safety_failure_count,maximum_run_cost_micros_sgd,p95_latency_ms,
                    thresholds,failure_reasons,passed,contains_private_essay_text,live_provider_released
                ) values (
                    %(policy_version)s,%(evaluator_version)s,%(provider_name)s,%(model_name)s,%(provider_policy_version)s,
                    %(educator_reference)s,%(anchor_set_sha256)s,%(candidate_set_sha256)s,%(anchor_count)s,%(run_count)s,
                    %(schema_valid_rate)s,%(evidence_fidelity_rate)s,%(band_within_one_rate)s,%(repeat_stability_passed)s,
                    %(instructional_usefulness_rate)s,%(age_appropriate_tone_rate)s,%(case_recognition_rate)s,
                    %(false_claim_count)s,%(safety_failure_count)s,%(maximum_run_cost_micros_sgd)s,%(p95_latency_ms)s,
                    %(thresholds)s,%(failure_reasons)s,%(passed)s,%(contains_private_essay_text)s,%(live_provider_released)s
                ) on conflict(provider_name,model_name,provider_policy_version,candidate_set_sha256) do nothing
                returning id::text as gate_report_id,*
            """,
                {
                    **payload,
                    "thresholds": Jsonb(payload["thresholds"]),
                    "failure_reasons": Jsonb(payload["failure_reasons"]),
                },
            ).fetchone()
            inserted = row is not None
            if row is None:
                row = connection.execute(
                    "select id::text as gate_report_id,* from english_essay_calibration_gate_reports where provider_name=%s and model_name=%s and provider_policy_version=%s and candidate_set_sha256=%s",
                    (
                        report.provider_name,
                        report.model_name,
                        report.provider_policy_version,
                        report.candidate_set_sha256,
                    ),
                ).fetchone()
            if inserted:
                connection.execute(
                    "insert into beta_audit_events(event_type,actor_user_id,request_id,metadata) values ('english_essay_calibration_report_recorded',%s,%s,%s)",
                    (
                        actor_user_id,
                        request_id,
                        Jsonb(
                            {
                                "gate_report_id": row["gate_report_id"],
                                "provider_name": report.provider_name,
                                "model_name": report.model_name,
                                "passed": report.passed,
                            }
                        ),
                    ),
                )
            return _public_row(dict(row))

    def record_privacy_review(
        self, body: PrivacyReviewRequest, actor_user_id: str, request_id: str
    ) -> dict:
        payload = body.model_dump(mode="json")
        with self._connect() as connection, connection.transaction():
            existing = connection.execute(
                "select id::text as privacy_review_id,* from english_essay_feedback_privacy_reviews where request_id=%s",
                (request_id,),
            ).fetchone()
            if existing:
                return _public_row(dict(existing))
            row = connection.execute(
                """
                insert into english_essay_feedback_privacy_reviews(
                    calibration_gate_report_id,reviewer_user_id,guardian_consent_process_verified,
                    consent_policy_version,retention_policy_version,retention_days,deletion_workflow_verified,
                    raw_essay_logging_excluded,provider_agreement_reference,regional_privacy_review_reference,
                    provider_data_region,provider_retention_days,subprocessors_reviewed,
                    automated_safety_classification_verified,safeguarding_contact_reference,review_notes,request_id
                ) values (
                    %(calibration_gate_report_id)s,%(reviewer_user_id)s,%(guardian_consent_process_verified)s,
                    %(consent_policy_version)s,%(retention_policy_version)s,%(retention_days)s,%(deletion_workflow_verified)s,
                    %(raw_essay_logging_excluded)s,%(provider_agreement_reference)s,%(regional_privacy_review_reference)s,
                    %(provider_data_region)s,%(provider_retention_days)s,%(subprocessors_reviewed)s,
                    %(automated_safety_classification_verified)s,%(safeguarding_contact_reference)s,%(review_notes)s,%(request_id)s
                ) returning id::text as privacy_review_id,*
            """,
                {**payload, "reviewer_user_id": actor_user_id, "request_id": request_id},
            ).fetchone()
            connection.execute(
                "insert into beta_audit_events(event_type,actor_user_id,request_id,metadata) values ('english_essay_privacy_review_recorded',%s,%s,%s)",
                (
                    actor_user_id,
                    request_id,
                    Jsonb(
                        {
                            "privacy_review_id": row["privacy_review_id"],
                            "calibration_gate_report_id": str(body.calibration_gate_report_id),
                            "passed": row["passed"],
                        }
                    ),
                ),
            )
            return _public_row(dict(row))

    def record_release_decision(
        self,
        *,
        calibration_gate_report_id: UUID,
        privacy_review_id: UUID,
        action: str,
        reason: str,
        actor_user_id: str,
        request_id: str,
    ) -> dict:
        event_type = (
            "english_essay_feedback_released"
            if action == "released"
            else "english_essay_feedback_suspended"
        )
        try:
            with self._connect() as connection, connection.transaction():
                existing = connection.execute(
                    "select id::text as release_event_id,* from english_essay_feedback_release_events where request_id=%s",
                    (request_id,),
                ).fetchone()
                if existing:
                    return _public_row(dict(existing))
                row = connection.execute(
                    "insert into english_essay_feedback_release_events(calibration_gate_report_id,privacy_review_id,actor_user_id,action,reason,request_id) values (%s,%s,%s,%s,%s,%s) returning id::text as release_event_id,*",
                    (
                        calibration_gate_report_id,
                        privacy_review_id,
                        actor_user_id,
                        action,
                        reason,
                        request_id,
                    ),
                ).fetchone()
                connection.execute(
                    "insert into beta_audit_events(event_type,actor_user_id,request_id,metadata) values (%s,%s,%s,%s)",
                    (
                        event_type,
                        actor_user_id,
                        request_id,
                        Jsonb(
                            {
                                "release_event_id": row["release_event_id"],
                                "calibration_gate_report_id": str(calibration_gate_report_id),
                                "privacy_review_id": str(privacy_review_id),
                            }
                        ),
                    ),
                )
                return _public_row(dict(row))
        except psycopg.errors.RaiseException as exc:
            raise EnglishEssayReleaseError(
                "release_gate_failed", "The release evidence is missing, mismatched, or failing."
            ) from exc

    def record_consent(
        self, student_id: UUID, body: ConsentDecisionRequest, actor_user_id: str, request_id: str
    ) -> dict:
        payload = body.model_dump(mode="python")
        with self._connect() as connection, connection.transaction():
            existing = connection.execute(
                "select id::text as consent_event_id,* from english_essay_processing_consent_events where request_id=%s",
                (request_id,),
            ).fetchone()
            if existing:
                return _public_row(dict(existing))
            row = connection.execute(
                "insert into english_essay_processing_consent_events(student_id,actor_user_id,action,consent_policy_version,guardian_reference_sha256,expires_at,reason,request_id) values (%(student_id)s,%(actor_user_id)s,%(action)s,%(consent_policy_version)s,%(guardian_reference_sha256)s,%(expires_at)s,%(reason)s,%(request_id)s) returning id::text as consent_event_id,*",
                {
                    **payload,
                    "student_id": student_id,
                    "actor_user_id": actor_user_id,
                    "request_id": request_id,
                },
            ).fetchone()
            connection.execute(
                "insert into beta_audit_events(event_type,actor_user_id,target_user_id,request_id,metadata) values ('english_essay_consent_recorded',%s,%s,%s,%s)",
                (
                    actor_user_id,
                    student_id,
                    request_id,
                    Jsonb(
                        {
                            "consent_event_id": row["consent_event_id"],
                            "action": body.action,
                            "consent_policy_version": body.consent_policy_version,
                        }
                    ),
                ),
            )
            return _public_row(dict(row))

    def evidence(
        self,
        provider_name: str,
        model_name: str,
        provider_policy_version: str,
        *,
        environment_enabled: bool,
    ) -> dict:
        with self._connect() as connection:
            calibration = connection.execute(
                "select id::text as gate_report_id,* from english_essay_calibration_gate_reports where provider_name=%s and model_name=%s and provider_policy_version=%s order by created_at desc,id desc limit 1",
                (provider_name, model_name, provider_policy_version),
            ).fetchone()
            review = (
                connection.execute(
                    "select id::text as privacy_review_id,* from english_essay_feedback_privacy_reviews where calibration_gate_report_id=%s order by created_at desc,id desc limit 1",
                    (calibration["id"],),
                ).fetchone()
                if calibration
                else None
            )
            decision = (
                connection.execute(
                    "select id::text as release_event_id,* from english_essay_feedback_release_events where calibration_gate_report_id=%s and privacy_review_id=%s order by created_at desc,id desc limit 1",
                    (calibration["id"], review["id"]),
                ).fetchone()
                if review
                else None
            )
        return _evidence(
            provider_name=provider_name,
            model_name=model_name,
            provider_policy_version=provider_policy_version,
            environment_enabled=environment_enabled,
            calibration=_public_row(dict(calibration)) if calibration else None,
            privacy_review=_public_row(dict(review)) if review else None,
            release_decision=_public_row(dict(decision)) if decision else None,
        )

    def has_active_consent(
        self, student_id: str, consent_policy_version: str, *, at: datetime | None = None
    ) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "select action,expires_at from english_essay_processing_consent_events where student_id=%s and consent_policy_version=%s order by created_at desc,id desc limit 1",
                (student_id, consent_policy_version),
            ).fetchone()
        now = at or datetime.now(UTC)
        return bool(
            row and row["action"] == "granted" and row["expires_at"] and row["expires_at"] > now
        )
