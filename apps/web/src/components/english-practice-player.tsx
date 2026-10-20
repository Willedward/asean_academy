"use client";

import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Lightbulb,
  RefreshCw,
  RotateCcw,
  Send,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

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
} from "@/beta-kit/components/ui";
import {
  classifyEnglishError,
  getNextEnglishQuestion,
  revealEnglishHint,
  submitEnglishAttempt,
  type EnglishAnswers,
  type EnglishAttemptResponse,
  type EnglishErrorCategory,
  type EnglishHintResponse,
  type EnglishNextQuestionResponse,
} from "@/lib/api/english";
import { cn } from "@/lib/utils";

type EnglishPracticeApi = {
  getNextQuestion: typeof getNextEnglishQuestion;
  submitAttempt: typeof submitEnglishAttempt;
  revealHint: typeof revealEnglishHint;
  classifyError: typeof classifyEnglishError;
};

const defaultApi: EnglishPracticeApi = {
  getNextQuestion: getNextEnglishQuestion,
  submitAttempt: submitEnglishAttempt,
  revealHint: revealEnglishHint,
  classifyError: classifyEnglishError,
};

const ERROR_OPTIONS: {
  key: EnglishErrorCategory;
  label: string;
  detail: string;
}[] = [
  {
    key: "unknown_meaning",
    label: "I did not know the word",
    detail: "The word or an option was unfamiliar.",
  },
  {
    key: "missed_clue",
    label: "I missed the clue",
    detail: "I overlooked evidence in the sentence or passage.",
  },
  {
    key: "option_trap",
    label: "I chose a tempting option",
    detail: "An option sounded plausible but did not fit the evidence.",
  },
  {
    key: "tone_mismatch",
    label: "I misread the tone",
    detail: "My answer did not match the writer's attitude or context.",
  },
];

function answerPresent(answer: string | string[] | undefined): boolean {
  return Array.isArray(answer) ? answer.length > 0 : Boolean(answer?.trim());
}

export function EnglishPracticePlayer({
  sessionId,
  api = defaultApi,
}: {
  sessionId: string;
  api?: EnglishPracticeApi;
}) {
  const [current, setCurrent] = useState<EnglishNextQuestionResponse | null>(
    null,
  );
  const [answers, setAnswers] = useState<EnglishAnswers>({});
  const [attempt, setAttempt] = useState<EnglishAttemptResponse | null>(null);
  const [hint, setHint] = useState<EnglishHintResponse | null>(null);
  const [classification, setClassification] =
    useState<EnglishErrorCategory | null>(null);
  const [classificationSaved, setClassificationSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadQuestion() {
    setBusy(true);
    try {
      const response = await api.getNextQuestion(sessionId);
      setCurrent(response);
      setAnswers({});
      setAttempt(null);
      setHint(null);
      setClassification(null);
      setClassificationSaved(false);
      setError(null);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "English practice could not be loaded.",
      );
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    let active = true;
    void api
      .getNextQuestion(sessionId)
      .then((response) => {
        if (active) setCurrent(response);
      })
      .catch((caught: unknown) => {
        if (active)
          setError(
            caught instanceof Error
              ? caught.message
              : "English practice could not be loaded.",
          );
      });
    return () => {
      active = false;
    };
  }, [api, sessionId]);

  const question = current?.question;
  const allAnswersPresent = useMemo(
    () =>
      Boolean(
        question?.parts.every((part) =>
          answerPresent(answers[String(part.position)]),
        ),
      ),
    [answers, question],
  );

  async function checkAnswer() {
    if (!question || !allAnswersPresent) return;
    setBusy(true);
    try {
      setAttempt(
        await api.submitAttempt(
          sessionId,
          question.stable_key,
          question.revision,
          answers,
        ),
      );
      setError(null);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Your answer could not be checked.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function openHint() {
    if (!question) return;
    setBusy(true);
    try {
      setHint(await api.revealHint(sessionId, question.stable_key));
      setError(null);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The hint could not be opened.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function saveClassification() {
    if (!attempt || !classification) return;
    setBusy(true);
    try {
      await api.classifyError(attempt.attempt_id, classification);
      setClassificationSaved(true);
      setError(null);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The reflection could not be saved.",
      );
    } finally {
      setBusy(false);
    }
  }

  function setSingle(position: number, value: string) {
    setAnswers((existing) => ({ ...existing, [String(position)]: value }));
  }

  function setBankedChoice(position: number, value: string) {
    setAnswers((existing) => {
      const next = { ...existing };
      for (const [key, answer] of Object.entries(next)) {
        if (key !== String(position) && answer === value) delete next[key];
      }
      if (value) next[String(position)] = value;
      else delete next[String(position)];
      return next;
    });
  }

  function toggleMultiple(position: number, value: string) {
    setAnswers((existing) => {
      const key = String(position);
      const selected = Array.isArray(existing[key]) ? existing[key] : [];
      return {
        ...existing,
        [key]: selected.includes(value)
          ? selected.filter((candidate) => candidate !== value)
          : [...selected, value],
      };
    });
  }

  if (error && !current) {
    return (
      <div role="alert">
        <Card className="items-start gap-4">
          <Tag tone="danger" icon={AlertTriangle}>
            Practice unavailable
          </Tag>
          <H2>We could not load this English practice session.</H2>
          <Muted>{error}</Muted>
          <Button icon={RefreshCw} onClick={() => void loadQuestion()}>
            Try again
          </Button>
        </Card>
      </div>
    );
  }

  if (!current) {
    return (
      <Card className="animate-pulse">
        <Muted>Loading English practice…</Muted>
      </Card>
    );
  }

  if (current.status === "completed" || !question) {
    const retryNeeded = current.session.incorrect_count > 0;
    return (
      <Card tone="success" className="items-center gap-4 py-10 text-center">
        <CheckCircle2 size={48} className="text-ns-success" aria-hidden />
        <Eyebrow>PRACTICE COMPLETE</Eyebrow>
        <H1>
          {current.session.correct_count} of {current.session.question_count}{" "}
          correct
        </H1>
        <Muted className="max-w-xl text-base leading-7">
          {retryNeeded
            ? "Review the feedback and return to this lesson when an exit ticket appears in your retry queue."
            : "You completed this English objective-practice session."}
        </Muted>
        <div className="flex flex-wrap justify-center gap-3">
          <Button variant="primary" href="/english">
            View English course
          </Button>
          <Button href={`/english/lessons/${current.session.lesson_key}`}>
            Return to lesson
          </Button>
        </div>
      </Card>
    );
  }

  const position = current.position ?? current.session.resolved_count + 1;
  const canContinue = Boolean(attempt?.correct || classificationSaved);
  const isBankedCloze =
    question.question_type === "banked_cloze" && Boolean(question.passage);
  const wordBank = question.word_bank ?? question.parts[0]?.options ?? [];
  const usedWords = new Map<string, number>();
  for (const part of question.parts) {
    const answer = answers[String(part.position)];
    if (typeof answer === "string" && answer)
      usedWords.set(answer, part.position);
  }

  function renderBankedParagraph(paragraph: string, paragraphIndex: number) {
    const fragments = paragraph.split(/(\{\{[1-9][0-9]*\}\})/g);
    return (
      <p key={paragraphIndex} className="m-0 text-[16px] leading-[3.25rem]">
        {fragments.map((fragment, fragmentIndex) => {
          const marker = fragment.match(/^\{\{([1-9][0-9]*)\}\}$/);
          if (!marker)
            return (
              <span key={`${paragraphIndex}-${fragmentIndex}`}>{fragment}</span>
            );
          const gap = Number(marker[1]);
          const selected = answers[String(gap)];
          const result = attempt?.parts.find((item) => item.position === gap);
          return (
            <span
              className={cn(
                "mx-1 inline-flex rounded-xl border-2 align-middle",
                result?.correct && "border-ns-success",
                result && !result.correct && "border-ns-danger",
                !result && "border-ns-line-strong",
              )}
              key={`${paragraphIndex}-gap-${gap}`}
            >
              <label className="sr-only" htmlFor={`banked-gap-${gap}`}>
                Gap {gap}
              </label>
              <select
                id={`banked-gap-${gap}`}
                aria-label={`Gap ${gap}`}
                aria-invalid={result ? !result.correct : undefined}
                value={typeof selected === "string" ? selected : ""}
                disabled={Boolean(attempt)}
                onChange={(event) => setBankedChoice(gap, event.target.value)}
                className={cn(
                  "h-10 min-w-32 rounded-[10px] border-0 bg-ns-raised px-3 text-[15px] font-semibold text-ns-ink",
                  focusRing,
                )}
              >
                <option value="">Gap {gap}</option>
                {wordBank.map((option) => (
                  <option key={option.key} value={option.key}>
                    {option.text}
                  </option>
                ))}
              </select>
            </span>
          );
        })}
      </p>
    );
  }

  return (
    <article className="flex flex-col gap-5 lg:gap-6">
      <Link
        href={`/english/lessons/${current.session.lesson_key}`}
        className="inline-flex items-center gap-2 self-start text-sm font-semibold text-ns-ink no-underline hover:underline"
      >
        <ArrowLeft size={17} aria-hidden /> Save and leave
      </Link>

      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <Eyebrow>
              {current.session.mode === "retry_review"
                ? "RETRY REVIEW"
                : "ENGLISH PRACTICE"}
            </Eyebrow>
            <H1>
              Question {position} of {current.session.question_count}
            </H1>
          </div>
          <div className="flex gap-2">
            <Tag>Difficulty {question.difficulty}</Tag>
            <Tag tone="brand">{question.outcome_code}</Tag>
          </div>
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
          <span>These questions remain hidden from production learners.</span>
        </Callout>
      ) : null}

      {question.passage ? (
        <Card tone="sunken" className="gap-4">
          <Eyebrow>
            {isBankedCloze
              ? "BANKED STORY CLOZE"
              : question.passage.text_type.toUpperCase()}
          </Eyebrow>
          <H2>{isBankedCloze ? question.title : question.passage.title}</H2>
          {isBankedCloze ? (
            <>
              <p className="m-0 text-[16px] leading-7">
                {question.instructions}
              </p>
              <section
                aria-labelledby="word-bank-heading"
                className="rounded-xl border border-ns-line bg-ns-raised p-4"
              >
                <h3
                  id="word-bank-heading"
                  className="m-0 text-sm font-bold uppercase tracking-wide text-ns-muted"
                >
                  Word bank · {wordBank.length} words for{" "}
                  {question.parts.length} gaps
                </h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {wordBank.map((option) => {
                    const usedAt = usedWords.get(option.key);
                    return (
                      <span
                        key={option.key}
                        className={cn(
                          "rounded-full border px-3 py-1.5 text-sm font-semibold",
                          usedAt
                            ? "border-ns-ink bg-ns-brand-soft text-ns-ink"
                            : "border-ns-line-strong bg-ns-raised text-ns-muted",
                        )}
                      >
                        {option.text}
                        {usedAt ? ` · gap ${usedAt}` : ""}
                      </span>
                    );
                  })}
                </div>
              </section>
              <Divider />
              <h3 className="m-0 text-lg font-bold">
                {question.passage.title}
              </h3>
              {question.passage.paragraphs.map(renderBankedParagraph)}
            </>
          ) : (
            question.passage.paragraphs.map((paragraph) => (
              <p key={paragraph} className="m-0 text-[16px] leading-7">
                {paragraph}
              </p>
            ))
          )}
          {question.passage.attribution ? (
            <Muted className="text-xs">{question.passage.attribution}</Muted>
          ) : null}
        </Card>
      ) : null}

      <Card className="gap-4">
        {isBankedCloze ? (
          <>
            <H2>{attempt ? "Passage feedback" : "Complete every gap"}</H2>
            {!attempt ? (
              <Muted>
                {Object.keys(answers).length} of {question.parts.length} gaps
                answered. You can clear or change any answer before checking the
                whole passage.
              </Muted>
            ) : null}
            {hint ? (
              <Callout tone="amber" icon={Lightbulb}>
                <strong>Gap hints</strong>
                <ol className="m-0 space-y-1 pl-5">
                  {hint.parts.map((partHint, index) => (
                    <li key={index}>{partHint}</li>
                  ))}
                </ol>
              </Callout>
            ) : null}
            {attempt ? (
              <ol
                className="m-0 grid gap-3 p-0 sm:grid-cols-2"
                aria-label="Passage feedback"
              >
                {attempt.parts.map((result) => (
                  <li className="list-none" key={result.position}>
                    <Callout
                      tone={result.correct ? "success" : "amber"}
                      icon={result.correct ? CheckCircle2 : AlertTriangle}
                    >
                      <strong>
                        Gap {result.position}:{" "}
                        {result.correct ? "Correct" : "Review the clue"}
                      </strong>
                      <span>{result.feedback}</span>
                    </Callout>
                  </li>
                ))}
              </ol>
            ) : null}
          </>
        ) : (
          <>
            <H2>{question.title}</H2>
            <p className="m-0 text-[16px] leading-7">{question.instructions}</p>
            <Divider />
            {question.parts.map((part) => {
              const key = String(part.position);
              const selected = answers[key];
              const result = attempt?.parts.find(
                (item) => item.position === part.position,
              );
              return (
                <fieldset
                  key={part.position}
                  className="m-0 flex min-w-0 flex-col gap-3 border-0 p-0"
                >
                  <legend className="mb-2 text-[16px] font-semibold leading-6">
                    {part.prompt}
                  </legend>
                  {part.response_type === "short_text" ? (
                    <input
                      value={typeof selected === "string" ? selected : ""}
                      onChange={(event) =>
                        setSingle(part.position, event.target.value)
                      }
                      disabled={Boolean(attempt)}
                      maxLength={1000}
                      className={cn(
                        "h-12 rounded-xl border border-ns-line-strong bg-ns-raised px-4 text-base",
                        focusRing,
                      )}
                      aria-label={`Answer for part ${part.position}`}
                    />
                  ) : (
                    <div className="grid gap-2">
                      {part.options.map((option) => {
                        const checked = Array.isArray(selected)
                          ? selected.includes(option.key)
                          : selected === option.key;
                        return (
                          <label
                            key={option.key}
                            className={cn(
                              "flex cursor-pointer items-start gap-3 rounded-xl border p-3 text-[15px] leading-6",
                              checked
                                ? "border-ns-ink bg-ns-brand-soft"
                                : "border-ns-line bg-ns-raised hover:bg-ns-sunken",
                              attempt && "cursor-default",
                            )}
                          >
                            <input
                              type={
                                part.response_type === "single_choice"
                                  ? "radio"
                                  : "checkbox"
                              }
                              name={`part-${part.position}`}
                              value={option.key}
                              checked={checked}
                              disabled={Boolean(attempt)}
                              onChange={() =>
                                part.response_type === "single_choice"
                                  ? setSingle(part.position, option.key)
                                  : toggleMultiple(part.position, option.key)
                              }
                              className="mt-1"
                            />
                            <span>
                              <strong>{option.key}.</strong> {option.text}
                            </span>
                          </label>
                        );
                      })}
                    </div>
                  )}
                  {hint?.parts[part.position - 1] ? (
                    <Callout tone="amber" icon={Lightbulb}>
                      <span>{hint.parts[part.position - 1]}</span>
                    </Callout>
                  ) : null}
                  {result ? (
                    <Callout
                      tone={result.correct ? "success" : "amber"}
                      icon={result.correct ? CheckCircle2 : AlertTriangle}
                    >
                      <strong>
                        {result.correct ? "Correct" : "Check the evidence"}
                      </strong>
                      <span>{result.feedback}</span>
                    </Callout>
                  ) : null}
                </fieldset>
              );
            })}
          </>
        )}
      </Card>

      {attempt?.needs_error_classification ? (
        <Card className="gap-4">
          <div>
            <Eyebrow>ONE-MINUTE REFLECTION</Eyebrow>
            <H2>What caused this mistake?</H2>
          </div>
          <Muted>
            Choose the closest reason. This makes later review more useful.
          </Muted>
          <div className="grid gap-2 sm:grid-cols-2">
            {ERROR_OPTIONS.map((option) => (
              <label
                key={option.key}
                className={cn(
                  "flex cursor-pointer gap-3 rounded-xl border p-3",
                  classification === option.key
                    ? "border-ns-ink bg-ns-brand-soft"
                    : "border-ns-line bg-ns-raised",
                  classificationSaved && "cursor-default",
                )}
              >
                <input
                  type="radio"
                  name="error-category"
                  checked={classification === option.key}
                  disabled={classificationSaved}
                  onChange={() => setClassification(option.key)}
                />
                <span>
                  <strong className="block text-sm">{option.label}</strong>
                  <span className="block text-xs leading-5 text-ns-muted">
                    {option.detail}
                  </span>
                </span>
              </label>
            ))}
          </div>
          {classificationSaved ? (
            <Tag tone="success" icon={CheckCircle2}>
              Reflection saved
            </Tag>
          ) : (
            <Button
              disabled={!classification || busy}
              onClick={() => void saveClassification()}
            >
              Save reflection
            </Button>
          )}
          {attempt.retry_queued ? (
            <Callout tone="amber" icon={RotateCcw}>
              <strong>Exit ticket queued</strong>
              <span>This question will appear in retry review.</span>
            </Callout>
          ) : null}
        </Card>
      ) : null}

      {error ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <span>{error}</span>
        </Callout>
      ) : null}

      <div className="flex flex-wrap justify-end gap-3">
        {!attempt && !hint ? (
          <Button
            icon={Lightbulb}
            disabled={busy}
            onClick={() => void openHint()}
          >
            Show hint
          </Button>
        ) : null}
        {!attempt ? (
          <Button
            variant="primary"
            iconRight={Send}
            disabled={!allAnswersPresent || busy}
            onClick={() => void checkAnswer()}
          >
            Check answer
          </Button>
        ) : (
          <Button
            variant="primary"
            iconRight={RefreshCw}
            disabled={!canContinue || busy}
            onClick={() => void loadQuestion()}
          >
            Continue
          </Button>
        )}
      </div>
    </article>
  );
}
