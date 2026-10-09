"use client";

/**
 * Drop-in tutor for a practice question: the "Ask the hornbill" entry point plus
 * the chat window, wired to the Learning API.
 *
 *   <TutorDock
 *     practiceSessionId={sessionId}
 *     questionKey={question.stable_key}
 *     questionRevision={question.revision}
 *     wrongTries={attempt?.correct ? 0 : attempt?.attempt_number ?? 0}
 *     solutionOpen={Boolean(solution)}
 *     questionLabel={`Question ${position}`}
 *   />
 *
 * Place it where the button should appear (for example next to the hint
 * buttons). The window itself is fixed to the screen, so it does not change the
 * page layout. Each question gets a fresh conversation.
 */
import { useState, type ReactNode } from "react";

import type { Href } from "../types";
import { AskHornbillButton, AskHornbillCard, AskHornbillNudge } from "./launcher";
import { ReportReplySheet, TutorPlanSheet } from "./sheets";
import { TutorView } from "./tutor-view";
import type { TutorLaunchState, TutorReportReason } from "./types";
import { useTutor, type TutorIdentity } from "./use-tutor";

export interface TutorDockProps extends TutorIdentity {
  /**
   * Wrong checks on this question so far. The tutor only appears after the
   * first try (decision 2026-10-09). 0 hides it.
   */
  wrongTries: number;
  /** Whether Give up has opened the solution. The server's lock state wins once a reply arrives. */
  solutionOpen?: boolean;
  /** API: PracticeSessionResponse.mode. The tutor never appears in a checkpoint. */
  practiceMode?: string;
  /** Free plan: the button shows a lock and opens the Season pass sheet. NEW (V2 plans). */
  plan?: "included" | "locked";
  /** e.g. "Question 2 · part (b)" */
  questionLabel: string;
  /** One line of the question for the pinned bar on phones. */
  questionSummary?: ReactNode;
  studentName?: string;
  /** button: inline button. nudge: button plus the hornbill's one-line nudge. card: desktop side card. */
  launcher?: "button" | "nudge" | "card";
  plansHref?: Href;
  signInHref?: string;
  /** NEW backend. Leave out to hide "Report this reply". */
  onReport?: (report: { sessionId: string; messageId: string; reason: TutorReportReason; note: string }) => Promise<void>;
  /** NEW backend. Sends the Season pass details to the parent. */
  onSendToParent?: () => Promise<void>;
  accessToken?: string;
  /**
   * Told when the chat window opens or closes. On desktop the panel covers the
   * right 456px of the screen, so a page can add `lg:pr-[456px]` while it is open.
   */
  onOpenChange?: (open: boolean) => void;
}

/** Keys the inner dock by question, so a new question always starts a new conversation. */
export function TutorDock(props: TutorDockProps) {
  return <TutorDockForQuestion key={`${props.practiceSessionId}:${props.questionKey}:${props.questionRevision}`} {...props} />;
}

function TutorDockForQuestion({
  practiceSessionId,
  questionKey,
  questionRevision,
  wrongTries,
  solutionOpen = false,
  practiceMode,
  plan = "included",
  questionLabel,
  questionSummary,
  studentName,
  launcher = "button",
  plansHref = "/plans",
  signInHref = "/login",
  onReport,
  onSendToParent,
  accessToken,
  onOpenChange,
}: TutorDockProps) {
  const tutor = useTutor({
    practiceSessionId,
    questionKey,
    questionRevision,
    accessToken,
    onSignIn: () => window.location.assign(signInHref),
  });
  const { state } = tutor;
  const [open, setOpenState] = useState(false);
  const setOpen = (next: boolean) => {
    setOpenState(next);
    onOpenChange?.(next);
  };
  const [draft, setDraft] = useState("");
  const [planOpen, setPlanOpen] = useState(false);
  const [parentSent, setParentSent] = useState(false);
  const [reportFor, setReportFor] = useState<string | null>(null);
  const [reportState, setReportState] = useState<"idle" | "sending" | "sent">("idle");

  const hidden = practiceMode === "checkpoint" || wrongTries < 1 || state.availability === "disabled";
  if (hidden) return null;

  const launchState: TutorLaunchState = plan === "locked" || state.planRequired ? "locked" : "available";
  const showPlan = planOpen || (open && state.planRequired);

  const openTutor = () => {
    if (launchState === "locked") {
      setPlanOpen(true);
      return;
    }
    setOpen(true);
    void tutor.ensureSession();
  };
  const send = (text: string) => {
    setDraft("");
    void tutor.send(text);
  };
  const startWith = (text: string) => {
    if (launchState === "locked") {
      setPlanOpen(true);
      return;
    }
    setOpen(true);
    send(text);
  };

  return (
    <>
      {launcher === "card" ? (
        <AskHornbillCard state={launchState} onOpen={openTutor} onStarter={startWith} />
      ) : (
        <span className="contents">
          {launcher === "nudge" && !open ? <AskHornbillNudge /> : null}
          <AskHornbillButton state={launchState} onClick={openTutor} />
        </span>
      )}

      {open && !showPlan ? (
        <TutorView
          questionLabel={questionLabel}
          questionSummary={questionSummary}
          wrongTries={wrongTries}
          solutionOpen={state.lock ? !state.lock.solution_locked : solutionOpen}
          studentName={studentName}
          messages={state.messages}
          sending={state.send === "sending" || state.session === "creating"}
          suggestions={state.suggestions}
          nextStep={state.nextStep}
          notice={state.notice}
          draft={draft}
          onDraftChange={setDraft}
          onSend={send}
          onRetry={() => void tutor.retry()}
          onClose={() => setOpen(false)}
          onReport={
            onReport && state.sessionId
              ? (messageId) => {
                  setReportState("idle");
                  setReportFor(messageId);
                }
              : undefined
          }
        />
      ) : null}

      {reportFor && onReport && state.sessionId ? (
        <ReportReplySheet
          sent={reportState === "sent"}
          submitting={reportState === "sending"}
          onCancel={() => setReportFor(null)}
          onSubmit={async (reason, note) => {
            setReportState("sending");
            try {
              await onReport({ sessionId: state.sessionId ?? "", messageId: reportFor, reason, note });
              setReportState("sent");
            } catch {
              setReportState("idle");
            }
          }}
        />
      ) : null}

      {showPlan ? (
        <TutorPlanSheet
          plansHref={plansHref}
          parentSent={parentSent}
          onSendToParent={
            onSendToParent
              ? () => {
                  void onSendToParent().then(() => setParentSent(true));
                }
              : undefined
          }
          onClose={() => {
            setPlanOpen(false);
            setOpen(false);
          }}
        />
      ) : null}
    </>
  );
}
