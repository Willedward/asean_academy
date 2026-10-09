"use client";

/**
 * The hornbill tutor window. Phones: a tall sheet over the practice screen with
 * the question pinned at the top. Desktop (lg): a panel docked to the right, so
 * the question stays visible and usable.
 *
 * Stateless: everything comes from props. `TutorDock` feeds it from the API;
 * the /beta-kit/tutor previews feed it sample data.
 *
 * Canvas: TutorStart.m, TutorThinking.m, Tutor.m, Tutor.d, TutorStillStuck.m,
 * TutorAnswerLocked.m, TutorSolution.m, TutorSolution.d, TutorLowQuota.m,
 * TutorOutForToday.m, TutorOffline.m
 */
import { useEffect, useId, useRef, type ReactNode } from "react";

import { TUTOR_MESSAGE_MAX_LENGTH } from "@/lib/api/tutor";
import { cn } from "@/lib/utils";

import { Button } from "../components/ui";
import type { Href } from "../types";
import {
  AiNotice,
  AssistantMessage,
  Composer,
  Greeting,
  NextStep,
  NoticeView,
  QuestionPin,
  ReportLink,
  StarterQuestions,
  StudentMessage,
  SuggestedReplies,
  Thinking,
  TriesTag,
  TutorHeader,
} from "./parts";
import type { TutorChatMessage, TutorNotice } from "./types";

/** Keyframes for the typing dots. Rendered once; React hoists and dedupes it. */
export function TutorStyles() {
  return (
    <style href="ns-tutor-keyframes" precedence="default">
      {"@keyframes ns-dot{0%,80%,100%{opacity:.25;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}" +
        "@keyframes ns-sheet{0%{transform:translateY(32px);opacity:0}100%{transform:none;opacity:1}}"}
    </style>
  );
}

export interface TutorViewProps {
  /** e.g. "Question 2 · part (b)" */
  questionLabel: string;
  /** One line of the question for the pinned bar on phones. */
  questionSummary?: ReactNode;
  /** API: AttemptResponse.attempt_number of wrong checks so far. */
  wrongTries: number;
  /** API: TutorReplyResponse.answer_lock_state.solution_locked === false */
  solutionOpen: boolean;
  /** Learner's first name for the hello. */
  studentName?: string;
  messages: TutorChatMessage[];
  /** A reply is on its way. Locks sending (no duplicate submits). */
  sending?: boolean;
  /** API: TutorReplyResponse.suggested_replies (max 4) */
  suggestions?: string[];
  /** API: TutorReplyResponse.recommended_next_action */
  nextStep?: string | null;
  notice?: TutorNotice | null;
  /** Composer text (controlled when onDraftChange is given). */
  draft?: string;
  onDraftChange?: (value: string) => void;
  onSend?: (text: string) => void;
  /** Explicit retry after a failed send. Never automatic. */
  onRetry?: () => void;
  /** Close the window (the session stays open on the server). */
  onClose?: () => void;
  /** Used by previews instead of onClose. */
  closeHref?: Href;
  /** Tapping the next step: back to the question by default. */
  onNextStep?: () => void;
  nextStepHref?: Href;
  /** Opens "Report this reply" for a message. Hidden when not given. */
  onReport?: (messageId: string) => void;
  reportHref?: Href;
  /** Draws the window inside its parent instead of fixed to the screen (tests, side by side previews). */
  inline?: boolean;
  /** Fixed clock for previews and tests. */
  now?: Date;
  /** Fixed time zone for previews (server and browser render the same text). Defaults to the browser's. */
  timeZone?: string;
}

export function TutorView({
  questionLabel,
  questionSummary,
  wrongTries,
  solutionOpen,
  studentName,
  messages,
  sending,
  suggestions = [],
  nextStep,
  notice,
  draft,
  onDraftChange,
  onSend,
  onRetry,
  onClose,
  closeHref,
  onNextStep,
  nextStepHref,
  onReport,
  reportHref,
  inline,
  now,
  timeZone,
}: TutorViewProps) {
  const titleId = useId();
  const inputId = useId();
  const listRef = useRef<HTMLDivElement>(null);
  const hasAsked = messages.some((message) => message.role === "student");
  const lastAssistant = [...messages].reverse().find((message) => message.role === "assistant");
  const out = notice?.kind === "out_for_today";
  const blocked = out || notice?.kind === "unavailable_question" || notice?.kind === "enrolment_required";
  const noticeInChat = notice && notice.kind !== "quota_low";

  // Keep the learner's latest question at the top, so a long reply reads from its start.
  useEffect(() => {
    const list = listRef.current;
    if (!list) return;
    const asked = list.querySelectorAll<HTMLElement>("[data-tutor-role='student']");
    const last = asked[asked.length - 1];
    list.scrollTop = last ? Math.max(0, last.offsetTop - list.offsetTop - 12) : 0;
    if (sending || (notice && notice.kind !== "quota_low")) list.scrollTop = list.scrollHeight;
  }, [messages.length, sending, notice]);

  useEffect(() => {
    if (!inline && onSend) document.getElementById(inputId)?.focus({ preventScroll: true });
  }, [inline, inputId, onSend]);

  const send = (text: string) => {
    if (!sending && text.trim()) onSend?.(text);
  };

  const body = (
    <section
      role="dialog"
      aria-labelledby={titleId}
      className={cn(
        "relative flex min-h-0 grow flex-col overflow-hidden bg-ns-surface font-ns text-ns-ink",
        inline ? "rounded-3xl border border-ns-line shadow-ns-md" : "mt-[72px] rounded-t-3xl shadow-ns-lg motion-safe:animate-[ns-sheet_.35s_ease-out_both] lg:mt-0 lg:rounded-3xl lg:border lg:border-ns-line",
      )}
      onKeyDown={(event) => {
        if (event.key === "Escape") onClose?.();
      }}
    >
      <div className="flex shrink-0 flex-col gap-2.5 border-b border-ns-line px-4 pt-2 pb-3 lg:px-5 lg:pt-4">
        <span aria-hidden="true" className={cn("h-1 w-10 self-center rounded-full bg-ns-line", !inline && "lg:hidden")} />
        <TutorHeader
          titleId={titleId}
          sub={solutionOpen ? "AI helper · explaining the solution" : "AI helper · uses the lesson"}
          onClose={onClose}
          closeHref={closeHref}
        />
        <div className={cn(!inline && "lg:hidden")}>
          <QuestionPin
            label={questionLabel}
            summary={questionSummary}
            wrongTries={wrongTries}
            solutionOpen={solutionOpen}
            onClick={onClose}
            href={closeHref}
          />
        </div>
        <div className={cn("hidden flex-wrap gap-1.5", !inline && "lg:flex")}>
          <span className="inline-flex h-6 items-center rounded-full bg-ns-sunken px-2.5 text-xs font-semibold text-ns-muted shadow-[inset_0_0_0_1px_var(--color-ns-line)]">
            {questionLabel}
          </span>
          <TriesTag wrongTries={wrongTries} solutionOpen={solutionOpen} />
        </div>
      </div>

      <div ref={listRef} aria-live="polite" className="flex min-h-0 grow flex-col gap-3.5 overflow-y-auto p-4 lg:p-5">
        {!hasAsked ? (
          <>
            <AiNotice />
            <Greeting name={studentName} />
          </>
        ) : null}
        {messages.map((message) =>
          message.role === "student" ? (
            <StudentMessage key={message.id} message={message} />
          ) : (
            <AssistantMessage
              key={message.id}
              message={message}
              report={
                message.id === lastAssistant?.id && (onReport || reportHref) ? (
                  <ReportLink onClick={onReport ? () => onReport(message.id) : undefined} href={reportHref} />
                ) : undefined
              }
            />
          ),
        )}
        {!hasAsked && !blocked ? <StarterQuestions onPick={send} disabled={sending} /> : null}
        {sending ? <Thinking /> : null}
        {noticeInChat ? <NoticeView notice={notice} onRetry={onRetry} now={now} timeZone={timeZone} /> : null}
      </div>

      <div className="flex shrink-0 flex-col gap-2.5 border-t border-ns-line bg-ns-surface px-4 pt-3 pb-5 lg:px-5">
        {out ? (
          <>
            <Button variant="primary" full onClick={onClose} href={closeHref}>
              Back to the question
            </Button>
          </>
        ) : (
          <>
            {nextStep && !sending ? <NextStep label={nextStep} onClick={onNextStep ?? onClose} href={nextStepHref} /> : null}
            {hasAsked && !sending ? (
              <SuggestedReplies items={suggestions} onPick={send} disabled={blocked} />
            ) : null}
            {notice?.kind === "quota_low" ? <NoticeView notice={notice} now={now} timeZone={timeZone} /> : null}
            <Composer
              inputId={inputId}
              value={draft}
              onChange={onDraftChange}
              onSend={() => send(draft ?? "")}
              sending={sending}
              disabled={blocked}
              maxLength={TUTOR_MESSAGE_MAX_LENGTH}
              placeholder={
                solutionOpen ? "Ask about any step" : hasAsked ? "Ask about this question" : "Or type your own question"
              }
            />
          </>
        )}
      </div>
    </section>
  );

  if (inline) {
    return (
      <div className="ns-root flex h-full min-h-[640px] flex-col">
        <TutorStyles />
        {body}
      </div>
    );
  }
  return (
    <div className="ns-root fixed inset-0 z-40 flex flex-col lg:inset-auto lg:top-4 lg:right-4 lg:bottom-4 lg:w-[440px]">
      <TutorStyles />
      <div aria-hidden="true" className="absolute inset-0 bg-ns-dark/45 lg:hidden" onClick={onClose} />
      {body}
    </div>
  );
}
