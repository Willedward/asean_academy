"use client";

/**
 * Report a reply, and the free-plan Season pass sheet.
 * Canvas: TutorReport.m, TutorPlan.m
 */
import { useId, useState } from "react";
import { BookOpen, Lightbulb, Mail, Target } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { RewardLine } from "../components/rewards";
import { Button, Eyebrow, Muted, Sheet, focusRing } from "../components/ui";
import type { Href } from "../types";
import { HornbillAvatar } from "./parts";
import { REPORT_REASONS, type TutorReportReason } from "./types";

export interface ReportReplySheetProps {
  /**
   * NEW backend: POST /tutor/sessions/{id}/messages/{message_id}/report
   * with { reason, note }. See TUTOR.md.
   */
  onSubmit?: (reason: TutorReportReason, note: string) => void | Promise<void>;
  onCancel?: () => void;
  cancelHref?: Href;
  /** Shows the thank-you state. */
  sent?: boolean;
  submitting?: boolean;
  initialReason?: TutorReportReason;
}

export function ReportReplySheet({
  onSubmit,
  onCancel,
  cancelHref,
  sent,
  submitting,
  initialReason = "maths_wrong",
}: ReportReplySheetProps) {
  const titleId = useId();
  const noteId = useId();
  const [reason, setReason] = useState<TutorReportReason>(initialReason);
  const [note, setNote] = useState("");
  if (sent) {
    return (
      <Sheet titleId={titleId}>
        <div className="flex flex-col items-center gap-2 text-center">
          <Hornbill size={88} mood="happy" branch={false} />
          <h2 id={titleId} className="m-0 text-xl leading-7 font-semibold">
            Thanks for telling us
          </h2>
          <Muted>A teacher on the NextScholar team will look at this reply.</Muted>
        </div>
        <Button variant="primary" full onClick={onCancel} href={cancelHref}>
          Back to the chat
        </Button>
      </Sheet>
    );
  }
  return (
    <Sheet titleId={titleId}>
      <h2 id={titleId} className="m-0 text-xl leading-7 font-semibold">
        Report this reply
      </h2>
      <Muted>A teacher on the NextScholar team will look at it. Thanks for helping the hornbill get better.</Muted>
      <form
        className="flex flex-col gap-3.5"
        onSubmit={(event) => {
          event.preventDefault();
          void onSubmit?.(reason, note.trim());
        }}
      >
        <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
          <legend className="sr-only">What went wrong?</legend>
          {REPORT_REASONS.map((option) => (
            <label
              key={option.value}
              className={cn(
                "flex min-h-12 cursor-pointer items-center gap-3 rounded-xl border-[1.5px] px-3.5 text-[15px] font-semibold",
                reason === option.value ? "border-ns-ink bg-ns-brand-soft" : "border-ns-line bg-ns-raised",
              )}
            >
              <input
                type="radio"
                name="reason"
                value={option.value}
                checked={reason === option.value}
                onChange={() => setReason(option.value)}
                className={cn("m-0 size-5 accent-ns-ink", focusRing)}
              />
              {option.label}
            </label>
          ))}
        </fieldset>
        <label htmlFor={noteId} className="text-[15px] font-semibold">
          Anything else? <span className="font-normal text-ns-muted">(optional)</span>
        </label>
        <textarea
          id={noteId}
          name="note"
          rows={2}
          maxLength={500}
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="For example: 3 has power 2, not 3"
          className={cn("resize-none rounded-xl border-[1.5px] border-ns-line-strong bg-ns-raised px-3.5 py-3 text-base leading-[22px]", focusRing)}
        />
        <div className="flex flex-col gap-2">
          <Button variant="primary" full type="submit" disabled={submitting}>
            {submitting ? "Sending…" : "Send report"}
          </Button>
          <Button full onClick={onCancel} href={cancelHref}>
            Cancel
          </Button>
        </div>
      </form>
    </Sheet>
  );
}

export interface TutorPlanSheetProps {
  /** NEW: sends the Season pass details to the parent on file. */
  onSendToParent?: () => void;
  parentSent?: boolean;
  onClose?: () => void;
  closeHref?: Href;
  plansHref: Href;
}

/** Free plan: the tutor is part of the Season pass. Students are 12 to 15, so the main action involves a parent. */
export function TutorPlanSheet({ onSendToParent, parentSent, onClose, closeHref, plansHref }: TutorPlanSheetProps) {
  const titleId = useId();
  return (
    <Sheet titleId={titleId}>
      <div className="flex items-center gap-3">
        <Hornbill size={80} mood="happy" outfit="cap" branch={false} label="Hornbill with a graduation cap" />
        <div className="flex min-w-0 grow flex-col gap-1">
          <Eyebrow>SEASON PASS</Eyebrow>
          <h2 id={titleId} className="m-0 text-xl leading-[26px] font-bold">
            Get help from the hornbill on every question
          </h2>
        </div>
      </div>
      <div aria-hidden="true" className="flex flex-col gap-1.5 rounded-[14px] bg-ns-sunken p-3">
        <span className="self-end rounded-[14px_14px_4px_14px] bg-ns-ink px-3 py-2 text-[13px] leading-[18px] text-ns-on-brand">
          I still don’t get it
        </span>
        <span className="flex items-start gap-1.5 self-start">
          <HornbillAvatar size={24} />
          <span className="rounded-[4px_14px_14px_14px] border border-ns-line bg-ns-raised px-3 py-2 text-[13px] leading-[18px]">
            No problem. Let’s try a smaller number first…
          </span>
        </span>
      </div>
      <RewardLine icon={<Target size={20} aria-hidden />} title="Help on any practice question" sub="After your first try, so you always think first." />
      <RewardLine icon={<BookOpen size={20} aria-hidden />} title="Explains every step of the solution" sub="Ask “why?” as many times as you need." />
      <RewardLine icon={<Lightbulb size={20} aria-hidden />} title="Hints stay free for everyone" sub="You can keep practising on the free plan." />
      <div className="flex flex-col gap-2">
        <Button variant="primary" full icon={Mail} onClick={onSendToParent} disabled={parentSent}>
          {parentSent ? "Sent to your parent" : "Send this to my parent"}
        </Button>
        <Button full onClick={onClose} href={closeHref}>
          Not now
        </Button>
      </div>
      <Link href={plansHref} className={cn("self-center text-sm font-semibold", focusRing)}>
        See what’s in the Season pass
      </Link>
    </Sheet>
  );
}
