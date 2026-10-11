/**
 * Getting into English from the home screen (decision 2026-10-11): the
 * dashboard shows an "Up next in English" card under the maths "Up next" card,
 * and the Course tab has a Maths | English switch on both sides.
 *
 * Canvas: Dashboard.m, Dashboard.d (English card), CourseMap.m, CourseMap.d (switch)
 */
import Link from "next/link";
import { ArrowRight, BookOpen, ChevronRight, FileText, Target } from "lucide-react";

import { cn } from "@/lib/utils";

import { XpPill } from "../components/rewards";
import { Bar, Button, Card, H3, Muted, Tag, focusRing } from "../components/ui";
import type { Href, Quest } from "../types";

/** NEW. Everything the dashboard needs to point a learner back into English. */
export interface EnglishUpNext {
  /** The grammar unit in progress (or the next one to start). NEW: grammar progress per learner. */
  grammar?: { title: string; done: number; total: number; href: Href };
  /** The latest unsubmitted essay draft. NEW: essay drafts with autosave. */
  draft?: { title: string; words: number; minWords: number; submitXp: number; href: Href };
  /** Today's English quest, if any. NEW: daily quests. */
  quest?: Quest;
  /** XP shown on the card (the grammar set or the quest). */
  xp: number;
  /** English home, the English side of the Course tab. */
  homeHref: Href;
}

/** Canvas: Dashboard.m, Dashboard.d */
export function EnglishUpNextCard({ data }: { data: EnglishUpNext }) {
  const { grammar, draft, quest } = data;
  return (
    <Card className="gap-3.5">
      <div className="flex items-center gap-2">
        <Tag tone="brand" icon={BookOpen}>
          English
        </Tag>
        <span className="text-[13px] text-ns-muted">Up next</span>
        <span className="ml-auto">
          <XpPill xp={data.xp} />
        </span>
      </div>

      {grammar ? (
        <div className="flex flex-col gap-2">
          <H3>{grammar.title}</H3>
          <Muted>
            Grammar · {grammar.done} of {grammar.total} questions done. Each answer gets a one-line reason.
          </Muted>
          <Bar pct={(grammar.done / Math.max(1, grammar.total)) * 100} fill="success" />
        </div>
      ) : null}

      {draft ? (
        <Link
          href={draft.href}
          className={cn("flex items-center gap-3 rounded-xl bg-ns-sunken p-3 text-ns-ink no-underline hover:bg-ns-line/60", focusRing)}
        >
          <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-[10px] bg-ns-raised text-ns-amber-text">
            <FileText size={18} aria-hidden />
          </span>
          <span className="flex min-w-0 grow flex-col">
            <span className="text-sm leading-5 font-bold">Draft saved: {draft.title}</span>
            <span className="text-[13px] leading-[18px] text-ns-muted">
              {draft.words} of {draft.minWords} words · submit for +{draft.submitXp} XP
            </span>
          </span>
          <ChevronRight size={18} className="shrink-0 text-ns-muted" aria-hidden />
        </Link>
      ) : null}

      {quest ? (
        <span className="inline-flex items-start gap-1.5 text-[13px] leading-[18px] font-semibold text-ns-amber-text">
          <Target size={16} className="mt-px shrink-0" aria-hidden />
          English quest: {quest.title} ({Math.min(quest.progress, quest.target)} of {quest.target})
        </span>
      ) : null}

      <div className="flex flex-col gap-1 lg:flex-row lg:gap-2">
        {grammar ? (
          <div className="lg:grow">
            <Button variant="primary" full href={grammar.href} iconRight={ArrowRight}>
              {grammar.done ? "Continue grammar" : "Start grammar"}
            </Button>
          </div>
        ) : null}
        <Button variant="ghost" full href={data.homeHref} iconRight={ChevronRight} className="lg:hidden">
          See all English
        </Button>
        <Button href={data.homeHref} className="hidden lg:inline-flex">
          All English
        </Button>
      </div>
    </Card>
  );
}
