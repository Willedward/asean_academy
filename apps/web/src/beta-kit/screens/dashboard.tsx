import Link from "next/link";
import { ArrowRight, ChevronRight, RotateCcw } from "lucide-react";

import { Hornbill } from "../components/hornbill";
import { LessonRow } from "../components/lesson-row";
import {
  DoubleXpPill,
  LeagueChip,
  LeagueMini,
  LeagueTable,
  LevelCard,
  LevelRing,
  MascotSays,
  QuestsCard,
  Stars,
  StreakCard,
  StreakChip,
  WeekDots,
  XpChip,
  XpPill,
  levelPct,
} from "../components/rewards";
import { GameIcon } from "../components/icons";
import { Button, Card, Eyebrow, H1, H2, H3, Muted, ProgressBar, Stat } from "../components/ui";
import { AppShell, StatBar } from "../shell/app-shell";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import type { ContinueCard as ContinueData, League, Player, QuestBoard, StreakWeek, UnitSummary } from "../types";

/* ------------------------------------------------------------------ */
/* Pieces reused by other screens                                      */
/* ------------------------------------------------------------------ */

export function ContinueCard({ data }: { data: ContinueData }) {
  return (
    <Card className="gap-3.5 p-6 shadow-ns-md">
      <div className="flex items-center gap-2.5">
        <span className="inline-flex h-6 items-center rounded-full bg-ns-amber-soft px-2.5 text-xs font-semibold text-ns-amber-text">Up next</span>
        <span className="text-[13px] text-ns-muted">{data.lessonLabel}</span>
        <span className="ml-auto">
          <XpPill xp={data.xp} />
        </span>
      </div>
      <H2 className="lg:text-[22px] lg:leading-[30px]">{data.title}</H2>
      <div className="flex items-center gap-2">
        <Muted className="grow text-[15px] leading-[22px]">{data.description}</Muted>
        <Stars count={data.stars} size={18} />
      </div>
      <ProgressBar label="Guided practice" value={data.progressLabel} pct={data.progressPct} />
      <div className="flex flex-col gap-2 lg:flex-row lg:items-center">
        <Button variant="primary" full href={data.primary.href} iconRight={ArrowRight} className="lg:w-auto">
          {data.primary.label}
        </Button>
        {data.secondary ? (
          <Button variant="ghost" href={data.secondary.href} className="hidden lg:inline-flex">
            {data.secondary.label}
          </Button>
        ) : null}
      </div>
    </Card>
  );
}

export function ReviewDueCard({ count, xp, href }: { count: number; xp: number; href: string }) {
  return (
    <Card tone="amber" className="gap-3.5">
      <div className="flex items-start gap-3">
        <Hornbill size={60} mood="think" branch={false} />
        <div className="flex grow flex-col gap-1.5">
          <DoubleXpPill />
          <H3>
            {count} question{count === 1 ? " is" : "s are"} back for review
          </H3>
          <Muted>Clear {count === 1 ? "it" : "them"} for +{xp} XP and a step toward the Review master badge.</Muted>
        </div>
      </div>
      <Button size="sm" icon={RotateCcw} href={href}>
        Review it · +{xp} XP
      </Button>
    </Card>
  );
}

export function UnitMiniCard({ unit, lessonsShown = 3 }: { unit: UnitSummary; lessonsShown?: number }) {
  return (
    <Card className="gap-3.5">
      <div className="flex items-center gap-2">
        <div className="flex grow flex-col gap-0.5">
          <Eyebrow muted>Unit {unit.code}</Eyebrow>
          <H3>{unit.title}</H3>
        </div>
        <span className="inline-flex items-center gap-1 text-sm font-extrabold">
          <GameIcon name="star" size={16} className="text-ns-gold" />
          {unit.starsEarned}/{unit.starsTotal}
        </span>
      </div>
      <ProgressBar label="Unit progress" value={`${unit.lessonsProficient} of ${unit.lessons.length} lessons`} pct={(unit.lessonsProficient / unit.lessons.length) * 100} fill="success" />
      <div className="-mx-3 flex flex-col">
        {unit.lessons.slice(0, lessonsShown).map((lesson) => (
          <LessonRow key={lesson.key} lesson={lesson} compact />
        ))}
      </div>
      <Button variant="ghost" full href={unit.href} iconRight={ChevronRight}>
        See all {unit.lessons.length} lessons
      </Button>
    </Card>
  );
}

export function WeekStatsCard({ player, week, progressHref }: { player: Player; week: StreakWeek; progressHref: string }) {
  return (
    <Card className="gap-4 p-6">
      <div className="flex items-center justify-between">
        <H3>This week</H3>
        <Link href={progressHref} className="text-sm font-semibold text-ns-amber-text">
          See progress
        </Link>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <Stat
          value={
            <span className="inline-flex items-center gap-1">
              <GameIcon name="bolt" size={22} className="text-ns-amber" />
              {player.xpThisWeek}
            </span>
          }
          label="XP this week"
        />
        <Stat value="62%" label="Right first try" />
        <Stat
          value={
            <span className="inline-flex items-center gap-1">
              <GameIcon name="flame" size={22} className="text-ns-amber" />
              {player.streakDays}
            </span>
          }
          label="Day streak"
        />
      </div>
      <WeekDots week={week} />
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* Dashboard                                                           */
/* ------------------------------------------------------------------ */

export interface DashboardProps {
  player: Player;
  greeting: string;
  continueCard: ContinueData;
  quests: QuestBoard;
  week: StreakWeek;
  league: League;
  unit: UnitSummary;
  reviewDue: { count: number; xp: number; href: string } | null;
  routes?: KitRoutes;
}

/** Canvas: Dashboard.m, Dashboard.d, Dashboard.t */
export function DashboardScreen({ player, greeting, continueCard, quests, week, league, unit, reviewDue, routes = PREVIEW_ROUTES }: DashboardProps) {
  const bonusLeft = quests.quests.filter((q) => q.progress < q.target).length;
  const nudge =
    bonusLeft > 0 ? (
      <>
        {greeting}, {player.displayName.split(" ")[0]}! {bonusLeft} more quest{bonusLeft === 1 ? "" : "s"} for a{" "}
        <b className="text-ns-amber-text">+{quests.bonusXp} XP bonus</b>.
      </>
    ) : (
      <>
        {greeting}, {player.displayName.split(" ")[0]}! All quests done. Keep the streak going.
      </>
    );

  return (
    <AppShell active="learn" player={player} routes={routes} top={<StatBar player={player} routes={routes} />}>
      {/* Desktop greeting row */}
      <div className="hidden items-center gap-4 lg:flex">
        <LevelRing size={64} level={player.level} pct={levelPct(player)} outfit={player.equippedOutfit} />
        <div className="flex grow flex-col gap-0.5">
          <Muted className="text-[15px]">{greeting}</Muted>
          <H1 className="lg:text-[30px] lg:leading-[38px]">
            {player.displayName.split(" ")[0]}, you are on a {player.streakDays}-day streak
          </H1>
        </div>
        <div className="flex gap-2">
          <StreakChip days={player.streakDays} href={routes.streak} />
          <XpChip xp={player.xpTotal} href={routes.quests} />
          <LeagueChip rank={player.leagueRank} href={routes.league} />
        </div>
      </div>

      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-6">
        <div className="flex flex-col gap-4 lg:gap-5">
          <MascotSays mood="happy" outfit={player.equippedOutfit} size={72}>
            {nudge}
          </MascotSays>
          <ContinueCard data={continueCard} />
          <div className="lg:hidden">
            <StreakCard player={player} week={week} />
          </div>
          <div className="lg:hidden">
            <QuestsCard board={quests} seeAllHref={routes.quests} />
          </div>
          {reviewDue ? (
            <div className="lg:hidden">
              <ReviewDueCard {...reviewDue} />
            </div>
          ) : null}
          <div className="lg:hidden">
            <LeagueMini league={league} href={routes.league} />
          </div>
          <div className="lg:hidden">
            <LevelCard player={player} routes={routes} />
          </div>
          <UnitMiniCard unit={unit} lessonsShown={3} />
        </div>

        <div className="hidden flex-col gap-5 lg:flex">
          <StreakCard player={player} week={week} />
          <QuestsCard board={quests} seeAllHref={routes.quests} />
          {reviewDue ? <ReviewDueCard {...reviewDue} /> : null}
          <Card className="gap-3">
            <div className="flex items-center justify-between">
              <H3>
                {league.name} · {league.weekLabel.toLowerCase()}
              </H3>
              <Link href={routes.league} className="text-sm font-bold text-ns-amber-text">
                Full table
              </Link>
            </div>
            <LeagueTable league={{ ...league, entries: league.entries.slice(0, 4) }} compact />
            <Muted className="text-[13px]">
              Top {league.crownPlaces} wear the golden crown next week. Ends in {league.endsIn}.
            </Muted>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
