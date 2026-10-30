"use client";

import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  Button,
  Callout,
  Card,
  Eyebrow,
  H1,
  H2,
  Muted,
  Steps,
  Tag,
  focusRing,
} from "@/beta-kit/components/ui";
import {
  getNextEnglishDiagnosticQuestion,
  submitEnglishDiagnosticAttempt,
  type EnglishAnswers,
  type EnglishDiagnosticNextQuestionResponse,
} from "@/lib/api/english";
import { cn } from "@/lib/utils";

type EnglishDiagnosticApi = {
  getNextQuestion: typeof getNextEnglishDiagnosticQuestion;
  submitAttempt: typeof submitEnglishDiagnosticAttempt;
};

const defaultApi: EnglishDiagnosticApi = {
  getNextQuestion: getNextEnglishDiagnosticQuestion,
  submitAttempt: submitEnglishDiagnosticAttempt,
};

function present(answer: string | string[] | undefined): boolean {
  return Array.isArray(answer) ? answer.length > 0 : Boolean(answer?.trim());
}

export function EnglishDiagnosticPlayer({
  sessionId,
  api = defaultApi,
}: {
  sessionId: string;
  api?: EnglishDiagnosticApi;
}) {
  const router = useRouter();
  const [current, setCurrent] =
    useState<EnglishDiagnosticNextQuestionResponse | null>(null);
  const [answers, setAnswers] = useState<EnglishAnswers>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setBusy(true);
    try {
      const response = await api.getNextQuestion(sessionId);
      if (response.status === "completed") {
        router.replace(`/english/diagnostics/${sessionId}/result`);
        return;
      }
      setCurrent(response);
      setAnswers({});
      setError(null);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The English diagnostic could not be loaded.",
      );
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    let active = true;
    void api.getNextQuestion(sessionId).then(
      (response) => {
        if (!active) return;
        if (response.status === "completed") {
          router.replace(`/english/diagnostics/${sessionId}/result`);
          return;
        }
        setCurrent(response);
        setError(null);
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
  }, [api, router, sessionId]);

  const question = current?.question;
  const complete = useMemo(
    () =>
      Boolean(
        question?.parts.every((part) =>
          present(answers[String(part.position)]),
        ),
      ),
    [answers, question],
  );

  function setSingle(position: number, value: string) {
    setAnswers((existing) => ({ ...existing, [String(position)]: value }));
  }

  function setBanked(position: number, value: string) {
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

  async function submit() {
    if (!question || !complete) return;
    setBusy(true);
    try {
      const response = await api.submitAttempt(
        sessionId,
        question.stable_key,
        question.revision,
        answers,
      );
      if (response.diagnostic_completed) {
        router.replace(`/english/diagnostics/${sessionId}/result`);
      } else {
        await load();
      }
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Your response could not be saved.",
      );
      setBusy(false);
    }
  }

  if (error && !current) {
    return (
      <div role="alert">
        <Card className="items-start gap-4">
          <Tag tone="danger" icon={AlertTriangle}>
            Diagnostic unavailable
          </Tag>
          <H2>We could not load this English diagnostic.</H2>
          <Muted>{error}</Muted>
          <Button icon={RefreshCw} onClick={() => void load()}>
            Try again
          </Button>
        </Card>
      </div>
    );
  }
  if (!current || !question) {
    return (
      <Card className="animate-pulse">
        <Muted>Loading protected English diagnostic…</Muted>
      </Card>
    );
  }

  const position = current.position ?? current.session.resolved_count + 1;
  const banked = question.question_type === "banked_cloze";
  const openCloze = question.question_type === "open_cloze";
  const wordBank = question.word_bank ?? [];

  function renderClozeParagraph(paragraph: string, paragraphIndex: number) {
    return (
      <p key={paragraphIndex} className="m-0 text-[16px] leading-[3.5rem]">
        {paragraph.split(/(\{\{[1-9][0-9]*\}\})/g).map((fragment, index) => {
          const marker = fragment.match(/^\{\{([1-9][0-9]*)\}\}$/);
          if (!marker) return <span key={index}>{fragment}</span>;
          const gap = Number(marker[1]);
          const answer = answers[String(gap)];
          return (
            <span key={`gap-${gap}`} className="mx-1 inline-flex align-middle">
              <label className="sr-only" htmlFor={`diagnostic-gap-${gap}`}>
                Gap {gap}
              </label>
              {banked ? (
                <select
                  id={`diagnostic-gap-${gap}`}
                  value={typeof answer === "string" ? answer : ""}
                  onChange={(event) => setBanked(gap, event.target.value)}
                  className={cn(
                    "h-10 min-w-32 rounded-xl border border-ns-line-strong bg-ns-raised px-3 font-semibold",
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
              ) : (
                <input
                  id={`diagnostic-gap-${gap}`}
                  value={typeof answer === "string" ? answer : ""}
                  onChange={(event) => setSingle(gap, event.target.value)}
                  autoComplete="off"
                  spellCheck={false}
                  maxLength={32}
                  placeholder={String(gap)}
                  className={cn(
                    "h-10 w-28 rounded-xl border border-ns-line-strong bg-ns-raised px-3 text-center font-semibold",
                    focusRing,
                  )}
                />
              )}
            </span>
          );
        })}
      </p>
    );
  }

  return (
    <article className="flex flex-col gap-5 lg:gap-6">
      <Link
        href="/english"
        className="inline-flex items-center gap-2 self-start text-sm font-semibold text-ns-ink"
      >
        <ArrowLeft size={17} aria-hidden /> Leave and return later
      </Link>
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <Eyebrow>
              {current.session.purpose.toUpperCase()} · PROTECTED DIAGNOSTIC
            </Eyebrow>
            <H1>
              Question group {position} of {current.session.question_count}
            </H1>
          </div>
          <Tag icon={ShieldCheck}>No feedback during the form</Tag>
        </div>
        <Steps
          done={position - 1}
          current={position - 1}
          total={current.session.question_count}
        />
      </div>
      {current.session.development_drafts ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <strong>Development diagnostic</strong>
          <span>
            This form remains hidden from production learners until review is
            complete.
          </span>
        </Callout>
      ) : null}
      {error ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <span>{error}</span>
        </Callout>
      ) : null}

      <Card className="gap-5">
        <div>
          <Eyebrow>{question.question_type.replaceAll("_", " ")}</Eyebrow>
          <H2>{question.title}</H2>
          <Muted className="mt-1">{question.instructions}</Muted>
        </div>
        {question.passage ? (
          <section
            className="rounded-2xl bg-ns-sunken p-5"
            aria-label={question.passage.title}
          >
            {!banked && !openCloze ? <H2>{question.passage.title}</H2> : null}
            <div className="mt-3 flex flex-col gap-4 text-ns-ink">
              {question.passage.paragraphs.map((paragraph, index) =>
                banked || openCloze ? (
                  renderClozeParagraph(paragraph, index)
                ) : (
                  <p key={index} className="m-0 leading-7">
                    {paragraph}
                  </p>
                ),
              )}
            </div>
          </section>
        ) : null}

        {!banked && !openCloze ? (
          <div className="flex flex-col gap-5">
            {question.parts.map((part) => (
              <fieldset
                key={part.position}
                className="m-0 rounded-2xl border border-ns-line p-4"
              >
                <legend className="px-2 font-semibold text-ns-ink">
                  {part.position}. {part.prompt}
                </legend>
                {part.response_type === "short_text" ? (
                  <input
                    aria-label={`Answer ${part.position}`}
                    value={
                      typeof answers[String(part.position)] === "string"
                        ? (answers[String(part.position)] as string)
                        : ""
                    }
                    onChange={(event) =>
                      setSingle(part.position, event.target.value)
                    }
                    autoComplete="off"
                    className={cn(
                      "mt-3 h-11 w-full rounded-xl border border-ns-line-strong px-3",
                      focusRing,
                    )}
                  />
                ) : (
                  <div className="mt-3 grid gap-2">
                    {part.options.map((option) => {
                      const value = answers[String(part.position)];
                      const checked = Array.isArray(value)
                        ? value.includes(option.key)
                        : value === option.key;
                      return (
                        <label
                          key={option.key}
                          className="flex cursor-pointer items-start gap-3 rounded-xl border border-ns-line p-3 hover:bg-ns-sunken"
                        >
                          <input
                            type={
                              part.response_type === "multiple_response"
                                ? "checkbox"
                                : "radio"
                            }
                            name={`part-${part.position}`}
                            value={option.key}
                            checked={checked}
                            onChange={() =>
                              part.response_type === "multiple_response"
                                ? toggleMultiple(part.position, option.key)
                                : setSingle(part.position, option.key)
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
              </fieldset>
            ))}
          </div>
        ) : null}
      </Card>
      <div className="flex justify-end">
        <Button
          variant="primary"
          icon={ArrowRight}
          disabled={!complete || busy}
          onClick={() => void submit()}
        >
          {busy
            ? "Saving…"
            : position === current.session.question_count
              ? "Submit final group"
              : "Save and continue"}
        </Button>
      </div>
    </article>
  );
}
