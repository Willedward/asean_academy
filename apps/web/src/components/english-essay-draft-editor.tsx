"use client";

import {
  AlertTriangle,
  Check,
  CheckCircle2,
  CloudOff,
  Info,
  LockKeyhole,
  RefreshCw,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button, Callout, Card, Divider, Eyebrow, H1, H2, Muted, Tag } from "@/beta-kit/components/ui";
import {
  createEnglishEssaySubmission,
  EnglishEssayDraftApiError,
  getEnglishEssayDraft,
  type EnglishEssayDraftResponse,
  type EnglishEssayPreSubmitResponse,
  type EnglishEssaySubmissionResponse,
  preSubmitEnglishEssayDraft,
  updateEnglishEssayDraft,
} from "@/lib/api/english";

type SaveState = "saved" | "local" | "saving" | "offline" | "conflict";

type LocalBackup = {
  text: string;
  baseEditRevision: number;
  savedAt: string;
};

function backupKey(draftId: string): string {
  return `nextscholar:english-essay-draft:${draftId}`;
}

export function countEssayWords(text: string): number {
  return text.match(/[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*/g)?.length ?? 0;
}

function savedLabel(value: string): string {
  return new Intl.DateTimeFormat("en-SG", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Singapore",
  }).format(new Date(value));
}

export function EnglishEssayDraftEditor({
  initialDraft,
}: {
  initialDraft: EnglishEssayDraftResponse;
}) {
  const [body, setBody] = useState(initialDraft.body);
  const [lastServerBody, setLastServerBody] = useState(initialDraft.body);
  const [editRevision, setEditRevision] = useState(initialDraft.edit_revision);
  const [updatedAt, setUpdatedAt] = useState(initialDraft.updated_at);
  const [saveState, setSaveState] = useState<SaveState>("saved");
  const [hydrated, setHydrated] = useState(false);
  const [retryNonce, setRetryNonce] = useState(0);
  const [preSubmit, setPreSubmit] =
    useState<EnglishEssayPreSubmitResponse | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [submission, setSubmission] =
    useState<EnglishEssaySubmissionResponse | null>(null);
  const [submissionBusy, setSubmissionBusy] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const bodyRef = useRef(body);
  const savingRef = useRef(false);

  useEffect(() => {
    bodyRef.current = body;
  }, [body]);

  const localWordCount = countEssayWords(body);
  const guidance = initialDraft.prompt.word_count_guidance;
  const progress = guidance
    ? Math.min(100, Math.round((localWordCount / guidance) * 100))
    : 0;

  useEffect(() => {
    const encoded = window.localStorage.getItem(backupKey(initialDraft.draft_id));
    if (encoded) {
      try {
        const backup = JSON.parse(encoded) as LocalBackup;
        if (backup.text !== initialDraft.body) {
          queueMicrotask(() => {
            setBody(backup.text);
            setSaveState(
              backup.baseEditRevision === initialDraft.edit_revision
                ? "local"
                : "conflict",
            );
          });
        }
      } catch {
        window.localStorage.removeItem(backupKey(initialDraft.draft_id));
      }
    }
    queueMicrotask(() => setHydrated(true));
  }, [initialDraft.body, initialDraft.draft_id, initialDraft.edit_revision]);

  useEffect(() => {
    if (!hydrated || body === lastServerBody) return;
    const backup: LocalBackup = {
      text: body,
      baseEditRevision: editRevision,
      savedAt: new Date().toISOString(),
    };
    window.localStorage.setItem(backupKey(initialDraft.draft_id), JSON.stringify(backup));
  }, [
    body,
    editRevision,
    hydrated,
    initialDraft.draft_id,
    lastServerBody,
  ]);

  useEffect(() => {
    if (
      !hydrated ||
      body === lastServerBody ||
      saveState === "conflict" ||
      saveState === "offline" ||
      saveState === "saving" ||
      savingRef.current
    )
      return;
    const textToSave = body;
    const revisionToSave = editRevision;
    const timer = window.setTimeout(() => {
      savingRef.current = true;
      setSaveState("saving");
      void updateEnglishEssayDraft(
        initialDraft.draft_id,
        textToSave,
        revisionToSave,
      ).then(
        (saved) => {
          setEditRevision(saved.edit_revision);
          setUpdatedAt(saved.updated_at);
          setLastServerBody(saved.body);
          if (bodyRef.current === saved.body) {
            window.localStorage.removeItem(backupKey(initialDraft.draft_id));
            setSaveState("saved");
          } else {
            setSaveState("local");
          }
          savingRef.current = false;
        },
        (caught: unknown) => {
          savingRef.current = false;
          setSaveState(
            caught instanceof EnglishEssayDraftApiError && caught.status === 409
              ? "conflict"
              : "offline",
          );
        },
      );
    }, 800);
    return () => window.clearTimeout(timer);
  }, [
    body,
    editRevision,
    hydrated,
    initialDraft.draft_id,
    lastServerBody,
    retryNonce,
    saveState,
  ]);

  async function loadServerCopy() {
    try {
      const latest = await getEnglishEssayDraft(initialDraft.draft_id);
      setBody(latest.body);
      setLastServerBody(latest.body);
      setEditRevision(latest.edit_revision);
      setUpdatedAt(latest.updated_at);
      window.localStorage.removeItem(backupKey(initialDraft.draft_id));
      setSaveState("saved");
      setPreSubmit(null);
      setConfirmed(false);
      setSubmissionError(null);
    } catch {
      setSaveState("offline");
    }
  }

  async function reviewForSubmission() {
    setSubmissionBusy(true);
    setSubmissionError(null);
    setConfirmed(false);
    try {
      const reviewed = await preSubmitEnglishEssayDraft(
        initialDraft.draft_id,
        editRevision,
      );
      setPreSubmit(reviewed);
    } catch (caught) {
      setPreSubmit(null);
      setSubmissionError(
        caught instanceof EnglishEssayDraftApiError && caught.status === 409
          ? "The saved draft changed before review. Load the latest saved copy and try again."
          : "The pre-submission checks could not be completed. Try again.",
      );
    } finally {
      setSubmissionBusy(false);
    }
  }

  async function submitSnapshot() {
    if (!preSubmit?.can_submit || !confirmed) return;
    setSubmissionBusy(true);
    setSubmissionError(null);
    try {
      const created = await createEnglishEssaySubmission(
        initialDraft.draft_id,
        preSubmit.edit_revision,
      );
      setSubmission(created);
      setPreSubmit(null);
      setConfirmed(false);
    } catch (caught) {
      setSubmissionError(
        caught instanceof EnglishEssayDraftApiError && caught.status === 409
          ? "This saved revision changed or was already submitted. Save a new revision before submitting again."
          : "The permanent snapshot could not be created. Your saved draft is unchanged; try again.",
      );
    } finally {
      setSubmissionBusy(false);
    }
  }

  const status = {
    saved: { icon: Check, text: "Saved remotely", tone: "text-ns-muted" },
    local: { icon: Check, text: "Backed up on this device", tone: "text-ns-muted" },
    saving: { icon: RefreshCw, text: "Saving…", tone: "text-ns-muted" },
    offline: { icon: CloudOff, text: "Saved on this device; remote save failed", tone: "text-amber-800" },
    conflict: { icon: AlertTriangle, text: "Another tab saved a newer version", tone: "text-red-700" },
  }[saveState];
  const StatusIcon = status.icon;

  return (
    <div className="flex flex-col gap-5">
      {initialDraft.prompt.development_preview ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <strong>Development preview</strong>
          <span>This prompt still requires English and editorial approval.</span>
        </Callout>
      ) : null}
      {saveState === "conflict" ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <strong>Your text has not been overwritten.</strong>
          <span>
            A newer remote revision exists. Copy your current text if needed,
            then load the latest saved copy before continuing.
          </span>
          <Button onClick={() => void loadServerCopy()}>Load latest saved copy</Button>
        </Callout>
      ) : null}
      <section className="flex flex-col gap-2">
        <Eyebrow>EXTENDED WRITING · WORKING DRAFT</Eyebrow>
        <H1>{initialDraft.prompt.title}</H1>
        <div className="flex flex-wrap gap-2">
          <Tag>{initialDraft.prompt.time_limit_minutes} minutes</Tag>
          {guidance ? <Tag>About {guidance} words</Tag> : null}
          <Tag>Submission available</Tag>
          <Tag tone="amber">AI marking unavailable</Tag>
        </div>
      </section>
      <div className="grid items-start gap-5 lg:grid-cols-[360px_minmax(0,1fr)]">
        <Card className="gap-4">
          <H2>Your task</H2>
          <p className="m-0 text-base leading-7 text-ns-ink">
            {initialDraft.prompt.prompt_text}
          </p>
          <Divider />
          <ul className="m-0 flex flex-col gap-2 pl-5 text-sm leading-6 text-ns-muted">
            {initialDraft.prompt.instructions.map((instruction) => (
              <li key={instruction}>{instruction}</li>
            ))}
          </ul>
          <Divider />
          <Muted className="text-sm">
            The 30-minute timing and word count are preparation guidance based
            on currently reported test information, not an official scoring rule.
          </Muted>
        </Card>
        <Card className="gap-3">
          <label htmlFor="essay-draft" className="font-semibold text-ns-ink">
            Your essay
          </label>
          <textarea
            id="essay-draft"
            value={body}
            onChange={(event) => {
              setBody(event.target.value);
              if (saveState !== "conflict") setSaveState("local");
              setPreSubmit(null);
              setConfirmed(false);
              setSubmissionError(null);
            }}
            maxLength={20000}
            spellCheck
            aria-describedby="essay-draft-status essay-draft-count"
            className="h-[520px] w-full resize-y rounded-xl border-[1.5px] border-ns-line-strong bg-ns-raised p-4 text-[17px] leading-7 text-ns-ink focus:border-ns-brand focus:outline-none focus:ring-2 focus:ring-ns-brand/20"
          />
          <div className="flex flex-wrap items-center gap-3">
            <span id="essay-draft-count" className="text-sm font-semibold tabular-nums">
              {localWordCount} words
            </span>
            {guidance ? <Muted className="text-sm">Guidance: about {guidance}</Muted> : null}
            <span
              id="essay-draft-status"
              role="status"
              className={`ml-auto inline-flex items-center gap-1.5 text-sm font-semibold ${status.tone}`}
            >
              <StatusIcon size={15} aria-hidden /> {status.text}
            </span>
          </div>
          {guidance ? (
            <div
              role="progressbar"
              aria-label={`Words toward ${guidance}`}
              aria-valuenow={progress}
              aria-valuemin={0}
              aria-valuemax={100}
              className="h-1.5 overflow-hidden rounded-full bg-ns-line"
            >
              <div className="h-full rounded-full bg-ns-amber" style={{ width: `${progress}%` }} />
            </div>
          ) : null}
          {saveState === "offline" ? (
            <Button
              onClick={() => {
                setSaveState("local");
                setRetryNonce((value) => value + 1);
              }}
            >
              Retry remote save
            </Button>
          ) : null}
          <Muted className="text-xs">
            Remote edit revision {editRevision} · Last remote save {savedLabel(updatedAt)}
          </Muted>
        </Card>
      </div>
      <section aria-label="Essay submission">
        <Card className="gap-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-1">
            <Eyebrow>SUBMIT A PERMANENT SNAPSHOT</Eyebrow>
            <H2>Review your saved revision before submitting</H2>
            <Muted>
              Submission preserves the exact essay, prompt and instructional
              rubric revisions. It does not request AI feedback or create an
              official score.
            </Muted>
          </div>
          <LockKeyhole className="text-ns-brand" aria-hidden />
        </div>
        <Button
          variant="primary"
          onClick={() => void reviewForSubmission()}
          disabled={
            submissionBusy ||
            saveState !== "saved" ||
            body !== lastServerBody
          }
        >
          {submissionBusy && !preSubmit
            ? "Checking saved revision…"
            : "Review before submitting"}
        </Button>
        {saveState !== "saved" || body !== lastServerBody ? (
          <Muted className="text-sm">
            Wait for the latest changes to be saved remotely before reviewing.
          </Muted>
        ) : null}
        {submissionError ? (
          <Callout tone="amber" icon={AlertTriangle}>
            <strong>Submission was not completed.</strong>
            <span>{submissionError}</span>
          </Callout>
        ) : null}
        {preSubmit ? (
          <div
            className="flex flex-col gap-4"
            role="region"
            aria-label="Pre-submission checks"
          >
            <Divider />
            <div className="flex flex-wrap gap-2">
              <Tag>{preSubmit.word_count} words</Tag>
              <Tag>{preSubmit.paragraph_count} paragraphs</Tag>
              <Tag>Draft revision {preSubmit.edit_revision}</Tag>
              <Tag>
                Prompt r{preSubmit.prompt_revision} · Rubric r
                {preSubmit.rubric_revision}
              </Tag>
            </div>
            <ul className="m-0 flex list-none flex-col gap-2 p-0">
              {preSubmit.checks.map((check) => {
                const CheckIcon =
                  check.status === "pass"
                    ? CheckCircle2
                    : check.status === "info"
                      ? Info
                      : AlertTriangle;
                const tone =
                  check.status === "block"
                    ? "border-red-200 bg-red-50 text-red-800"
                    : check.status === "warning"
                      ? "border-amber-200 bg-amber-50 text-amber-900"
                      : "border-ns-line bg-ns-raised text-ns-ink";
                return (
                  <li
                    key={check.check_key}
                    className={`flex items-start gap-2 rounded-xl border p-3 text-sm leading-6 ${tone}`}
                  >
                    <CheckIcon size={18} className="mt-0.5 shrink-0" aria-hidden />
                    <span>{check.message}</span>
                  </li>
                );
              })}
            </ul>
            {preSubmit.can_submit ? (
              <>
                <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-ns-line-strong bg-ns-surface p-4 text-sm leading-6 text-ns-ink">
                  <input
                    type="checkbox"
                    checked={confirmed}
                    onChange={(event) => setConfirmed(event.target.checked)}
                    className="mt-1 size-4 accent-ns-brand"
                  />
                  <span>
                    I understand that this creates a permanent snapshot of
                    saved draft revision {preSubmit.edit_revision}. I can keep
                    editing afterward and submit a later revision separately.
                  </span>
                </label>
                <Button
                  variant="primary"
                  onClick={() => void submitSnapshot()}
                  disabled={!confirmed || submissionBusy}
                >
                  {submissionBusy ? "Submitting snapshot…" : "Submit saved revision"}
                </Button>
              </>
            ) : (
              <Muted>
                Resolve the blocking checks, save the draft, then run the
                review again.
              </Muted>
            )}
          </div>
        ) : null}
        {submission ? (
          <Callout tone="success" icon={CheckCircle2}>
            <strong>
              Submission revision {submission.submission_revision} is saved permanently.
            </strong>
            <span>
              Draft revision {submission.draft_edit_revision} · {submission.word_count} words · Submitted {savedLabel(submission.submitted_at)}
            </span>
            <span>
              No AI feedback or official score was generated. You may continue
              editing this draft and submit a later revision.
            </span>
          </Callout>
        ) : null}
        </Card>
      </section>
    </div>
  );
}
