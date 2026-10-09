"use client";

/**
 * Entry points to the hornbill tutor. Shown only after the learner's first try.
 * Canvas: TutorEntry.m (button + nudge), TutorEntry.d (card), TutorPlan.m (locked)
 */
import { Lock, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { Bubble } from "../components/rewards";
import { Card, H3, Muted, focusRing } from "../components/ui";
import type { Href } from "../types";
import { HornbillAvatar, StarterQuestions } from "./parts";
import type { TutorLaunchState } from "./types";

export function AskHornbillButton({
  state,
  onClick,
  href,
  full,
  variant = "soft",
  className,
}: {
  state: TutorLaunchState;
  onClick?: () => void;
  href?: Href;
  full?: boolean;
  variant?: "soft" | "primary";
  className?: string;
}) {
  if (state === "hidden") return null;
  const locked = state === "locked";
  const classes = cn(
    "inline-flex h-11 items-center justify-center gap-2 rounded-full border-[1.5px] py-0 pr-4 pl-1.5 text-[15px] font-bold whitespace-nowrap no-underline",
    variant === "primary" ? "border-ns-ink bg-ns-ink text-ns-on-brand hover:bg-ns-dark" : "border-ns-ink bg-ns-brand-soft text-ns-ink hover:bg-ns-sunken",
    full && "flex w-full",
    focusRing,
    className,
  );
  const inner = (
    <>
      <HornbillAvatar size={32} mood="happy" />
      Ask the hornbill
      {locked ? <Lock size={16} aria-label="Season pass" /> : null}
    </>
  );
  return href ? (
    <Link href={href} className={classes}>
      {inner}
    </Link>
  ) : (
    <button type="button" onClick={onClick} className={classes} aria-haspopup="dialog">
      {inner}
    </button>
  );
}

/** One-line nudge from the hornbill above the phone footer, the first time the button appears. */
export function AskHornbillNudge({ children = "Stuck? Ask me. I’ll help you think it through, without giving it away." }: { children?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2.5 motion-safe:animate-ns-pop">
      <div className="motion-safe:animate-ns-float">
        <Hornbill size={58} mood="happy" pose="point" branch={false} />
      </div>
      <div className="grow">
        <Bubble>{children}</Bubble>
      </div>
    </div>
  );
}

/** Desktop side card: starters plus the button. */
export function AskHornbillCard({
  state,
  onOpen,
  onStarter,
  href,
}: {
  state: TutorLaunchState;
  onOpen?: () => void;
  /** Opens the tutor and sends the starter as the first message. */
  onStarter?: (text: string) => void;
  href?: Href;
}) {
  if (state === "hidden") return null;
  return (
    <Card className="gap-3.5 border-[#B9CCCA] shadow-ns-md">
      <div className="flex items-center gap-3">
        <div className="motion-safe:animate-ns-float">
          <Hornbill size={84} mood="happy" pose="point" branch={false} />
        </div>
        <div className="flex min-w-0 grow flex-col gap-1">
          <H3>Stuck? Ask the hornbill</H3>
          <Muted>I’ll help you think it through, step by step. I won’t give the answer away.</Muted>
        </div>
      </div>
      {state === "available" ? <StarterQuestions onPick={onStarter} disabled={!onStarter} /> : null}
      <AskHornbillButton state={state} onClick={onOpen} href={href} full variant="primary" />
      <span className="flex items-start gap-1.5 text-xs leading-4 text-ns-muted">
        <ShieldCheck size={14} className="shrink-0" aria-hidden />
        AI helper. Your answer is checked by the answer checker, not the chat.
      </span>
    </Card>
  );
}
