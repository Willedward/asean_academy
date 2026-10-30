"use client";

import { AlertTriangle, Check, CloudOff, RefreshCw } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button, Callout, Card, Divider, Eyebrow, H1, H2, Muted, Tag } from "@/beta-kit/components/ui";
import {
  EnglishEssayDraftApiError,
  getEnglishEssayDraft,
  type EnglishEssayDraftResponse,
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
    } catch {
      setSaveState("offline");
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
          <Tag tone="amber">Submission disabled</Tag>
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
    </div>
  );
}
