"use client";

import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  PlayCircle,
  RotateCcw,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { EnglishLessonHeader } from "@/beta-kit/live/english-learning-screens";
import {
  Button,
  Callout,
  Card,
  Divider,
  H2,
  H3,
  Muted,
  Tag,
} from "@/beta-kit/components/ui";
import {
  createEnglishPracticeSession,
  type EnglishLessonResponse,
} from "@/lib/api/english";

const SECTION_LABEL = {
  retrieval_warmup: "Retrieval warm-up",
  explicit_model: "Learn the method",
  worked_analysis: "Worked analysis",
  guided_practice: "Guided practice",
  independent_application: "Independent application",
  error_classification: "Diagnose the mistake",
  exit_ticket: "Exit ticket",
} as const;

export function EnglishLessonPanel({ lesson }: { lesson: EnglishLessonResponse }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function begin(mode: "guided_practice" | "retry_review") {
    setBusy(true);
    setError(null);
    try {
      const session = await createEnglishPracticeSession(lesson.stable_key, mode);
      router.push(`/english/practice/${session.session_id}`);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "English practice could not be started.",
      );
      setBusy(false);
    }
  }

  return (
    <article className="flex flex-col gap-5 lg:gap-6">
      <Link
        href="/english"
        className="inline-flex items-center gap-2 self-start text-sm font-semibold text-ns-ink no-underline hover:underline"
      >
        <ArrowLeft size={17} aria-hidden /> Back to English
      </Link>

      {lesson.development_preview ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <strong>Development lesson</strong>
          <span>This draft is available only in the review environment.</span>
        </Callout>
      ) : null}

      <EnglishLessonHeader
        code={lesson.lesson_code}
        outcome={lesson.outcome_code}
        title={lesson.title}
        summary={lesson.summary}
        minutes={lesson.estimated_minutes}
      />

      {lesson.sections.map((section) => (
        <Card key={section.position} className="gap-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Tag tone="brand">
              {section.position}. {SECTION_LABEL[section.section_type]}
            </Tag>
            {section.question_count ? (
              <Tag>{section.question_count} questions</Tag>
            ) : null}
          </div>
          <H2>{section.title}</H2>
          <div className="flex flex-col gap-3 text-[16px] leading-7 text-ns-ink">
            {section.content.map((paragraph) => (
              <p key={paragraph} className="m-0">
                {paragraph}
              </p>
            ))}
          </div>
        </Card>
      ))}

      <Card tone="brand" className="gap-4">
        <div className="flex items-center gap-2">
          <CheckCircle2 size={22} aria-hidden />
          <H3>Apply the context-clue routine</H3>
        </div>
        <p className="m-0 max-w-2xl text-sm leading-6 text-ns-on-dark-muted">
          Complete all {lesson.practice.question_count} objective questions.
          Answers are marked immediately without a paid AI call.
        </p>
        {error ? (
          <Callout tone="amber" icon={AlertTriangle}>
            <span>{error}</span>
          </Callout>
        ) : null}
        <Divider />
        <div className="flex flex-wrap gap-3">
          <Button
            variant="gold"
            icon={PlayCircle}
            disabled={
              busy ||
              (!lesson.practice.available && !lesson.practice.development_available)
            }
            onClick={() => void begin("guided_practice")}
          >
            {busy ? "Starting…" : "Start lesson practice"}
          </Button>
          {lesson.practice.retry_question_count > 0 ? (
            <Button
              icon={RotateCcw}
              disabled={busy}
              onClick={() => void begin("retry_review")}
            >
              Retry {lesson.practice.retry_question_count} exit ticket
            </Button>
          ) : null}
        </div>
        {!lesson.practice.available && !lesson.practice.development_available ? (
          <Muted>Practice unlocks after the content revision is published.</Muted>
        ) : null}
      </Card>
    </article>
  );
}
