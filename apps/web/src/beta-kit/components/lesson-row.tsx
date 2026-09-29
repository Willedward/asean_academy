import Link from "next/link";
import { Check, CheckCircle2, Clock, Lock } from "lucide-react";

import { cn } from "@/lib/utils";

import type { LessonSummary, LessonUiState, Tone } from "../types";
import { Stars, XpTag } from "./rewards";
import { Tag, focusRing } from "./ui";

const LABEL: Record<LessonUiState, { label: string; tone: Tone }> = {
  locked: { label: "Locked", tone: "neutral" },
  ready: { label: "Ready to start", tone: "brand" },
  practising: { label: "Practising", tone: "amber" },
  proficient: { label: "Proficient", tone: "success" },
  mastered: { label: "Mastered", tone: "success" },
  in_review: { label: "Being reviewed", tone: "neutral" },
};

export function LessonStateTag({ state }: { state: LessonUiState }) {
  const { label, tone } = LABEL[state];
  const icon = state === "locked" ? Lock : state === "in_review" ? Clock : state === "proficient" || state === "mastered" ? CheckCircle2 : undefined;
  return (
    <Tag tone={tone} icon={icon}>
      {label}
    </Tag>
  );
}

/** One lesson in a unit list. `compact` hides the state tag (dashboard). */
export function LessonRow({ lesson, compact }: { lesson: LessonSummary; compact?: boolean }) {
  const locked = lesson.state === "locked";
  const done = lesson.state === "proficient" || lesson.state === "mastered";
  const practising = lesson.state === "practising";
  const meta = locked
    ? (lesson.lockedReason ?? "Locked")
    : `${lesson.minutes} min · ${lesson.questionCount} question${lesson.questionCount === 1 ? "" : "s"}`;

  const inner = (
    <>
      <span
        className={cn(
          "inline-flex size-9 shrink-0 items-center justify-center rounded-full text-[15px] font-bold",
          done && "bg-ns-success-soft text-ns-success",
          practising && "bg-ns-amber-soft text-ns-amber-text",
          locked && "bg-ns-sunken text-ns-muted",
          !done && !practising && !locked && "bg-ns-brand-soft text-ns-ink",
        )}
      >
        {done ? <Check size={18} aria-label="Done" /> : locked ? <Lock size={16} aria-label="Locked" /> : lesson.position}
      </span>
      <div className="flex min-w-0 grow flex-col gap-0.5">
        <span className={cn("text-base leading-[22px] font-semibold", locked ? "text-ns-muted" : "text-ns-ink")}>
          Lesson {lesson.position} · {lesson.title}
        </span>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <span className="text-[13px] leading-[18px] text-ns-muted">{meta}</span>
          {!locked && lesson.stars > 0 ? <Stars count={lesson.stars} size={13} /> : null}
          {!locked && lesson.stars === 0 && lesson.xpAvailable ? <XpTag xp={lesson.xpAvailable} size={12} /> : null}
        </div>
      </div>
      {compact ? null : <LessonStateTag state={lesson.state} />}
    </>
  );

  const rowClass = cn("flex items-center gap-3.5 rounded-xl px-4 py-3", practising && "bg-ns-amber-soft");
  if (locked) return <div className={rowClass}>{inner}</div>;
  return (
    <Link href={lesson.href} className={cn(rowClass, "text-inherit no-underline hover:bg-ns-sunken", practising && "hover:bg-ns-amber-soft", focusRing)}>
      {inner}
    </Link>
  );
}
