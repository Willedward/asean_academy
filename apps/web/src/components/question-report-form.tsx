"use client";

import { Flag } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  createQuestionReport,
  type ReportCategory,
} from "@/lib/api/question-reports";

export function QuestionReportForm({
  sessionId,
  questionKey,
  questionRevision,
  submit = createQuestionReport,
}: {
  sessionId: string;
  questionKey: string;
  questionRevision: number;
  submit?: typeof createQuestionReport;
}) {
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<ReportCategory>("possible_error");
  const [comment, setComment] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);

  async function send() {
    if (!comment.trim()) return;
    setState("sending");
    setError(null);
    try {
      await submit({
        session_id: sessionId,
        question_key: questionKey,
        question_revision: questionRevision,
        category,
        comment: comment.trim(),
      });
      setState("sent");
    } catch (caught) {
      setState("idle");
      setError(caught instanceof Error ? caught.message : "The report could not be sent.");
    }
  }

  if (state === "sent") {
    return <p className="text-sm font-semibold text-emerald-700" role="status">Report received. An administrator can now review this exact question revision.</p>;
  }
  if (!open) {
    return <Button onClick={() => setOpen(true)} variant="outline"><Flag className="mr-2 size-4" />Report a problem</Button>;
  }
  return (
    <section className="w-full rounded-2xl border border-slate-200 bg-slate-50 p-4" aria-label="Report a question problem">
      <label className="block text-sm font-bold" htmlFor="report-category">Problem type</label>
      <select className="mt-1 w-full rounded-lg border bg-white p-3" id="report-category" onChange={(event) => setCategory(event.target.value as ReportCategory)} value={category}>
        <option value="possible_error">Possible error</option>
        <option value="unclear_wording">Unclear wording</option>
        <option value="display_problem">Display problem</option>
        <option value="other">Other</option>
      </select>
      <label className="mt-3 block text-sm font-bold" htmlFor="report-comment">What happened?</label>
      <textarea className="mt-1 min-h-24 w-full rounded-lg border bg-white p-3" id="report-comment" maxLength={1000} onChange={(event) => setComment(event.target.value)} value={comment} />
      {error ? <p className="text-sm text-rose-700" role="alert">{error}</p> : null}
      <div className="mt-3 flex gap-2">
        <Button disabled={!comment.trim() || state === "sending"} onClick={() => void send()}>{state === "sending" ? "Sending…" : "Send report"}</Button>
        <Button onClick={() => setOpen(false)} variant="outline">Cancel</Button>
      </div>
    </section>
  );
}
