import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { GameIcon } from "../components/icons";
import { Confetti, Medal, XpBar } from "../components/rewards";
import { Button, Muted, Tag } from "../components/ui";
import { BareShell } from "../shell/app-shell";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import type { Badge, BadgeIcon, Href, Outfit, RankTitle, StreakWeek, Tier } from "../types";

export interface CelebrationAction {
  label: string;
  href: Href;
}

/* ------------------------------------------------------------------ */
/* Big moment layout                                                   */
/* ------------------------------------------------------------------ */

/** Translucent card on the dark celebration background. */
export function DarkCard({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("flex flex-col gap-3 rounded-[18px] border border-ns-on-brand/14 bg-ns-on-brand/8 p-4", className)}>
      {children}
    </div>
  );
}

export interface BigMomentProps {
  eyebrow: string;
  /** The big picture: hornbill, flame, trophy. Decorative. */
  art: ReactNode;
  title: string;
  sub: ReactNode;
  /** Reward cards under the title (use DarkCard). */
  children?: ReactNode;
  primary: CelebrationAction;
  secondary?: CelebrationAction;
  confettiSeed?: number;
}

/**
 * Full-screen dark celebration with confetti and a gold call to action.
 * Phones fill the screen; desktop centres a 440px column.
 */
export function BigMoment({ eyebrow, art, title, sub, children, primary, secondary, confettiSeed = 5 }: BigMomentProps) {
  return (
    <BareShell className="bg-ns-ink text-ns-on-brand" overlay={<Confetti count={46} seed={confettiSeed} />}>
      <main className="relative mx-auto flex min-h-dvh w-full max-w-[440px] flex-col lg:justify-center lg:py-10">
        <div className="flex grow flex-col gap-5 px-4 pt-6 lg:grow-0">
          <div className="flex flex-col items-center gap-2.5 pt-6 text-center">
            <span className="text-[13px] font-extrabold tracking-[0.12em] text-ns-gold uppercase">{eyebrow}</span>
            <div aria-hidden="true" className="animate-ns-pop">
              {art}
            </div>
            <h1 className="m-0 text-[40px] leading-[44px] font-black">{title}</h1>
            <p className="m-0 max-w-[300px] text-base leading-6 text-ns-on-dark-muted">{sub}</p>
          </div>
          {children}
        </div>
        <div className="flex flex-col gap-2 px-4 pt-3 pb-6 lg:pt-8">
          <Button variant="gold" full href={primary.href} className="h-13 text-[17px]">
            {primary.label}
          </Button>
          {secondary ? (
            <Button variant="ghost" full href={secondary.href} className="font-bold text-ns-on-brand hover:bg-ns-on-brand/10">
              {secondary.label}
            </Button>
          ) : null}
        </div>
      </main>
    </BareShell>
  );
}

/** Soft gold glow behind the hero art. */
function Glow({ size, children }: { size: number; children: ReactNode }) {
  return (
    <div
      className="relative flex items-center justify-center rounded-full bg-[radial-gradient(circle,rgb(227_164_75/0.35),rgb(227_164_75/0)_70%)]"
      style={{ width: size, height: size }}
    >
      {children}
    </div>
  );
}

function DarkMedalRow({ icon, tier, title, sub }: { icon: BadgeIcon; tier: Tier; title: string; sub: string }) {
  return (
    <DarkCard>
      <div className="flex items-center gap-3">
        <Medal icon={icon} tier={tier} size={52} pop />
        <div className="flex min-w-0 grow flex-col gap-0.5">
          <b className="text-base">{title}</b>
          <span className="text-[13px] text-ns-on-dark-muted">{sub}</span>
        </div>
      </div>
    </DarkCard>
  );
}

/* ------------------------------------------------------------------ */
/* Level up                                                            */
/* ------------------------------------------------------------------ */

export interface LevelUpProps {
  /** NEW: Player.level after the XP was added. */
  level: number;
  /** NEW: Player.rankTitle */
  rankTitle: RankTitle;
  /** NEW: Player.xpTotal */
  xpTotal: number;
  /** NEW. Outfit unlocked at this level, if any. */
  unlocked: { outfit: Outfit; name: string } | null;
  /** NEW: Player.xpIntoLevel / xpForLevel for the new level. */
  xpIntoLevel: number;
  xpForLevel: number;
  /** NEW. The next level that unlocks something. */
  nextUnlock: { level: number; itemName: string; rankTitle?: RankTitle };
  primary: CelebrationAction;
  secondary?: CelebrationAction;
}

/** Canvas: LevelUp.m */
export function LevelUpScreen({
  level,
  rankTitle,
  xpTotal,
  unlocked,
  xpIntoLevel,
  xpForLevel,
  nextUnlock,
  primary,
  secondary,
}: LevelUpProps) {
  const art = (
    <Glow size={220}>
      <Hornbill size={190} mood="happy" pose="cheer" outfit={unlocked?.outfit ?? null} branch={false} />
      <span className="absolute top-[18px] right-[18px] inline-flex size-[58px] items-center justify-center rounded-full border-4 border-ns-ink bg-ns-gold text-[26px] font-black text-ns-ink">
        {level}
      </span>
    </Glow>
  );
  return (
    <BigMoment
      eyebrow="Level up"
      art={art}
      title={`Level ${level}!`}
      sub={`You are a ${rankTitle} now. ${xpTotal.toLocaleString("en-US")} XP earned since you started.`}
      primary={primary}
      secondary={secondary}
    >
      {unlocked ? (
        <DarkCard>
          <div className="flex items-center gap-3">
            <span className="inline-flex size-[52px] shrink-0 items-center justify-center rounded-[14px] bg-ns-surface">
              <Hornbill size={46} crop="head" outfit={unlocked.outfit} />
            </span>
            <div className="flex min-w-0 flex-col gap-0.5">
              <span className="text-xs font-extrabold tracking-[0.08em] text-ns-gold">UNLOCKED</span>
              <b className="text-[17px] leading-6">{unlocked.name} for your hornbill</b>
            </div>
          </div>
        </DarkCard>
      ) : null}
      <DarkCard>
        <XpBar level={level} current={xpIntoLevel} needed={xpForLevel} dark />
        <span className="text-[13px] leading-[18px] text-ns-on-dark-muted">
          Level {nextUnlock.level} unlocks {nextUnlock.itemName.toLowerCase()}.
          {nextUnlock.rankTitle ? (
            <>
              {" "}
              Level {nextUnlock.level} also makes you <b className="text-ns-on-brand">{nextUnlock.rankTitle}</b>.
            </>
          ) : null}
        </span>
      </DarkCard>
    </BigMoment>
  );
}

/* ------------------------------------------------------------------ */
/* Streak milestone                                                    */
/* ------------------------------------------------------------------ */

const DAY_LETTERS = ["M", "T", "W", "T", "F", "S", "S"];

function DarkWeek({ week }: { week: StreakWeek }) {
  return (
    <div className="flex justify-between">
      {week.days.map((day, i) => (
        <div key={i} className="flex flex-col items-center gap-1">
          <span
            className={cn(
              "inline-flex size-9 items-center justify-center rounded-full",
              day === "done" && "bg-[linear-gradient(180deg,#F6C063_0%,#E3A44B_45%,#C87A1E_100%)] text-white",
              day === "freeze" && "bg-ns-success-soft text-ns-success",
              (day === "today" || day === "empty") && "bg-ns-on-brand/10 text-ns-on-dark-muted",
            )}
          >
            {day === "freeze" ? <GameIcon name="snow" size={18} /> : day === "done" ? <GameIcon name="flame" size={18} /> : null}
          </span>
          <span className="text-xs text-ns-on-dark-muted">{DAY_LETTERS[i]}</span>
        </div>
      ))}
    </div>
  );
}

export interface StreakMilestoneProps {
  /** NEW: Player.streakDays */
  days: number;
  /** NEW. The last 7 days, Monday first. */
  week: StreakWeek;
  /** NEW. Badge earned at this milestone. */
  badge: { name: string; icon: BadgeIcon; tier: Tier };
  /** NEW, e.g. "+ 1 streak freeze for a busy day" */
  bonus: string;
  /** NEW. Days for the next milestone. */
  nextMilestone: number;
  continueHref: Href;
  routes?: KitRoutes;
}

/** Canvas: StreakMilestone.m */
export function StreakMilestoneScreen({
  days,
  week,
  badge,
  bonus,
  nextMilestone,
  continueHref,
  routes = PREVIEW_ROUTES,
}: StreakMilestoneProps) {
  const art = (
    <div className="relative flex size-[200px] items-center justify-center">
      <span className="inline-flex animate-ns-flame text-ns-gold">
        <GameIcon name="flame" size={180} />
      </span>
      <span className="absolute top-[86px] text-[56px] leading-none font-black text-ns-ink">{days}</span>
    </div>
  );
  return (
    <BigMoment
      eyebrow="Streak milestone"
      art={art}
      title={`${days}-day streak!`}
      sub={
        days === 7
          ? "A whole week of practice. Your hornbill is proud."
          : `${days} days of practice in a row. Your hornbill is proud.`
      }
      primary={{ label: "Keep going", href: continueHref }}
      secondary={{ label: `Next milestone: ${nextMilestone} days`, href: routes.streak }}
    >
      <DarkCard>
        <DarkWeek week={week} />
      </DarkCard>
      <DarkMedalRow icon={badge.icon} tier={badge.tier} title={`${badge.name} badge`} sub={bonus} />
    </BigMoment>
  );
}

/* ------------------------------------------------------------------ */
/* Unit mastered                                                       */
/* ------------------------------------------------------------------ */

export interface UnitMasteredProps {
  /** API: CourseMap unit code, e.g. "N1" */
  unitCode: string;
  /** API: unit title */
  unitTitle: string;
  /** NEW: checkpoint score, e.g. { correct: 7, total: 8 } */
  checkpoint: { correct: number; total: number };
  /** NEW */
  xpEarned: number;
  /** API: number of lessons in the unit. */
  lessonCount: number;
  /** NEW */
  badge: { name: string; icon: BadgeIcon; tier: Tier; rarity: string };
  primary: CelebrationAction;
  secondary?: CelebrationAction;
}

/** Canvas: UnitMastered.m */
export function UnitMasteredScreen({
  unitCode,
  unitTitle,
  checkpoint,
  xpEarned,
  lessonCount,
  badge,
  primary,
  secondary,
}: UnitMasteredProps) {
  const art = (
    <div className="relative flex h-[210px] w-[220px] items-end justify-center">
      <span className="absolute top-0 left-1/2 -translate-x-1/2 text-ns-gold">
        <GameIcon name="trophy" size={150} />
      </span>
      <div className="relative ml-[110px]">
        <Hornbill size={110} mood="happy" pose="cheer" outfit="cap" branch={false} />
      </div>
    </div>
  );
  const stats = [
    { value: `${checkpoint.correct}/${checkpoint.total}`, label: "Checkpoint" },
    { value: `+${xpEarned}`, label: "XP" },
    { value: String(lessonCount), label: "Lessons" },
  ];
  return (
    <BigMoment
      eyebrow="Unit mastered"
      art={art}
      title={`${unitCode} mastered!`}
      sub={`${unitTitle} is done. That is one full unit of the Maths test.`}
      primary={primary}
      secondary={secondary}
    >
      <DarkCard>
        <dl className="m-0 grid grid-cols-3 gap-2 text-center">
          {stats.map((stat) => (
            <div key={stat.label} className="flex flex-col-reverse gap-0.5">
              <dt className="text-xs text-ns-on-dark-muted">{stat.label}</dt>
              <dd className="m-0 text-2xl font-bold">{stat.value}</dd>
            </div>
          ))}
        </dl>
      </DarkCard>
      <DarkMedalRow icon={badge.icon} tier={badge.tier} title={badge.name} sub={badge.rarity} />
    </BigMoment>
  );
}

/* ------------------------------------------------------------------ */
/* Badge unlocked                                                      */
/* ------------------------------------------------------------------ */

export interface BadgeUnlockedProps {
  /** NEW */
  badge: Badge;
  /** NEW. Why it was earned, in the learner's terms. */
  reason: string;
  /** NEW */
  xp: number;
  /** The page under the dialog (dimmed). */
  background?: ReactNode;
  continueHref: Href;
  routes?: KitRoutes;
}

const TIER_LABEL: Record<Tier, string> = { gold: "Gold", silver: "Silver", bronze: "Bronze" };

/** Canvas: BadgeUnlocked.m. A dialog over the current page, with confetti. */
export function BadgeUnlockedScreen({
  badge,
  reason,
  xp,
  background,
  continueHref,
  routes = PREVIEW_ROUTES,
}: BadgeUnlockedProps) {
  const titleId = "badge-unlocked-title";
  return (
    <BareShell>
      {background ? (
        <div inert className="mx-auto flex max-w-[720px] flex-col gap-4 px-4 pt-20 lg:pt-24">
          {background}
        </div>
      ) : null}
      <div className="fixed inset-0 z-40 bg-ns-dark/60">
        <Confetti count={30} seed={9} />
        <div className="flex min-h-full items-start justify-center px-4 pt-[150px] pb-10 lg:items-center lg:pt-10">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            className="relative flex w-full max-w-[420px] animate-ns-pop flex-col items-center gap-3 rounded-[28px] bg-ns-raised px-[22px] pt-7 pb-[22px] text-center shadow-ns-lg"
          >
            <span className="text-xs font-extrabold tracking-[0.12em] text-ns-amber-text">NEW BADGE</span>
            <Medal icon={badge.icon} tier={badge.tier} size={120} pop />
            <h2 id={titleId} className="m-0 text-[28px] leading-8 font-black">
              {badge.name}
            </h2>
            <Muted className="text-[15px] leading-[22px]">{reason}</Muted>
            <div className="flex gap-2">
              <Tag tone="amber">+{xp} XP</Tag>
              <Tag>{TIER_LABEL[badge.tier]}</Tag>
            </div>
            <div className="mt-1.5 flex w-full flex-col gap-2">
              <Button variant="primary" full href={continueHref}>
                Awesome!
              </Button>
              <Button variant="ghost" full href={routes.badges}>
                See all badges
              </Button>
            </div>
          </div>
        </div>
      </div>
    </BareShell>
  );
}
