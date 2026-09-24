"use client";

import {
  ArrowLeft,
  CheckCircle2,
  CircleAlert,
  Lightbulb,
  RefreshCw,
  Send,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { MathContent, type ContentBlock } from "@/components/math-content";
import { Button } from "@/components/ui/button";
import {
  getNextQuestion,
  giveUp,
  revealHint,
  submitAttempt,
  type AttemptResponse,
  type GiveUpResponse,
  type HintResponse,
  type NextQuestionResponse,
} from "@/lib/api/practice";

type PracticeApi = {
  getNextQuestion: typeof getNextQuestion;
  submitAttempt: typeof submitAttempt;
  revealHint: typeof revealHint;
  giveUp: typeof giveUp;
};

const defaultApi: PracticeApi = {
  getNextQuestion,
  submitAttempt,
  revealHint,
  giveUp,
};

export function PracticePlayer({
  sessionId,
  api = defaultApi,
}: {
  sessionId: string;
  api?: PracticeApi;
}) {
  const [current, setCurrent] = useState<NextQuestionResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [attempt, setAttempt] = useState<AttemptResponse | null>(null);
  const [hints, setHints] = useState<HintResponse[]>([]);
  const [solution, setSolution] = useState<GiveUpResponse["solution"] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function loadQuestion() {
    setBusy(true);
    try {
      const response = await api.getNextQuestion(sessionId);
      setCurrent(response);
      setAnswers({});
      setAttempt(null);
      setHints([]);
      setSolution(null);
      setError(null);
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Practice could not be loaded.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    let active = true;
    void api
      .getNextQuestion(sessionId)
      .then((response) => {
        if (active) {
          setCurrent(response);
          setError(null);
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(
            caught instanceof Error ? caught.message : "Practice could not be loaded.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [api, sessionId]);

  const question = current?.question;
  const allAnswersPresent = useMemo(
    () =>
      Boolean(
        question?.parts.every((part) => (answers[String(part.position)] ?? "").trim()),
      ),
    [answers, question],
  );

  async function checkAnswers() {
    if (!question || !allAnswersPresent) return;
    setBusy(true);
    try {
      const response = await api.submitAttempt(
        sessionId,
        question.stable_key,
        question.revision,
        answers,
      );
      setAttempt(response);
      setError(null);
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "The answer could not be checked.");
    } finally {
      setBusy(false);
    }
  }

  async function openHint(stage: 1 | 2) {
    if (!question) return;
    setBusy(true);
    try {
      const response = await api.revealHint(sessionId, question.stable_key, stage);
      setHints((existing) => [
        ...existing.filter((hint) => hint.stage !== response.stage),
        response,
      ]);
      setError(null);
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "The hint could not be opened.");
    } finally {
      setBusy(false);
    }
  }

  async function revealSolution() {
    if (!question) return;
    setBusy(true);
    try {
      const response = await api.giveUp(sessionId, question.stable_key);
      setSolution(response.solution);
      setError(null);
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "The solution could not be opened.");
    } finally {
      setBusy(false);
    }
  }

  if (error && !current) {
    return (
      <div className="status-card border-rose-200 bg-rose-50" role="alert">
        <CircleAlert aria-hidden="true" className="size-5 text-rose-700" />
        <div className="grow">
          <p className="status-title">Practice unavailable</p>
          <p className="status-copy">{error}</p>
        </div>
        <Button variant="outline" onClick={() => void loadQuestion()}>
          <RefreshCw aria-hidden="true" className="mr-2 size-4" />
          Retry
        </Button>
      </div>
    );
  }

  if (!current) {
    return <div className="status-card animate-pulse" role="status">Loading practice…</div>;
  }

  if (current.status === "completed" || !question) {
    return (
      <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-8 text-center">
        <CheckCircle2 aria-hidden="true" className="mx-auto size-12 text-emerald-700" />
        <h1 className="text-3xl font-black">Practice complete</h1>
        <p className="text-slate-700">
          You resolved {current.session.resolved_count} of {current.session.question_count} questions.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Button asChild>
            <Link href="/progress">View progress</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={`/lessons/${current.session.lesson_key}`}>Return to lesson</Link>
          </Button>
        </div>
      </section>
    );
  }

  return (
    <article className="space-y-6">
      <Link
        className="inline-flex items-center gap-2 text-sm font-semibold text-teal-800 hover:underline"
        href={`/lessons/${current.session.lesson_key}`}
      >
        <ArrowLeft aria-hidden="true" className="size-4" />
        Exit practice
      </Link>

      {current.session.development_drafts ? (
        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">
          <strong>Development practice.</strong> These questions are drafts and are not available to production learners.
        </div>
      ) : null}

      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="mb-1 text-sm font-bold uppercase tracking-wide text-teal-700">
            {current.stage?.replace("_", " ") ?? "Practice"} · Question {current.position} of {current.session.question_count}
          </p>
          <h1 className="m-0 text-3xl font-black tracking-tight">{question.title}</h1>
        </div>
        <span className="rounded-full bg-slate-200 px-3 py-1 text-sm font-semibold">
          {question.total_marks} {question.total_marks === 1 ? "mark" : "marks"}
        </span>
      </header>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        {question.stem.length ? (
          <p className="mt-0 text-lg leading-8">
            <MathContent blocks={question.stem as ContentBlock[]} />
          </p>
        ) : null}

        <div className="space-y-7">
          {question.parts.map((part) => {
            const result = attempt?.parts.find((candidate) => candidate.position === part.position);
            return (
              <fieldset className="border-0 p-0" key={part.position}>
                <legend className="mb-3 text-lg font-semibold leading-8">
                  {part.label ? <span className="mr-2">({part.label})</span> : null}
                  <MathContent blocks={part.prompt as ContentBlock[]} />
                  <span className="ml-2 text-sm font-normal text-slate-500">[{part.marks}]</span>
                </legend>
                <label className="block text-sm font-bold text-slate-700" htmlFor={`answer-${part.position}`}>
                  Final answer
                </label>
                <input
                  autoComplete="off"
                  className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-lg outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-200"
                  disabled={Boolean(attempt?.correct || solution)}
                  id={`answer-${part.position}`}
                  maxLength={500}
                  onChange={(event) =>
                    setAnswers((existing) => ({
                      ...existing,
                      [String(part.position)]: event.target.value,
                    }))
                  }
                  placeholder={part.input_placeholder}
                  value={answers[String(part.position)] ?? ""}
                />
                {result?.error ? (
                  <p className="mb-0 mt-2 text-sm text-rose-700">{result.error}</p>
                ) : null}
              </fieldset>
            );
          })}
        </div>
      </section>

      {hints.map((hint) => (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5" key={hint.stage}>
          <h2 className="mt-0 text-lg font-extrabold">Hint {hint.stage}</h2>
          {hint.parts.map((part) => (
            <p className="mb-0 leading-7" key={part.position}>
              <MathContent blocks={part.content as ContentBlock[]} />
            </p>
          ))}
        </section>
      ))}

      {attempt ? (
        <section
          className={`rounded-2xl border p-5 ${
            attempt.correct
              ? "border-emerald-200 bg-emerald-50"
              : "border-rose-200 bg-rose-50"
          }`}
          role="status"
        >
          <h2 className="mt-0 text-xl font-extrabold">
            {attempt.correct ? "Correct" : "Try again"}
          </h2>
          <p className="mb-0">
            {attempt.correct
              ? `You earned ${attempt.marks_awarded} of ${attempt.marks_available} marks.`
              : "That final answer is not correct yet. You can retry or open an authored hint."}
          </p>
        </section>
      ) : null}

      {solution ? (
        <section className="rounded-2xl border border-sky-200 bg-sky-50 p-5">
          <h2 className="mt-0 text-xl font-extrabold">Worked solution</h2>
          {solution.parts.map((part) => (
            <div className="space-y-3" key={part.position}>
              <p className="font-semibold">
                Answer: <MathContent blocks={[{ type: "inline_math", latex: part.canonical_latex }]} />
              </p>
              {part.steps.map((step, index) => {
                const content = Array.isArray(step.content) ? step.content : [];
                return (
                  <div className="rounded-xl bg-white p-4 leading-7" key={index}>
                    <MathContent blocks={content as ContentBlock[]} />
                  </div>
                );
              })}
            </div>
          ))}
        </section>
      ) : null}

      {error ? <p className="text-sm font-semibold text-rose-700" role="alert">{error}</p> : null}

      <div className="flex flex-wrap gap-3">
        {attempt?.correct || solution ? (
          <Button disabled={busy} onClick={() => void loadQuestion()}>
            Continue
          </Button>
        ) : (
          <>
            <Button disabled={busy || !allAnswersPresent} onClick={() => void checkAnswers()}>
              <Send aria-hidden="true" className="mr-2 size-4" />
              Check final answer
            </Button>
            <Button
              disabled={busy || hints.some((hint) => hint.stage === 1)}
              onClick={() => void openHint(1)}
              variant="outline"
            >
              <Lightbulb aria-hidden="true" className="mr-2 size-4" />
              Hint 1
            </Button>
            <Button
              disabled={busy || !hints.some((hint) => hint.stage === 1) || hints.some((hint) => hint.stage === 2)}
              onClick={() => void openHint(2)}
              variant="outline"
            >
              Hint 2
            </Button>
            {attempt?.solution_available ? (
              <Button disabled={busy} onClick={() => void revealSolution()} variant="outline">
                Give up and show solution
              </Button>
            ) : null}
          </>
        )}
      </div>
    </article>
  );
}
