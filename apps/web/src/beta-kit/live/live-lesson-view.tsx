import {
  AlertTriangle,
  Clock3,
  Construction,
  PlayCircle,
  RefreshCw,
} from "lucide-react";

import type { LessonResponse } from "@/lib/api/course";
import type { LessonContentApi } from "@/components/lesson-content";
import { LessonContent } from "@/components/lesson-content";
import { LessonMediaPanel } from "@/components/lesson-media-panel";

import { BackLink } from "../screens/lesson";
import {
  Button,
  Callout,
  Card,
  Divider,
  Eyebrow,
  H1,
  H2,
  H3,
  Muted,
  Tag,
} from "../components/ui";

export function LiveLessonLoading() {
  return (
    <div
      className="flex animate-pulse flex-col gap-5"
      role="status"
      aria-label="Loading lesson"
    >
      <div className="h-5 w-40 rounded-full bg-ns-line" />
      <div className="h-12 w-4/5 rounded-xl bg-ns-line" />
      <div className="h-28 rounded-2xl bg-ns-brand-soft" />
      <div className="h-72 rounded-2xl bg-ns-line" />
    </div>
  );
}

export function LiveLessonError({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div role="alert">
      <Card className="items-start gap-4 p-6 lg:p-8">
        <Tag tone="danger" icon={AlertTriangle}>
          Lesson unavailable
        </Tag>
        <H2>We could not load this lesson.</H2>
        <Muted>{message}</Muted>
        <Button variant="primary" icon={RefreshCw} onClick={onRetry}>
          Try again
        </Button>
      </Card>
    </div>
  );
}

export function LiveLessonView({
  lesson,
  progressWarning,
  startingPractice,
  sectionApi,
  onStartPractice,
}: {
  lesson: LessonResponse;
  progressWarning: string | null;
  startingPractice: boolean;
  sectionApi?: LessonContentApi;
  onStartPractice: () => void;
}) {
  const practiceAvailable =
    lesson.practice.available || lesson.practice.development_available;

  return (
    <article className="flex flex-col gap-5 lg:gap-7">
      <BackLink href="/learn">Back to learning</BackLink>

      {lesson.development_preview ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <strong>Development lesson</strong>
          <span>
            This lesson revision is visible because draft preview is enabled.
          </span>
        </Callout>
      ) : null}

      {progressWarning ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <strong>Progress could not be recorded</strong>
          <span>{progressWarning} You can continue reading this lesson.</span>
        </Callout>
      ) : null}

      <header className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Tag tone="brand">Lesson {lesson.position}</Tag>
          {lesson.outcomes.map((outcome) => (
            <Tag key={outcome}>Outcome {outcome}</Tag>
          ))}
          <span className="inline-flex items-center gap-1.5 text-sm text-ns-muted">
            <Clock3 size={16} aria-hidden />
            {lesson.estimated_minutes} minutes
          </span>
        </div>
        <H1 className="lg:text-4xl lg:leading-[44px]">{lesson.title}</H1>
        <Muted className="max-w-3xl text-base leading-7">
          {lesson.summary}
        </Muted>
      </header>

      <Card tone="sunken" className="gap-3">
        <H3>By the end you can</H3>
        <ul className="m-0 flex list-disc flex-col gap-2 pl-5 text-[15px] leading-6">
          {lesson.objectives.map((objective) => (
            <li key={objective}>{objective}</li>
          ))}
        </ul>
      </Card>

      {lesson.sections.length ? (
        <>
          <LessonMediaPanel />
          <LessonContent
            api={sectionApi}
            appearance="nextscholar"
            lessonKey={lesson.stable_key}
            sections={lesson.sections}
          />
        </>
      ) : lesson.learning_material_state === "pending" ? (
        <Card tone="sunken" className="items-center gap-3 py-9 text-center">
          <Construction size={36} className="text-ns-amber-text" aria-hidden />
          <H2>Lesson material is being prepared</H2>
          <Muted className="max-w-xl">
            Video, explanations, worked examples and recall checks can be added
            later. This placeholder contains no invented teaching material.
          </Muted>
        </Card>
      ) : null}

      <Card className="gap-4 shadow-ns-md">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-1">
            <Eyebrow>APPLY WHAT YOU LEARNT</Eyebrow>
            <H2>Guided practice</H2>
          </div>
          <Tag tone={practiceAvailable ? "brand" : "neutral"}>
            {lesson.practice.question_count} question
            {lesson.practice.question_count === 1 ? "" : "s"}
          </Tag>
        </div>
        <Divider />
        <Muted className="text-[15px] leading-6">
          Enter final answers and receive deterministic marking. If an answer is
          wrong, you can retry or open the authored hints.
          {lesson.practice.development_available
            ? " These draft questions are available only in development preview."
            : ""}
        </Muted>
        <Button
          variant="primary"
          icon={PlayCircle}
          disabled={!practiceAvailable || startingPractice}
          onClick={onStartPractice}
        >
          {startingPractice
            ? "Starting practice…"
            : !practiceAvailable
              ? "Practice unavailable"
              : lesson.practice.development_available
                ? "Start draft practice"
                : "Start practice"}
        </Button>
      </Card>
    </article>
  );
}
