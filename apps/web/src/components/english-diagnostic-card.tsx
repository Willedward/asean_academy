"use client";

import { ArrowRight, ClipboardCheck, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  Button,
  Callout,
  Card,
  Eyebrow,
  H2,
  Muted,
  Tag,
} from "@/beta-kit/components/ui";
import {
  createEnglishDiagnosticSession,
  getNextEnglishDiagnostic,
  type EnglishDiagnosticNextResponse,
} from "@/lib/api/english";

export function EnglishDiagnosticCard() {
  const router = useRouter();
  const [next, setNext] = useState<EnglishDiagnosticNextResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    void getNextEnglishDiagnostic().then(
      (response) => {
        if (active) {
          setNext(response);
          setError(null);
        }
      },
      (caught: unknown) => {
        if (active)
          setError(
            caught instanceof Error
              ? caught.message
              : "The English diagnostic could not be loaded.",
          );
      },
    );
    return () => {
      active = false;
    };
  }, [reload]);

  async function start() {
    if (!next?.purpose) return;
    setBusy(true);
    setError(null);
    try {
      const session = await createEnglishDiagnosticSession(next.purpose);
      router.push(`/english/diagnostics/${session.session_id}`);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The English diagnostic could not be started.",
      );
      setBusy(false);
    }
  }

  if (error) {
    return (
      <Callout tone="amber" icon={RefreshCw}>
        <strong>English diagnostic unavailable</strong>
        <span>{error}</span>
        <Button onClick={() => setReload((value) => value + 1)}>
          Try again
        </Button>
      </Callout>
    );
  }
  if (!next) {
    return (
      <Card className="animate-pulse">
        <Muted>Loading English diagnostic…</Muted>
      </Card>
    );
  }

  const resultId = next.result_session_id;
  return (
    <Card className="gap-4 border-ns-brand bg-ns-brand-soft/40">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="max-w-2xl">
          <Eyebrow>OBJECTIVE ENGLISH DIAGNOSTIC</Eyebrow>
          <H2>{next.title}</H2>
          <Muted className="mt-1">{next.message}</Muted>
          <div className="mt-3 flex flex-wrap gap-2">
            <Tag icon={ClipboardCheck}>20 scored parts</Tag>
            <Tag>Feedback after the full form</Tag>
            {next.estimated_minutes ? (
              <Tag>{next.estimated_minutes} minutes</Tag>
            ) : null}
          </div>
        </div>
        {next.status === "start" ? (
          <Button
            variant="primary"
            icon={ArrowRight}
            disabled={busy}
            onClick={() => void start()}
          >
            {busy ? "Starting…" : `Start ${next.purpose}`}
          </Button>
        ) : null}
        {next.status === "resume" && next.session_id ? (
          <Button
            variant="primary"
            icon={ArrowRight}
            href={`/english/diagnostics/${next.session_id}`}
          >
            Resume
          </Button>
        ) : null}
        {resultId ? (
          <Button
            href={`/english/diagnostics/${resultId}/result`}
            icon={ArrowRight}
          >
            View results
          </Button>
        ) : null}
        {next.status === "content_pending" ? (
          <Tag tone="neutral">In preparation</Tag>
        ) : null}
      </div>
      {next.status === "baseline_complete" ? (
        <p className="m-0 text-sm font-semibold text-ns-muted">
          Your endline stays locked until the Sprint lesson checkpoints are
          mastered. You can continue learning now and return here later.
        </p>
      ) : null}
      {next.status === "completed" ? (
        <Link href="/english" className="text-sm font-semibold text-ns-ink">
          Continue reviewing your English course
        </Link>
      ) : null}
    </Card>
  );
}
