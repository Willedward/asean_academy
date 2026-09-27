"use client";

import {
  BookOpenText,
  Brain,
  Check,
  CheckCircle2,
  CircleAlert,
  ListChecks,
  Send,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { MathContent, type ContentBlock } from "@/components/math-content";
import { Button } from "@/components/ui/button";
import {
  checkLessonActiveRecall,
  getLessonSectionProgress,
  setLessonSectionCompletion,
  type ActiveRecallAttemptResponse,
  type LessonSectionProgressResponse,
} from "@/lib/api/progress";

type BaseSection = {
  stable_key: string;
  position: number;
  title: string;
};

type ExplanationSection = BaseSection & {
  type: "explanation";
  blocks: ContentBlock[];
};

type WorkedExampleSection = BaseSection & {
  type: "worked_example";
  prompt: ContentBlock[];
  steps: { position: number; content: ContentBlock[] }[];
  verification_note: string;
};

type ActiveRecallSection = BaseSection & {
  type: "active_recall";
  prompt: ContentBlock[];
  response_type: "numeric" | "algebraic_expression";
};

type SummarySection = BaseSection & {
  type: "summary";
  blocks: ContentBlock[];
};

export type LessonSection =
  | ExplanationSection
  | WorkedExampleSection
  | ActiveRecallSection
  | SummarySection;

export type LessonContentApi = {
  getProgress: typeof getLessonSectionProgress;
  setCompletion: typeof setLessonSectionCompletion;
  checkRecall: typeof checkLessonActiveRecall;
};

const defaultApi: LessonContentApi = {
  getProgress: getLessonSectionProgress,
  setCompletion: setLessonSectionCompletion,
  checkRecall: checkLessonActiveRecall,
};

function SectionLabel({ section }: { section: LessonSection }) {
  if (section.type === "worked_example") {
    return <><ListChecks aria-hidden="true" className="size-4" />Worked example</>;
  }
  if (section.type === "active_recall") {
    return <><Brain aria-hidden="true" className="size-4" />Active recall</>;
  }
  if (section.type === "summary") {
    return <><CheckCircle2 aria-hidden="true" className="size-4" />Summary</>;
  }
  return <><BookOpenText aria-hidden="true" className="size-4" />Explanation</>;
}

function CompletionButton({
  busy,
  completed,
  onClick,
}: {
  busy: boolean;
  completed: boolean;
  onClick: () => void;
}) {
  return (
    <Button aria-pressed={completed} disabled={busy} onClick={onClick} variant="outline">
      {completed ? <Check aria-hidden="true" className="mr-2 size-4" /> : null}
      {busy
        ? "Saving…"
        : completed
          ? "Mark section incomplete"
          : "Mark section complete"}
    </Button>
  );
}

function RecallCheck({
  busy,
  completed,
  result,
  section,
  value,
  onChange,
  onSubmit,
}: {
  busy: boolean;
  completed: boolean;
  result?: ActiveRecallAttemptResponse;
  section: ActiveRecallSection;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
}) {
  const inputId = `recall-${section.stable_key}`;
  return (
    <div className="mt-5 border-t border-teal-200 pt-5">
      <label className="block text-sm font-bold text-slate-800" htmlFor={inputId}>
        Your answer
      </label>
      <div className="mt-2 flex flex-col gap-3 sm:flex-row">
        <input
          autoComplete="off"
          className="min-w-0 grow rounded-xl border border-slate-300 bg-white px-4 py-3 text-lg outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-200"
          id={inputId}
          maxLength={500}
          onChange={(event) => onChange(event.target.value)}
          placeholder={
            section.response_type === "numeric"
              ? "Enter a number"
              : "For example: 2^2 * 3 * 7"
          }
          value={value}
        />
        <Button disabled={busy || !value.trim()} onClick={onSubmit}>
          <Send aria-hidden="true" className="mr-2 size-4" />
          {busy ? "Checking…" : "Check answer"}
        </Button>
      </div>
      {result ? (
        <div
          className={`mt-4 rounded-xl border p-4 ${
            result.correct
              ? "border-emerald-200 bg-emerald-50 text-emerald-950"
              : "border-rose-200 bg-rose-50 text-rose-950"
          }`}
          role="status"
        >
          <p className="m-0 font-bold">{result.correct ? "Correct" : "Try again"}</p>
          {!result.correct ? (
            <p className="mb-0 mt-1 text-sm">
              {result.error ?? "That answer is not correct yet. Check your prime factors and try again."}
            </p>
          ) : null}
          {result.correct && result.feedback.length ? (
            <p className="mb-0 mt-2 leading-7">
              <MathContent blocks={result.feedback as ContentBlock[]} />
            </p>
          ) : null}
        </div>
      ) : completed ? (
        <p className="mb-0 mt-3 inline-flex items-center gap-2 text-sm font-semibold text-emerald-800">
          <CheckCircle2 aria-hidden="true" className="size-4" />
          Recall check completed
        </p>
      ) : (
        <p className="mb-0 mt-3 text-sm text-slate-600">
          A correct answer completes this section. It does not affect your practice marks.
        </p>
      )}
    </div>
  );
}

export function LessonContent({
  api = defaultApi,
  lessonKey,
  sections,
}: {
  api?: LessonContentApi;
  lessonKey: string;
  sections: LessonSection[];
}) {
  const [progress, setProgress] = useState<LessonSectionProgressResponse | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [recallResults, setRecallResults] = useState<
    Record<string, ActiveRecallAttemptResponse>
  >({});

  useEffect(() => {
    let active = true;
    void api
      .getProgress(lessonKey)
      .then((response) => {
        if (active) {
          setProgress(response);
          setError(null);
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Section progress could not be loaded.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [api, lessonKey]);

  const completed = useMemo(
    () => new Set(progress?.completed_section_keys ?? []),
    [progress],
  );
  const completedCount = progress?.completed_count ?? 0;
  const percentage = sections.length
    ? Math.round((100 * completedCount) / sections.length)
    : 0;

  async function toggleCompletion(sectionKey: string) {
    const nextCompleted = !completed.has(sectionKey);
    setBusyKey(sectionKey);
    try {
      const response = await api.setCompletion(
        lessonKey,
        sectionKey,
        nextCompleted,
      );
      setProgress(response);
      setError(null);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error ? caught.message : "Section progress could not be saved.",
      );
    } finally {
      setBusyKey(null);
    }
  }

  async function checkRecall(sectionKey: string) {
    setBusyKey(sectionKey);
    try {
      const response = await api.checkRecall(
        lessonKey,
        sectionKey,
        answers[sectionKey] ?? "",
      );
      setRecallResults((existing) => ({ ...existing, [sectionKey]: response }));
      setProgress(response.progress);
      setError(null);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error ? caught.message : "The recall answer could not be checked.",
      );
    } finally {
      setBusyKey(null);
    }
  }

  return (
    <section className="space-y-5" aria-labelledby="lesson-notes-title">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="mb-1 text-sm font-bold uppercase tracking-[0.12em] text-teal-700">
              Lesson notes
            </p>
            <h2 id="lesson-notes-title" className="m-0 text-2xl font-black">
              Learn the ideas, then practise them
            </h2>
          </div>
          <p className="m-0 text-sm font-semibold text-slate-600">
            {completedCount} of {sections.length} sections complete
          </p>
        </div>
        <div
          aria-label={`${percentage}% of lesson-note sections complete`}
          aria-valuemax={100}
          aria-valuemin={0}
          aria-valuenow={percentage}
          className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200"
          role="progressbar"
        >
          <div
            className="h-full rounded-full bg-teal-600 transition-[width]"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {error ? (
        <div className="status-card border-amber-200 bg-amber-50" role="alert">
          <CircleAlert aria-hidden="true" className="size-5 text-amber-700" />
          <div>
            <p className="status-title">Progress is temporarily unavailable</p>
            <p className="status-copy">{error} You can continue reading the notes.</p>
          </div>
        </div>
      ) : null}

      {sections.map((section) => {
        const isCompleted = completed.has(section.stable_key);
        const isBusy = busyKey === section.stable_key;
        return (
          <article
            className={`rounded-3xl border bg-white p-6 shadow-sm sm:p-8 ${
              section.type === "active_recall"
                ? "border-teal-200 bg-teal-50/60"
                : section.type === "summary"
                  ? "border-sky-200 bg-sky-50/60"
                  : "border-slate-200"
            }`}
            id={section.stable_key}
            key={section.stable_key}
          >
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <p className="m-0 inline-flex items-center gap-2 text-xs font-extrabold uppercase tracking-[0.12em] text-teal-700">
                <SectionLabel section={section} />
              </p>
              {isCompleted ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800">
                  <Check aria-hidden="true" className="size-3.5" />Complete
                </span>
              ) : null}
            </div>
            <h3 className="mt-0 text-2xl font-extrabold tracking-tight">
              {section.title}
            </h3>

            {section.type === "explanation" || section.type === "summary" ? (
              <div className="whitespace-pre-line text-base leading-8 text-slate-700">
                <MathContent blocks={section.blocks} />
              </div>
            ) : null}

            {section.type === "worked_example" ? (
              <div>
                <div className="rounded-2xl bg-slate-100 p-4 text-lg font-semibold leading-8">
                  <MathContent blocks={section.prompt} />
                </div>
                <ol className="mt-5 space-y-4 pl-0">
                  {section.steps.map((step) => (
                    <li className="flex gap-4" key={step.position}>
                      <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-teal-700 text-sm font-bold text-white">
                        {step.position}
                      </span>
                      <div className="min-w-0 grow whitespace-pre-line pt-0.5 leading-8 text-slate-700">
                        <MathContent blocks={step.content} />
                      </div>
                    </li>
                  ))}
                </ol>
                <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-950">
                  <strong>Check:</strong> {section.verification_note}
                </div>
              </div>
            ) : null}

            {section.type === "active_recall" ? (
              <>
                <p className="text-lg leading-8 text-slate-800">
                  <MathContent blocks={section.prompt} />
                </p>
                <RecallCheck
                  busy={isBusy}
                  completed={isCompleted}
                  onChange={(value) =>
                    setAnswers((existing) => ({
                      ...existing,
                      [section.stable_key]: value,
                    }))
                  }
                  onSubmit={() => void checkRecall(section.stable_key)}
                  result={recallResults[section.stable_key]}
                  section={section}
                  value={answers[section.stable_key] ?? ""}
                />
              </>
            ) : (
              <div className="mt-6">
                <CompletionButton
                  busy={isBusy}
                  completed={isCompleted}
                  onClick={() => void toggleCompletion(section.stable_key)}
                />
              </div>
            )}
          </article>
        );
      })}
    </section>
  );
}
