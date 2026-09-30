"use client";

import { CircleAlert, RefreshCw, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { LiveDiagnosticResult } from "@/beta-kit/live/live-diagnostic-view";
import { Button } from "@/components/ui/button";
import {
  getDiagnosticResult,
  type DiagnosticResult,
} from "@/lib/api/diagnostics";

const labels: Record<DiagnosticResult["band"], string> = {
  getting_started: "Getting started",
  on_track: "On track",
  ahead: "Ahead",
};

export function DiagnosticResultPanel({
  sessionId,
  load = getDiagnosticResult,
  appearance = "established",
}: {
  sessionId: string;
  load?: typeof getDiagnosticResult;
  appearance?: "established" | "nextscholar";
}) {
  const [result, setResult] = useState<DiagnosticResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    void load(sessionId).then(
      (value) => active && setResult(value),
      (caught: unknown) =>
        active &&
        setError(
          caught instanceof Error
            ? caught.message
            : "Your readiness result could not be loaded.",
        ),
    );
    return () => {
      active = false;
    };
  }, [load, reload, sessionId]);
  if (appearance === "nextscholar") {
    return (
      <LiveDiagnosticResult
        result={result}
        error={error}
        onRetry={() => {
          setError(null);
          setReload((value) => value + 1);
        }}
      />
    );
  }
  if (error)
    return (
      <div className="status-card border-rose-200 bg-rose-50" role="alert">
        <CircleAlert className="size-5 text-rose-700" />
        <div className="grow">
          <p className="status-title">Result unavailable</p>
          <p className="status-copy">{error}</p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            setError(null);
            setReload((value) => value + 1);
          }}
        >
          <RefreshCw className="mr-2 size-4" />
          Retry
        </Button>
      </div>
    );
  if (!result)
    return (
      <div className="status-card animate-pulse" role="status">
        Calculating your readiness evidence…
      </div>
    );
  return (
    <div className="space-y-7">
      <header className="rounded-3xl bg-teal-900 p-8 text-white">
        <p className="mb-2 inline-flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-teal-200">
          <Sparkles className="size-4" />
          {result.purpose} Mathematics readiness
        </p>
        <h1 className="m-0 text-4xl font-black">{labels[result.band]}</h1>
        <p className="mb-0 mt-3 text-lg text-teal-50">
          You earned {result.score} of {result.max_score} weighted marks (
          {result.percentage}%). This is learning evidence, not a label or
          predicted scholarship result.
        </p>
      </header>
      <section>
        <h2 className="text-2xl font-black">Results by syllabus outcome</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {result.outcome_scores.map((outcome) => (
            <div
              className="rounded-2xl border border-slate-200 bg-white p-5"
              key={outcome.outcome_code}
            >
              <div className="flex items-center justify-between gap-3">
                <strong>Outcome {outcome.outcome_code}</strong>
                <span>{outcome.percentage}%</span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full bg-teal-600"
                  style={{ width: `${outcome.percentage}%` }}
                />
              </div>
              <p className="mb-0 text-sm text-slate-500">
                {outcome.score} of {outcome.max_score} weighted marks
              </p>
            </div>
          ))}
        </div>
      </section>
      <section className="grid gap-5 md:grid-cols-2">
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
          <h2 className="mt-0 text-xl font-black">Strengths to keep using</h2>
          <p className="mb-0">
            {result.strengths.length
              ? result.strengths.map((code) => `Outcome ${code}`).join(", ")
              : "Your course practice will build these as you progress."}
          </p>
        </div>
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
          <h2 className="mt-0 text-xl font-black">What to work on next</h2>
          <p className="mb-0">
            {result.priorities.length
              ? result.priorities.map((code) => `Outcome ${code}`).join(", ")
              : "Continue through the course and keep your current momentum."}
          </p>
        </div>
      </section>
      <div className="flex flex-wrap gap-3">
        <Button asChild>
          <Link href="/learn">Continue to your course</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/diagnostics">Readiness overview</Link>
        </Button>
      </div>
    </div>
  );
}
