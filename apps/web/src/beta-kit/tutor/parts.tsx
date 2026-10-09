"use client";

/**
 * Small presentational pieces of the hornbill tutor. Pure props, no data fetching.
 * Canvas page: "AI tutor (V2)".
 */
import type { ReactNode } from "react";
import {
  AlertCircle,
  ArrowUp,
  ChevronDown,
  ChevronRight,
  Clock,
  FileText,
  Flag,
  Layers,
  Lock,
  RefreshCw,
  Search,
  ShieldCheck,
  Target,
  WifiOff,
  X,
} from "lucide-react";
import Link from "next/link";

import { TutorContent } from "@/components/tutor-content";
import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { Button, Tag, focusRing } from "../components/ui";
import type { Href } from "../types";
import { modeLabel, resetLabel } from "./format";
import { STARTER_QUESTIONS, type TutorChatMessage, type TutorNotice } from "./types";

type Mood = "normal" | "happy" | "think" | "kind" | "sleepy" | "wow";

/** Hornbill head in a round frame, for chat avatars and buttons. */
export function HornbillAvatar({ size = 32, mood = "normal", className }: { size?: number; mood?: Mood; className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn("inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-ns-brand-soft", className)}
      style={{ width: size, height: size }}
    >
      <Hornbill size={size} mood={mood} crop="head" animated={false} />
    </span>
  );
}

/** Header: avatar, name, "AI helper" status line and close. */
export function TutorHeader({
  sub = "AI helper · uses the lesson",
  onClose,
  closeHref,
  titleId,
}: {
  sub?: string;
  onClose?: () => void;
  closeHref?: Href;
  titleId: string;
}) {
  const close = cn("inline-flex size-11 shrink-0 items-center justify-center rounded-full text-ns-ink hover:bg-ns-sunken", focusRing);
  const label = "Close the hornbill and go back to the question";
  return (
    <div className="flex items-center gap-2.5">
      <HornbillAvatar size={40} mood="happy" />
      <div className="flex min-w-0 grow flex-col">
        <h2 id={titleId} className="m-0 text-[17px] leading-[22px] font-bold text-ns-ink">
          Hornbill
        </h2>
        <span className="inline-flex items-center gap-1.5 text-xs leading-4 text-ns-muted">
          <span aria-hidden="true" className="size-2 rounded-full bg-[#2E9E6B]" />
          {sub}
        </span>
      </div>
      {closeHref ? (
        <Link href={closeHref} aria-label={label} className={close}>
          <X size={22} aria-hidden />
        </Link>
      ) : (
        <button type="button" aria-label={label} onClick={onClose} className={close}>
          <X size={22} aria-hidden />
        </button>
      )}
    </div>
  );
}

/** The question pinned at the top of the phone sheet. Tapping it goes back to the question. */
export function QuestionPin({
  label,
  summary,
  wrongTries,
  solutionOpen,
  onClick,
  href,
}: {
  label: string;
  summary?: ReactNode;
  wrongTries: number;
  solutionOpen: boolean;
  onClick?: () => void;
  href?: Href;
}) {
  const inner = (
    <>
      <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-[10px] border border-ns-line bg-ns-raised text-ns-muted">
        <FileText size={16} aria-hidden />
      </span>
      <span className="flex min-w-0 grow flex-col gap-0.5 text-left">
        <span className="flex items-center gap-2">
          <span className="text-[13px] font-bold">{label}</span>
          <TriesTag wrongTries={wrongTries} solutionOpen={solutionOpen} />
        </span>
        {summary ? <span className="truncate text-[13px] leading-[18px] text-ns-muted">{summary}</span> : null}
      </span>
      <ChevronDown size={18} className="shrink-0 text-ns-muted" aria-hidden />
    </>
  );
  const classes = cn(
    "flex w-full items-center gap-2.5 rounded-[14px] border border-ns-line bg-ns-sunken px-3 py-2.5 text-ns-ink no-underline",
    focusRing,
  );
  const aria = "Show the question";
  return href ? (
    <Link href={href} aria-label={aria} className={classes}>
      {inner}
    </Link>
  ) : (
    <button type="button" aria-label={aria} onClick={onClick} className={classes}>
      {inner}
    </button>
  );
}

export function TriesTag({ wrongTries, solutionOpen }: { wrongTries: number; solutionOpen: boolean }) {
  if (solutionOpen) return <Tag tone="success">Solution open</Tag>;
  return <Tag>{wrongTries === 1 ? "1 wrong try" : `${wrongTries} wrong tries`}</Tag>;
}

/** One-time note at the top of a new chat. */
export function AiNotice() {
  return (
    <div className="flex items-start gap-2 rounded-xl bg-ns-sunken px-3 py-2.5 text-[13px] leading-[18px] text-ns-muted">
      <ShieldCheck size={16} className="mt-px shrink-0" aria-hidden />
      <span>
        I’m an AI, so I can make mistakes. Your answer is always checked by the answer checker, not by me. I won’t give
        away the answer before the solution opens.
      </span>
    </div>
  );
}

/** Bubble shell shared by real replies and the local greeting. */
function AssistantShell({
  children,
  mood = "normal",
  label,
  footer,
}: {
  children: ReactNode;
  mood?: Mood;
  label?: string | null;
  footer?: ReactNode;
}) {
  return (
    <div className="flex max-w-[92%] items-start gap-2 self-start">
      <HornbillAvatar size={32} mood={mood} />
      <div className="flex min-w-0 flex-col gap-1.5">
        <div className="flex min-w-0 flex-col gap-2.5 rounded-[4px_18px_18px_18px] border border-ns-line bg-ns-raised px-3.5 py-3 text-[15px] leading-[23px] text-ns-ink shadow-ns-sm">
          {children}
        </div>
        {label || footer ? (
          <div className="flex flex-wrap items-center gap-3">
            {label ? <span className="text-xs leading-4 font-bold text-ns-amber-text">{label}</span> : null}
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function ReportLink({ onClick, href }: { onClick?: () => void; href?: Href }) {
  const classes = cn("inline-flex min-h-6 items-center gap-1 text-xs leading-4 font-semibold text-ns-muted no-underline hover:text-ns-ink", focusRing);
  const inner = (
    <>
      <Flag size={13} aria-hidden />
      Report this reply
    </>
  );
  return href ? (
    <Link href={href} className={classes}>
      {inner}
    </Link>
  ) : (
    <button type="button" onClick={onClick} className={classes}>
      {inner}
    </button>
  );
}

/** The hornbill's hello. Written by the frontend: the first message of a session always comes from the learner. */
export function Greeting({ name, mood = "happy" }: { name?: string; mood?: Mood }) {
  return (
    <AssistantShell mood={mood}>
      <p className="m-0">Hi{name ? ` ${name}` : ""}! I can see you’ve had a go at this question.</p>
      <p className="m-0">What would help most? Pick one, or type your own question.</p>
    </AssistantShell>
  );
}

/** A server reply. Renders only `blocks`, through the app's KaTeX path. */
export function AssistantMessage({ message, report }: { message: TutorChatMessage; report?: ReactNode }) {
  const mood: Mood = message.safety === "answer_leakage_blocked" ? "kind" : "normal";
  return (
    <AssistantShell mood={mood} label={modeLabel(message.mode)} footer={report}>
      <TutorContent blocks={message.blocks} />
      {message.safety === "answer_leakage_blocked" ? (
        <div className="flex items-center gap-2 rounded-[10px] bg-ns-sunken px-2.5 py-2 text-[13px] leading-[18px] text-ns-muted">
          <Lock size={14} className="shrink-0" aria-hidden />
          The full answer stays hidden until the solution opens.
        </div>
      ) : null}
      {message.safety === "provider_fallback" ? (
        <span className="text-xs leading-4 text-ns-muted">A shorter reply while the hornbill is busy.</span>
      ) : null}
    </AssistantShell>
  );
}

export function StudentMessage({ message }: { message: TutorChatMessage }) {
  return (
    <div data-tutor-role="student" className="flex max-w-[80%] flex-col gap-1 self-end">
      <div className="rounded-[18px_18px_4px_18px] bg-ns-ink px-3.5 py-2.5 text-[15px] leading-[22px] whitespace-pre-wrap text-ns-on-brand">
        {message.blocks.map((block) => block.content).join("")}
      </div>
      {message.delivery === "failed" ? (
        <span className="inline-flex items-center gap-1 self-end text-xs font-semibold text-ns-danger">
          <AlertCircle size={13} aria-hidden />
          No reply yet
        </span>
      ) : null}
    </div>
  );
}

const DOT = "inline-block size-2 rounded-full bg-ns-muted motion-safe:animate-[ns-dot_1.2s_ease-in-out_infinite]";

export function Thinking() {
  return (
    <div role="status" className="flex items-center gap-2 self-start">
      <HornbillAvatar size={32} mood="think" />
      <span className="inline-flex items-center gap-[5px] rounded-[4px_18px_18px_18px] border border-ns-line bg-ns-raised px-4 py-3.5" aria-hidden>
        <span className={DOT} />
        <span className={DOT} style={{ animationDelay: "0.15s" }} />
        <span className={DOT} style={{ animationDelay: "0.3s" }} />
      </span>
      <span className="text-[13px] text-ns-muted">Thinking about your answer…</span>
    </div>
  );
}

const STARTER_ICON = { alert: AlertCircle, search: Search, layers: Layers };

export function StarterQuestions({ onPick, disabled }: { onPick?: (text: string) => void; disabled?: boolean }) {
  return (
    <div role="group" aria-label="Starter questions" className="flex flex-col gap-2">
      {STARTER_QUESTIONS.map(({ text, icon }) => {
        const Icon = STARTER_ICON[icon];
        return (
          <button
            key={text}
            type="button"
            disabled={disabled}
            onClick={() => onPick?.(text)}
            className={cn(
              "flex h-[52px] items-center gap-3 rounded-[14px] border-[1.5px] border-ns-line bg-ns-raised px-4 text-left text-[15px] font-semibold text-ns-ink shadow-ns-sm hover:border-ns-line-strong disabled:opacity-45",
              focusRing,
            )}
          >
            <span className="inline-flex size-8 items-center justify-center rounded-[10px] bg-ns-amber-soft text-ns-amber-text">
              <Icon size={18} aria-hidden />
            </span>
            <span className="grow">{text}</span>
            <ChevronRight size={18} className="text-ns-muted" aria-hidden />
          </button>
        );
      })}
    </div>
  );
}

/** Up to 4 server-suggested replies. Clicking one sends it like typed text. */
export function SuggestedReplies({ items, onPick, disabled }: { items: string[]; onPick?: (text: string) => void; disabled?: boolean }) {
  if (!items.length) return null;
  return (
    <div role="group" aria-label="Suggested replies" className="flex flex-wrap gap-2">
      {items.slice(0, 4).map((text) => (
        <button
          key={text}
          type="button"
          disabled={disabled}
          onClick={() => onPick?.(text)}
          className={cn(
            "inline-flex min-h-9 items-center rounded-full border-[1.5px] border-ns-line-strong bg-ns-raised px-3.5 py-1.5 text-left text-sm leading-[18px] font-semibold text-ns-ink hover:bg-ns-sunken disabled:opacity-45",
            focusRing,
          )}
        >
          {text}
        </button>
      ))}
    </div>
  );
}

/** The server's recommended next action. Today it is free text, so it only takes the learner back to the question. */
export function NextStep({ label, onClick, href }: { label: string; onClick?: () => void; href?: Href }) {
  const classes = cn(
    "inline-flex min-h-10 items-center gap-2 self-start rounded-full border-[1.5px] border-ns-amber-line bg-ns-amber-soft px-4 py-2 text-left text-sm font-bold text-ns-amber-text no-underline",
    focusRing,
  );
  const inner = (
    <>
      <Target size={16} className="shrink-0" aria-hidden />
      <span>
        Next step: <span className="text-ns-ink">{label}</span>
      </span>
    </>
  );
  return href ? (
    <Link href={href} className={classes}>
      {inner}
    </Link>
  ) : (
    <button type="button" onClick={onClick} className={classes}>
      {inner}
    </button>
  );
}

export function QuotaNote({ remaining, resetsAt, now, timeZone }: { remaining: number; resetsAt: string; now?: Date; timeZone?: string }) {
  return (
    <div role="status" className="flex items-center gap-2 rounded-xl bg-ns-amber-soft px-3 py-2 text-[13px] leading-[18px] font-semibold text-ns-amber-text">
      <Clock size={16} className="shrink-0" aria-hidden />
      <span>
        {remaining === 1 ? "1 question" : `${remaining} questions`} left for the hornbill today. More at{" "}
        {resetLabel(resetsAt, now, timeZone)}.
      </span>
    </div>
  );
}

function Bullets({ items }: { items: ReactNode[] }) {
  return (
    <ul className="m-0 flex list-none flex-col gap-1.5 p-0 text-left text-[15px] leading-[22px] text-ns-ink">
      {items.map((item, index) => (
        <li key={index} className="flex items-baseline gap-2">
          <span aria-hidden="true" className="size-1.5 shrink-0 -translate-y-0.5 rounded-full bg-ns-amber" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

/** Daily messages used up. Everything else keeps working. */
export function OutForToday({ resetsAt, now, timeZone }: { resetsAt: string | null; now?: Date; timeZone?: string }) {
  return (
    <div role="status" className="flex flex-col items-center gap-2.5 rounded-[20px] border border-ns-line bg-ns-raised px-4 py-5 text-center shadow-ns-sm">
      <Hornbill size={96} mood="sleepy" branch={false} label="Sleepy hornbill" />
      <h3 className="m-0 text-[19px] leading-[26px] font-semibold">That’s all my help for today</h3>
      <p className="m-0 text-sm leading-5 text-ns-muted">
        You’ve used today’s hornbill questions. I’ll be back at{" "}
        <b className="text-ns-ink">{resetLabel(resetsAt, now, timeZone)}</b>.
      </p>
      <div className="flex flex-col gap-2 self-stretch rounded-xl bg-ns-sunken px-3.5 py-3 text-left">
        <p className="m-0 text-sm leading-5 font-bold text-ns-ink">Everything else still works:</p>
        <Bullets items={["Hints for this question", "Give up and see the full solution, after 2 tries", "Your Try again list and lessons"]} />
      </div>
    </div>
  );
}

/** Model or network trouble. The chat is kept and only an explicit tap retries. */
export function OfflineCard({ requestId, onRetry, rateLimited }: { requestId?: string; onRetry?: () => void; rateLimited?: boolean }) {
  return (
    <div role="alert" className="flex flex-col gap-2.5 rounded-2xl border border-[#F1C2BB] bg-ns-danger-soft p-3.5">
      <div className="flex items-start gap-2.5">
        <span className="flex text-ns-danger">
          {rateLimited ? <Clock size={20} aria-hidden /> : <WifiOff size={20} aria-hidden />}
        </span>
        <div className="flex min-w-0 grow flex-col gap-0.5">
          <b className="text-[15px] leading-5 text-ns-ink">
            {rateLimited ? "That was quick! Wait a moment" : "The hornbill can’t answer right now"}
          </b>
          <span className="text-[13px] leading-[18px] text-ns-ink">
            {rateLimited
              ? "Send again in a few seconds."
              : "Your chat is saved. Try again in a moment. Hints and the solution still work."}
          </span>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {onRetry ? (
          <Button size="sm" icon={RefreshCw} onClick={onRetry}>
            Try again
          </Button>
        ) : null}
        {requestId ? (
          <details className="text-xs text-ns-muted">
            <summary className="cursor-pointer">Support code</summary>
            <code>{requestId}</code>
          </details>
        ) : null}
      </div>
    </div>
  );
}

const PLAIN_NOTICE: Partial<Record<TutorNotice["kind"], { title: string; body: string }>> = {
  session_expired: { title: "This chat timed out", body: "Send your message again to start a fresh chat on this question." },
  closed: { title: "This chat has ended", body: "Send a message to start a new chat on this question." },
  unavailable_question: {
    title: "The hornbill can’t help with this question yet",
    body: "Hints, Give up and the worked solution still work.",
  },
  enrolment_required: { title: "The hornbill needs an active course", body: "Ask your teacher or parent to check your NextScholar enrolment." },
  attempt_required: { title: "Have a go first", body: "Check an answer, then I can see what you tried and help from there." },
};

/** Any notice that is not a reply: quota, out for today, offline, expired, unavailable. */
export function NoticeView({
  notice,
  onRetry,
  now,
  timeZone,
}: {
  notice: TutorNotice;
  onRetry?: () => void;
  now?: Date;
  timeZone?: string;
}) {
  switch (notice.kind) {
    case "quota_low":
      return <QuotaNote remaining={notice.remaining} resetsAt={notice.resetsAt} now={now} timeZone={timeZone} />;
    case "out_for_today":
      return <OutForToday resetsAt={notice.resetsAt} now={now} timeZone={timeZone} />;
    case "offline":
      return <OfflineCard requestId={notice.requestId} onRetry={onRetry} />;
    case "rate_limited":
      return <OfflineCard requestId={notice.requestId} onRetry={onRetry} rateLimited />;
    case "error":
      return (
        <OfflineCard requestId={notice.requestId} onRetry={onRetry} />
      );
  }
  const copy = PLAIN_NOTICE[notice.kind];
  if (!copy) return null;
  return (
    <div role="status" className="flex items-start gap-2.5 rounded-2xl bg-ns-sunken p-3.5">
      <HornbillAvatar size={32} mood="kind" />
      <div className="flex flex-col gap-0.5">
        <b className="text-[15px] leading-5 text-ns-ink">{copy.title}</b>
        <span className="text-[13px] leading-[18px] text-ns-muted">{copy.body}</span>
      </div>
    </div>
  );
}

/** Message box. Enter sends, Shift+Enter adds a line. */
export function Composer({
  value,
  onChange,
  onSend,
  sending,
  disabled,
  placeholder = "Ask about this question",
  maxLength,
  inputId,
}: {
  value?: string;
  onChange?: (value: string) => void;
  onSend?: () => void;
  sending?: boolean;
  disabled?: boolean;
  placeholder?: string;
  maxLength: number;
  inputId: string;
}) {
  const text = value ?? "";
  const canSend = !disabled && !sending && text.trim().length > 0;
  return (
    <form
      className="flex items-end gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        if (canSend) onSend?.();
      }}
    >
      <label htmlFor={inputId} className="sr-only">
        Message the hornbill
      </label>
      <textarea
        id={inputId}
        rows={1}
        maxLength={maxLength}
        placeholder={placeholder}
        disabled={disabled}
        value={onChange ? text : undefined}
        defaultValue={onChange ? undefined : text}
        readOnly={!onChange}
        onChange={(event) => onChange?.(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault();
            if (canSend) onSend?.();
          }
        }}
        className={cn(
          "max-h-32 min-h-12 grow resize-none rounded-3xl border-[1.5px] border-ns-line-strong bg-ns-raised px-4 py-3 text-base leading-[22px] text-ns-ink placeholder:text-ns-muted/80 disabled:bg-ns-sunken disabled:opacity-60",
          focusRing,
        )}
      />
      <button
        type="submit"
        aria-label={sending ? "The hornbill is replying" : "Send"}
        disabled={!canSend}
        className={cn(
          "inline-flex size-12 shrink-0 items-center justify-center gap-[3px] rounded-full text-ns-on-brand",
          sending || canSend ? "bg-ns-ink" : "bg-ns-line-strong",
          focusRing,
        )}
      >
        {sending ? (
          <>
            <span className="inline-block size-[5px] rounded-full bg-ns-on-brand motion-safe:animate-[ns-dot_1.2s_ease-in-out_infinite]" />
            <span className="inline-block size-[5px] rounded-full bg-ns-on-brand motion-safe:animate-[ns-dot_1.2s_ease-in-out_infinite]" style={{ animationDelay: "0.15s" }} />
            <span className="inline-block size-[5px] rounded-full bg-ns-on-brand motion-safe:animate-[ns-dot_1.2s_ease-in-out_infinite]" style={{ animationDelay: "0.3s" }} />
          </>
        ) : (
          <ArrowUp size={20} aria-hidden />
        )}
      </button>
    </form>
  );
}
