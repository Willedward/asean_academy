"use client";

import { RotateCcw } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  adminRequest,
  type ResetDiagnosticResult,
} from "@/lib/api/admin-dashboard";
import { ApiRequestError } from "@/lib/api/errors";

type Purpose = "baseline" | "endline";

type ResetApi = (
  learnerId: string,
  purpose: Purpose,
  reason: string,
) => Promise<ResetDiagnosticResult>;

const defaultReset: ResetApi = (learnerId, purpose, reason) =>
  adminRequest<ResetDiagnosticResult>(
    "students/" +
      encodeURIComponent(learnerId) +
      "/diagnostics/" +
      purpose +
      "/reset",
    { reason },
  );

function errorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    return (
      error.message + (error.requestId ? " Request ID: " + error.requestId : "")
    );
  }
  return error instanceof Error
    ? error.message
    : "The diagnostic could not be reset.";
}

export function AdminDiagnosticReset({
  learnerId,
  purpose,
  onReset,
  reset = defaultReset,
}: {
  learnerId: string;
  purpose: Purpose;
  onReset: () => void;
  reset?: ResetApi;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      await reset(learnerId, purpose, reason.trim());
      setOpen(false);
      setReason("");
      onReset();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <Button variant="outline" onClick={() => setOpen(true)}>
        <RotateCcw aria-hidden className="mr-2 size-4" />
        Review {purpose} reset
      </Button>
    );
  }

  return (
    <div className="mt-4 space-y-3 rounded-xl border border-amber-300 bg-amber-50 p-4">
      <p className="m-0 font-bold capitalize">Reset {purpose} diagnostic?</p>
      <p className="m-0 text-sm leading-6">
        This preserves the submitted result in history as reset and allows a new
        attempt. Use this only for an exceptional invalid attempt.
      </p>
      <label
        className="block text-sm font-bold"
        htmlFor={"diagnostic-reset-" + purpose}
      >
        Reason for {purpose} reset
      </label>
      <textarea
        className="block min-h-24 w-full rounded-lg border bg-white p-3"
        id={"diagnostic-reset-" + purpose}
        maxLength={500}
        minLength={10}
        onChange={(event) => setReason(event.target.value)}
        value={reason}
      />
      <div className="flex flex-wrap gap-2">
        <Button
          disabled={busy || reason.trim().length < 10}
          onClick={() => void confirm()}
        >
          {busy ? "Resetting…" : "Confirm diagnostic reset"}
        </Button>
        <Button
          disabled={busy}
          variant="outline"
          onClick={() => {
            setOpen(false);
            setReason("");
            setError(null);
          }}
        >
          Cancel
        </Button>
      </div>
      {error ? (
        <p className="m-0 text-sm font-semibold text-rose-800" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
