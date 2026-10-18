import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  RefreshCw,
  Send,
  ShieldCheck,
  Target,
} from "lucide-react";

import { MathContent, type ContentBlock } from "@/components/math-content";
import type {
  DiagnosticNext,
  DiagnosticResult,
  DiagnosticSession,
} from "@/lib/api/diagnostics";
import { cn } from "@/lib/utils";

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
  ProgressBar,
  Stat,
  Steps,
  Tag,
  focusRing,
} from "../components/ui";

type DiagnosticItem = DiagnosticSession["items"][number];
type Answers = Record<number, Record<string, string>>;
type SaveState = "idle" | "saving" | "saved";

const resultLabels: Record<DiagnosticResult["band"], string> = {
  getting_started: "Getting started",
  on_track: "On track",
  ahead: "Ahead",
};

export function LiveDiagnosticLoading({ label }: { label: string }) {
  return (
    <div
      className="flex animate-pulse flex-col gap-5"
      role="status"
      aria-label={label}
    >
      <div className="h-5 w-44 rounded-full bg-ns-line" />
      <div className="h-10 w-3/4 rounded-xl bg-ns-line" />
      <div className="h-36 rounded-2xl bg-ns-brand-soft" />
      <div className="h-48 rounded-2xl bg-ns-line" />
    </div>
  );
}

export function LiveDiagnosticError({
  title,
  message,
  onRetry,
}: {
  title: string;
  message: string;
  onRetry: () => void;
}) {
  return (
    <div role="alert">
      <Card className="items-start gap-4 p-6 lg:p-8">
        <Tag tone="danger" icon={AlertTriangle}>
          Unable to load
        </Tag>
        <H2>{title}</H2>
        <Muted>{message}</Muted>
        <Button variant="primary" icon={RefreshCw} onClick={onRetry}>
          Try again
        </Button>
      </Card>
    </div>
  );
}

export function LiveDiagnosticLanding({
  next,
  busy,
  error,
  onStart,
  onRetry,
}: {
  next: DiagnosticNext | null;
  busy: boolean;
  error: string | null;
  onStart: () => void;
  onRetry: () => void;
}) {
  if (error) {
    return (
      <LiveDiagnosticError
        title="Your readiness check could not be loaded."
        message={error}
        onRetry={onRetry}
      />
    );
  }
  if (!next) return <LiveDiagnosticLoading label="Loading readiness check" />;

  const canStart = next.status === "start";
  const canResume = next.status === "resume" && next.session_id;
  const canView =
    ["baseline_complete", "completed"].includes(next.status) &&
    next.result_session_id;

  return (
    <article className="flex flex-col gap-5 lg:gap-6">
      <header className="flex flex-col gap-2">
        <Eyebrow>READINESS</Eyebrow>
        <H1>{next.title}</H1>
        <Muted className="max-w-2xl text-base leading-7">{next.message}</Muted>
      </header>

      <Card className="gap-5 p-6 lg:p-8">
        <div className="flex items-start gap-4">
          <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-ns-brand-soft text-ns-ink">
            <ClipboardCheck size={23} aria-hidden />
          </span>
          <div className="flex min-w-0 grow flex-col gap-1">
            <H2>Your current mathematics evidence</H2>
            <Muted>
              This check helps choose a useful starting point for your course.
              It is not a grade or a prediction.
            </Muted>
          </div>
        </div>

        {next.estimated_minutes || next.question_count ? (
          <>
            <Divider />
            <div className="grid grid-cols-2 gap-5 sm:grid-cols-3">
              {next.question_count ? (
                <Stat value={next.question_count} label="questions" />
              ) : null}
              {next.estimated_minutes ? (
                <Stat value={`~${next.estimated_minutes}`} label="minutes" />
              ) : null}
              <Stat value="Allowed" label="calculator" />
            </div>
          </>
        ) : null}

        <Callout tone="brand" icon={ShieldCheck}>
          <strong>Work at your own pace</strong>
          <span>
            There is no timer, hint, or answer feedback during the check.
            Completed answers save automatically so you can return later.
          </span>
        </Callout>

        <div className="flex flex-wrap gap-3">
          {canStart ? (
            <Button
              variant="primary"
              iconRight={ArrowRight}
              disabled={busy}
              onClick={onStart}
            >
              {busy ? "Starting…" : "Start readiness check"}
            </Button>
          ) : null}
          {canResume ? (
            <Button
              variant="primary"
              iconRight={ArrowRight}
              href={`/diagnostics/${next.session_id}`}
            >
              Resume check
            </Button>
          ) : null}
          {canView ? (
            <Button
              variant="primary"
              iconRight={ArrowRight}
              href={`/diagnostics/${next.result_session_id}/result`}
            >
              View results
            </Button>
          ) : null}
          {next.status === "content_pending" ? (
            <Button href="/learn">Continue to course</Button>
          ) : null}
        </div>
      </Card>
    </article>
  );
}

export function LiveDiagnosticPlayer({
  session,
  item,
  answers,
  currentIndex,
  answeredCount,
  saveState,
  error,
  submitting,
  allComplete,
  onAnswerChange,
  onPrevious,
  onNext,
  onSubmit,
  onRetry,
}: {
  session: DiagnosticSession | null;
  item: DiagnosticItem | undefined;
  answers: Answers;
  currentIndex: number;
  answeredCount: number;
  saveState: SaveState;
  error: string | null;
  submitting: boolean;
  allComplete: boolean;
  onAnswerChange: (position: number, value: string) => void;
  onPrevious: () => void;
  onNext: () => void;
  onSubmit: () => void;
  onRetry: () => void;
}) {
  if (error && !session) {
    return (
      <LiveDiagnosticError
        title="The readiness check is unavailable."
        message={error}
        onRetry={onRetry}
      />
    );
  }
  if (!session || !item) {
    return <LiveDiagnosticLoading label="Loading readiness check" />;
  }

  const currentAnswers = answers[item.position] ?? {};
  const complete = item.question.parts.every((part) =>
    Boolean((currentAnswers[String(part.position)] ?? "").trim()),
  );
  const lastQuestion = currentIndex === session.items.length - 1;
  const answeredPercentage = session.items.length
    ? Math.round((answeredCount * 100) / session.items.length)
    : 0;

  return (
    <article className="flex flex-col gap-5 lg:gap-6">
      <div className="flex flex-col gap-4">
        <Button
          className="w-fit px-0"
          variant="ghost"
          size="sm"
          icon={ArrowLeft}
          href="/diagnostics"
        >
          Exit and return later
        </Button>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div className="flex flex-col gap-1">
            <Eyebrow>{session.purpose.toUpperCase()} READINESS</Eyebrow>
            <H1>
              Question {item.position} of {session.items.length}
            </H1>
          </div>
          <Tag tone="brand">
            {answeredCount}/{session.items.length} answered
          </Tag>
        </div>
        <Steps
          done={answeredCount}
          current={Math.max(0, currentIndex)}
          total={session.items.length}
        />
        <span className="sr-only">
          {answeredPercentage}% of the readiness check answered
        </span>
      </div>

      <Callout tone="brand" icon={Clock3}>
        <strong>No timer</strong>
        <span>
          Enter a final answer for every part. Results are shown only after the
          complete check is submitted.
        </span>
      </Callout>

      <Card className="gap-5 p-6 lg:p-8">
        <div className="flex flex-wrap items-center gap-2">
          <Tag>Outcome {item.outcome_code}</Tag>
          <Tag tone="brand">
            {item.question.calculator_allowed
              ? "Calculator allowed"
              : "No calculator"}
          </Tag>
          <Tag>
            {item.question.total_marks}{" "}
            {item.question.total_marks === 1 ? "mark" : "marks"}
          </Tag>
        </div>
        <H2>{item.question.title}</H2>
        {item.question.stem.length ? (
          <div className="text-[17px] leading-7 lg:text-lg">
            <MathContent
              assets={item.question.assets}
              assetScope={{
                kind: "question",
                stableKey: item.question.stable_key,
              }}
              blocks={item.question.stem as ContentBlock[]}
            />
          </div>
        ) : null}
        <Divider />
        <div className="flex flex-col gap-7">
          {item.question.parts.map((part) => {
            const inputId = `diagnostic-answer-${item.position}-${part.position}`;
            const partName =
              item.question.parts.length === 1 && !part.label
                ? "Your final answer"
                : `Part (${part.label ?? part.position})`;
            return (
              <fieldset
                className="m-0 flex min-w-0 flex-col gap-2 border-0 p-0"
                key={part.position}
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <label
                    htmlFor={inputId}
                    className="flex min-w-0 grow flex-col gap-1"
                  >
                    <span className="text-[15px] font-bold">{partName}</span>
                    <span className="text-sm leading-6 text-ns-muted">
                      <MathContent
                        assets={item.question.assets}
                        assetScope={{
                          kind: "question",
                          stableKey: item.question.stable_key,
                        }}
                        blocks={part.prompt as ContentBlock[]}
                      />
                    </span>
                  </label>
                  <Tag>
                    {part.marks} {part.marks === 1 ? "mark" : "marks"}
                  </Tag>
                </div>
                <input
                  id={inputId}
                  name={`answer-${part.position}`}
                  type="text"
                  inputMode={
                    part.response_type === "numeric" ? "decimal" : "text"
                  }
                  autoComplete="off"
                  autoCapitalize="off"
                  spellCheck={false}
                  maxLength={500}
                  value={currentAnswers[String(part.position)] ?? ""}
                  placeholder={part.input_placeholder}
                  onChange={(event) =>
                    onAnswerChange(part.position, event.target.value)
                  }
                  className={cn(
                    "h-[52px] w-full rounded-lg border-[1.5px] border-ns-line-strong bg-ns-raised px-4 font-ns-math text-xl text-ns-ink placeholder:text-ns-muted/80",
                    focusRing,
                  )}
                />
                <span className="text-[13px] leading-[18px] text-ns-muted">
                  {part.response_type === "numeric"
                    ? "Enter a number."
                    : "Enter an algebraic expression using standard keyboard notation."}
                </span>
              </fieldset>
            );
          })}
        </div>
      </Card>

      <div className="min-h-6 text-sm text-ns-muted" role="status">
        {saveState === "saving" ? (
          "Saving answer…"
        ) : saveState === "saved" ? (
          <span className="inline-flex items-center gap-1.5 font-semibold text-ns-success">
            <Check size={17} aria-hidden /> Answer saved
          </span>
        ) : complete ? (
          "Your answer will save automatically."
        ) : (
          "Complete every part to save this question."
        )}
      </div>

      {error ? (
        <Callout tone="danger" icon={AlertTriangle}>
          <strong>Your latest change was not saved.</strong>
          <span>{error}</span>
        </Callout>
      ) : null}

      <nav
        className="flex flex-wrap justify-between gap-3"
        aria-label="Readiness questions"
      >
        <Button
          icon={ArrowLeft}
          disabled={currentIndex === 0}
          onClick={onPrevious}
        >
          Previous
        </Button>
        {lastQuestion ? (
          <Button
            variant="primary"
            iconRight={Send}
            disabled={!allComplete || submitting || saveState === "saving"}
            onClick={onSubmit}
          >
            {submitting ? "Submitting…" : "Submit readiness check"}
          </Button>
        ) : (
          <Button variant="primary" iconRight={ArrowRight} onClick={onNext}>
            Next
          </Button>
        )}
      </nav>
      {lastQuestion && !allComplete ? (
        <Muted>
          Answer all {session.items.length} questions before submitting. You can
          use Previous to return to an unanswered question.
        </Muted>
      ) : null}
    </article>
  );
}

export function LiveDiagnosticResult({
  result,
  error,
  onRetry,
}: {
  result: DiagnosticResult | null;
  error: string | null;
  onRetry: () => void;
}) {
  if (error) {
    return (
      <LiveDiagnosticError
        title="Your readiness result could not be loaded."
        message={error}
        onRetry={onRetry}
      />
    );
  }
  if (!result) {
    return <LiveDiagnosticLoading label="Calculating readiness evidence" />;
  }

  const recommendations = result.recommendations;
  const start = recommendations[0];
  const strengths = result.topic_scores
    .filter((topic) => topic.percentage >= 80)
    .sort((left, right) => right.percentage - left.percentage)
    .slice(0, 3);
  const levelLabel = (schoolLevel: "secondary_1" | "secondary_2") =>
    schoolLevel === "secondary_1" ? "Level 1" : "Level 2";

  return (
    <article className="flex flex-col gap-5 lg:gap-6">
      <Card className="gap-5 p-6 lg:p-8" tone="brand">
        <Tag tone="amber" icon={CheckCircle2}>
          CHECK COMPLETE
        </Tag>
        <div className="flex flex-col gap-2">
          <Eyebrow>
            {result.purpose.toUpperCase()} MATHEMATICS READINESS
          </Eyebrow>
          <H1>{resultLabels[result.band]}</H1>
          <p className="m-0 max-w-2xl text-base leading-7 text-ns-on-brand/80">
            You earned {result.score} of {result.max_score} weighted marks. This
            is learning evidence to guide your next steps, not a grade or a
            predicted result.
          </p>
        </div>
        <div className="rounded-xl bg-white/10 p-4">
          <ProgressBar
            label="Overall evidence"
            value={`${result.percentage}%`}
            pct={result.percentage}
            fill="success"
          />
        </div>
      </Card>

      <section
        className="flex flex-col gap-4"
        aria-labelledby="recommendations-title"
      >
        <div className="flex items-center gap-3">
          <BookOpen size={22} className="text-ns-amber-text" aria-hidden />
          <h2
            id="recommendations-title"
            className="m-0 text-xl leading-7 font-semibold"
          >
            Your recommended learning path
          </h2>
        </div>
        {start ? (
          <Card tone="amber" className="gap-5 p-5 lg:p-6">
            <div className="flex flex-wrap items-center gap-2">
              <Tag tone="amber" icon={Target}>
                START HERE
              </Tag>
              <span className="text-[13px] font-semibold text-ns-muted">
                {levelLabel(start.school_level)} · {start.topic_code} ·{" "}
                {start.topic_title}
              </span>
            </div>
            <div className="flex flex-col gap-1.5">
              <H2>{start.lesson_title}</H2>
              <Muted>{start.reason}</Muted>
            </div>
            <ProgressBar
              label={`${start.topic_title} readiness`}
              value={`${start.percentage}%`}
              pct={start.percentage}
              fill="amber"
            />
            <div>
              <Button
                variant="primary"
                iconRight={ArrowRight}
                href={`/lessons/${start.lesson_key}`}
              >
                Start recommended lesson
              </Button>
            </div>
          </Card>
        ) : (
          <Card tone="sunken" shadow={false}>
            <H2>Continue from your course map</H2>
            <Muted>
              Lesson recommendations will appear after the reviewed course
              content is published.
            </Muted>
          </Card>
        )}
        {recommendations.length > 1 ? (
          <div className="grid gap-3 md:grid-cols-2">
            {recommendations.slice(1).map((recommendation) => (
              <Card
                key={recommendation.topic_group_key}
                shadow={false}
                className="gap-3"
              >
                <div className="flex items-center gap-2">
                  <span className="inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-ns-brand-soft text-[13px] font-extrabold text-ns-ink">
                    {recommendation.rank}
                  </span>
                  <span className="text-xs font-bold text-ns-muted">
                    {levelLabel(recommendation.school_level)} ·{" "}
                    {recommendation.topic_code}
                  </span>
                </div>
                <H3>{recommendation.lesson_title}</H3>
                <Muted>
                  {recommendation.topic_title} · {recommendation.percentage}%
                  readiness
                </Muted>
                <Button href={`/lessons/${recommendation.lesson_key}`}>
                  Open lesson
                </Button>
              </Card>
            ))}
          </div>
        ) : null}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card tone="success" shadow={false}>
          <Eyebrow>STRENGTHS TO KEEP USING</Eyebrow>
          <H2>What is working</H2>
          {strengths.length ? (
            <div className="flex flex-col gap-2">
              {strengths.map((topic) => (
                <div
                  key={topic.topic_group_key}
                  className="flex items-center justify-between gap-3 text-sm"
                >
                  <span className="font-semibold">
                    {topic.topic_code} · {topic.title}
                  </span>
                  <span className="font-bold tabular-nums text-ns-success">
                    {topic.percentage}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <Muted>
              Your course practice will build these as you progress.
            </Muted>
          )}
        </Card>
        <Card tone="amber" shadow={false}>
          <Eyebrow>HOW THIS PLAN WAS CHOSEN</Eyebrow>
          <H2>Clear and consistent</H2>
          <Muted>
            Your topic scores are ranked from lowest to highest. Within each
            topic, the plan starts with the lesson tied to the tested skill that
            needs the most practice. No paid AI call is used.
          </Muted>
        </Card>
      </section>

      <section className="flex flex-col gap-4" aria-labelledby="topics-title">
        <div className="flex items-center gap-3">
          <Target size={22} className="text-ns-amber-text" aria-hidden />
          <h2 id="topics-title" className="m-0 text-xl leading-7 font-semibold">
            Readiness by topic
          </h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {result.topic_scores.map((topic) => (
            <Card key={topic.topic_group_key} shadow={false} className="gap-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col gap-0.5">
                  <span className="text-xs font-bold text-ns-muted">
                    {levelLabel(topic.school_level)} · {topic.topic_code}
                  </span>
                  <H3>{topic.title}</H3>
                </div>
                <span className="text-sm font-black tabular-nums">
                  {topic.percentage}%
                </span>
              </div>
              <ProgressBar
                label={`${topic.score} of ${topic.max_score} weighted marks`}
                value=""
                pct={topic.percentage}
                fill={topic.percentage >= 80 ? "success" : "amber"}
              />
            </Card>
          ))}
        </div>
      </section>

      <div className="flex flex-wrap gap-3">
        <Button
          variant="primary"
          iconRight={ArrowRight}
          href={start ? `/lessons/${start.lesson_key}` : "/learn"}
        >
          {start ? "Start my learning plan" : "Continue to your course"}
        </Button>
        <Button href="/diagnostics">Readiness overview</Button>
      </div>
    </article>
  );
}
