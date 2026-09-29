import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";
import { BarChart3, ChevronLeft, Home, Map as MapIcon, User, X } from "lucide-react";

import { cn } from "@/lib/utils";

import { GameIcon } from "../components/icons";
import { LeagueChip, LevelRing, StreakChip, XpBar, XpChip, levelPct } from "../components/rewards";
import { IconButton, Steps, focusRing } from "../components/ui";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import type { Href, NavKey, Player } from "../types";

export function Logo({ height = 22, reversed }: { height?: number; reversed?: boolean }) {
  // The SVG is 647 x 103.
  return (
    <Image
      src={reversed ? "/beta-kit/logo-reversed.svg" : "/beta-kit/logo.svg"}
      alt="NextScholar"
      width={Math.round((height * 647) / 103)}
      height={height}
      unoptimized
      priority
    />
  );
}

/* ------------------------------------------------------------------ */
/* Navigation                                                          */
/* ------------------------------------------------------------------ */

const NAV: { key: NavKey; label: string; desktopLabel: string }[] = [
  { key: "learn", label: "Learn", desktopLabel: "Learn" },
  { key: "course", label: "Course", desktopLabel: "Course map" },
  { key: "league", label: "League", desktopLabel: "League" },
  { key: "progress", label: "Progress", desktopLabel: "Progress" },
  { key: "me", label: "Me", desktopLabel: "Me" },
];

function NavIcon({ nav, size }: { nav: NavKey; size: number }) {
  switch (nav) {
    case "learn":
      return <Home size={size} aria-hidden />;
    case "course":
      return <MapIcon size={size} aria-hidden />;
    case "league":
      return <GameIcon name="trophy" size={size} />;
    case "progress":
      return <BarChart3 size={size} aria-hidden />;
    case "me":
      return <User size={size} aria-hidden />;
  }
}

export function BottomNav({ active, routes = PREVIEW_ROUTES }: { active: NavKey; routes?: KitRoutes }) {
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-30 flex h-[72px] border-t border-ns-line bg-ns-raised px-2 pb-3 lg:hidden"
    >
      {NAV.map((item) => {
        const on = item.key === active;
        return (
          <Link
            key={item.key}
            href={routes.nav[item.key]}
            aria-current={on ? "page" : undefined}
            className={cn(
              "flex flex-1 flex-col items-center gap-0.5 pt-1.5 text-xs no-underline",
              on ? "font-bold text-ns-ink" : "font-medium text-ns-muted",
              focusRing,
            )}
          >
            <span className={cn("flex h-[30px] w-14 items-center justify-center rounded-full", on && "bg-ns-brand-soft")}>
              <NavIcon nav={item.key} size={22} />
            </span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

/** Desktop sidebar card: hornbill in its level ring, XP bar, streak, league. */
export function PlayerCard({ player, routes = PREVIEW_ROUTES }: { player: Player; routes?: KitRoutes }) {
  return (
    <div className="flex flex-col gap-3 rounded-[18px] border border-ns-line bg-ns-raised p-3.5 shadow-ns-sm">
      <div className="flex items-center gap-3">
        <LevelRing size={48} level={player.level} pct={levelPct(player)} outfit={player.equippedOutfit} />
        <div className="flex flex-col">
          <Link href={routes.profile} className="text-sm font-extrabold text-ns-ink no-underline">
            {player.displayName}
          </Link>
          <span className="text-xs text-ns-muted">
            Level {player.level} · {player.rankTitle}
          </span>
        </div>
      </div>
      <XpBar level={player.level} current={player.xpIntoLevel} needed={player.xpForLevel} showLabel={false} height={8} />
      <span className="text-xs text-ns-muted tabular-nums">
        {player.xpIntoLevel} / {player.xpForLevel} XP to Level {player.level + 1}
      </span>
      <div className="flex gap-1.5">
        <StreakChip small days={player.streakDays} href={routes.streak} />
        <LeagueChip small rank={player.leagueRank} href={routes.league} />
      </div>
    </div>
  );
}

export function Sidebar({ active, player, routes = PREVIEW_ROUTES }: { active: NavKey | null; player: Player; routes?: KitRoutes }) {
  return (
    <aside className="sticky top-0 hidden h-dvh w-[264px] shrink-0 flex-col gap-6 border-r border-ns-line bg-ns-surface px-5 pt-7 pb-6 lg:flex">
      <Link href={routes.nav.learn} className="block px-3.5">
        <Logo height={26} />
      </Link>
      <nav aria-label="Main" className="flex flex-col gap-1">
        {NAV.map((item) => {
          const on = item.key === active;
          return (
            <Link
              key={item.key}
              href={routes.nav[item.key]}
              aria-current={on ? "page" : undefined}
              className={cn(
                "flex h-11 items-center gap-3 rounded-full px-3.5 text-[15px] no-underline",
                on ? "bg-ns-brand-soft font-bold text-ns-ink" : "font-medium text-ns-muted hover:bg-ns-sunken",
                focusRing,
              )}
            >
              <NavIcon nav={item.key} size={20} />
              {item.desktopLabel}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto">
        <PlayerCard player={player} routes={routes} />
      </div>
    </aside>
  );
}

/* ------------------------------------------------------------------ */
/* Top bars (phones)                                                   */
/* ------------------------------------------------------------------ */

export function TopBar({
  title,
  sub,
  backHref,
  right,
  logo,
}: {
  title?: string;
  sub?: string;
  backHref?: Href;
  right?: ReactNode;
  logo?: boolean;
}) {
  return (
    <header className="flex h-[60px] shrink-0 items-center gap-2 border-b border-ns-line bg-ns-surface px-4">
      {backHref ? (
        <Link
          href={backHref}
          aria-label="Back"
          className={cn("-ml-2.5 inline-flex size-11 items-center justify-center rounded-full text-ns-ink", focusRing)}
        >
          <ChevronLeft size={24} aria-hidden />
        </Link>
      ) : null}
      {logo ? <Logo /> : null}
      <div className="flex min-w-0 grow flex-col">
        {title ? <div className="truncate text-base leading-[22px] font-semibold">{title}</div> : null}
        {sub ? <div className="truncate text-xs text-ns-muted">{sub}</div> : null}
      </div>
      {right}
    </header>
  );
}

/** Home screen top bar: hornbill in level ring, streak, XP, league rank. */
export function StatBar({ player, routes = PREVIEW_ROUTES }: { player: Player; routes?: KitRoutes }) {
  return (
    <header className="flex h-16 shrink-0 items-center gap-2 border-b border-ns-line bg-ns-surface px-4">
      <Link href={routes.profile} aria-label={`Level ${player.level}, see my hornbill`} className={cn("rounded-full", focusRing)}>
        <LevelRing size={44} level={player.level} pct={levelPct(player)} outfit={player.equippedOutfit} />
      </Link>
      <span className="grow" />
      <StreakChip days={player.streakDays} href={routes.streak} />
      <XpChip xp={player.xpTotal} href={routes.quests} />
      <LeagueChip rank={player.leagueRank} href={routes.league} />
    </header>
  );
}

/** Practice, checkpoint and grammar header: label, question count, chip, close. */
export function QuestionHeader({
  label,
  questionLabel,
  done,
  current,
  total,
  right,
  closeLabel = "Leave practice. Your place is saved",
  closeHref,
}: {
  label: string;
  questionLabel: string;
  done: number;
  current: number;
  total: number;
  right?: ReactNode;
  closeLabel?: string;
  closeHref?: Href;
}) {
  return (
    <header className="flex shrink-0 flex-col gap-2 border-b border-ns-line bg-ns-surface px-4 pt-2 pb-3 lg:px-0 lg:pt-0 lg:pb-4 lg:border-b-0">
      <div className="flex items-center gap-1.5">
        <div className="flex grow flex-col">
          <span className="text-xs font-semibold text-ns-muted">{label}</span>
          <span className="text-base font-bold lg:text-[28px] lg:leading-9">{questionLabel}</span>
        </div>
        {right}
        <IconButton icon={X} label={closeLabel} href={closeHref} />
      </div>
      <Steps done={done} current={current} total={total} />
    </header>
  );
}

/* ------------------------------------------------------------------ */
/* Page shells                                                         */
/* ------------------------------------------------------------------ */

export interface ShellProps {
  player: Player;
  routes?: KitRoutes;
  children: ReactNode;
  /** Phone top bar. Hidden from 1024px up, where the sidebar takes over. */
  top?: ReactNode;
  /** Sticky footer (action bar). Shown on phones and desktop. */
  footer?: ReactNode;
  /** Adds a decorative layer, e.g. <Confetti />. */
  overlay?: ReactNode;
  className?: string;
  maxWidth?: number;
}

/** Tab screens: bottom nav on phones, sidebar on desktop. */
export function AppShell({ active, player, routes = PREVIEW_ROUTES, children, top, footer, overlay, className, maxWidth = 1080 }: ShellProps & { active: NavKey }) {
  return (
    <div className="ns-root relative min-h-dvh bg-ns-surface font-ns text-ns-ink lg:flex">
      {overlay}
      <Sidebar active={active} player={player} routes={routes} />
      <div className="flex min-h-dvh min-w-0 grow flex-col">
        {top ? <div className="sticky top-0 z-20 lg:hidden">{top}</div> : null}
        <main className="flex grow justify-center px-4 pt-4 pb-28 lg:px-14 lg:pt-10 lg:pb-16">
          <div className={cn("flex w-full flex-col gap-4 lg:gap-6", className)} style={{ maxWidth }}>
            {children}
          </div>
        </main>
        {footer ? <div className="sticky bottom-[72px] z-20 lg:bottom-0">{footer}</div> : null}
      </div>
      <BottomNav active={active} routes={routes} />
    </div>
  );
}

/**
 * Focus screens (lesson, practice, checkpoint, essay): no bottom nav on
 * phones. Desktop still shows the sidebar so XP and streak stay visible.
 */
export function FocusShell({
  player,
  routes = PREVIEW_ROUTES,
  children,
  top,
  footer,
  overlay,
  className,
  maxWidth = 1040,
  active = "course",
  desktopTop,
}: ShellProps & { active?: NavKey | null; desktopTop?: ReactNode }) {
  return (
    <div className="ns-root relative min-h-dvh bg-ns-surface font-ns text-ns-ink lg:flex">
      {overlay}
      <Sidebar active={active} player={player} routes={routes} />
      <div className="flex min-h-dvh min-w-0 grow flex-col">
        {top ? <div className="sticky top-0 z-20 lg:hidden">{top}</div> : null}
        <main className="flex grow justify-center px-4 pt-4 pb-8 lg:px-14 lg:pt-10 lg:pb-16">
          <div className={cn("flex w-full flex-col gap-4 lg:gap-6", className)} style={{ maxWidth }}>
            {desktopTop ? <div className="hidden lg:block">{desktopTop}</div> : null}
            {children}
          </div>
        </main>
        {footer ? <div className="sticky bottom-0 z-20">{footer}</div> : null}
      </div>
    </div>
  );
}

/** Screens with no app chrome (landing, sign in, onboarding, errors). */
export function BareShell({ children, className, overlay }: { children: ReactNode; className?: string; overlay?: ReactNode }) {
  return (
    <div className={cn("ns-root relative min-h-dvh overflow-hidden bg-ns-surface font-ns text-ns-ink", className)}>
      {overlay}
      {children}
    </div>
  );
}

/** Standard footer bar for actions. */
export function FooterBar({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("flex flex-col gap-2 border-t border-ns-line bg-ns-surface px-4 pt-3 pb-5 lg:px-14", className)}>
      <div className="mx-auto flex w-full max-w-[1040px] flex-col gap-2">{children}</div>
    </div>
  );
}
