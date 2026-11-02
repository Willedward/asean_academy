import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { EssayFeedbackReleaseEvidence } from "@/lib/api/admin-dashboard";

import { EnglishEssayReleasePanel } from "./english-essay-release-panel";

afterEach(cleanup);

const evidence: EssayFeedbackReleaseEvidence = {
  state: "ready_for_release",
  environment_enabled: false,
  live_provider_available: false,
  provider_name: "candidate-provider",
  model_name: "candidate-model",
  provider_policy_version: "english-essay-feedback-policy-v1",
  blockers: ["An academic administrator must explicitly release the provider."],
  calibration: {
    gate_report_id: "10000000-0000-4000-8000-000000000001",
    policy_version: "english-essay-calibration-policy-v1",
    evaluator_version: "english-essay-calibration-evaluator-v1",
    provider_name: "candidate-provider",
    model_name: "candidate-model",
    provider_policy_version: "english-essay-feedback-policy-v1",
    educator_reference: "educator-ref-private-001",
    anchor_set_sha256: "a".repeat(64),
    candidate_set_sha256: "b".repeat(64),
    anchor_count: 12,
    run_count: 24,
    schema_valid_rate: 1,
    evidence_fidelity_rate: 1,
    band_within_one_rate: 1,
    repeat_stability_passed: true,
    instructional_usefulness_rate: 1,
    age_appropriate_tone_rate: 1,
    case_recognition_rate: 1,
    false_claim_count: 0,
    safety_failure_count: 0,
    maximum_run_cost_micros_sgd: 400000,
    p95_latency_ms: 8000,
    thresholds: {
      minimum_anchors: 12,
      maximum_anchors: 16,
      runs_per_anchor: 2,
      minimum_schema_valid_rate: 1,
      minimum_evidence_fidelity_rate: 1,
      minimum_band_within_one_rate: 0.9,
      maximum_repeat_band_drift: 1,
      minimum_instructional_usefulness_rate: 0.9,
      minimum_age_appropriate_tone_rate: 1,
      minimum_case_recognition_rate: 1,
      maximum_false_claim_count: 0,
      maximum_safety_failure_count: 0,
      maximum_run_cost_micros_sgd: 1000000,
      maximum_p95_latency_ms: 20000,
    },
    failure_reasons: [],
    passed: true,
    contains_private_essay_text: false,
    live_provider_released: false,
    created_at: "2026-11-02T00:00:00Z",
  },
  privacy_review: {
    privacy_review_id: "10000000-0000-4000-8000-000000000002",
    calibration_gate_report_id: "10000000-0000-4000-8000-000000000001",
    reviewer_user_id: "10000000-0000-4000-8000-000000000003",
    request_id: "request-privacy-review",
    guardian_consent_process_verified: true,
    consent_policy_version: "english-essay-consent-v1",
    retention_policy_version: "english-essay-retention-v1",
    retention_days: 90,
    deletion_workflow_verified: true,
    raw_essay_logging_excluded: true,
    provider_agreement_reference: "provider-agreement-ref-private-001",
    regional_privacy_review_reference: "privacy-review-ref-private-001",
    provider_data_region: "Singapore",
    provider_retention_days: 0,
    subprocessors_reviewed: true,
    automated_safety_classification_verified: true,
    safeguarding_contact_reference: "safeguarding-ref-private-001",
    review_notes: "Private evidence is held outside the application.",
    passed: true,
    created_at: "2026-11-02T00:00:00Z",
  },
  release_decision: null,
};

describe("EnglishEssayReleasePanel", () => {
  it("shows privacy-safe evidence and requires the exact release phrase", async () => {
    const api = {
      evidence: vi.fn(async () => evidence),
      calibration: vi.fn(),
      privacy: vi.fn(),
      decision: vi.fn(async (body) => ({
        release_event_id: "10000000-0000-4000-8000-000000000004",
        actor_user_id: "10000000-0000-4000-8000-000000000003",
        request_id: "request-release",
        created_at: "2026-11-02T00:00:00Z",
        ...body,
      })),
      consent: vi.fn(),
    };
    render(<EnglishEssayReleasePanel api={api} />);

    expect(await screen.findByText("ready for release")).toBeInTheDocument();
    expect(screen.getByText("Environment switch").parentElement).toHaveTextContent("Disabled");
    fireEvent.click(screen.getByText("3. Explicit release or suspension decision"));
    const button = screen.getByRole("button", { name: "Record release" });
    expect(button).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/Type exactly/), {
      target: { value: "release" },
    });
    fireEvent.change(screen.getByLabelText("Release audit reason"), {
      target: { value: "The bounded evidence and privacy review have passed." },
    });
    expect(button).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/Type exactly/), {
      target: { value: "RELEASE LIVE ENGLISH ESSAY FEEDBACK" },
    });
    expect(button).toBeEnabled();
    fireEvent.click(button);

    await waitFor(() => expect(api.decision).toHaveBeenCalledWith({
      calibration_gate_report_id: evidence.calibration?.gate_report_id,
      privacy_review_id: evidence.privacy_review?.privacy_review_id,
      action: "released",
      confirmation: "RELEASE LIVE ENGLISH ESSAY FEEDBACK",
      reason: "The bounded evidence and privacy review have passed.",
    }));
  });

  it("explains that no provider call happens on this screen", async () => {
    const api = {
      evidence: vi.fn(async () => ({ ...evidence, state: "blocked_no_calibration", calibration: null, privacy_review: null, blockers: ["A calibration report is required."] } as EssayFeedbackReleaseEvidence)),
      calibration: vi.fn(), privacy: vi.fn(), decision: vi.fn(), consent: vi.fn(),
    };
    render(<EnglishEssayReleasePanel api={api} />);
    expect(await screen.findByText(/never sends an essay to a provider/i)).toBeInTheDocument();
    expect(screen.getByText("A calibration report is required.")).toBeInTheDocument();
  });
});
