"use client";

import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import { useEffect, useState } from "react";

import {
  Button,
  Callout,
  Card,
  Eyebrow,
  H1,
  H2,
  Muted,
  ProgressBar,
  Tag,
} from "@/beta-kit/components/ui";
import {
  getEnglishDiagnosticResult,
  type EnglishDiagnosticSessionResponse,
} from "@/lib/api/english";

const TASK_LABELS = {
  vocabulary_in_context: "Vocabulary in context",
  banked_cloze: "Banked cloze",
  open_cloze: "Open cloze",
  reading_comprehension: "Reading comprehension",
} as const;

export function EnglishDiagnosticResult({ sessionId }: { sessionId: string }) {
  const [result, setResult] = useState<EnglishDiagnosticSessionResponse | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    void getEnglishDiagnosticResult(sessionId).then(
      (response) => {
        if (active) {
          setResult(response);
          setError(null);
        }
      },
      (caught: unknown) => {
        if (active)
          setError(
            caught instanceof Error
              ? caught.message
              : "Your English result could not be loaded.",
          );
      },
    );
    return () => {
      active = false;
    };
  }, [reload, sessionId]);

  if (error) {
    return (
      <Callout tone="amber" icon={AlertTriangle}>
        <strong>Result unavailable</strong>
        <span>{error}</span>
        <Button
          icon={RefreshCw}
          onClick={() => setReload((value) => value + 1)}
        >
          Try again
        </Button>
      </Callout>
    );
  }
  if (!result)
    return (
      <Card className="animate-pulse">
        <Muted>Loading your English skill profile…</Muted>
      </Card>
    );

  const percentage = result.percentage ?? 0;
  return (
    <div className="flex flex-col gap-5">
      <Card tone="success" className="items-center gap-4 py-9 text-center">
        <CheckCircle2 size={48} className="text-ns-success" aria-hidden />
        <Eyebrow>{result.purpose.toUpperCase()} COMPLETE</Eyebrow>
        <H1>
          {result.correct_parts} of {result.total_parts} parts correct
        </H1>
        <Tag tone="success">
          {percentage}% · {result.band}
        </Tag>
        <Muted className="max-w-2xl leading-7">
          This is a NextScholar skill profile, not an official ASEAN Scholarship
          score. Use the strand breakdown to decide what to practise next.
        </Muted>
      </Card>
      <section className="grid gap-4 sm:grid-cols-2">
        {result.task_scores.map((score) => (
          <Card key={score.task_type} className="gap-4">
            <div>
              <Eyebrow>SKILL STRAND</Eyebrow>
              <H2>{TASK_LABELS[score.task_type]}</H2>
            </div>
            <ProgressBar
              label="Scored parts"
              value={`${score.correct_parts} / ${score.total_parts}`}
              pct={score.percentage}
              fill={score.percentage >= 75 ? "success" : "amber"}
            />
            <Button
              href={`/english/lessons/${score.recommended_lesson_key}`}
              icon={ArrowRight}
            >
              Review {score.recommended_lesson_title}
            </Button>
          </Card>
        ))}
      </section>
      <div className="flex flex-wrap justify-center gap-3">
        <Button variant="primary" href="/english">
          Return to English course
        </Button>
      </div>
    </div>
  );
}
