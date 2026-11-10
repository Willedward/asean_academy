"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  adminRequest,
  type CalibrationEvidence,
  type CalibrationReportInput,
  type ConsentDecision,
  type ConsentDecisionInput,
  type EssayFeedbackReleaseEvidence,
  type PrivacyReview,
  type PrivacyReviewInput,
  type ReleaseDecision,
  type ReleaseDecisionInput,
} from "@/lib/api/admin-dashboard";
import { ApiRequestError } from "@/lib/api/errors";

const RELEASE_CONFIRMATION = "RELEASE LIVE ENGLISH ESSAY FEEDBACK";
const SUSPEND_CONFIRMATION = "SUSPEND LIVE ENGLISH ESSAY FEEDBACK";

type EssayReleaseApi = {
  evidence: () => Promise<EssayFeedbackReleaseEvidence>;
  calibration: (body: CalibrationReportInput) => Promise<CalibrationEvidence>;
  privacy: (body: PrivacyReviewInput) => Promise<PrivacyReview>;
  decision: (body: ReleaseDecisionInput) => Promise<ReleaseDecision>;
  consent: (
    learnerId: string,
    body: ConsentDecisionInput,
  ) => Promise<ConsentDecision>;
};

const defaultApi: EssayReleaseApi = {
  evidence: () => adminRequest("english-essay-feedback/release-evidence"),
  calibration: (body) =>
    adminRequest("english-essay-feedback/calibration-reports", body),
  privacy: (body) =>
    adminRequest("english-essay-feedback/privacy-reviews", body),
  decision: (body) =>
    adminRequest("english-essay-feedback/release-decisions", body),
  consent: (learnerId, body) =>
    adminRequest(
      `students/${encodeURIComponent(learnerId)}/english-essay-consent-events`,
      body,
    ),
};

function errorMessage(error: unknown) {
  if (error instanceof ApiRequestError)
    return `${error.message}${error.requestId ? ` Request ID: ${error.requestId}` : ""}`;
  return error instanceof Error ? error.message : "The operation failed.";
}

function label(value: string) {
  return value.replaceAll("_", " ");
}

function Evidence({ value }: { value: EssayFeedbackReleaseEvidence }) {
  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="m-0 text-xl font-bold">Current release state</h2>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-bold capitalize">
          {label(value.state)}
        </span>
      </div>
      <p className="break-all text-sm text-slate-600">
        {value.provider_name} · {value.model_name} · {value.provider_policy_version}
      </p>
      <dl className="grid gap-3 sm:grid-cols-3">
        <div><dt>Environment switch</dt><dd className="font-bold">{value.environment_enabled ? "Enabled" : "Disabled"}</dd></div>
        <div><dt>Calibration</dt><dd className="font-bold">{value.calibration?.passed ? "Passed" : value.calibration ? "Failed" : "Missing"}</dd></div>
        <div><dt>Privacy review</dt><dd className="font-bold">{value.privacy_review?.passed ? "Passed" : value.privacy_review ? "Failed" : "Missing"}</dd></div>
      </dl>
      {value.blockers.length ? (
        <ul className="list-disc pl-5 text-sm text-amber-900">
          {value.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)}
        </ul>
      ) : <p className="font-bold text-emerald-800">Every release layer is active.</p>}
      {value.calibration ? (
        <details>
          <summary className="cursor-pointer font-bold">Privacy-safe calibration aggregate</summary>
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
            <div><dt>Educator reference</dt><dd>{value.calibration.educator_reference}</dd></div>
            <div><dt>Anchors / runs</dt><dd>{value.calibration.anchor_count} / {value.calibration.run_count}</dd></div>
            <div><dt>Safety failures</dt><dd>{value.calibration.safety_failure_count}</dd></div>
            <div><dt>Evidence fidelity</dt><dd>{value.calibration.evidence_fidelity_rate}</dd></div>
            <div><dt>Instructional usefulness</dt><dd>{value.calibration.instructional_usefulness_rate}</dd></div>
            <div><dt>P95 latency</dt><dd>{value.calibration.p95_latency_ms} ms</dd></div>
          </dl>
        </details>
      ) : null}
    </section>
  );
}

const fieldClass = "mt-1 block w-full rounded-lg border bg-white p-3";

export function EnglishEssayReleasePanel({ api = defaultApi }: { api?: EssayReleaseApi }) {
  const [evidence, setEvidence] = useState<EssayFeedbackReleaseEvidence | null>(null);
  const [calibrationJson, setCalibrationJson] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try { setEvidence(await api.evidence()); }
    catch (caught) { setError(errorMessage(caught)); }
  }, [api]);

  useEffect(() => {
    let active = true;
    void api.evidence().then(
      (value) => {
        if (active) setEvidence(value);
      },
      (caught: unknown) => {
        if (active) setError(errorMessage(caught));
      },
    );
    return () => {
      active = false;
    };
  }, [api]);

  async function run(action: () => Promise<unknown>, message: string) {
    setBusy(true); setError(null); setNotice(null);
    try { await action(); setNotice(message); await load(); }
    catch (caught) { setError(errorMessage(caught)); }
    finally { setBusy(false); }
  }

  if (!evidence)
    return <div className="status-card" role={error ? "alert" : "status"}>{error ?? "Loading release evidence…"}</div>;

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-teal-200 bg-teal-50 p-5 text-sm leading-6">
        This control never sends an essay to a provider. It stores only aggregate calibration results,
        opaque references and append-only decisions. A recorded release still cannot activate traffic while
        the deployment switch is off or learner consent is missing.
      </div>
      <Evidence value={evidence} />
      {error ? <p role="alert" className="text-red-700">{error}</p> : null}
      {notice ? <p role="status" className="text-emerald-800">{notice}</p> : null}

      <details className="rounded-2xl border border-slate-200 bg-white p-5">
        <summary className="cursor-pointer text-lg font-bold">1. Import calibration aggregate</summary>
        <p className="text-sm text-slate-600">Paste only the JSON report produced by the offline evaluator. Essay text and provider responses are rejected by the API contract.</p>
        <label className="block font-bold" htmlFor="calibration-json">Calibration report JSON</label>
        <textarea id="calibration-json" className={`${fieldClass} min-h-48 font-mono text-xs`} value={calibrationJson} onChange={(event) => setCalibrationJson(event.target.value)} />
        <Button className="mt-3" disabled={busy || !calibrationJson.trim()} onClick={() => void run(async () => {
          let parsed: CalibrationReportInput;
          try { parsed = JSON.parse(calibrationJson) as CalibrationReportInput; }
          catch { throw new Error("Calibration report must be valid JSON."); }
          await api.calibration(parsed);
        }, "Calibration report recorded.")}>Record calibration report</Button>
      </details>

      <PrivacyForm api={api} evidence={evidence} busy={busy} run={run} />
      <DecisionForm api={api} evidence={evidence} busy={busy} run={run} />
      <ConsentForm api={api} busy={busy} run={run} />
    </div>
  );
}

function PrivacyForm({ api, evidence, busy, run }: { api: EssayReleaseApi; evidence: EssayFeedbackReleaseEvidence; busy: boolean; run: (action: () => Promise<unknown>, message: string) => Promise<void> }) {
  const [checks, setChecks] = useState({ guardian_consent_process_verified: false, deletion_workflow_verified: false, raw_essay_logging_excluded: false, subprocessors_reviewed: false, automated_safety_classification_verified: false });
  const [notes, setNotes] = useState("");
  const gateId = evidence.calibration?.gate_report_id ?? "";
  const allChecked = Object.values(checks).every(Boolean);
  return (
    <details className="rounded-2xl border border-slate-200 bg-white p-5">
      <summary className="cursor-pointer text-lg font-bold">2. Record privacy and safeguarding review</summary>
      <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={(event) => {
        event.preventDefault(); const form = new FormData(event.currentTarget);
        const body: PrivacyReviewInput = {
          calibration_gate_report_id: gateId,
          ...checks,
          consent_policy_version: String(form.get("consent_policy_version")),
          retention_policy_version: String(form.get("retention_policy_version")),
          retention_days: Number(form.get("retention_days")),
          provider_agreement_reference: String(form.get("provider_agreement_reference")),
          regional_privacy_review_reference: String(form.get("regional_privacy_review_reference")),
          provider_data_region: String(form.get("provider_data_region")),
          provider_retention_days: Number(form.get("provider_retention_days")),
          safeguarding_contact_reference: String(form.get("safeguarding_contact_reference")),
          review_notes: notes,
        };
        void run(() => api.privacy(body), "Privacy review recorded.");
      }}>
        <input type="hidden" name="gate_id" value={gateId} />
        {Object.keys(checks).map((key) => <label className="flex items-start gap-2 text-sm leading-5" key={key}><input type="checkbox" className="size-5 shrink-0" checked={checks[key as keyof typeof checks]} onChange={(event) => setChecks({ ...checks, [key]: event.target.checked })} />{label(key)}</label>)}
        <Text name="consent_policy_version" label="Consent policy version" value="english-essay-consent-v1" />
        <Text name="retention_policy_version" label="Retention policy version" value="english-essay-retention-v1" />
        <Text name="retention_days" label="Application retention days" value="90" type="number" />
        <Text name="provider_retention_days" label="Provider retention days" value="0" type="number" />
        <Text name="provider_agreement_reference" label="Provider agreement reference" value="" placeholder="provider-agreement-ref-…" />
        <Text name="regional_privacy_review_reference" label="Regional privacy review reference" value="" placeholder="privacy-review-ref-…" />
        <Text name="provider_data_region" label="Provider data region" value="" />
        <Text name="safeguarding_contact_reference" label="Safeguarding contact reference" value="" placeholder="safeguarding-ref-…" />
        <label className="sm:col-span-2">Review notes<textarea required minLength={10} maxLength={2000} className={`${fieldClass} min-h-24`} value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
        <Button className="sm:col-span-2" type="submit" disabled={busy || !gateId || !allChecked || notes.trim().length < 10}>Record passing privacy review</Button>
      </form>
    </details>
  );
}

function Text({ name, label: title, value, type = "text", placeholder }: { name: string; label: string; value: string; type?: string; placeholder?: string }) {
  return <label>{title}<input required className={fieldClass} name={name} type={type} defaultValue={value} placeholder={placeholder} /></label>;
}

function DecisionForm({ api, evidence, busy, run }: { api: EssayReleaseApi; evidence: EssayFeedbackReleaseEvidence; busy: boolean; run: (action: () => Promise<unknown>, message: string) => Promise<void> }) {
  const [action, setAction] = useState<"released" | "suspended">("released");
  const [confirmation, setConfirmation] = useState("");
  const [reason, setReason] = useState("");
  const expected = action === "released" ? RELEASE_CONFIRMATION : SUSPEND_CONFIRMATION;
  const calibrationId = evidence.calibration?.gate_report_id;
  const privacyId = evidence.privacy_review?.privacy_review_id;
  return <details className="rounded-2xl border border-red-200 bg-red-50/30 p-5">
    <summary className="cursor-pointer text-lg font-bold">3. Explicit release or suspension decision</summary>
    <div className="mt-4 space-y-4">
      <label>Decision<select className={fieldClass} value={action} onChange={(event) => { setAction(event.target.value as "released" | "suspended"); setConfirmation(""); }}><option value="released">Release</option><option value="suspended">Suspend</option></select></label>
      <label>Type exactly: <strong>{expected}</strong><input className={fieldClass} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} /></label>
      <label>Release audit reason<textarea className={`${fieldClass} min-h-24`} minLength={10} maxLength={1000} value={reason} onChange={(event) => setReason(event.target.value)} /></label>
      <Button disabled={busy || !calibrationId || !privacyId || confirmation !== expected || reason.trim().length < 10} onClick={() => void run(() => api.decision({ calibration_gate_report_id: calibrationId!, privacy_review_id: privacyId!, action, confirmation, reason: reason.trim() }), `${action === "released" ? "Release" : "Suspension"} decision recorded.`)}>Record {action === "released" ? "release" : "suspension"}</Button>
    </div>
  </details>;
}

function ConsentForm({ api, busy, run }: { api: EssayReleaseApi; busy: boolean; run: (action: () => Promise<unknown>, message: string) => Promise<void> }) {
  const [action, setAction] = useState<"granted" | "revoked">("granted");
  return <details className="rounded-2xl border border-slate-200 bg-white p-5">
    <summary className="cursor-pointer text-lg font-bold">Learner guardian-consent evidence</summary>
    <p className="text-sm text-slate-600">Store only a SHA-256 reference produced by the private consent workflow—never a guardian name, email or document.</p>
    <form className="grid gap-4 sm:grid-cols-2" onSubmit={(event) => {
      event.preventDefault(); const form = new FormData(event.currentTarget);
      const learnerId = String(form.get("learner_id"));
      const expires = String(form.get("expires_at"));
      const guardian = String(form.get("guardian_reference_sha256"));
      const body: ConsentDecisionInput = { action, consent_policy_version: "english-essay-consent-v1", reason: String(form.get("reason")), guardian_reference_sha256: action === "granted" ? guardian : null, expires_at: action === "granted" ? new Date(expires).toISOString() : null };
      void run(() => api.consent(learnerId, body), "Consent decision recorded.");
    }}>
      <Text name="learner_id" label="Learner ID" value="" />
      <label>Decision<select className={fieldClass} value={action} onChange={(event) => setAction(event.target.value as "granted" | "revoked")}><option value="granted">Grant</option><option value="revoked">Revoke</option></select></label>
      {action === "granted" ? <><Text name="guardian_reference_sha256" label="Opaque guardian reference (SHA-256)" value="" /><Text name="expires_at" label="Consent expiry" value="" type="datetime-local" /></> : null}
      <label className="sm:col-span-2">Consent audit reason<textarea required minLength={10} maxLength={1000} name="reason" className={`${fieldClass} min-h-20`} /></label>
      <Button className="sm:col-span-2" type="submit" disabled={busy}>Record consent {action}</Button>
    </form>
  </details>;
}
