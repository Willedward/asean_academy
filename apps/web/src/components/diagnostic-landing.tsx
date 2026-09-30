"use client";

import {
  ArrowRight,
  CircleAlert,
  ClipboardCheck,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { LiveDiagnosticLanding } from "@/beta-kit/live/live-diagnostic-view";
import { Button } from "@/components/ui/button";
import {
  createDiagnosticSession,
  getNextDiagnostic,
  type DiagnosticNext,
} from "@/lib/api/diagnostics";

export function DiagnosticLanding({
  loadNext = getNextDiagnostic,
  start = createDiagnosticSession,
  appearance = "established",
}: {
  loadNext?: () => Promise<DiagnosticNext>;
  start?: typeof createDiagnosticSession;
  appearance?: "established" | "nextscholar";
}) {
  const router = useRouter();
  const [next, setNext] = useState<DiagnosticNext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    void loadNext().then(
      (value) => {
        if (active) {
          setNext(value);
          setError(null);
        }
      },
      (caught: unknown) => {
        if (active)
          setError(
            caught instanceof Error
              ? caught.message
              : "The readiness check could not be loaded.",
          );
      },
    );
    return () => {
      active = false;
    };
  }, [loadNext, reload]);

  async function begin() {
    if (!next?.purpose) return;
    setBusy(true);
    setError(null);
    try {
      const session = await start(next.purpose);
      router.push(`/diagnostics/${session.session_id}`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The readiness check could not be started.",
      );
      setBusy(false);
    }
  }

  if (appearance === "nextscholar") {
    return (
      <LiveDiagnosticLanding
        next={next}
        busy={busy}
        error={error}
        onStart={() => void begin()}
        onRetry={() => {
          setError(null);
          setReload((value) => value + 1);
        }}
      />
    );
  }

  if (error) {
    return (
      <div className="status-card border-rose-200 bg-rose-50" role="alert">
        <CircleAlert aria-hidden="true" className="size-5 text-rose-700" />
        <div className="grow">
          <p className="status-title">Readiness check unavailable</p>
          <p className="status-copy">{error}</p>
        </div>
        <Button
          variant="outline"
          onClick={() => setReload((value) => value + 1)}
        >
          <RefreshCw aria-hidden="true" className="mr-2 size-4" />
          Retry
        </Button>
      </div>
    );
  }
  if (!next)
    return (
      <div className="status-card animate-pulse" role="status">
        Loading readiness check…
      </div>
    );

  const canStart = next.status === "start";
  const canResume = next.status === "resume" && next.session_id;
  const canView =
    ["baseline_complete", "completed"].includes(next.status) &&
    next.result_session_id;

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="max-w-2xl">
          <p className="mb-2 inline-flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-teal-700">
            <ClipboardCheck aria-hidden="true" className="size-4" />
            Mathematics readiness evidence
          </p>
          <h1 className="m-0 text-3xl font-black">{next.title}</h1>
          <p className="mt-3 leading-7 text-slate-600">{next.message}</p>
          {next.estimated_minutes && next.question_count ? (
            <p className="text-sm font-semibold text-slate-500">
              About {next.estimated_minutes} minutes · {next.question_count}{" "}
              questions · calculator allowed
            </p>
          ) : null}
          <p className="text-sm text-slate-500">
            There is no timer, hint, or answer feedback during the check. Each
            completed answer is saved so you can return later.
          </p>
        </div>
        {canStart ? (
          <Button disabled={busy} onClick={() => void begin()}>
            {busy ? "Starting…" : "Start readiness check"}
            <ArrowRight aria-hidden="true" className="ml-2 size-4" />
          </Button>
        ) : null}
        {canResume ? (
          <Button asChild>
            <Link href={`/diagnostics/${next.session_id}`}>
              Resume check
              <ArrowRight aria-hidden="true" className="ml-2 size-4" />
            </Link>
          </Button>
        ) : null}
        {canView ? (
          <Button asChild>
            <Link href={`/diagnostics/${next.result_session_id}/result`}>
              View results
              <ArrowRight aria-hidden="true" className="ml-2 size-4" />
            </Link>
          </Button>
        ) : null}
        {next.status === "content_pending" ? (
          <Button asChild variant="outline">
            <Link href="/learn">Continue to course</Link>
          </Button>
        ) : null}
      </div>
    </section>
  );
}
