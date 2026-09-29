"use client";

import { ArrowLeft, ArrowRight, Check, CircleAlert, RefreshCw, Send } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { MathContent, type ContentBlock } from "@/components/math-content";
import { Button } from "@/components/ui/button";
import {
  getDiagnosticSession,
  saveDiagnosticResponse,
  submitDiagnosticSession,
  type DiagnosticSession,
} from "@/lib/api/diagnostics";

type Answers = Record<number, Record<string, string>>;
type DiagnosticApi = {
  get: typeof getDiagnosticSession;
  save: typeof saveDiagnosticResponse;
  submit: typeof submitDiagnosticSession;
};
const defaultApi: DiagnosticApi = { get: getDiagnosticSession, save: saveDiagnosticResponse, submit: submitDiagnosticSession };
const encoded = (value: Record<string, string> | undefined) => JSON.stringify(value ?? {});

export function DiagnosticPlayer({ sessionId, api = defaultApi }: { sessionId: string; api?: DiagnosticApi }) {
  const router = useRouter();
  const [session, setSession] = useState<DiagnosticSession | null>(null);
  const [answers, setAnswers] = useState<Answers>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const saved = useRef<Record<number, string>>({});

  useEffect(() => {
    let active = true;
    void api.get(sessionId).then(
      (value) => {
        if (!active) return;
        if (value.state === "submitted") {
          router.replace(`/diagnostics/${sessionId}/result`);
          return;
        }
        const restored: Answers = {};
        const snapshots: Record<number, string> = {};
        for (const item of value.items) {
          restored[item.position] = item.saved_answers ?? {};
          snapshots[item.position] = encoded(item.saved_answers ?? {});
        }
        saved.current = snapshots;
        setAnswers(restored);
        setSession(value);
      },
      (caught: unknown) => active && setError(caught instanceof Error ? caught.message : "The readiness check could not be loaded."),
    );
    return () => { active = false; };
  }, [api, router, sessionId]);

  const item = session?.items[currentIndex];
  const currentAnswers = useMemo(
    () => item ? answers[item.position] ?? {} : {},
    [answers, item],
  );
  const complete = useMemo(
    () => Boolean(item?.question.parts.every((part) => (currentAnswers[String(part.position)] ?? "").trim())),
    [currentAnswers, item],
  );

  useEffect(() => {
    if (!item || !complete || encoded(currentAnswers) === saved.current[item.position]) return;
    setSaveState("saving");
    const timer = window.setTimeout(() => {
      void api.save(sessionId, item.position, currentAnswers).then(
        () => {
          saved.current[item.position] = encoded(currentAnswers);
          setSaveState("saved");
          setError(null);
        },
        (caught: unknown) => {
          setSaveState("idle");
          setError(caught instanceof Error ? caught.message : "This answer could not be saved.");
        },
      );
    }, 700);
    return () => window.clearTimeout(timer);
  }, [api, complete, currentAnswers, item, sessionId]);

  async function saveDirtyItems() {
    if (!session) return;
    for (const candidate of session.items) {
      const value = answers[candidate.position] ?? {};
      const isComplete = candidate.question.parts.every((part) => (value[String(part.position)] ?? "").trim());
      if (!isComplete) throw new Error(`Question ${candidate.position} still needs an answer.`);
      if (encoded(value) !== saved.current[candidate.position]) {
        await api.save(sessionId, candidate.position, value);
        saved.current[candidate.position] = encoded(value);
      }
    }
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      await saveDirtyItems();
      await api.submit(sessionId);
      router.push(`/diagnostics/${sessionId}/result`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The readiness check could not be submitted.");
      setSubmitting(false);
    }
  }

  if (error && !session) return <div className="status-card border-rose-200 bg-rose-50" role="alert"><CircleAlert className="size-5 text-rose-700" /><div className="grow"><p className="status-title">Readiness check unavailable</p><p className="status-copy">{error}</p></div><Button variant="outline" onClick={() => window.location.reload()}><RefreshCw className="mr-2 size-4" />Retry</Button></div>;
  if (!session || !item) return <div className="status-card animate-pulse" role="status">Loading readiness check…</div>;

  const answeredCount = session.items.filter((candidate) => {
    const value = answers[candidate.position] ?? {};
    return candidate.question.parts.every((part) => (value[String(part.position)] ?? "").trim());
  }).length;
  const allComplete = answeredCount === session.items.length;

  return (
    <article className="space-y-6">
      <header className="space-y-3">
        <Link className="inline-flex items-center gap-2 text-sm font-semibold text-teal-800 hover:underline" href="/diagnostics"><ArrowLeft className="size-4" />Exit and return later</Link>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div><p className="mb-1 text-sm font-bold uppercase tracking-wide text-teal-700">{session.purpose} readiness · Question {item.position} of {session.items.length}</p><h1 className="m-0 text-3xl font-black">{item.question.title}</h1></div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold">{answeredCount}/{session.items.length} answered</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-200" aria-label={`${answeredCount} of ${session.items.length} answered`}><div className="h-full bg-teal-600 transition-all" style={{ width: `${answeredCount * 100 / session.items.length}%` }} /></div>
      </header>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        {item.question.stem.length ? <div className="mb-6 text-lg leading-8"><MathContent blocks={item.question.stem as ContentBlock[]} /></div> : null}
        <div className="space-y-7">
          {item.question.parts.map((part) => (
            <fieldset className="border-0 p-0" key={part.position}>
              <legend className="mb-3 text-lg font-semibold leading-8">{part.label ? <span className="mr-2">({part.label})</span> : null}<MathContent blocks={part.prompt as ContentBlock[]} /><span className="ml-2 text-sm font-normal text-slate-500">[{part.marks}]</span></legend>
              <label className="block text-sm font-bold text-slate-700" htmlFor={`diagnostic-answer-${item.position}-${part.position}`}>Final answer</label>
              <input autoComplete="off" className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-lg outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-200" id={`diagnostic-answer-${item.position}-${part.position}`} maxLength={500} onChange={(event) => { setSaveState("idle"); setAnswers((existing) => ({ ...existing, [item.position]: { ...(existing[item.position] ?? {}), [String(part.position)]: event.target.value } })); }} placeholder={part.input_placeholder} value={currentAnswers[String(part.position)] ?? ""} />
            </fieldset>
          ))}
        </div>
        <p className="mb-0 mt-4 min-h-5 text-sm text-slate-500" role="status">{saveState === "saving" ? "Saving answer…" : saveState === "saved" ? <span className="inline-flex items-center gap-1 text-emerald-700"><Check className="size-4" />Answer saved</span> : complete ? "Your answer will save automatically." : "Complete every part to save this question."}</p>
      </section>

      {error ? <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-900" role="alert">{error}</div> : null}
      <nav className="flex flex-wrap justify-between gap-3" aria-label="Diagnostic questions">
        <Button disabled={currentIndex === 0} onClick={() => { setError(null); setCurrentIndex((value) => value - 1); }} variant="outline"><ArrowLeft className="mr-2 size-4" />Previous</Button>
        {currentIndex < session.items.length - 1 ? <Button onClick={() => { setError(null); setCurrentIndex((value) => value + 1); }}>Next<ArrowRight className="ml-2 size-4" /></Button> : <Button disabled={!allComplete || submitting || saveState === "saving"} onClick={() => void submit()}>{submitting ? "Submitting…" : "Submit readiness check"}<Send className="ml-2 size-4" /></Button>}
      </nav>
    </article>
  );
}
