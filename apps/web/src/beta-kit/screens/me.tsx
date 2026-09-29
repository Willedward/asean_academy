import Link from "next/link";
import { useId, type ReactNode } from "react";
import { ArrowRight, Lock, LogOut, RotateCcw, Trash2, User } from "lucide-react";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { GameIcon } from "../components/icons";
import { LessonStateTag } from "../components/lesson-row";
import {
  BadgeTile,
  DoubleXpPill,
  LevelRing,
  MiniChips,
  Medal,
  StreakChip,
  XpBar,
  XpChip,
  XpTag,
  levelPct,
} from "../components/rewards";
import { Avatar, Button, Card, Divider, Eyebrow, H1, H2, H3, Muted, Sheet, Tag, focusRing } from "../components/ui";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import { AppShell, TopBar } from "../shell/app-shell";
import type { Badge, Href, League, LeagueEntry, LessonUiState, OutfitItem, Player, RankTitle, ReviewItem, Tone, UnitSummary, XpLine } from "../types";
import { BackLink, BadgeProgressRow, XpRulesCard } from "./learn";

/**
 * A form action: a URL, or a server action from the page. Screens stay
 * server-safe; the page decides what submitting does.
 */
export type FormAction = string | ((formData: FormData) => void | Promise<void>);

const firstName = (player: Player) => player.displayName.split(" ")[0] ?? player.displayName;
const fmt = (n: number) => n.toLocaleString("en-US");

/** Text input with a `name`, for server forms. Matches the kit Field. */
export function FormField({
  name,
  label,
  defaultValue,
  hint,
  readOnly,
  mono,
}: {
  name: string;
  label: string;
  defaultValue?: string;
  hint?: string;
  readOnly?: boolean;
  mono?: boolean;
}) {
  const id = useId();
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <label htmlFor={id} className="text-[15px] leading-5 font-semibold">
        {label}
      </label>
      <input
        id={id}
        name={name}
        type="text"
        defaultValue={defaultValue}
        readOnly={readOnly}
        autoComplete="off"
        aria-describedby={hint ? `${id}-hint` : undefined}
        className={cn(
          "h-12 w-full min-w-0 rounded-lg border-[1.5px] border-ns-line-strong px-4 text-base text-ns-ink",
          readOnly ? "bg-ns-sunken" : "bg-ns-raised",
          mono && "font-mono tracking-wide",
          focusRing,
        )}
      />
      {hint ? (
        <p id={`${id}-hint`} className="m-0 text-sm leading-5 text-ns-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Progress                                                            */
/* ------------------------------------------------------------------ */

const RANKS: { title: RankTitle; levels: string }[] = [
  { title: "Applicant", levels: "1–4" },
  { title: "Test-taker", levels: "5–9" },
  { title: "Shortlisted", levels: "10–14" },
  { title: "Interviewee", levels: "15–19" },
  { title: "Scholar", levels: "20+" },
];

export function RankLadder({ current }: { current: RankTitle }) {
  const index = Math.max(0, RANKS.findIndex((rank) => rank.title === current));
  return (
    <div className="relative">
      <div aria-hidden="true" className="absolute top-4 right-[31px] left-[31px] h-[3px] bg-ns-line">
        <div className="h-full bg-ns-amber" style={{ width: `${(index / (RANKS.length - 1)) * 100}%` }} />
      </div>
      <ol aria-label="Ranks" className="relative m-0 flex list-none justify-between p-0">
        {RANKS.map((rank, i) => {
          const on = i === index;
          const done = i < index;
          return (
            <li key={rank.title} aria-current={on ? "step" : undefined} className="flex w-[62px] flex-col items-center gap-[3px]">
              <span
                className={cn(
                  "inline-flex size-[34px] items-center justify-center rounded-full",
                  on ? "bg-ns-ink text-ns-gold" : done ? "bg-ns-success text-white" : "bg-ns-sunken text-ns-line-strong",
                )}
              >
                <GameIcon name="star" size={16} />
              </span>
              <span className={cn("text-center text-[11px] leading-[14px]", on ? "font-extrabold" : "font-semibold", on || done ? "text-ns-ink" : "text-ns-muted")}>
                {rank.title}
              </span>
              <span className="text-[10px] text-ns-muted">Lv {rank.levels}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function ProgressLevelCard({ player }: { player: Player }) {
  return (
    <Card className="gap-3.5">
      <div className="flex items-center gap-3.5">
        <LevelRing size={72} level={player.level} pct={levelPct(player)} outfit={player.equippedOutfit} />
        <div className="flex min-w-0 flex-col gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <b className="text-xl">Level {player.level}</b>
            <Tag tone="amber">{player.rankTitle}</Tag>
          </div>
          <span className="text-[13px] leading-[18px] text-ns-muted">
            {fmt(player.xpTotal)} XP in total · {fmt(player.xpThisWeek)} this week
          </span>
        </div>
      </div>
      <XpBar level={player.level} current={player.xpIntoLevel} needed={player.xpForLevel} />
      <RankLadder current={player.rankTitle} />
    </Card>
  );
}

function StatCell({ href, icon, value, label, sub }: { href: Href; icon: ReactNode; value: string; label: string; sub: string }) {
  return (
    <Link href={href} className={cn("flex rounded-2xl text-inherit no-underline", focusRing)}>
      <Card className="grow gap-0.5 p-4 hover:bg-ns-sunken">
        <span className="inline-flex items-center gap-1 text-[26px] leading-8 font-bold tabular-nums">
          {icon}
          {value}
        </span>
        <span className="text-[13px] leading-[18px] text-ns-muted">{label}</span>
        <span className="text-xs text-ns-muted">{sub}</span>
      </Card>
    </Link>
  );
}

function BadgeShelf({ badges, allHref }: { badges: Badge[]; allHref: Href }) {
  const earned = badges.filter((badge) => badge.earned).slice(0, 4);
  const near = badges.filter((badge) => !badge.earned && badge.progress).slice(0, 2);
  return (
    <Card className="gap-3.5">
      <div className="flex items-center justify-between">
        <H3>Badges</H3>
        <Link href={allHref} className="text-sm font-semibold text-ns-amber-text underline" aria-label={`All ${badges.length} badges`}>
          All {badges.length}
        </Link>
      </div>
      <ul className="m-0 grid list-none grid-cols-4 gap-2 p-0">
        {earned.map((badge) => (
          <li key={badge.id} className="flex flex-col items-center gap-1.5 text-center">
            <Medal icon={badge.icon} tier={badge.tier} size={56} />
            <span className="text-xs leading-[15px] font-extrabold">{badge.name}</span>
          </li>
        ))}
      </ul>
      {near.length > 0 ? (
        <>
          <Divider />
          <Eyebrow>Almost there</Eyebrow>
          <div className="flex flex-col gap-2.5">
            {near.map((badge) => (
              <BadgeProgressRow key={badge.id} badge={badge} dim />
            ))}
          </div>
        </>
      ) : null}
    </Card>
  );
}

/**
 * Totals for the course. Derive from ProgressResponse.lessons
 * (LessonProgressResponse): correct_count, question_count,
 * eventual_correct_percentage, gave_up_count, state.
 */
export interface ProgressStats {
  lessonsProficient: number;
  lessonCount: number;
  /** % right on the first answer. NEW (first-answer tracking). */
  firstTryPct: number;
  firstTryRight: number;
  answered: number;
  /** API: LessonProgressResponse.eventual_correct_percentage (course average) */
  eventualPct: number;
  /** API: sum of LessonProgressResponse.resolved_count */
  questionsDone: number;
  /** API: sum of LessonProgressResponse.gave_up_count */
  solutionsShown: number;
}

/** One lesson outcome row. API: LessonProgressResponse.position, lesson_title, state. */
export interface OutcomeRow {
  /** e.g. "1.1" */
  code: string;
  title: string;
  state: LessonUiState;
}

/** NEW. One line of recent work with the XP it earned. */
export interface RecentWorkItem {
  id: string;
  title: string;
  when: string;
  result: { label: string; tone: Tone };
  xp: number;
}

export interface ProgressProps {
  player: Player;
  /** API: CourseMapResponse.title */
  courseTitle: string;
  league: League;
  unit: UnitSummary;
  badges: Badge[];
  stats: ProgressStats;
  /** NEW. Oldest due Try again question, if any. */
  retry: (ReviewItem & { dueNote: string }) | null;
  outcomes: OutcomeRow[];
  recent: RecentWorkItem[];
  routes?: KitRoutes;
}

function StatsCard({ stats }: { stats: ProgressStats }) {
  const cells = [
    {
      value: (
        <>
          {stats.lessonsProficient} <span className="text-base font-semibold text-ns-muted">of {stats.lessonCount}</span>
        </>
      ),
      label: "Lessons proficient",
    },
    { value: `${stats.firstTryPct}%`, label: "Right first try", sub: `${stats.firstTryRight} of ${stats.answered} answered questions` },
    { value: `${stats.eventualPct}%`, label: "Right in the end", sub: "after hints and retries" },
    { value: String(stats.questionsDone), label: "Questions done", sub: `${stats.solutionsShown} solution${stats.solutionsShown === 1 ? "" : "s"} shown` },
  ];
  return (
    <Card className="p-6">
      <dl className="m-0 grid grid-cols-2 gap-x-4 gap-y-5 lg:grid-cols-4">
        {cells.map((cell) => (
          <div key={cell.label} className="flex flex-col gap-0.5">
            <dt className="order-2 text-sm leading-5 text-ns-muted">{cell.label}</dt>
            <dd className="order-1 m-0 text-[26px] leading-8 font-bold tabular-nums">{cell.value}</dd>
            {cell.sub ? <span className="order-3 text-xs text-ns-muted">{cell.sub}</span> : null}
          </div>
        ))}
      </dl>
    </Card>
  );
}

function RetryCard({ item }: { item: NonNullable<ProgressProps["retry"]> }) {
  return (
    <Card tone="amber" className="gap-3">
      <div className="flex items-center justify-between gap-2">
        <H3>Try again</H3>
        <DoubleXpPill />
      </div>
      <div className="flex items-center gap-2.5">
        <div className="flex min-w-0 grow flex-col gap-0.5">
          <span className="text-[15px] leading-5 font-semibold">{item.title}</span>
          <span className="text-[13px] leading-[18px] text-ns-muted">{item.dueNote}</span>
        </div>
        <XpTag xp={item.xp} />
        <Button size="sm" icon={RotateCcw} href={item.href} ariaLabel={`Retry ${item.title}`}>
          Retry
        </Button>
      </div>
    </Card>
  );
}

function OutcomesCard({ unit, outcomes }: { unit: UnitSummary; outcomes: OutcomeRow[] }) {
  return (
    <Card className="gap-3.5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <H3>{unit.code} by outcome</H3>
        {unit.checkpoint.open ? <Tag tone="success">Unit checkpoint open</Tag> : <Tag icon={Lock}>Unit checkpoint locked</Tag>}
      </div>
      <ul className="m-0 flex list-none flex-col gap-3 p-0">
        {outcomes.map((row) => (
          <li key={row.code} className="flex items-center gap-3">
            <span className="w-7 shrink-0 text-sm font-semibold text-ns-muted tabular-nums">{row.code}</span>
            <span className="min-w-0 grow text-[15px] leading-[22px] font-semibold">{row.title}</span>
            <LessonStateTag state={row.state} />
          </li>
        ))}
      </ul>
    </Card>
  );
}

function RecentWorkCard({ items }: { items: RecentWorkItem[] }) {
  return (
    <Card className="gap-3.5">
      <H3>Recent work</H3>
      <ul className="m-0 flex list-none flex-col gap-3.5 p-0">
        {items.map((item) => (
          <li key={item.id} className="flex items-center gap-2.5">
            <div className="flex min-w-0 grow flex-col">
              <span className="text-[15px] leading-5 font-semibold">{item.title}</span>
              <span className="text-[13px] leading-[18px] text-ns-muted">{item.when}</span>
            </div>
            <Tag tone={item.result.tone}>{item.result.label}</Tag>
            {item.xp > 0 ? (
              <XpTag xp={item.xp} className="w-[62px] justify-end" />
            ) : (
              <span className="w-[62px] text-right text-[13px] text-ns-muted">+0</span>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
}

/** Canvas: Progress.m, Progress.d */
export function ProgressScreen({ player, courseTitle, league, unit, badges, stats, retry, outcomes, recent, routes = PREVIEW_ROUTES }: ProgressProps) {
  const you = league.entries.find((entry) => entry.isYou);
  const ahead = you ? league.entries.find((entry) => entry.rank === you.rank - 1) : undefined;
  const leagueSub = you && ahead ? `${ahead.xp - you.xp} XP behind #${ahead.rank}` : you ? "Top of the table" : "Not in the league";
  const retryCard = retry ? <RetryCard item={retry} /> : null;
  return (
    <AppShell
      active="progress"
      player={player}
      routes={routes}
      top={<TopBar title="Progress" right={<MiniChips player={player} routes={routes} />} />}
    >
      <div className="flex flex-col gap-1">
        <H1>Your progress</H1>
        <Muted className="hidden text-base leading-6 lg:block">{courseTitle}</Muted>
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-6">
        <div className="flex flex-col gap-4">
          <ProgressLevelCard player={player} />
          <div className="grid grid-cols-3 gap-3">
            <StatCell
              href={routes.streak}
              icon={<GameIcon name="flame" size={22} className="text-ns-amber" />}
              value={String(player.streakDays)}
              label="Day streak"
              sub={`Best ${player.bestStreakDays} · ${player.streakFreezes} freeze${player.streakFreezes === 1 ? "" : "s"}`}
            />
            <StatCell
              href={routes.league}
              icon={<GameIcon name="trophy" size={22} />}
              value={player.leagueRank ? `#${player.leagueRank}` : "-"}
              label={league.name}
              sub={leagueSub}
            />
            <StatCell
              href={unit.href}
              icon={<GameIcon name="star" size={22} className="text-ns-gold" />}
              value={String(unit.starsEarned)}
              label={`Stars in ${unit.code}`}
              sub={`of ${unit.starsTotal}`}
            />
          </div>
        </div>
        <BadgeShelf badges={badges} allHref={routes.badges} />
      </div>
      <div className="flex flex-col gap-2">
        <StatsCard stats={stats} />
        <Muted className="text-sm">
          &quot;Right first try&quot; counts only your first answer to each question. It shows what you knew before any hints.
        </Muted>
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-6">
        <div className="flex flex-col gap-4">
          {retryCard ? <div className="lg:hidden">{retryCard}</div> : null}
          <OutcomesCard unit={unit} outcomes={outcomes} />
        </div>
        <div className="flex flex-col gap-4 lg:gap-6">
          {retryCard ? <div className="hidden lg:block">{retryCard}</div> : null}
          <RecentWorkCard items={recent} />
        </div>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Settings                                                            */
/* ------------------------------------------------------------------ */

/** NEW. Stored per learner by the gamification service. */
export interface GameSettings {
  sounds: boolean;
  celebrations: boolean;
  showInLeague: boolean;
  streakReminder: boolean;
  /** e.g. "19:30" */
  reminderTime: string;
}

export interface SettingsProps {
  player: Player;
  /** API: ProfileResponse.display_name, ProfileResponse.email */
  profile: { displayName: string; email: string };
  gameSettings: GameSettings;
  /** API: EnrolmentResponse.course_key (course title), ProfileResponse.target_track (intake) */
  course: { title: string; intake: string };
  /** Form actions. Field names: display_name; sounds, celebrations, show_in_league, streak_reminder; confirm. */
  actions?: {
    saveProfile?: FormAction;
    /** Submit on change from a small client wrapper; there is no save button. */
    saveGameSettings?: FormAction;
    signOut?: FormAction;
    deleteAccount?: FormAction;
  };
  /** Link that opens the delete dialog (e.g. ?dialog=delete). */
  deleteHref: Href;
  /** Shows the delete confirmation over the page. */
  deleteDialog?: { badgesEarned: number; cancelHref: Href; /** What is typed in the confirm box so far. */ typed?: string } | null;
  routes?: KitRoutes;
}

/** Checkbox styled as a switch. Server-safe: uses defaultChecked. */
export function SwitchRow({ name, label, description, defaultChecked }: { name: string; label: string; description?: string; defaultChecked: boolean }) {
  const id = useId();
  return (
    <label htmlFor={`${id}-input`} className="flex min-h-11 cursor-pointer items-center gap-3">
      <span className="flex min-w-0 grow flex-col gap-0.5">
        <span id={`${id}-label`} className="text-base leading-[22px] font-semibold">
          {label}
        </span>
        {description ? (
          <span id={`${id}-desc`} className="text-[13px] leading-[18px] text-ns-muted">
            {description}
          </span>
        ) : null}
      </span>
      <input
        id={`${id}-input`}
        type="checkbox"
        role="switch"
        name={name}
        defaultChecked={defaultChecked}
        aria-labelledby={`${id}-label`}
        aria-describedby={description ? `${id}-desc` : undefined}
        className="peer sr-only"
      />
      <span
        aria-hidden="true"
        className="relative h-7 w-12 shrink-0 rounded-full bg-ns-line transition-colors peer-checked:bg-ns-ink peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-ns-success after:absolute after:top-[3px] after:left-[3px] after:size-[22px] after:rounded-full after:bg-white after:shadow-ns-sm after:transition-transform peer-checked:after:translate-x-5"
      />
    </label>
  );
}

function DeleteDialog({ player, badgesEarned, cancelHref, typed, action }: { player: Player; badgesEarned: number; cancelHref: Href; typed?: string; action?: FormAction }) {
  const titleId = useId();
  return (
    <Sheet titleId={titleId}>
      <H2 className="text-xl">
        <span id={titleId}>Delete your account?</span>
      </H2>
      <div className="flex items-center gap-2.5">
        <Hornbill size={64} mood="sleepy" branch={false} />
        <p className="m-0 text-[15px] leading-[22px] text-ns-muted">
          Your profile, every answer and all progress will be removed, including your{" "}
          <b className="text-ns-ink">
            {player.streakDays}-day streak, {fmt(player.xpTotal)} XP and {badgesEarned} badge{badgesEarned === 1 ? "" : "s"}
          </b>
          . Your invitation cannot be reused.
        </p>
      </div>
      <form action={action} className="flex flex-col gap-4">
        <FormField name="confirm" label="Type DELETE to confirm" defaultValue={typed} mono />
        <div className="flex flex-col gap-2">
          <Button type="submit" variant="danger" full icon={Trash2}>
            Delete my account
          </Button>
          <Button full href={cancelHref}>
            Keep my account
          </Button>
        </div>
      </form>
    </Sheet>
  );
}

/** Canvas: Settings.m, Settings.d, SettingsDelete.m */
export function SettingsScreen({
  player,
  profile,
  gameSettings,
  course,
  actions,
  deleteHref,
  deleteDialog,
  routes = PREVIEW_ROUTES,
}: SettingsProps) {
  return (
    <AppShell
      active="me"
      player={player}
      routes={routes}
      maxWidth={640}
      className="lg:mr-auto"
      top={<TopBar backHref={routes.profile} title="Settings" right={<MiniChips player={player} routes={routes} />} />}
    >
      <div className="flex flex-col gap-1">
        <BackLink href={routes.profile} label="Me" />
        <H1>Settings</H1>
      </div>

      <Card className="gap-5 p-6">
        <H2>Profile</H2>
        <form action={actions?.saveProfile} className="flex flex-col gap-5">
          <FormField name="display_name" label="Display name" defaultValue={profile.displayName} />
          <FormField name="email" label="Google account" defaultValue={profile.email} readOnly hint="You sign in with this account. It cannot be changed here." />
          <div>
            <Button type="submit" variant="primary">
              Save changes
            </Button>
          </div>
        </form>
      </Card>

      <Card className="gap-3 p-6">
        <div className="flex items-center justify-between">
          <H2>Game settings</H2>
          <Hornbill size={40} crop="head" outfit={player.equippedOutfit} />
        </div>
        <form action={actions?.saveGameSettings} className="flex flex-col gap-3">
          <SwitchRow name="sounds" label="Sounds" description="A soft chime for right answers and level ups." defaultChecked={gameSettings.sounds} />
          <SwitchRow
            name="celebrations"
            label="Celebrations"
            description="Confetti and the hornbill dance. Turns off by itself if your device reduces motion."
            defaultChecked={gameSettings.celebrations}
          />
          <SwitchRow
            name="show_in_league"
            label="Show me in the Beta League"
            description="Others see your first name and weekly XP only."
            defaultChecked={gameSettings.showInLeague}
          />
          <SwitchRow
            name="streak_reminder"
            label="Streak reminder"
            description={`One nudge at ${gameSettings.reminderTime} if you have not practised today.`}
            defaultChecked={gameSettings.streakReminder}
          />
        </form>
        <Muted className="text-[13px] leading-[18px]">XP never comes from speed, and mistakes never cost XP.</Muted>
      </Card>

      <Card className="gap-3.5 p-6">
        <H2>Course</H2>
        <dl className="m-0 flex flex-col gap-3">
          <div className="flex flex-col-reverse gap-0.5">
            <dd className="m-0 text-base font-semibold">{course.title}</dd>
            <dt className="text-[13px] text-ns-muted">Enrolled in</dt>
          </div>
          <div className="flex flex-col-reverse gap-0.5">
            <dd className="m-0 text-base font-semibold">{course.intake}</dd>
            <dt className="text-[13px] text-ns-muted">Intake</dt>
          </div>
        </dl>
        <Muted>To change your intake, message the NextScholar team. Your progress stays with this course.</Muted>
      </Card>

      <Card className="gap-4 p-6">
        <H2>Account</H2>
        <form action={actions?.signOut} className="flex items-center gap-3">
          <div className="flex min-w-0 grow flex-col gap-0.5">
            <span className="text-base font-semibold">Sign out</span>
            <span className="text-sm text-ns-muted">On this device only.</span>
          </div>
          <Button type="submit" size="sm" icon={LogOut}>
            Sign out
          </Button>
        </form>
        <Divider />
        <div className="flex flex-col items-start gap-2">
          <span className="text-base font-semibold text-ns-danger">Delete account</span>
          <Muted>Removes your profile, answers and progress for good. This cannot be undone.</Muted>
          <Button variant="danger" size="sm" icon={Trash2} href={deleteHref}>
            Delete my account
          </Button>
        </div>
      </Card>

      {deleteDialog ? (
        <DeleteDialog player={player} badgesEarned={deleteDialog.badgesEarned} cancelHref={deleteDialog.cancelHref} typed={deleteDialog.typed} action={actions?.deleteAccount} />
      ) : null}
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Me (profile and wardrobe)                                           */
/* ------------------------------------------------------------------ */

export interface ProfileProps {
  player: Player;
  /** NEW */
  wardrobe: OutfitItem[];
  /** NEW */
  badges: Badge[];
  /** NEW. e.g. "Headphones unlock in 80 XP" */
  nextUnlockLabel?: string;
  /** Equip an outfit. Field name: outfit. */
  equipAction?: FormAction;
  routes?: KitRoutes;
}

function WardrobeTile({ item }: { item: OutfitItem }) {
  const art =
    item.outfit === "flame-scarf" ? (
      <GameIcon name="flame" size={34} className="text-ns-amber" />
    ) : (
      <Hornbill size={64} crop="head" outfit={item.outfit} />
    );
  const box = cn(
    "relative flex h-[84px] w-full items-center justify-center rounded-2xl border-2 bg-ns-raised lg:h-24",
    item.equipped ? "border-ns-amber" : "border-ns-line",
  );
  const caption = (
    <>
      <span className="text-center text-xs leading-4 font-extrabold lg:text-[13px]">{item.name}</span>
      <span className={cn("text-center text-[11px] leading-4 lg:text-xs", item.equipped ? "text-ns-amber-text" : "text-ns-muted")}>
        {item.equipped ? "Equipped" : item.requirement}
      </span>
    </>
  );
  if (!item.unlocked) {
    return (
      <li className="flex flex-col items-center gap-1">
        <div className={cn(box, "opacity-50")}>
          {art}
          <span className="absolute top-1.5 right-1.5 text-ns-muted">
            <GameIcon name="lock" size={14} />
          </span>
        </div>
        {caption}
        <span className="sr-only">Locked</span>
      </li>
    );
  }
  return (
    <li>
      <button
        type="submit"
        name="outfit"
        value={item.outfit}
        aria-pressed={item.equipped}
        className={cn("flex w-full cursor-pointer flex-col items-center gap-1 rounded-2xl bg-transparent p-0 text-ns-ink", focusRing)}
      >
        <span className={cn(box, !item.equipped && "hover:border-ns-line-strong")}>{art}</span>
        {caption}
      </button>
    </li>
  );
}

/** Canvas: Profile.m, Profile.d */
export function ProfileScreen({ player, wardrobe, badges, nextUnlockLabel, equipAction, routes = PREVIEW_ROUTES }: ProfileProps) {
  const earned = badges.filter((badge) => badge.earned).length;
  return (
    <AppShell
      active="me"
      player={player}
      routes={routes}
      maxWidth={1120}
      top={
        <TopBar
          title="Me"
          right={
            <Link href={routes.settings} className={cn("rounded-full px-1 py-2.5 text-[15px] font-bold text-ns-amber-text underline", focusRing)}>
              Settings
            </Link>
          }
        />
      }
    >
      <H1 className="hidden lg:block">Me</H1>
      <div className="grid items-start gap-4 lg:grid-cols-[360px_minmax(0,1fr)] lg:gap-6">
        <Card className="gap-3.5 lg:gap-4 lg:p-6">
          <div className="flex flex-col items-center gap-1.5 py-2">
            <div className="flex size-[180px] animate-ns-float items-center justify-center rounded-full bg-ns-amber-soft lg:size-[220px]">
              <span className="lg:hidden">
                <Hornbill size={160} mood="happy" outfit={player.equippedOutfit} label="Your hornbill" />
              </span>
              <span className="hidden lg:block">
                <Hornbill size={196} mood="happy" outfit={player.equippedOutfit} label="Your hornbill" />
              </span>
            </div>
            <h2 className="m-0 text-[22px] leading-8 font-extrabold lg:text-2xl">
              <span className="lg:hidden">{firstName(player)}</span>
              <span className="hidden lg:inline">{player.displayName}</span>
            </h2>
            <div className="flex flex-wrap justify-center gap-1.5">
              <Tag tone="brand">Level {player.level}</Tag>
              <Tag tone="amber">{player.rankTitle}</Tag>
              <span className="hidden lg:inline-flex">
                <Tag>{player.intake}</Tag>
              </span>
            </div>
          </div>
          <XpBar level={player.level} current={player.xpIntoLevel} needed={player.xpForLevel} />
          <dl className="m-0 hidden grid-cols-3 gap-2 lg:grid">
            <ProfileStat value={fmt(player.xpTotal)} label="Total XP" />
            <ProfileStat value={String(player.bestStreakDays)} label="Best streak" />
            <ProfileStat value={player.leagueRank ? `#${player.leagueRank}` : "-"} label="League" />
          </dl>
          <div className="hidden lg:block">
            <Button full icon={User} href={routes.settings}>
              Settings
            </Button>
          </div>
        </Card>

        <div className="flex flex-col gap-4 lg:gap-6">
          <Card className="gap-3 lg:gap-3.5 lg:p-6">
            <div className="flex items-center justify-between gap-2">
              <H3>Wardrobe</H3>
              {nextUnlockLabel ? <span className="hidden text-[13px] font-bold text-ns-amber-text lg:inline">{nextUnlockLabel}</span> : null}
            </div>
            <form action={equipAction}>
              <ul className="m-0 grid list-none grid-cols-3 gap-3 p-0 lg:grid-cols-6">
                {wardrobe.map((item) => (
                  <WardrobeTile key={item.outfit} item={item} />
                ))}
              </ul>
            </form>
          </Card>

          <Card className="gap-3 lg:hidden">
            <dl className="m-0 grid grid-cols-3 gap-2">
              <ProfileStat value={fmt(player.xpTotal)} label="Total XP" />
              <ProfileStat value={String(player.bestStreakDays)} label="Best streak" />
              <ProfileStat value={String(earned)} label="Badges" />
            </dl>
            <Button full href={routes.badges}>
              See all badges
            </Button>
          </Card>

          <Card className="hidden gap-4 p-6 lg:flex">
            <div className="flex items-center justify-between">
              <H3>
                <Link href={routes.badges} className="text-ns-ink no-underline hover:underline">
                  Badges
                </Link>
              </H3>
              <Tag tone="amber">
                {earned} of {badges.length}
              </Tag>
            </div>
            <ul className="m-0 grid list-none grid-cols-5 gap-x-3 gap-y-[22px] p-0">
              {badges.map((badge) => (
                <li key={badge.id}>
                  <BadgeTile badge={badge} />
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}

function ProfileStat({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex flex-col-reverse gap-0.5">
      <dt className="text-[13px] leading-[18px] text-ns-muted">{label}</dt>
      <dd className="m-0 text-[26px] leading-8 font-bold tabular-nums">{value}</dd>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* League                                                              */
/* ------------------------------------------------------------------ */

export interface LeagueProps {
  player: Player;
  /** NEW. league.endsIn is the long form, e.g. "2 days 5 hours". */
  league: League;
  /** e.g. "2d 5h" for the phone top bar. */
  endsInShort: string;
  /** NEW. "How to climb" list. */
  climbRules: XpLine[];
  practiseHref: Href;
  routes?: KitRoutes;
}

const PODIUM = [
  { rank: 2, height: 84, colour: "bg-ns-silver" },
  { rank: 1, height: 110, colour: "bg-ns-gold" },
  { rank: 3, height: 64, colour: "bg-ns-bronze" },
];
const MEDAL_BG = ["bg-ns-gold", "bg-ns-silver", "bg-ns-bronze"];

function Podium({ league, player }: { league: League; player: Player }) {
  return (
    <ol aria-label="Top 3" className="m-0 flex list-none items-end justify-center gap-2 p-0 pt-2">
      {PODIUM.map((spot) => {
        const entry = league.entries.find((e) => e.rank === spot.rank);
        if (!entry) return null;
        return (
          <li key={spot.rank} className="flex flex-col items-center justify-end gap-1">
            {spot.rank === 1 ? (
              <span className="-mb-1.5 text-ns-gold">
                <GameIcon name="crown" size={24} />
              </span>
            ) : null}
            {entry.isYou ? (
              <LevelRing size={56} level={player.level} pct={levelPct(player)} outfit={player.equippedOutfit} />
            ) : (
              <Avatar initials={entry.initials} size={52} />
            )}
            <b className="text-sm">{entry.isYou ? "You" : entry.name.split(" ")[0]}</b>
            <span className="text-xs text-ns-muted tabular-nums">{entry.xp} XP</span>
            <span
              className={cn("flex w-[88px] justify-center rounded-t-[14px] pt-2 text-2xl font-black text-ns-ink", spot.colour)}
              style={{ height: spot.height }}
            >
              <span className="sr-only">Place </span>
              {spot.rank}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function ChaseCard({ league, practiseHref, wide }: { league: League; practiseHref: Href; wide?: boolean }) {
  if (!league.chase) return null;
  const title = `${league.chase.xpBehind} XP to pass ${league.chase.name}`;
  return (
    <Card tone="amber" className={cn(wide ? "gap-3.5" : "flex-row items-center gap-3 p-4")}>
      <div className="flex min-w-0 grow items-center gap-3">
        <GameIcon name="bolt" size={wide ? 28 : 24} className="shrink-0 text-ns-amber" />
        <div className="flex min-w-0 flex-col gap-0.5">
          <H3>{title}</H3>
          <Muted className={cn(!wide && "text-[13px] leading-[18px]")}>
            One practice set is about 60 XP.{wide ? " Review questions are double." : ""}
          </Muted>
        </div>
      </div>
      {wide ? (
        <Button variant="primary" full href={practiseHref} iconRight={ArrowRight}>
          Practise now
        </Button>
      ) : (
        <Button variant="primary" size="sm" href={practiseHref}>
          Practise
        </Button>
      )}
    </Card>
  );
}

function LeagueRow({ entry, player, crowned }: { entry: LeagueEntry; player: Player; crowned: boolean }) {
  return (
    <div
      className={cn(
        "flex items-center gap-3.5 rounded-xl px-3 py-2.5",
        entry.isYou && "border-[1.5px] border-ns-amber-line bg-ns-amber-soft",
      )}
    >
      {crowned ? (
        <span className={cn("inline-flex size-[30px] shrink-0 items-center justify-center rounded-full text-sm font-black text-ns-ink", MEDAL_BG[entry.rank - 1])}>
          {entry.rank}
        </span>
      ) : (
        <span className="w-[30px] shrink-0 text-center text-[15px] font-extrabold text-ns-muted">{entry.rank}</span>
      )}
      {entry.isYou ? (
        <LevelRing size={40} level={player.level} pct={levelPct(player)} outfit={player.equippedOutfit} />
      ) : (
        <Avatar initials={entry.initials} size={40} />
      )}
      <div className="flex min-w-0 grow flex-col">
        <span className={cn("text-[15px]", entry.isYou ? "font-extrabold" : "font-bold")}>
          {entry.name}
          {entry.isYou ? " (you)" : ""}
        </span>
        {entry.note ? <span className="text-xs font-bold text-ns-success">{entry.note}</span> : null}
      </div>
      {crowned ? (
        <span className="text-ns-gold">
          <GameIcon name="crown" size={20} />
          <span className="sr-only">Crown zone</span>
        </span>
      ) : null}
      <span className="w-[70px] text-right text-[15px] font-extrabold tabular-nums">{entry.xp} XP</span>
    </div>
  );
}

function FullLeagueTable({ league, player }: { league: League; player: Player }) {
  return (
    <Card className="gap-1 p-3">
      <ol className="m-0 flex list-none flex-col gap-1 p-0">
        {league.entries.map((entry) => (
          <li key={entry.rank}>
            <LeagueRow entry={entry} player={player} crowned={entry.rank <= league.crownPlaces} />
            {entry.rank === league.crownPlaces ? (
              <div className="flex items-center gap-2.5 px-3 pt-2 pb-1 text-xs font-extrabold tracking-[0.06em] text-ns-amber-text">
                <span className="h-px grow bg-ns-amber-line" />
                CROWN ZONE ENDS
                <span className="h-px grow bg-ns-amber-line" />
              </div>
            ) : null}
          </li>
        ))}
      </ol>
    </Card>
  );
}

function PhoneLeagueRest({ entries }: { entries: LeagueEntry[] }) {
  return (
    <Card className="gap-0 px-3 py-2">
      <ol className="m-0 flex list-none flex-col p-0">
        {entries.map((entry) => (
          <li key={entry.rank} className="flex items-center gap-3 px-1 py-2">
            <span className="w-[22px] text-[15px] font-extrabold text-ns-muted">{entry.rank}</span>
            <Avatar initials={entry.initials} size={36} />
            <div className="flex min-w-0 grow flex-col">
              <span className="text-[15px] font-bold">{entry.name}</span>
              {entry.note ? <span className="text-xs font-bold text-ns-success">{entry.note}</span> : null}
            </div>
            <span className="text-[15px] font-extrabold tabular-nums">
              {entry.xp}
              <span className="sr-only"> XP</span>
            </span>
          </li>
        ))}
      </ol>
    </Card>
  );
}

function PrizeCard({ crownPlaces }: { crownPlaces: number }) {
  return (
    <Card className="flex-row items-center gap-4">
      <span className="flex size-24 shrink-0 items-center justify-center rounded-3xl bg-ns-ink">
        <Hornbill size={84} mood="happy" outfit="crown" branch={false} />
      </span>
      <div className="flex min-w-0 flex-col gap-1">
        <Eyebrow>This week’s prize</Eyebrow>
        <H3>The golden crown</H3>
        <Muted>The top {crownPlaces} wear it on their hornbill all next week.</Muted>
      </div>
    </Card>
  );
}

/** Canvas: League.m, League.d */
export function LeagueScreen({ player, league, endsInShort, climbRules, practiseHref, routes = PREVIEW_ROUTES }: LeagueProps) {
  return (
    <AppShell
      active="league"
      player={player}
      routes={routes}
      top={
        <TopBar
          title={league.name}
          right={<span className="text-[13px] font-bold whitespace-nowrap text-ns-muted">Ends in {endsInShort}</span>}
        />
      }
    >
      <div className="hidden items-end gap-4 lg:flex">
        <div className="flex grow flex-col gap-1.5">
          <Eyebrow>
            {league.weekLabel} · ends in {league.endsIn}
          </Eyebrow>
          <H1>{league.name}</H1>
          <Muted className="text-base leading-6">
            Everyone in the beta is in one league. XP comes from practice and lessons, never from speed.
          </Muted>
        </div>
        <div className="flex gap-2">
          <StreakChip days={player.streakDays} href={routes.streak} />
          <XpChip xp={player.xpTotal} href={routes.quests} />
        </div>
      </div>

      {/* Phones: podium, chase, the rest of the table */}
      <div className="flex flex-col gap-4 lg:hidden">
        <h1 className="sr-only">{league.name}</h1>
        <Podium league={league} player={player} />
        <ChaseCard league={league} practiseHref={practiseHref} />
        <PhoneLeagueRest entries={league.entries.filter((entry) => entry.rank > 3)} />
        <Muted className="text-[13px] leading-[18px]">
          Everyone in the beta is in one league. Top {league.crownPlaces} wear the golden crown for a week. XP comes from practice and
          lessons, never from speed.
        </Muted>
      </div>

      {/* Desktop: full table and side cards */}
      <div className="hidden items-start gap-6 lg:grid lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <FullLeagueTable league={league} player={player} />
        <div className="flex flex-col gap-5">
          <ChaseCard league={league} practiseHref={practiseHref} wide />
          <PrizeCard crownPlaces={league.crownPlaces} />
          <XpRulesCard title="How to climb" rules={climbRules} note="You can hide yourself from the league in Settings." />
        </div>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Badges                                                              */
/* ------------------------------------------------------------------ */

export interface BadgesProps {
  player: Player;
  /** NEW */
  badges: Badge[];
  /** NEW. The badge closest to being earned, with a plain hint. */
  almost?: { badge: Badge; hint: string } | null;
  routes?: KitRoutes;
}

/** Canvas: Badges.m */
export function BadgesScreen({ player, badges, almost, routes = PREVIEW_ROUTES }: BadgesProps) {
  const earned = badges.filter((badge) => badge.earned).length;
  const count = (
    <Tag tone="amber">
      {earned} of {badges.length}
    </Tag>
  );
  return (
    <AppShell active="me" player={player} routes={routes} maxWidth={880} top={<TopBar backHref={routes.profile} title="Badges" right={count} />}>
      <div className="hidden flex-col gap-1 lg:flex">
        <BackLink href={routes.profile} label="Me" />
        <div className="flex items-center gap-3">
          <H1>Badges</H1>
          {count}
        </div>
      </div>
      {almost ? (
        <Card tone="amber" className="flex-row items-center gap-3 p-4">
          <span className="opacity-60">
            <Medal icon={almost.badge.icon} tier={almost.badge.tier} size={48} />
          </span>
          <div className="flex min-w-0 flex-col gap-0.5">
            <Eyebrow>Almost there</Eyebrow>
            <H3>{almost.badge.name}</H3>
            <Muted className="text-[13px] leading-[18px]">{almost.hint}</Muted>
          </div>
        </Card>
      ) : null}
      <ul className="m-0 grid list-none grid-cols-3 gap-x-3 gap-y-[22px] p-0 lg:grid-cols-5">
        {badges.map((badge) => (
          <li key={badge.id} title={badge.description}>
            <BadgeTile badge={badge} />
            <span className="sr-only">
              {badge.description}. {badge.earned ? "Earned." : "Not earned yet."}
            </span>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}
