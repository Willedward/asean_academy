import Link from "next/link";
import { ArrowRight, Check, ChevronLeft, Clock, Eye, Flag, Lock, RotateCcw, Target } from "lucide-react";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { GameIcon } from "../components/icons";
import { LessonRow, LessonStateTag } from "../components/lesson-row";
import {
  BonusChest,
  Confetti,
  DoubleXpPill,
  MascotCard,
  MascotSays,
  Medal,
  MiniChips,
  QuestRow,
  QuestsCard,
  Stars as StarRow,
  XpPill,
  XpTag,
} from "../components/rewards";
import { Bar, Button, Card, Eyebrow, H1, H2, H3, IconCircle, Muted, ProgressBar, Tag, focusRing } from "../components/ui";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import { AppShell, FocusShell, FooterBar, StatBar, TopBar } from "../shell/app-shell";
import type {
  Badge,
  ContinueCard as ContinueData,
  Href,
  LaterReviewItem,
  Outfit,
  Player,
  QuestBoard,
  ReviewItem,
  StreakDay,
  StreakMilestone,
  StreakWeek,
  UnitSummary,
  XpLine,
} from "../types";
import { ContinueCard, WeekStatsCard } from "./dashboard";

/* ------------------------------------------------------------------ */
/* Shared pieces (also used by screens/me.tsx)                         */
/* ------------------------------------------------------------------ */

const firstName = (player: Player) => player.displayName.split(" ")[0] ?? player.displayName;

/** Desktop-only back link above a page heading ("< Course"). */
export function BackLink({ href, label }: { href: Href; label: string }) {
  return (
    <Link
      href={href}
      className={cn(
        "hidden h-8 items-center gap-1 self-start rounded-full pr-2 text-sm font-semibold text-ns-muted no-underline hover:text-ns-ink lg:inline-flex",
        focusRing,
      )}
    >
      <ChevronLeft size={16} aria-hidden />
      {label}
    </Link>
  );
}

function StarGlyph({ size = 14, className }: { size?: number; className?: string }) {
  return <GameIcon name="star" size={size} className={cn("text-ns-gold", className)} />;
}

/** Plain list of how XP is earned ("Right first try +10 XP"). */
export function XpRulesCard({ title, rules, note }: { title: string; rules: XpLine[]; note?: string }) {
  return (
    <Card className="gap-3">
      <H3>{title}</H3>
      <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
        {rules.map((rule) => (
          <li key={rule.label} className="flex items-center gap-2">
            <span className="grow text-[15px] leading-5">{rule.label}</span>
            <XpTag xp={rule.xp} size={14} />
          </li>
        ))}
      </ul>
      {note ? <Muted className="text-[13px] leading-[18px]">{note}</Muted> : null}
    </Card>
  );
}

/** "Master N1 to win / Number master badge and +100 XP". */
export function UnitRewardLine({ unit, pill }: { unit: UnitSummary; pill?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <Medal icon="trophy" tier="gold" size={40} />
      <div className="flex min-w-0 grow flex-col gap-0.5">
        <span className="text-[15px] leading-5 font-bold">Master {unit.code} to win</span>
        <span className="text-[13px] leading-[18px] text-ns-muted">
          {unit.checkpoint.rewardBadge} badge and +{unit.checkpoint.rewardXp} XP
        </span>
      </div>
      {pill ? <XpPill xp={unit.checkpoint.rewardXp} /> : null}
    </div>
  );
}

/** One question on the Try again list, compact (dashboard). */
function ReviewLine({ item }: { item: ReviewItem }) {
  return (
    <li className="flex items-center gap-2.5">
      <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-ns-raised text-ns-amber-text">
        <RotateCcw size={16} aria-hidden />
      </span>
      <span className="flex min-w-0 grow flex-col">
        <span className="text-[15px] leading-5 font-semibold">{item.title}</span>
        <span className="text-[13px] leading-[18px] text-ns-muted">{item.reason}</span>
      </span>
      <XpTag xp={item.xp} />
    </li>
  );
}

/** Small medal with a progress bar, e.g. Review master 12/20. */
export function BadgeProgressRow({ badge, dim, barFill = "amber" }: { badge: Badge; dim?: boolean; barFill?: "amber" | "success" }) {
  const current = badge.progress?.current ?? 0;
  const target = badge.progress?.target ?? 1;
  return (
    <div className="flex items-center gap-2.5">
      <span className={cn("inline-flex", dim && "opacity-50")}>
        <Medal icon={badge.icon} tier={badge.tier} size={36} />
      </span>
      <div className="flex min-w-0 grow flex-col gap-1">
        <b className="text-sm leading-5">{badge.name}</b>
        <div role="progressbar" aria-label={`${badge.name} progress`} aria-valuenow={current} aria-valuemin={0} aria-valuemax={target}>
          <Bar pct={(current / target) * 100} height={6} fill={barFill} />
        </div>
      </div>
      <span className="text-[13px] text-ns-muted tabular-nums">
        {current}/{target}
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Dashboard: new student (level 1)                                    */
/* ------------------------------------------------------------------ */

/** API: NextActionResponse with type "start_lesson". */
export interface StartLessonCardData {
  /** e.g. "Lesson 1 of 7 · 25 min". API: CourseLessonMap.position, estimated_minutes */
  lessonLabel: string;
  /** API: NextActionResponse.title */
  title: string;
  /** API: NextActionResponse.description */
  description: string;
  /** e.g. "Start Lesson 1" */
  ctaLabel: string;
  /** API: NextActionResponse.href */
  href: Href;
  /** NEW. XP on offer in the lesson. */
  xp: number;
}

export interface DashboardNewProps {
  player: Player;
  /** NEW. Sign-up bonus already credited. */
  welcomeBonusXp: number;
  start: StartLessonCardData;
  quests: QuestBoard;
  /** NEW. "How you earn XP" list. */
  xpRules: XpLine[];
  /** NEW. Next wardrobe item and when it unlocks. */
  nextUnlock: { level: number; outfit: Outfit; description: string };
  routes?: KitRoutes;
}

function StartCard({ start }: { start: StartLessonCardData }) {
  return (
    <Card className="gap-3.5 p-6 shadow-ns-md">
      <div className="flex flex-wrap items-center gap-2.5">
        <Tag tone="amber">Start here</Tag>
        <span className="text-[13px] text-ns-muted">{start.lessonLabel}</span>
        <span className="ml-auto">
          <XpPill xp={start.xp} />
        </span>
      </div>
      <H2 className="lg:text-[22px] lg:leading-[30px]">{start.title}</H2>
      <Muted className="text-[15px] leading-[22px]">{start.description}</Muted>
      <div className="flex items-center gap-2">
        <StarRow count={0} size={22} />
        <span className="text-[13px] text-ns-muted">Win up to 3 stars</span>
      </div>
      <Button variant="primary" full href={start.href} iconRight={ArrowRight} className="lg:w-auto lg:self-start">
        {start.ctaLabel}
      </Button>
    </Card>
  );
}

function TodaysQuestsCard({ board }: { board: QuestBoard }) {
  return (
    <Card className="gap-4">
      <div className="flex items-center justify-between gap-3">
        <H3>Today’s quests</H3>
        <span className="text-[13px] text-ns-muted">New every morning</span>
      </div>
      {board.quests.map((quest) => (
        <QuestRow key={quest.id} quest={quest} />
      ))}
      <BonusChest board={board} />
    </Card>
  );
}

function UnlockTeaser({ unlock }: { unlock: DashboardNewProps["nextUnlock"] }) {
  return (
    <Card tone="sunken" className="flex-row items-center gap-3 p-4">
      <span className="relative inline-flex size-14 shrink-0 items-center justify-center rounded-2xl bg-ns-amber-soft">
        <Hornbill size={48} crop="head" outfit={unlock.outfit} />
        <span className="absolute -top-1 -right-1 text-ns-muted">
          <GameIcon name="lock" size={16} />
        </span>
      </span>
      <div className="flex min-w-0 grow flex-col gap-0.5">
        <H3>Unlock at Level {unlock.level}</H3>
        <Muted>{unlock.description}</Muted>
      </div>
    </Card>
  );
}

/** Canvas: DashboardNew.m */
export function DashboardNewScreen({ player, welcomeBonusXp, start, quests, xpRules, nextUnlock, routes = PREVIEW_ROUTES }: DashboardNewProps) {
  const earn = <XpRulesCard title="How you earn XP" rules={xpRules} note="Mistakes never cost XP. Speed never earns it." />;
  return (
    <AppShell active="learn" player={player} routes={routes} top={<StatBar player={player} routes={routes} />}>
      <H1 className="sr-only">Welcome, {firstName(player)}</H1>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-6">
        <div className="flex flex-col gap-4 lg:gap-5">
          <MascotSays mood="happy" pose="cheer" outfit={player.equippedOutfit} size={72}>
            Welcome, {firstName(player)}! Your <b className="text-ns-amber-text">+{welcomeBonusXp} XP</b> bonus is in. Answer 1 question
            today to light your first streak flame.
          </MascotSays>
          <StartCard start={start} />
          <div className="lg:hidden">
            <TodaysQuestsCard board={quests} />
          </div>
          {earn}
          <div className="lg:hidden">
            <UnlockTeaser unlock={nextUnlock} />
          </div>
        </div>
        <div className="hidden flex-col gap-5 lg:flex">
          <TodaysQuestsCard board={quests} />
          <UnlockTeaser unlock={nextUnlock} />
        </div>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Dashboard: reviews waiting (double XP)                              */
/* ------------------------------------------------------------------ */

export interface ReviewRound {
  /** NEW. Due items from the Try again list. */
  items: ReviewItem[];
  /** NEW. Estimated minutes for the whole round. */
  minutes: number;
  /** NEW. The Review master badge with progress. */
  badge: Badge;
  startHref: Href;
  /** e.g. "Later. Go to Lesson 2". API: NextActionResponse */
  later: { label: string; href: Href };
}

export interface DashboardReviewProps {
  player: Player;
  /** e.g. "Welcome back" */
  greeting: string;
  review: ReviewRound;
  continueCard: ContinueData;
  quests: QuestBoard;
  week: StreakWeek;
  routes?: KitRoutes;
}

function ReviewRoundCard({ review }: { review: ReviewRound }) {
  const total = review.items.reduce((sum, item) => sum + item.xp, 0);
  const count = review.items.length;
  return (
    <Card tone="amber" className="gap-3.5 p-6 shadow-ns-md">
      <div className="flex items-center gap-2.5">
        <Hornbill size={64} mood="think" branch={false} />
        <div className="flex min-w-0 grow flex-col gap-1">
          <DoubleXpPill />
          <H2 className="text-[22px] leading-7">
            {count} question{count === 1 ? " is" : "s are"} back
          </H2>
          <span className="text-[13px] leading-[18px] text-ns-muted">
            About {review.minutes} minutes · up to +{total} XP
          </span>
        </div>
      </div>
      <p className="m-0 text-[15px] leading-[22px] text-ns-muted">
        A question you get right a few days later is one you will still know in the test.
      </p>
      <ul className="m-0 flex list-none flex-col gap-3 p-0">
        {review.items.map((item) => (
          <ReviewLine key={item.questionKey} item={item} />
        ))}
      </ul>
      <BadgeProgressRow badge={{ ...review.badge, name: `${review.badge.name} badge` }} barFill="success" />
      <div className="flex flex-col gap-1">
        <Button variant="primary" full href={review.startHref} iconRight={ArrowRight}>
          Start review · up to +{total} XP
        </Button>
        <Button variant="ghost" full href={review.later.href}>
          {review.later.label}
        </Button>
      </div>
    </Card>
  );
}

/** Canvas: DashboardReview.m */
export function DashboardReviewScreen({ player, greeting, review, continueCard, quests, week, routes = PREVIEW_ROUTES }: DashboardReviewProps) {
  return (
    <AppShell active="learn" player={player} routes={routes} top={<StatBar player={player} routes={routes} />}>
      <div className="flex flex-col gap-1">
        <Muted className="text-[15px] leading-[22px]">
          {greeting}, {firstName(player)}
        </Muted>
        <H1>Double XP is waiting</H1>
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-6">
        <div className="flex flex-col gap-4 lg:gap-5">
          <ReviewRoundCard review={review} />
          <ContinueCard data={continueCard} />
        </div>
        <div className="flex flex-col gap-4 lg:gap-5">
          <QuestsCard board={quests} seeAllHref={routes.quests} />
          <WeekStatsCard player={player} week={week} progressHref={routes.nav.progress} />
        </div>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Dashboard: unit finished                                            */
/* ------------------------------------------------------------------ */

export interface DashboardUnitDoneProps {
  player: Player;
  /** e.g. "Well done" */
  greeting: string;
  /** API: CourseUnitMap.title; code from the unit key. */
  unit: { code: string; title: string };
  /** NEW (stars, bonus) and derived from ProgressResponse (first try). */
  results: { starsEarned: number; starsTotal: number; bonusXp: number; firstTryPct: number };
  /** NEW. e.g. { name: "Number master", note: "Only 4 of 18 beta students have it" } */
  badge: { name: string; note: string };
  resultsHref: Href;
  /** NEW. Spaced recheck offer. */
  recheck: { xp: number; description: string; href: Href };
  quests: QuestBoard;
  /** Next unit still in review. API: CourseUnitMap with lessons content_pending. */
  nextUnit: { code: string } | null;
  routes?: KitRoutes;
}

function UnitDoneHero({ unit, results, badge, resultsHref }: Pick<DashboardUnitDoneProps, "unit" | "results" | "badge" | "resultsHref">) {
  const stats = [
    { value: `${results.starsEarned}/${results.starsTotal}`, label: "Stars" },
    { value: `+${results.bonusXp}`, label: "Bonus XP" },
    { value: `${results.firstTryPct}%`, label: "First try" },
  ];
  return (
    <section
      aria-labelledby="unit-done-title"
      className="relative flex flex-col gap-3.5 overflow-hidden rounded-[20px] bg-ns-ink p-5 text-ns-on-brand shadow-ns-md"
    >
      <Confetti count={18} seed={4} />
      <div className="relative flex items-center gap-3.5">
        <div className="relative size-[110px] shrink-0 text-ns-gold">
          <GameIcon name="trophy" size={96} />
          <div className="absolute -right-2.5 -bottom-1.5">
            <Hornbill size={64} mood="happy" pose="cheer" outfit="cap" branch={false} />
          </div>
        </div>
        <div className="flex min-w-0 flex-col gap-1">
          <span className="text-xs font-extrabold tracking-[0.12em] text-ns-gold">UNIT MASTERED</span>
          <h2 id="unit-done-title" className="m-0 text-2xl leading-7 font-black">
            {unit.code} is done!
          </h2>
          <span className="text-[13px] text-ns-on-dark-muted">{unit.title}</span>
        </div>
      </div>
      <dl className="relative m-0 grid grid-cols-3 gap-2 text-center">
        {stats.map((stat) => (
          <div key={stat.label} className="flex flex-col-reverse gap-0.5">
            <dt className="text-xs text-ns-on-dark-muted">{stat.label}</dt>
            <dd className="m-0 text-[22px] leading-7 font-bold tabular-nums">{stat.value}</dd>
          </div>
        ))}
      </dl>
      <div className="relative flex items-center gap-2.5">
        <Medal icon="trophy" tier="gold" size={40} pop />
        <div className="flex min-w-0 grow flex-col gap-0.5">
          <b className="text-[15px]">{badge.name} badge</b>
          <span className="text-xs text-ns-on-dark-muted">{badge.note}</span>
        </div>
      </div>
      <Button variant="gold" full href={resultsHref} className="relative">
        See checkpoint results
      </Button>
    </section>
  );
}

function RecheckOfferCard({ code, recheck }: { code: string; recheck: DashboardUnitDoneProps["recheck"] }) {
  return (
    <Card className="gap-3.5">
      <div className="flex items-start gap-3">
        <IconCircle icon={Target} tone="brand" size={44} />
        <div className="flex min-w-0 grow flex-col gap-1">
          <div className="flex items-center justify-between gap-2">
            <H3>Keep {code} fresh</H3>
            <XpPill xp={recheck.xp} />
          </div>
          <Muted>{recheck.description}</Muted>
        </div>
      </div>
      <Button variant="primary" full href={recheck.href} iconRight={ArrowRight}>
        Start a recheck
      </Button>
    </Card>
  );
}

function NextUnitPendingCard({ code }: { code: string }) {
  return (
    <Card tone="sunken" shadow={false} className="gap-3">
      <div className="flex items-start gap-3">
        <Hornbill size={56} mood="sleepy" branch={false} />
        <div className="flex min-w-0 grow flex-col gap-1">
          <H3>Next: {code} is being checked</H3>
          <Muted>A former scholar is reviewing every lesson and question. We will email you the day it opens.</Muted>
        </div>
      </div>
      <div>
        <Tag icon={Clock}>Being reviewed</Tag>
      </div>
    </Card>
  );
}

/** Canvas: DashboardUnitDone.m */
export function DashboardUnitDoneScreen({
  player,
  greeting,
  unit,
  results,
  badge,
  resultsHref,
  recheck,
  quests,
  nextUnit,
  routes = PREVIEW_ROUTES,
}: DashboardUnitDoneProps) {
  return (
    <AppShell active="learn" player={player} routes={routes} top={<StatBar player={player} routes={routes} />}>
      <div className="flex flex-col gap-1">
        <Muted className="text-[15px] leading-[22px]">
          {greeting}, {firstName(player)}
        </Muted>
        <H1>You finished {unit.code}</H1>
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-6">
        <div className="flex flex-col gap-4 lg:gap-5">
          <UnitDoneHero unit={unit} results={results} badge={badge} resultsHref={resultsHref} />
          <RecheckOfferCard code={unit.code} recheck={recheck} />
        </div>
        <div className="flex flex-col gap-4 lg:gap-5">
          <QuestsCard board={quests} seeAllHref={routes.quests} />
          {nextUnit ? <NextUnitPendingCard code={nextUnit.code} /> : null}
        </div>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Course map                                                          */
/* ------------------------------------------------------------------ */

export interface CourseMapProps {
  player: Player;
  /** API: CourseMapResponse.title / description */
  course: { title: string; description: string };
  /** API: CourseMapResponse.units, mapped to UnitSummary. */
  units: UnitSummary[];
  /** NEW. How many beta students hold the first unit's badge. */
  badgeHolderCount: number;
  /** True while more units are still being reviewed. */
  moreUnitsComing: boolean;
  routes?: KitRoutes;
}

function CourseUnitCard({ unit }: { unit: UnitSummary }) {
  const started = unit.lessons.some((lesson) => lesson.state !== "locked" && lesson.state !== "ready") || unit.xpEarned > 0;
  return (
    <Card className="gap-3.5 p-6 shadow-ns-md">
      <div className="flex flex-wrap items-center gap-2.5">
        <Tag tone={started ? "amber" : "brand"}>{started ? "In progress" : "Not started"}</Tag>
        <span className="text-[13px] text-ns-muted">{unit.lessons.length} lessons · checkpoint</span>
      </div>
      <div className="flex flex-col gap-1">
        <Eyebrow muted>Unit {unit.code}</Eyebrow>
        <H2 className="lg:text-[22px] lg:leading-[30px]">{unit.title}</H2>
      </div>
      <Muted className="text-[15px] leading-[22px]">{unit.description}</Muted>
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-[15px] font-bold">
        <span className="inline-flex items-center gap-1.5">
          <StarGlyph size={18} />
          {unit.starsEarned} of {unit.starsTotal} stars
        </span>
        <span className="inline-flex items-center gap-1.5">
          <GameIcon name="bolt" size={18} className="text-ns-amber" />
          {unit.xpEarned} of {unit.xpTotal} XP
        </span>
      </div>
      <ProgressBar
        label="Lessons proficient"
        value={`${unit.lessonsProficient} of ${unit.lessons.length}`}
        pct={(unit.lessonsProficient / Math.max(1, unit.lessons.length)) * 100}
        fill="success"
      />
      <UnitRewardLine unit={unit} pill />
      <Button variant="primary" full href={unit.href} iconRight={ArrowRight}>
        Open unit
      </Button>
    </Card>
  );
}

function MoreUnitsCard() {
  return (
    <Card tone="sunken" shadow={false} className="flex-row items-start gap-3.5">
      <Clock size={22} className="mt-0.5 shrink-0 text-ns-muted" aria-hidden />
      <div className="flex flex-col gap-1">
        <H3>More units are on the way</H3>
        <Muted>We add a unit only after every lesson and question has been checked. You will see it here when it is ready.</Muted>
      </div>
    </Card>
  );
}

/** Canvas: CourseMap.m, CourseMap.d */
export function CourseMapScreen({ player, course, units, badgeHolderCount, moreUnitsComing, routes = PREVIEW_ROUTES }: CourseMapProps) {
  const first = units[0];
  return (
    <AppShell
      active="course"
      player={player}
      routes={routes}
      maxWidth={1040}
      top={<TopBar title="Course" right={<MiniChips player={player} routes={routes} />} />}
    >
      <div className="flex flex-col gap-1.5">
        <Eyebrow muted>Your course</Eyebrow>
        <H1>{course.title}</H1>
        <Muted className="text-base leading-6">{course.description}</Muted>
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-2 lg:gap-6">
        <div className="flex flex-col gap-4">
          {units.map((unit) => (
            <CourseUnitCard key={unit.key} unit={unit} />
          ))}
        </div>
        <div className="flex flex-col gap-4">
          {first ? (
            <MascotCard mood="normal" size={64}>
              Every star you win in {first.code} counts toward the <b>{first.checkpoint.rewardBadge}</b> badge. Only {badgeHolderCount} beta
              students have it so far.
            </MascotCard>
          ) : null}
          {moreUnitsComing ? <MoreUnitsCard /> : null}
        </div>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Unit                                                                */
/* ------------------------------------------------------------------ */

/** NEW. A recheck that can raise lessons from proficient to mastered. */
export interface RecheckOffer {
  /** e.g. "Recheck ready: Lessons 3 and 4" */
  title: string;
  /** e.g. "5 questions, no hints. Get 4 right to mark both lessons mastered." */
  description: string;
  xp: number;
  /** e.g. "3rd star for both" */
  starNote: string;
  href: Href;
}

export interface UnitProps {
  player: Player;
  /** API: CourseMapResponse.title */
  courseTitle: string;
  unit: UnitSummary;
  /** e.g. "About 3.5 hours". Sum of CourseLessonMap.estimated_minutes. */
  timeLabel: string;
  /** Mascot nudge, e.g. "Lesson 2 is 2 questions away from its first star!" */
  nudge?: string;
  recheck?: RecheckOffer | null;
  /** "stars" explains stars, "labels" explains proficient and mastered. */
  legend: "stars" | "labels";
  routes?: KitRoutes;
}

function UnitChips({ unit, timeLabel }: { unit: UnitSummary; timeLabel: string }) {
  const mastered = unit.lessons.filter((lesson) => lesson.state === "mastered").length;
  const proficient = unit.lessons.filter((lesson) => lesson.state === "proficient").length;
  return (
    <div className="flex flex-wrap gap-2">
      {mastered > 0 ? (
        <>
          <Tag tone="success">{mastered} mastered</Tag>
          <Tag tone="success">{proficient} proficient</Tag>
        </>
      ) : (
        <>
          <Tag tone="success">
            {unit.lessonsProficient} of {unit.lessons.length} proficient
          </Tag>
          <Tag tone="amber" icon={StarGlyph}>
            {unit.starsEarned} of {unit.starsTotal} stars
          </Tag>
        </>
      )}
      <Tag icon={Clock}>{timeLabel}</Tag>
    </div>
  );
}

function RecheckCard({ recheck }: { recheck: RecheckOffer }) {
  return (
    <Card className="gap-3.5 border-ns-amber-line shadow-ns-md">
      <div className="flex items-start gap-3">
        <IconCircle icon={RotateCcw} tone="amber" size={44} />
        <div className="flex min-w-0 grow flex-col gap-1">
          <H3>{recheck.title}</H3>
          <Muted>{recheck.description}</Muted>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <XpPill xp={recheck.xp} />
            <StarRow count={3} size={16} />
            <span className="text-[13px] text-ns-muted">{recheck.starNote}</span>
          </div>
        </div>
      </div>
      <Button variant="primary" full href={recheck.href} iconRight={ArrowRight}>
        Start recheck · +{recheck.xp} XP
      </Button>
    </Card>
  );
}

function StarLegend() {
  return (
    <Card tone="sunken" shadow={false} className="flex-row items-start gap-2.5 p-4">
      <StarGlyph size={16} className="mt-0.5 shrink-0" />
      <p className="m-0 text-sm leading-5 text-ns-ink">
        <b>1 star</b> for any right answer, <b>2 stars</b> at 70% right (proficient, opens the next lesson), <b>3 stars</b> when a recheck
        shows it stuck.
      </p>
    </Card>
  );
}

function LabelLegend() {
  return (
    <Card tone="sunken" shadow={false} className="gap-3 p-4">
      <H3>What the labels mean</H3>
      <dl className="m-0 grid grid-cols-[auto_minmax(0,1fr)] items-start gap-x-3 gap-y-2.5">
        <dt>
          <LessonStateTag state="proficient" />
        </dt>
        <dd className="m-0 text-[13px] leading-[18px] text-ns-muted">70% right in the lesson practice.</dd>
        <dt>
          <LessonStateTag state="mastered" />
        </dt>
        <dd className="m-0 text-[13px] leading-[18px] text-ns-muted">Still right in a recheck 2 weeks later, or in the checkpoint.</dd>
      </dl>
    </Card>
  );
}

/** Unit checkpoint card: locked with a reward, or open. */
export function CheckpointCard({ unit }: { unit: UnitSummary }) {
  const { checkpoint } = unit;
  const total = unit.lessons.length;
  return (
    <Card className="gap-3.5">
      <div className="flex items-start gap-3">
        <IconCircle icon={Flag} tone="neutral" size={44} />
        <div className="flex min-w-0 grow flex-col gap-1">
          <div className="flex items-center justify-between gap-2">
            <H3>Unit checkpoint</H3>
            {checkpoint.open ? <Tag tone="success">Open</Tag> : null}
          </div>
          <Muted>
            {checkpoint.open
              ? `${checkpoint.questionCount} questions. All ${total} lessons are proficient, so it is open.`
              : `${checkpoint.questionCount} questions, about ${checkpoint.minutes} minutes. Pass with ${checkpoint.passMark} of ${checkpoint.questionCount} to master ${unit.code}. Opens after all ${total} lessons are proficient.`}
          </Muted>
        </div>
      </div>
      {checkpoint.open ? (
        <Button full href={checkpoint.href}>
          Start checkpoint
        </Button>
      ) : (
        <>
          <UnitRewardLine unit={unit} />
          <ProgressBar
            label="Lessons ready"
            value={`${unit.lessonsProficient} of ${total}`}
            pct={(unit.lessonsProficient / Math.max(1, total)) * 100}
            fill="success"
          />
          <Button full disabled icon={Lock}>
            Checkpoint locked
          </Button>
        </>
      )}
    </Card>
  );
}

/** Canvas: Unit.m, Unit.d, UnitRecheck.m */
export function UnitScreen({ player, courseTitle, unit, timeLabel, nudge, recheck, legend, routes = PREVIEW_ROUTES }: UnitProps) {
  const lessons = (
    <Card className="gap-0 overflow-hidden px-0 py-2">
      <ul className="m-0 flex list-none flex-col p-0">
        {unit.lessons.map((lesson) => (
          <li key={lesson.key}>
            <LessonRow lesson={lesson} />
          </li>
        ))}
      </ul>
    </Card>
  );
  const legendCard = legend === "stars" ? <StarLegend /> : <LabelLegend />;
  const nudgeBlock = nudge ? (
    <MascotSays mood="normal" outfit={player.equippedOutfit} size={64}>
      {nudge}
    </MascotSays>
  ) : null;

  return (
    <AppShell
      active="course"
      player={player}
      routes={routes}
      maxWidth={1040}
      top={<TopBar backHref={routes.nav.course} title={`Unit ${unit.code}`} right={<MiniChips player={player} routes={routes} />} />}
    >
      <div className="flex flex-col gap-2">
        <BackLink href={routes.nav.course} label="Course" />
        <Eyebrow muted>{courseTitle}</Eyebrow>
        <H1>
          {unit.code} · {unit.title}
        </H1>
        <UnitChips unit={unit} timeLabel={timeLabel} />
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] lg:gap-6">
        <div className="flex flex-col gap-4">
          {recheck ? <RecheckCard recheck={recheck} /> : null}
          {nudgeBlock ? <div className="lg:hidden">{nudgeBlock}</div> : null}
          {lessons}
          <div className={cn(legend === "labels" && "lg:hidden")}>{legendCard}</div>
        </div>
        <div className="flex flex-col gap-4">
          {nudgeBlock ? <div className="hidden lg:block">{nudgeBlock}</div> : null}
          <CheckpointCard unit={unit} />
          {legend === "labels" ? <div className="hidden lg:block">{legendCard}</div> : null}
        </div>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Review (Try again list)                                             */
/* ------------------------------------------------------------------ */

export type ReviewTab = "ready" | "later" | "cleared";

export interface ReviewProps {
  player: Player;
  /** NEW. Due now. */
  now: ReviewItem[];
  /** NEW. Waiting for their gap to pass. */
  later: LaterReviewItem[];
  /** NEW. Questions cleared for good. */
  clearedCount: number;
  tab: ReviewTab;
  tabHrefs: Record<ReviewTab, Href>;
  /** NEW. Review master badge with progress. */
  badge: Badge;
  /** e.g. "Clearing all 3 now also finishes today’s quest." */
  questNote?: string;
  startHref: Href;
  routes?: KitRoutes;
}

const REASON_ICON: Record<string, typeof Eye> = { "solution shown": Eye, "gave up": Flag, "keep it fresh": RotateCcw };

function ReviewTabs({ tab, hrefs, counts }: { tab: ReviewTab; hrefs: Record<ReviewTab, Href>; counts: Record<ReviewTab, number> }) {
  const tabs: { key: ReviewTab; label: string }[] = [
    { key: "ready", label: "Ready now" },
    { key: "later", label: "Later" },
    { key: "cleared", label: "Cleared" },
  ];
  return (
    <nav aria-label="Try again list" className="flex rounded-full border border-ns-line bg-ns-sunken p-1 lg:max-w-[420px]">
      {tabs.map((item) => {
        const on = item.key === tab;
        return (
          <Link
            key={item.key}
            href={hrefs[item.key]}
            aria-current={on ? "page" : undefined}
            className={cn(
              "flex h-11 flex-1 items-center justify-center rounded-full text-sm font-bold whitespace-nowrap no-underline",
              on ? "bg-ns-ink text-ns-on-brand" : "text-ns-ink hover:bg-ns-raised",
              focusRing,
            )}
          >
            {item.label} · {counts[item.key]}
          </Link>
        );
      })}
    </nav>
  );
}

function ReadyHero({ count }: { count: number }) {
  return (
    <Card tone="amber" className="flex-row items-center gap-3">
      <Hornbill size={84} mood="think" branch={false} />
      <div className="flex min-w-0 flex-col gap-1.5">
        <Eyebrow>Ready now</Eyebrow>
        <span className="text-2xl leading-7 font-black">
          {count} question{count === 1 ? " is" : "s are"} back
        </span>
        <DoubleXpPill />
      </div>
    </Card>
  );
}

function ReadyList({ items }: { items: ReviewItem[] }) {
  return (
    <Card className="gap-4">
      <div className="flex items-center justify-between">
        <H3>Ready now</H3>
        <span className="text-[13px] text-ns-muted">
          {items.length} question{items.length === 1 ? "" : "s"}
        </span>
      </div>
      <ul className="m-0 flex list-none flex-col gap-4 p-0">
        {items.map((item) => {
          const TagIcon = item.tag ? REASON_ICON[item.tag.label.toLowerCase()] : undefined;
          return (
            <li key={item.questionKey} className="flex items-center gap-3">
              <IconCircle icon={RotateCcw} tone="amber" size={36} />
              <div className="flex min-w-0 grow flex-col gap-0.5">
                <span className="text-[15px] leading-[22px] font-semibold">{item.title}</span>
                <span className="text-[13px] leading-[18px] text-ns-muted">{item.reason}</span>
                <XpTag xp={item.xp} size={12} />
                {item.tag ? (
                  <span className="pt-1">
                    <Tag tone={item.tag.tone} icon={TagIcon}>
                      {item.tag.label}
                    </Tag>
                  </span>
                ) : null}
              </div>
              <Button size="sm" href={item.href} ariaLabel={`Try ${item.title} again`}>
                Try
              </Button>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

function ReviewBadgeCard({ badge, questNote }: { badge: Badge; questNote?: string }) {
  const current = badge.progress?.current ?? 0;
  const target = badge.progress?.target ?? 1;
  const left = Math.max(0, target - current);
  return (
    <Card className="gap-3">
      <div className="flex items-start gap-3">
        <Medal icon={badge.icon} tier={badge.tier} size={44} />
        <div className="flex min-w-0 grow flex-col gap-0.5">
          <H3>{badge.name} badge</H3>
          <Muted className="text-[13px] leading-[18px]">
            Clear {left} more to earn it.{questNote ? ` ${questNote}` : ""}
          </Muted>
        </div>
      </div>
      <ProgressBar label="Reviews cleared" value={`${current} of ${target}`} pct={(current / target) * 100} fill="success" />
    </Card>
  );
}

function LaterList({ items }: { items: LaterReviewItem[] }) {
  return (
    <Card className="gap-3.5">
      <div className="flex items-center justify-between">
        <H3>Coming back later</H3>
        <span className="text-[13px] text-ns-muted">
          {items.length} question{items.length === 1 ? "" : "s"}
        </span>
      </div>
      <ul className="m-0 flex list-none flex-col gap-3 p-0">
        {items.map((item) => (
          <li key={item.questionKey} className="flex items-center gap-3">
            <IconCircle icon={Clock} tone="neutral" size={32} />
            <div className="flex min-w-0 grow flex-col">
              <span className="text-[15px] leading-5 font-semibold">{item.title}</span>
              <span className="text-[13px] leading-[18px] text-ns-muted">{item.reason}</span>
            </div>
            <Tag icon={Clock}>{item.dueLabel}</Tag>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function HowReviewWorks() {
  const lines = [
    "A question lands here when you see the solution, give up, or miss it in a checkpoint.",
    "It waits a few days first. That gap is what makes it stick.",
    "Get it right without the solution and it leaves the list.",
  ];
  return (
    <Card tone="sunken" shadow={false} className="gap-3">
      <H3>How this list works</H3>
      <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
        {lines.map((line) => (
          <li key={line} className="flex items-start gap-2.5 text-sm leading-5">
            <Check size={16} className="mt-0.5 shrink-0 text-ns-success" aria-hidden />
            {line}
          </li>
        ))}
      </ul>
    </Card>
  );
}

/** Canvas: Review.m, Review.d */
export function ReviewScreen({ player, now, later, clearedCount, tab, tabHrefs, badge, questNote, startHref, routes = PREVIEW_ROUTES }: ReviewProps) {
  const total = now.reduce((sum, item) => sum + item.xp, 0);
  const start =
    now.length > 0 ? (
      <Button variant="primary" full href={startHref} iconRight={ArrowRight}>
        Start review · up to +{total} XP
      </Button>
    ) : null;
  return (
    <FocusShell
      active="progress"
      player={player}
      routes={routes}
      maxWidth={1040}
      top={<TopBar backHref={routes.nav.progress} title="Try again" right={<MiniStreak player={player} routes={routes} />} />}
      footer={start ? <FooterBar className="lg:hidden">{start}</FooterBar> : undefined}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex flex-col gap-1">
          <BackLink href={routes.nav.progress} label="Progress" />
          <H1>Try again</H1>
          <Muted className="text-[15px] leading-[22px] lg:text-base">Questions worth another go. Each one is double XP.</Muted>
        </div>
        {now.length > 0 ? (
          <div className="hidden lg:block">
            <Button variant="primary" href={startHref} iconRight={ArrowRight}>
              Start review · up to +{total} XP
            </Button>
          </div>
        ) : null}
      </div>
      <div className="lg:hidden">
        <ReadyHero count={now.length} />
      </div>
      <ReviewTabs tab={tab} hrefs={tabHrefs} counts={{ ready: now.length, later: later.length, cleared: clearedCount }} />
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-6">
        <div className="flex flex-col gap-4 lg:gap-6">
          <div className="hidden lg:block">
            <ReadyHero count={now.length} />
          </div>
          <ReadyList items={now} />
        </div>
        <div className="flex flex-col gap-4 lg:gap-6">
          <ReviewBadgeCard badge={badge} questNote={questNote} />
          {later.length > 0 ? <LaterList items={later} /> : null}
          <HowReviewWorks />
        </div>
      </div>
    </FocusShell>
  );
}

function MiniStreak({ player, routes }: { player: Player; routes: KitRoutes }) {
  return (
    <Link
      href={routes.streak}
      aria-label={`${player.streakDays} day streak`}
      className={cn(
        "inline-flex h-8 shrink-0 items-center gap-1 rounded-full bg-ns-amber-soft pr-2.5 pl-1.5 text-sm font-extrabold text-ns-amber-text no-underline tabular-nums",
        focusRing,
      )}
    >
      <GameIcon name="flame" size={18} className={player.streakDays > 0 ? "text-ns-amber" : "text-ns-line-strong"} />
      {player.streakDays}
    </Link>
  );
}

/* ------------------------------------------------------------------ */
/* Quests                                                              */
/* ------------------------------------------------------------------ */

export interface QuestsProps {
  player: Player;
  quests: QuestBoard;
  /** NEW. Practice days this week toward the weekly goal. */
  weeklyGoal: { daysDone: number; target: number };
  /** NEW. Monthly challenge. */
  challenge: { label: string; title: string; reward: string; progressLabel: string; progress: number; target: number };
  routes?: KitRoutes;
}

function WeeklyGoalCard({ goal }: { goal: QuestsProps["weeklyGoal"] }) {
  const pct = Math.round((Math.min(goal.daysDone, goal.target) / Math.max(1, goal.target)) * 100);
  const left = Math.max(0, goal.target - goal.daysDone);
  return (
    <Card className="flex-row items-center gap-4">
      <span
        role="img"
        aria-label={`${goal.daysDone} of ${goal.target} days`}
        className="inline-flex size-[84px] shrink-0 items-center justify-center rounded-full"
        style={{ background: `conic-gradient(var(--color-ns-success) ${pct}%, var(--color-ns-line) 0)` }}
      >
        <span className="inline-flex size-[68px] flex-col items-center justify-center rounded-full bg-ns-raised">
          <b className="text-[22px] leading-6 tabular-nums">
            {goal.daysDone}/{goal.target}
          </b>
          <span className="text-[11px] text-ns-muted">days</span>
        </span>
      </span>
      <div className="flex min-w-0 flex-col gap-1">
        <H3>Weekly goal</H3>
        <Muted>
          Practise on {goal.target} days this week.{" "}
          {left === 0 ? "Goal reached. You earned a streak freeze." : `${left === 1 ? "One more day" : `${left} more days`} earns a streak freeze.`}
        </Muted>
      </div>
    </Card>
  );
}

function ChallengeCard({ challenge }: { challenge: QuestsProps["challenge"] }) {
  return (
    <Card className="gap-3">
      <div className="flex items-start gap-3.5">
        <span className="inline-flex size-[72px] shrink-0 items-center justify-center rounded-[18px] bg-ns-amber-soft">
          <Hornbill size={64} crop="head" outfit="scarf" />
        </span>
        <div className="flex min-w-0 grow flex-col gap-1">
          <Eyebrow>{challenge.label}</Eyebrow>
          <H3>{challenge.title}</H3>
          <Muted className="text-[13px] leading-[18px]">{challenge.reward}</Muted>
        </div>
      </div>
      <ProgressBar
        label={challenge.progressLabel}
        value={`${challenge.progress} of ${challenge.target}`}
        pct={(challenge.progress / Math.max(1, challenge.target)) * 100}
      />
    </Card>
  );
}

/** Canvas: Quests.m */
export function QuestsScreen({ player, quests, weeklyGoal, challenge, routes = PREVIEW_ROUTES }: QuestsProps) {
  return (
    <AppShell
      active="learn"
      player={player}
      routes={routes}
      maxWidth={960}
      top={
        <TopBar
          backHref={routes.nav.learn}
          title="Daily quests"
          right={<span className="text-[13px] font-bold whitespace-nowrap text-ns-muted">Resets in {quests.resetsIn}</span>}
        />
      }
    >
      <div className="hidden items-end justify-between gap-4 lg:flex">
        <div className="flex flex-col gap-1">
          <BackLink href={routes.nav.learn} label="Learn" />
          <H1>Daily quests</H1>
        </div>
        <span className="text-sm font-bold text-ns-muted">Resets in {quests.resetsIn}</span>
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-2 lg:gap-6">
        <QuestsCard board={quests} />
        <div className="flex flex-col gap-4 lg:gap-6">
          <WeeklyGoalCard goal={weeklyGoal} />
          <ChallengeCard challenge={challenge} />
          <MascotSays mood="kind" size={60}>
            New quests every morning. Easy ones first, then a stretch.
          </MascotSays>
        </div>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Streak                                                              */
/* ------------------------------------------------------------------ */

export interface StreakMonth {
  /** e.g. "October" */
  name: string;
  /** One entry per date, starting on the 1st. NEW. */
  days: StreakDay[];
  /** Blank cells before the 1st (0 = the 1st sits in the first column). */
  leadingBlanks?: number;
  /** e.g. "Freeze used on the 8th" */
  note?: string;
}

export interface StreakProps {
  player: Player;
  month: StreakMonth;
  milestones: StreakMilestone[];
  /** NEW. Freezes a student can hold at once. */
  maxFreezes: number;
  routes?: KitRoutes;
}

const FLAME_BG = "bg-[linear-gradient(180deg,#F6C063_0%,#E3A44B_45%,#C87A1E_100%)]";
const DAY_WORD: Record<StreakDay, string> = { done: "practised", freeze: "streak freeze used", today: "today", empty: "" };

export function MonthCalendar({ month }: { month: StreakMonth }) {
  return (
    <Card className="gap-3 p-[18px]">
      <div className="flex items-center justify-between gap-3">
        <H3>{month.name}</H3>
        {month.note ? <span className="text-[13px] text-ns-muted">{month.note}</span> : null}
      </div>
      <ol className="m-0 grid list-none grid-cols-7 gap-1.5 p-0">
        {Array.from({ length: month.leadingBlanks ?? 0 }, (_, i) => (
          <li key={`blank-${i}`} aria-hidden="true" />
        ))}
        {month.days.map((day, i) => {
          const date = i + 1;
          const label = `${month.name} ${date}${DAY_WORD[day] ? `, ${DAY_WORD[day]}` : ""}`;
          return (
            <li
              key={date}
              className={cn(
                "flex h-[38px] items-center justify-center rounded-[10px]",
                day === "done" && cn(FLAME_BG, "text-white"),
                day === "freeze" && "bg-ns-success-soft text-ns-success",
                day === "today" && "border-2 border-dashed border-ns-amber bg-ns-raised text-ns-amber",
                day === "empty" && "bg-ns-sunken text-[11px] text-ns-muted",
              )}
            >
              <span className="sr-only">{label}</span>
              {day === "done" || day === "today" ? (
                <GameIcon name="flame" size={14} />
              ) : day === "freeze" ? (
                <GameIcon name="snow" size={14} />
              ) : (
                <span aria-hidden="true">{date}</span>
              )}
            </li>
          );
        })}
      </ol>
    </Card>
  );
}

export function MilestoneTrack({ milestones }: { milestones: StreakMilestone[] }) {
  const lastReached = milestones.reduce((acc, m, i) => (m.reached ? i : acc), -1);
  const fill = milestones.length > 1 ? Math.max(0, lastReached) / (milestones.length - 1) : 0;
  return (
    <Card className="gap-3.5 p-[18px]">
      <H3>Milestones</H3>
      <div className="relative">
        <div aria-hidden="true" className="absolute top-[21px] right-[30px] left-[30px] h-[3px] bg-ns-line">
          <div className="h-full bg-ns-amber" style={{ width: `${fill * 100}%` }} />
        </div>
        <ol className="relative m-0 flex list-none justify-between p-0">
          {milestones.map((m) => (
            <li key={m.days} className="flex w-[60px] flex-col items-center gap-1.5">
              <span
                className={cn(
                  "inline-flex size-11 items-center justify-center rounded-full text-[15px] font-black",
                  m.reached ? cn(FLAME_BG, "text-white") : "bg-ns-sunken text-ns-muted",
                )}
              >
                {m.days}
              </span>
              <span className={cn("text-center text-[11px] leading-[14px] font-bold", m.reached ? "text-ns-ink" : "text-ns-muted")}>
                {m.reward}
                <span className="sr-only">{m.reached ? ", reached" : `, at ${m.days} days`}</span>
              </span>
            </li>
          ))}
        </ol>
      </div>
    </Card>
  );
}

/** Canvas: Streak.m */
export function StreakScreen({ player, month, milestones, maxFreezes, routes = PREVIEW_ROUTES }: StreakProps) {
  const lit = player.streakDays > 0;
  const freeze = (
    <Card className="flex-row items-start gap-3 p-[18px]">
      <span className="inline-flex size-12 shrink-0 items-center justify-center rounded-[14px] bg-ns-success-soft text-ns-success">
        <GameIcon name="snow" size={26} />
      </span>
      <div className="flex min-w-0 flex-col gap-0.5">
        <H3>
          Streak freeze: {player.streakFreezes} of {maxFreezes}
        </H3>
        <Muted className="text-[13px] leading-[18px]">
          Saves your streak on a missed day. Earn one each time you hit your weekly goal. Never sold.
        </Muted>
      </div>
    </Card>
  );
  return (
    <AppShell active="learn" player={player} routes={routes} maxWidth={960} top={<TopBar backHref={routes.nav.learn} title="Your streak" />}>
      <BackLink href={routes.nav.learn} label="Learn" />
      <div className="grid items-start gap-4 lg:grid-cols-2 lg:gap-6">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col items-center gap-1.5 pt-3 pb-1">
            <span className={cn("inline-flex", lit ? "animate-ns-flame text-ns-amber" : "text-ns-line-strong")}>
              <GameIcon name="flame" size={96} />
            </span>
            <h1 className="m-0 flex flex-col items-center gap-1.5">
              <span className="text-[56px] leading-[56px] font-black tabular-nums">{player.streakDays}</span>
              <span className="text-base leading-6 font-bold text-ns-muted">day streak · longest {player.bestStreakDays}</span>
            </h1>
          </div>
          <MascotSays mood="sleepy" size={56}>
            Just 1 question today keeps the flame alive.
          </MascotSays>
          <div className="hidden lg:block">{freeze}</div>
        </div>
        <div className="flex flex-col gap-4">
          <MonthCalendar month={month} />
          <div className="lg:hidden">{freeze}</div>
          <MilestoneTrack milestones={milestones} />
        </div>
      </div>
    </AppShell>
  );
}
