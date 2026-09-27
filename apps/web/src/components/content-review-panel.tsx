"use client";

import { useEffect, useState } from "react";

import { MathContent, type ContentBlock } from "@/components/math-content";
import { Button } from "@/components/ui/button";
import {
  adminRequest,
  type ContentItem,
  type ContentPreview,
  type ContentQueue,
  type LifecycleInput,
  type ReviewInput,
} from "@/lib/api/admin-dashboard";
import { ApiRequestError } from "@/lib/api/errors";

function errorMessage(error: unknown) {
  if (error instanceof ApiRequestError) {
    return `${error.message}${error.requestId ? ` Request ID: ${error.requestId}` : ""}`;
  }
  return error instanceof Error ? error.message : "The operation could not be completed.";
}

function label(value: string) {
  return value.replaceAll("_", " ");
}

function Blocks({ value }: { value: unknown }) {
  return <MathContent blocks={(Array.isArray(value) ? value : []) as ContentBlock[]} />;
}

type PreviewQuestion = {
  title: string;
  stem: ContentBlock[];
  difficulty: number;
  primary_outcome: string;
  total_marks: number;
  parts: {
    position: number;
    label?: string | null;
    marks: number;
    prompt: ContentBlock[];
    input_placeholder: string;
  }[];
};
type PreviewLesson = {
  title: string;
  summary: string;
  objectives: string[];
  sections: Record<string, unknown>[];
};
type PreviewCourse = {
  title: string;
  description: string;
  subject: string;
  school_level: string;
  units: { title: string; lessons: { title: string; outcomes: string[] }[] }[];
};

function StudentPreview({ preview }: { preview: ContentPreview }) {
  const content = preview.public_content;
  if (preview.content_kind === "question") {
    const question = content as unknown as PreviewQuestion;
    return (
      <article className="space-y-5 rounded-2xl border bg-slate-50 p-5">
        <div>
          <p className="m-0 text-sm font-semibold uppercase text-teal-700">
            Difficulty {question.difficulty} · Outcome {question.primary_outcome} · {question.total_marks} marks
          </p>
          <h3 className="mt-1 text-xl font-bold">{question.title}</h3>
          <Blocks value={question.stem} />
        </div>
        {question.parts.map((part) => (
          <section className="border-t pt-4" key={part.position}>
            <h4 className="font-bold">
              {part.label ? `Part (${part.label})` : `Part ${part.position}`} · {part.marks} marks
            </h4>
            <Blocks value={part.prompt} />
            <input
              aria-label={`Student answer for part ${part.position}`}
              className="mt-3 w-full rounded-lg border bg-white p-3"
              disabled
              placeholder={part.input_placeholder}
            />
          </section>
        ))}
      </article>
    );
  }
  if (preview.content_kind === "lesson") {
    const lesson = content as unknown as PreviewLesson;
    return (
      <article className="space-y-5 rounded-2xl border bg-slate-50 p-5">
        <h3 className="text-xl font-bold">{lesson.title}</h3>
        <p>{lesson.summary}</p>
        <ul className="list-disc pl-5">
          {lesson.objectives.map((objective) => <li key={objective}>{objective}</li>)}
        </ul>
        {lesson.sections.map((section) => (
          <section className="rounded-xl border bg-white p-4" key={String(section.stable_key)}>
            <p className="text-xs font-semibold uppercase text-teal-700">{label(String(section.type))}</p>
            <h4 className="font-bold">{String(section.title)}</h4>
            <Blocks value={section.blocks ?? section.prompt} />
            {Array.isArray(section.steps)
              ? section.steps.map((step) => (
                  <p className="border-l-2 border-teal-200 pl-3" key={String(step.position)}>
                    <Blocks value={step.content} />
                  </p>
                ))
              : null}
          </section>
        ))}
      </article>
    );
  }
  const course = content as unknown as PreviewCourse;
  return (
    <article className="space-y-4 rounded-2xl border bg-slate-50 p-5">
      <p className="m-0 text-sm font-semibold uppercase text-teal-700">
        {course.school_level.replaceAll("_", " ")} · {course.subject}
      </p>
      <h3 className="text-xl font-bold">{course.title}</h3>
      <p>{course.description}</p>
      {course.units.map((unit) => (
        <section key={unit.title}>
          <h4 className="font-bold">{unit.title}</h4>
          <ol className="list-decimal pl-5">
            {unit.lessons.map((lesson) => (
              <li key={lesson.title}>{lesson.title} · {lesson.outcomes.join(", ")}</li>
            ))}
          </ol>
        </section>
      ))}
    </article>
  );
}

function ReviewSummary({ item }: { item: ContentItem }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {(["mathematics", "editorial"] as const).map((dimension) => {
        const review = dimension === "mathematics" ? item.mathematics_review : item.editorial_review;
        return (
          <div className="rounded-xl border p-3" key={dimension}>
            <p className="m-0 font-bold capitalize">{dimension}</p>
            {review ? (
              <>
                <p className="my-1 capitalize">{label(review.decision)}</p>
                <p className="m-0 text-xs text-slate-600">{review.reviewer_email} · {new Date(review.created_at).toLocaleString("en-SG")}</p>
                <p className="mb-0 text-sm">{review.notes}</p>
              </>
            ) : <p className="mb-0 text-sm text-slate-600">Awaiting review</p>}
          </div>
        );
      })}
    </div>
  );
}

function ItemActions({
  academic,
  item,
  onChanged,
}: {
  academic: boolean;
  item: ContentItem;
  onChanged: () => void;
}) {
  const [preview, setPreview] = useState<ContentPreview>();
  const [dimension, setDimension] = useState<"mathematics" | "editorial">(
    academic ? "mathematics" : "editorial",
  );
  const [decision, setDecision] = useState<"approved" | "changes_requested">("approved");
  const [notes, setNotes] = useState("");
  const [reason, setReason] = useState("");
  const [confirmAction, setConfirmAction] = useState<"publish" | "retire" | null>(null);
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const base = `content/${item.content_kind}/${encodeURIComponent(item.stable_key)}`;

  async function openPreview() {
    setBusy(true);
    try {
      setPreview(await adminRequest<ContentPreview>(`${base}/preview`));
      setError(undefined);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function submitReview() {
    const body: ReviewInput = {
      source_revision: item.revision,
      source_content_sha256: item.source_content_sha256,
      review_fingerprint: item.review_fingerprint,
      dimension,
      decision,
      notes,
    };
    setBusy(true);
    try {
      await adminRequest(`${base}/reviews`, body);
      setNotes("");
      setError(undefined);
      onChanged();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function submitLifecycle(action: "publish" | "retire") {
    const body: LifecycleInput = {
      source_revision: item.revision,
      source_content_sha256: item.source_content_sha256,
      review_fingerprint: item.review_fingerprint,
      action,
      reason,
    };
    setBusy(true);
    try {
      await adminRequest(`${base}/lifecycle-requests`, body);
      setReason("");
      setConfirmAction(null);
      setError(undefined);
      onChanged();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <ReviewSummary item={item} />
      <div className="grid gap-3 rounded-xl border p-4 md:grid-cols-[180px_220px_1fr_auto]">
        <label>
          Review area
          <select
            aria-label={`Review area for ${item.stable_key}`}
            className="mt-1 w-full rounded-lg border bg-white p-2"
            onChange={(event) => setDimension(event.target.value as typeof dimension)}
            value={dimension}
          >
            <option disabled={!academic} value="mathematics">Mathematics</option>
            <option value="editorial">Editorial</option>
          </select>
        </label>
        <label>
          Decision
          <select
            aria-label={`Decision for ${item.stable_key}`}
            className="mt-1 w-full rounded-lg border bg-white p-2"
            onChange={(event) => setDecision(event.target.value as typeof decision)}
            value={decision}
          >
            <option value="approved">Approve</option>
            <option value="changes_requested">Request changes</option>
          </select>
        </label>
        <label>
          Review notes
          <input
            aria-label={`Review notes for ${item.stable_key}`}
            className="mt-1 w-full rounded-lg border bg-white p-2"
            maxLength={2000}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Record what you checked"
            value={notes}
          />
        </label>
        <Button className="self-end" disabled={busy || notes.trim().length < 10} onClick={() => void submitReview()}>
          Record review
        </Button>
      </div>
      <div className="flex flex-wrap gap-3">
        <Button variant="outline" disabled={busy} onClick={() => void openPreview()}>
          {preview ? "Refresh student preview" : "Preview as student"}
        </Button>
        {academic && item.can_request_publication ? (
          <Button variant="outline" onClick={() => setConfirmAction("publish")}>Review publication request</Button>
        ) : null}
        {academic && item.can_request_retirement ? (
          <Button variant="outline" onClick={() => setConfirmAction("retire")}>Review retirement request</Button>
        ) : null}
      </div>
      {item.blockers.length ? (
        <ul className="list-disc pl-5 text-sm text-amber-900">
          {item.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)}
        </ul>
      ) : null}
      {confirmAction ? (
        <div className="space-y-3 rounded-xl border border-amber-300 bg-amber-50 p-4">
          <p className="m-0 font-bold capitalize">Confirm {confirmAction} request</p>
          <p className="text-sm">
            This records a release request. It does not modify Git-authored content or publish directly to students.
          </p>
          <label className="block">
            Reason
            <textarea
              aria-label={`Reason for ${confirmAction} request`}
              className="mt-1 block min-h-24 w-full rounded-lg border bg-white p-3"
              maxLength={2000}
              onChange={(event) => setReason(event.target.value)}
              value={reason}
            />
          </label>
          <div className="flex gap-3">
            <Button disabled={busy || reason.trim().length < 10} onClick={() => void submitLifecycle(confirmAction)}>
              Confirm {confirmAction} request
            </Button>
            <Button variant="outline" onClick={() => setConfirmAction(null)}>Cancel</Button>
          </div>
        </div>
      ) : null}
      {error ? <p className="text-sm text-rose-700" role="alert">{error}</p> : null}
      {preview ? <StudentPreview preview={preview} /> : null}
    </div>
  );
}

export function ContentReviewPanel({ academic }: { academic: boolean }) {
  const [filters, setFilters] = useState({ kind: "", status: "", state: "", search: "" });
  const [applied, setApplied] = useState(filters);
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [data, setData] = useState<ContentQueue>();
  const [error, setError] = useState<string>();
  const query = new URLSearchParams({ limit: "25", offset: String(offset) });
  if (applied.kind) query.set("kind", applied.kind);
  if (applied.status) query.set("source_status", applied.status);
  if (applied.state) query.set("review_state", applied.state);
  if (applied.search) query.set("search", applied.search);
  const path = `content?${query}`;

  useEffect(() => {
    let active = true;
    void adminRequest<ContentQueue>(path).then(
      (value) => {
        if (active) {
          setData(value);
          setError(undefined);
        }
      },
      (caught: unknown) => {
        if (active) setError(errorMessage(caught));
      },
    );
    return () => { active = false; };
  }, [path, revision]);

  return (
    <div className="space-y-6">
      <p>
        Decisions are append-only and tied to the exact reviewed content. Student preview deliberately omits answers, hints and locked feedback.
      </p>
      <form
        className="grid gap-3 rounded-2xl border bg-white p-4 md:grid-cols-4"
        onSubmit={(event) => {
          event.preventDefault();
          setOffset(0);
          setApplied(filters);
          setData(undefined);
        }}
      >
        <label>Kind<select className="mt-1 block w-full rounded-lg border p-2" value={filters.kind} onChange={(event) => setFilters({ ...filters, kind: event.target.value })}>
          <option value="">All</option><option value="course">Course</option><option value="lesson">Lesson</option><option value="question">Question</option>
        </select></label>
        <label>Source status<select className="mt-1 block w-full rounded-lg border p-2" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
          <option value="">All</option><option value="draft">Draft</option><option value="reviewed">Reviewed</option><option value="published">Published</option><option value="retired">Retired</option>
        </select></label>
        <label>Review state<select className="mt-1 block w-full rounded-lg border p-2" value={filters.state} onChange={(event) => setFilters({ ...filters, state: event.target.value })}>
          <option value="">All</option><option value="unreviewed">Unreviewed</option><option value="partially_approved">Partially approved</option><option value="approved">Approved</option><option value="changes_requested">Changes requested</option><option value="publication_requested">Publication requested</option><option value="retirement_requested">Retirement requested</option>
        </select></label>
        <label>Search<input className="mt-1 block w-full rounded-lg border p-2" maxLength={100} type="search" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} /></label>
        <Button className="md:col-start-4" type="submit">Apply filters</Button>
      </form>
      {!data ? (
        <div className="status-card" role={error ? "alert" : "status"}>
          {error ?? "Loading review queue…"}
          {error ? <Button variant="outline" onClick={() => setRevision((value) => value + 1)}>Retry</Button> : null}
        </div>
      ) : !data.items.length ? <p>No content matches these filters.</p> : (
        <div className="space-y-5">
          {data.items.map((item) => (
            <article className="space-y-4 rounded-2xl border bg-white p-5" key={`${item.content_kind}:${item.stable_key}:${item.review_fingerprint}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div><p className="m-0 text-xs font-semibold uppercase text-teal-700">{item.content_kind} · {item.stable_key} · revision {item.revision}</p><h2 className="mt-1 text-xl font-bold">{item.title}</h2></div>
                <div className="flex gap-2"><span className="rounded-full bg-slate-100 px-3 py-1 text-sm capitalize">{item.source_status}</span><span className="rounded-full bg-teal-50 px-3 py-1 text-sm capitalize text-teal-900">{label(item.review_state)}</span></div>
              </div>
              <ItemActions academic={academic} item={item} onChanged={() => { setData(undefined); setRevision((value) => value + 1); }} />
            </article>
          ))}
        </div>
      )}
      {data ? (
        <div className="flex items-center justify-between">
          <Button variant="outline" disabled={offset === 0} onClick={() => { setData(undefined); setOffset(Math.max(0, offset - 25)); }}>Previous</Button>
          <span>{data.total ? offset + 1 : 0}–{Math.min(offset + 25, data.total)} of {data.total}</span>
          <Button variant="outline" disabled={offset + 25 >= data.total} onClick={() => { setData(undefined); setOffset(offset + 25); }}>Next</Button>
        </div>
      ) : null}
    </div>
  );
}
