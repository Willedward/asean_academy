import {
  AlertTriangle,
  CheckCircle2,
  Lightbulb,
  RefreshCw,
  Send,
} from "lucide-react";

import { MathContent, type ContentBlock } from "@/components/math-content";
import { QuestionReportForm } from "@/components/question-report-form";
import type {
  AttemptResponse,
  GiveUpResponse,
  HintResponse,
  NextQuestionResponse,
} from "@/lib/api/practice";
import { cn } from "@/lib/utils";

import { BackLink } from "../screens/lesson";
import { TutorDock } from "../tutor/tutor-dock";
import {
  Button,
  Callout,
  Card,
  Divider,
  Eyebrow,
  H1,
  H2,
  Muted,
  Steps,
  Tag,
  focusRing,
} from "../components/ui";

type Props = {
  sessionId: string;
  current: NextQuestionResponse | null;
  answers: Record<string, string>;
  attempt: AttemptResponse | null;
  hints: HintResponse[];
  solution: GiveUpResponse["solution"] | null;
  error: string | null;
  busy: boolean;
  allAnswersPresent: boolean;
  onAnswerChange: (position: number, value: string) => void;
  onCheckAnswers: () => void;
  onOpenHint: (stage: 1 | 2) => void;
  onRevealSolution: () => void;
  onContinue: () => void;
};

function LoadError({
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
          Practice unavailable
        </Tag>
        <H2>We could not load this practice session.</H2>
        <Muted>{message}</Muted>
        <Button variant="primary" icon={RefreshCw} onClick={onRetry}>
          Try again
        </Button>
      </Card>
    </div>
  );
}

function Loading() {
  return (
    <div
      className="flex animate-pulse flex-col gap-5"
      role="status"
      aria-label="Loading practice"
    >
      <div className="h-5 w-48 rounded-full bg-ns-line" />
      <div className="h-10 w-3/4 rounded-xl bg-ns-line" />
      <div className="h-36 rounded-2xl bg-ns-brand-soft" />
      <div className="h-52 rounded-2xl bg-ns-line" />
    </div>
  );
}

function Completed({ current }: { current: NextQuestionResponse }) {
  const checkpoint = current.session.mode === "checkpoint";
  const percentage = current.session.question_count
    ? Math.round(
        (1000 * current.session.correct_count) / current.session.question_count,
      ) / 10
    : 0;
  return (
    <Card className="items-center gap-4 py-10 text-center" tone="success">
      <CheckCircle2 size={48} className="text-ns-success" aria-hidden />
      <Eyebrow>
        {checkpoint ? "CHECKPOINT COMPLETE" : "PRACTICE COMPLETE"}
      </Eyebrow>
      <H1>{checkpoint ? "Checkpoint submitted" : "Practice complete"}</H1>
      <Muted className="max-w-lg text-base leading-7">
        {checkpoint
          ? `You answered ${current.session.correct_count} of ${current.session.question_count} correctly (${percentage}%).`
          : `You resolved ${current.session.resolved_count} of ${current.session.question_count} questions.`}
      </Muted>
      <div className="flex flex-wrap justify-center gap-3">
        <Button variant="primary" href="/progress">
          View progress
        </Button>
        {!checkpoint && current.session.lesson_key ? (
          <Button href={`/lessons/${current.session.lesson_key}`}>
            Return to lesson
          </Button>
        ) : null}
      </div>
    </Card>
  );
}

export function LivePracticeView({
  sessionId,
  current,
  answers,
  attempt,
  hints,
  solution,
  error,
  busy,
  allAnswersPresent,
  onAnswerChange,
  onCheckAnswers,
  onOpenHint,
  onRevealSolution,
  onContinue,
}: Props) {
  if (error && !current)
    return <LoadError message={error} onRetry={onContinue} />;
  if (!current) return <Loading />;

  const question = current.question;
  if (current.status === "completed" || !question)
    return <Completed current={current} />;

  const checkpoint = current.session.mode === "checkpoint";
  const lessonHref = current.session.lesson_key
    ? `/lessons/${current.session.lesson_key}`
    : "/progress";
  const leaveHref = checkpoint ? "/progress" : lessonHref;
  const position = current.position ?? current.session.resolved_count + 1;
  const finished = Boolean(attempt?.correct || solution);
  const wrongTries = attempt?.correct
    ? 0
    : Math.max(attempt?.attempt_number ?? 0, current.attempt_count ?? 0);
  const stage = checkpoint
    ? "Checkpoint"
    : current.session.mode === "retry_review"
      ? "Retry review"
      : `${(current.stage ?? "guided").replaceAll("_", " ")} practice`;

  return (
    <article className="flex flex-col gap-5 lg:gap-6">
      <div className="flex flex-col gap-4">
        <BackLink href={leaveHref}>
          {checkpoint ? "Exit checkpoint" : "Save and leave"}
        </BackLink>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div className="flex flex-col gap-1">
            <Eyebrow>{stage.toUpperCase()}</Eyebrow>
            <H1>
              Question {position} of {current.session.question_count}
            </H1>
          </div>
          <Tag tone="brand">
            {question.total_marks}{" "}
            {question.total_marks === 1 ? "mark" : "marks"}
          </Tag>
        </div>
        <Steps
          done={Math.max(0, position - 1)}
          current={Math.max(0, position - 1)}
          total={current.session.question_count}
        />
      </div>

      {current.session.development_drafts ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <strong>Development practice</strong>
          <span>
            These draft questions are available only while development preview
            is enabled.
          </span>
        </Callout>
      ) : null}

      <Card className="gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <Tag>Level {question.difficulty}</Tag>
          <Tag>Outcome {question.primary_outcome}</Tag>
          <Tag tone={question.calculator_allowed ? "brand" : "neutral"}>
            {question.calculator_allowed
              ? "Calculator allowed"
              : "No calculator"}
          </Tag>
        </div>
        <H2>{question.title}</H2>
        {question.stem.length ? (
          <div className="text-[17px] leading-7 lg:text-lg">
            <MathContent blocks={question.stem as ContentBlock[]} />
          </div>
        ) : null}
      </Card>

      <Card className="gap-5">
        {question.parts.map((part) => {
          const result = attempt?.parts.find(
            (candidate) => candidate.position === part.position,
          );
          const status = result
            ? result.correct
              ? "correct"
              : "wrong"
            : "none";
          const inputId = `answer-${part.position}`;
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
                  <span className="text-[15px] font-bold">
                    {question.parts.length === 1 && !part.label
                      ? "Your answer"
                      : `Part (${part.label ?? part.position})`}
                  </span>
                  <span className="text-sm leading-6 text-ns-muted">
                    <MathContent blocks={part.prompt as ContentBlock[]} />
                  </span>
                </label>
                <Tag
                  tone={
                    status === "correct"
                      ? "success"
                      : status === "wrong"
                        ? "danger"
                        : "neutral"
                  }
                >
                  {status === "correct"
                    ? "Correct"
                    : status === "wrong"
                      ? "Not yet"
                      : `${part.marks} ${part.marks === 1 ? "mark" : "marks"}`}
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
                value={answers[String(part.position)] ?? ""}
                placeholder={part.input_placeholder}
                disabled={finished}
                aria-invalid={status === "wrong" ? true : undefined}
                onChange={(event) =>
                  onAnswerChange(part.position, event.target.value)
                }
                className={cn(
                  "h-[52px] w-full rounded-lg border-[1.5px] bg-ns-raised px-4 font-ns-math text-xl text-ns-ink placeholder:text-ns-muted/80",
                  status === "correct"
                    ? "border-ns-success bg-ns-success-soft"
                    : status === "wrong"
                      ? "border-ns-danger"
                      : "border-ns-line-strong",
                  focusRing,
                )}
              />
              <span className="text-[13px] leading-[18px] text-ns-muted">
                {part.response_type === "numeric"
                  ? "Enter a number."
                  : "Enter an algebraic expression using standard keyboard notation."}
              </span>
              {result?.error ? (
                <span className="text-[13px] font-semibold text-ns-danger">
                  {result.error}
                </span>
              ) : null}
            </fieldset>
          );
        })}
      </Card>

      {hints.length ? (
        <section
          aria-label="Hints"
          className="flex flex-col gap-3 rounded-xl bg-ns-amber-soft p-4"
        >
          {[...hints]
            .sort((a, b) => a.stage - b.stage)
            .map((hint) => (
              <div key={hint.stage} className="flex items-start gap-3">
                <Tag tone="amber" icon={Lightbulb}>
                  Hint {hint.stage}
                </Tag>
                <div className="flex min-w-0 flex-col gap-2 text-[15px] leading-6">
                  {hint.parts.map((part) => (
                    <MathContent
                      key={part.position}
                      blocks={part.content as ContentBlock[]}
                    />
                  ))}
                </div>
              </div>
            ))}
        </section>
      ) : null}

      {attempt ? (
        <Callout
          tone={attempt.correct ? "success" : "danger"}
          icon={attempt.correct ? CheckCircle2 : AlertTriangle}
        >
          <strong>{attempt.correct ? "Correct" : "Try again"}</strong>
          <span>
            {attempt.correct
              ? `You earned ${attempt.marks_awarded} of ${attempt.marks_available} marks.`
              : "That final answer is not correct yet. Retry it or open an authored hint."}
          </span>
        </Callout>
      ) : null}

      {solution ? (
        <Card className="gap-5">
          <H2>Worked solution</H2>
          {solution.parts.map((part) => (
            <section className="flex flex-col gap-3" key={part.position}>
              <div className="rounded-xl bg-ns-sunken p-4">
                <Eyebrow muted>
                  {part.label ? `ANSWER (${part.label})` : "ANSWER"}
                </Eyebrow>
                <div className="mt-1 font-ns-math text-[22px]">
                  <MathContent
                    blocks={[
                      { type: "inline_math", latex: part.canonical_latex },
                    ]}
                  />
                </div>
              </div>
              <ol className="m-0 flex list-none flex-col gap-3 p-0">
                {part.steps.map((step, index) => {
                  const content = Array.isArray(step.content)
                    ? step.content
                    : [];
                  return (
                    <li className="flex items-start gap-3" key={index}>
                      <span className="inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-ns-brand-soft text-sm font-bold">
                        {index + 1}
                      </span>
                      <div className="min-w-0 grow pt-0.5 leading-7">
                        <MathContent blocks={content as ContentBlock[]} />
                      </div>
                    </li>
                  );
                })}
              </ol>
              <Divider />
            </section>
          ))}
        </Card>
      ) : null}

      {error ? (
        <Callout tone="danger" icon={AlertTriangle}>
          <span>{error}</span>
        </Callout>
      ) : null}

      <div className="flex flex-wrap gap-3 rounded-2xl border border-ns-line bg-ns-raised p-4 shadow-ns-sm">
        {finished ? (
          <Button variant="primary" disabled={busy} onClick={onContinue}>
            Continue
          </Button>
        ) : (
          <>
            <Button
              variant="primary"
              icon={Send}
              disabled={busy || !allAnswersPresent}
              onClick={onCheckAnswers}
            >
              Check final answer
            </Button>
            {!checkpoint ? (
              <>
                <Button
                  icon={Lightbulb}
                  disabled={busy || hints.some((hint) => hint.stage === 1)}
                  onClick={() => onOpenHint(1)}
                >
                  Hint 1
                </Button>
                <Button
                  disabled={
                    busy ||
                    !hints.some((hint) => hint.stage === 1) ||
                    hints.some((hint) => hint.stage === 2)
                  }
                  onClick={() => onOpenHint(2)}
                >
                  Hint 2
                </Button>
              </>
            ) : null}
            {attempt?.solution_available && !checkpoint ? (
              <Button disabled={busy} onClick={onRevealSolution}>
                Give up and show solution
              </Button>
            ) : null}
          </>
        )}
        {!checkpoint ? (
          <TutorDock
            practiceSessionId={sessionId}
            questionKey={question.stable_key}
            questionRevision={question.revision}
            practiceMode={current.session.mode}
            wrongTries={wrongTries}
            solutionOpen={Boolean(solution)}
            questionLabel={`Question ${position}`}
          />
        ) : null}
        <QuestionReportForm
          appearance="nextscholar"
          sessionId={sessionId}
          questionKey={question.stable_key}
          questionRevision={question.revision}
        />
      </div>
    </article>
  );
}
