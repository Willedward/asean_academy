"use client";

import { AlertTriangle, CheckCircle2, ShieldAlert, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  executeStudentDeletion,
  previewStudentDeletion,
  type AccountDeletionPreview,
  type AccountDeletionResult,
  type ExecuteAccountDeletionInput,
} from "@/lib/api/admin";
import { ApiRequestError } from "@/lib/api/errors";

type DeletionApi = {
  preview: typeof previewStudentDeletion;
  execute: typeof executeStudentDeletion;
};

const defaultApi: DeletionApi = {
  preview: previewStudentDeletion,
  execute: executeStudentDeletion,
};

function errorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    return (
      error.message + (error.requestId ? " Request ID: " + error.requestId : "")
    );
  }
  return error instanceof Error
    ? error.message
    : "The deletion operation could not be completed.";
}

function label(value: string): string {
  return value.replaceAll("_", " ");
}

export function AdminAccountDeletion({
  learnerId,
  studentEmail,
  api = defaultApi,
}: {
  learnerId: string;
  studentEmail: string;
  api?: DeletionApi;
}) {
  const [preview, setPreview] = useState<AccountDeletionPreview | null>(null);
  const [result, setResult] = useState<AccountDeletionResult | null>(null);
  const [confirmation, setConfirmation] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadPreview() {
    setBusy(true);
    setError(null);
    try {
      const value = await api.preview(learnerId);
      setPreview(value);
      setConfirmation("");
      setReason("");
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function execute() {
    if (!preview) return;
    const body: ExecuteAccountDeletionInput = {
      preview_token: preview.preview_token,
      confirmation_email: confirmation.trim(),
      reason: reason.trim(),
    };
    setBusy(true);
    setError(null);
    try {
      setResult(await api.execute(learnerId, body));
      setPreview(null);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    return (
      <section
        aria-labelledby="deletion-complete-title"
        className="rounded-2xl border border-ns-line bg-ns-raised p-5 shadow-ns-sm"
      >
        <div className="flex items-start gap-3">
          <CheckCircle2
            className="mt-0.5 shrink-0 text-ns-success"
            size={22}
            aria-hidden
          />
          <div className="min-w-0">
            <h3 className="m-0 text-lg font-bold" id="deletion-complete-title">
              Learner account deleted
            </h3>
            <p className="mb-2 mt-1 text-sm text-ns-muted">
              Completed {new Date(result.completed_at).toLocaleString("en-SG")}.
              The audit trail uses target reference{" "}
              <code className="break-all">{result.target_reference}</code>.
            </p>
            <p className="my-2 text-sm text-ns-muted">
              Retained records:{" "}
              {result.retained_records.length
                ? result.retained_records.map(label).join(", ")
                : "none"}
            </p>
            <Link
              className="text-sm font-bold text-ns-teal-2 underline"
              href="/admin/students"
            >
              Return to students
            </Link>
          </div>
        </div>
      </section>
    );
  }

  const expected = preview?.confirmation_value ?? studentEmail;
  const confirmationMatches =
    confirmation.trim().toLocaleLowerCase() ===
    expected.trim().toLocaleLowerCase();
  const canExecute =
    Boolean(preview) && confirmationMatches && reason.trim().length >= 10;

  return (
    <section
      aria-labelledby="account-deletion-title"
      className="rounded-2xl border border-ns-danger/30 bg-ns-danger-soft/35 p-5"
    >
      <div className="flex items-start gap-3">
        <ShieldAlert
          className="mt-0.5 shrink-0 text-ns-danger"
          size={22}
          aria-hidden
        />
        <div className="min-w-0 grow">
          <h3 className="m-0 text-lg font-bold" id="account-deletion-title">
            Delete learner account
          </h3>
          <p className="mb-0 mt-1 text-sm leading-6 text-ns-muted">
            Academic administrators can preview the exact affected records.
            Execution requires the signed preview, the learner&apos;s exact
            email, and an audit reason.
          </p>
        </div>
      </div>

      {!preview ? (
        <div className="mt-4">
          <Button
            disabled={busy}
            variant="outline"
            onClick={() => void loadPreview()}
          >
            <Trash2 aria-hidden className="mr-2 size-4" />
            {busy ? "Preparing preview…" : "Preview account deletion"}
          </Button>
        </div>
      ) : (
        <div className="mt-5 space-y-4">
          <div className="rounded-xl border border-ns-amber-line bg-ns-amber-soft p-4">
            <p className="m-0 font-bold">Permanent deletion preview</p>
            <p className="mb-0 mt-1 text-sm leading-6">
              Preview expires{" "}
              {new Date(preview.expires_at).toLocaleString("en-SG")}. Creating a
              new preview invalidates the current confirmation.
            </p>
          </div>

          <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(preview.counts).map(([key, value]) => (
              <div
                className="rounded-xl border border-ns-line bg-ns-raised p-3"
                key={key}
              >
                <dt className="text-xs font-semibold capitalize text-ns-muted">
                  {label(key)}
                </dt>
                <dd className="m-0 mt-1 text-xl font-bold tabular-nums">
                  {value}
                </dd>
              </div>
            ))}
          </dl>

          <div className="text-sm leading-6">
            <strong>Records retained after deletion:</strong>{" "}
            {preview.retained_records.length
              ? preview.retained_records.map(label).join(", ")
              : "none"}
          </div>

          <label
            className="block text-sm font-bold"
            htmlFor="deletion-confirmation"
          >
            Type {expected} to confirm
          </label>
          <input
            autoCapitalize="none"
            autoComplete="off"
            className="block w-full rounded-lg border bg-white p-3"
            id="deletion-confirmation"
            onChange={(event) => setConfirmation(event.target.value)}
            spellCheck={false}
            value={confirmation}
          />

          <label className="block text-sm font-bold" htmlFor="deletion-reason">
            Audit reason
          </label>
          <textarea
            className="block min-h-24 w-full rounded-lg border bg-white p-3"
            id="deletion-reason"
            maxLength={500}
            minLength={10}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Explain why this deletion was requested."
            value={reason}
          />

          {!confirmationMatches && confirmation ? (
            <p className="flex items-center gap-2 text-sm font-semibold text-ns-danger">
              <AlertTriangle size={17} aria-hidden />
              The confirmation email does not match.
            </p>
          ) : null}

          <div className="flex flex-wrap gap-3">
            <Button
              disabled={!canExecute || busy}
              onClick={() => void execute()}
            >
              {busy ? "Deleting…" : "Permanently delete learner"}
            </Button>
            <Button
              disabled={busy}
              variant="outline"
              onClick={() => {
                setPreview(null);
                setConfirmation("");
                setReason("");
                setError(null);
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {error ? (
        <p className="mt-4 text-sm font-semibold text-ns-danger" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
