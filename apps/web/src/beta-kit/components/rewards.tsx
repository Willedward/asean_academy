import Link from "next/link";
import type { ReactNode } from "react";
import { BookOpen, Check, ChevronRight, FileText, RotateCcw, Target } from "lucide-react";

import { cn } from "@/lib/utils";

import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import type { Badge, BadgeIcon, Href, League, Mood, Outfit, Player, Pose, Quest, QuestBoard, StreakWeek, Tier, XpLine } from "../types";
import { Hornbill } from "./hornbill";
import { GameIcon } from "./icons";
import { Bar, Card, H3, focusRing } from "./ui";

/* ------------------------------------------------------------------ */
/* Chips (top bar)                                                     */
/* ------------------------------------------------------------------ */

function Chip({
  href,
  label,
  className,
  children,
  small,
}: {
  href: Href;
  label: string;
  className: string;
  children: ReactNode;
  small?: boolean;
}) {
  return (
    <Link
      href={href}
      aria-label={label}
      className={cn(
        "inline-flex shrink-0 items-center gap-1 rounded-full font-extrabold no-underline tabular-nums",
        small ? "h-8 pr-2.5 pl-1.5 text-sm" : "h-9 gap-1.5 pr-3 pl-2 text-[15px]",
        focusRing,
        className,
      )}
    >
      {children}
    </Link>
  );
}

export function StreakChip({ days, href, small }: { days: number; href: Href; small?: boolean }) {
  const lit = days > 0;
  return (
    <Chip href={href} small={small} label={`${days} day streak`} className="bg-ns-amber-soft text-ns-amber-text">
      <span className={cn("inline-flex", lit && "animate-ns-flame", lit ? "text-ns-amber" : "text-ns-line-strong")}>
        <GameIcon name="flame" size={small ? 18 : 20} />
      </span>
      {days}
    </Chip>
  );
}

export function XpChip({ xp, href, small }: { xp: number; href: Href; small?: boolean }) {
  return (
    <Chip href={href} small={small} label={`${xp} XP`} className="bg-ns-brand-soft text-ns-ink">
      <GameIcon name="bolt" size={small ? 18 : 20} className="text-ns-amber" />
      {xp.toLocaleString("en-US")}
    </Chip>
  );
}

export function LeagueChip({ rank, href, small }: { rank: number | null; href: Href; small?: boolean }) {
  return (
    <Chip
      href={href}
      small={small}
      label={rank ? `Rank ${rank} in this week's league` : "Join this week's league"}
      className="bg-ns-brand-soft text-ns-ink"
    >
      <GameIcon name="trophy" size={small ? 18 : 20} />
      {rank ? `#${rank}` : "Join"}
    </Chip>
  );
}

/** Streak and XP, for the top bar of every tab screen. */
export function MiniChips({ player, routes = PREVIEW_ROUTES }: { player: Player; routes?: KitRoutes }) {
  return (
    <span className="inline-flex shrink-0 gap-1.5">
      <StreakChip small days={player.streakDays} href={routes.streak} />
      <XpChip small xp={player.xpTotal} href={routes.quests} />
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* Level                                                               */
/* ------------------------------------------------------------------ */

export function LevelRing({
  size,
  level,
  pct,
  outfit,
}: {
  size: number;
  level: number;
  pct: number;
  outfit?: Outfit | null;
}) {
  const inner = size - 8;
  return (
    <span
      className="relative inline-flex shrink-0 items-center justify-center rounded-full"
      style={{
        width: size,
        height: size,
        background: `conic-gradient(var(--color-ns-amber) ${pct}%, var(--color-ns-line) 0)`,
      }}
    >
      <span
        className="inline-flex items-center justify-center overflow-hidden rounded-full bg-ns-surface"
        style={{ width: inner, height: inner }}
      >
        <Hornbill size={inner - 4} crop="head" outfit={outfit} />
      </span>
      <span className="absolute -right-1 -bottom-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full border-2 border-ns-surface bg-ns-ink px-1 text-[10px] font-extrabold text-ns-on-brand">
        {level}
      </span>
    </span>
  );
}

export function levelPct(player: Player) {
  return Math.round((player.xpIntoLevel / Math.max(1, player.xpForLevel)) * 100);
}

export function XpBar({
  level,
  current,
  needed,
  showLabel = true,
  dark,
  height = 14,
}: {
  level: number;
  current: number;
  needed: number;
  showLabel?: boolean;
  dark?: boolean;
  height?: number;
}) {
  const pct = Math.round((current / Math.max(1, needed)) * 100);
  return (
    <div className="flex flex-col gap-2">
      {showLabel ? (
        <div className="flex justify-between text-sm leading-5">
          <span className={cn("font-extrabold", dark ? "text-ns-on-brand" : "text-ns-ink")}>Level {level}</span>
          <span className={cn("tabular-nums", dark ? "text-ns-on-dark-muted" : "text-ns-muted")}>
            {current} / {needed} XP
          </span>
        </div>
      ) : null}
      <div
        role="progressbar"
        aria-label={`XP to level ${level + 1}`}
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        className={cn("overflow-hidden rounded-full", dark ? "bg-ns-on-brand/20" : "bg-ns-brand-soft")}
        style={{ height }}
      >
        <div
          className="h-full animate-ns-shine rounded-full bg-[linear-gradient(90deg,var(--color-ns-amber),var(--color-ns-gold),var(--color-ns-gold-light),var(--color-ns-gold),var(--color-ns-amber))] bg-size-[200%_100%]"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* XP labels                                                           */
/* ------------------------------------------------------------------ */

export function Stars({ count, total = 3, size = 14 }: { count: number; total?: number; size?: number }) {
  return (
    <span role="img" aria-label={`${count} of ${total} stars`} className="inline-flex shrink-0 gap-px">
      {Array.from({ length: total }, (_, i) => (
        <GameIcon key={i} name="star" size={size} className={i < count ? "text-ns-gold" : "text-ns-line"} />
      ))}
    </span>
  );
}

export function XpTag({ xp, size = 13, dark, className }: { xp: number; size?: number; dark?: boolean; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-0.5 font-extrabold whitespace-nowrap tabular-nums",
        dark ? "text-ns-gold" : "text-ns-amber-text",
        className,
      )}
      style={{ fontSize: size, lineHeight: `${size + 5}px` }}
    >
      <GameIcon name="bolt" size={size + 1} className={dark ? "text-ns-gold" : "text-ns-amber"} />+{xp} XP
    </span>
  );
}

export function XpPill({ xp, dark }: { xp: number; dark?: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex h-[26px] shrink-0 items-center gap-1 rounded-full px-2.5 text-[13px] font-black whitespace-nowrap",
        dark ? "bg-ns-ink text-ns-gold" : "bg-ns-amber-soft text-ns-amber-text",
      )}
    >
      <GameIcon name="bolt" size={14} className={dark ? "text-ns-gold" : "text-ns-amber"} />+{xp} XP
    </span>
  );
}

export function DoubleXpPill() {
  return (
    <span className="inline-flex h-7 items-center gap-1 self-start rounded-full bg-ns-ink px-2.5 text-xs font-black tracking-[0.03em] whitespace-nowrap text-ns-gold">
      <GameIcon name="bolt" size={14} />
      DOUBLE XP
    </span>
  );
}

export function ComboChip({ label }: { label: string }) {
  return (
    <span className="inline-flex h-8 shrink-0 animate-ns-pop items-center gap-1.5 rounded-full bg-ns-ink px-3 text-sm font-black tracking-[0.02em] whitespace-nowrap text-ns-gold">
      <GameIcon name="flame" size={16} />
      {label}
    </span>
  );
}

/** "+10" rising from an answer. Decorative. */
export function XpPop({ text, className }: { text: string; className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute inline-flex animate-ns-rise items-center gap-1 text-[22px] font-black text-ns-amber [text-shadow:0_2px_0_#fff]",
        className,
      )}
    >
      <GameIcon name="bolt" size={22} />
      {text}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* Mascot talking                                                      */
/* ------------------------------------------------------------------ */

export function Bubble({ children, dark }: { children: ReactNode; dark?: boolean }) {
  return (
    <div
      className={cn(
        "relative rounded-2xl px-3.5 py-3 text-[15px] leading-[21px] font-semibold shadow-ns-sm",
        dark ? "bg-ns-on-brand/10 text-ns-on-brand" : "border border-ns-line bg-ns-raised text-ns-ink",
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "absolute top-[18px] -left-[7px] h-0 w-0 border-y-[7px] border-r-8 border-y-transparent",
          dark ? "border-r-ns-on-brand/10" : "border-r-ns-raised",
        )}
      />
      {children}
    </div>
  );
}

export function MascotSays({
  children,
  size = 72,
  mood = "normal",
  pose = "perch",
  outfit,
}: {
  children: ReactNode;
  size?: number;
  mood?: Mood;
  pose?: Pose;
  outfit?: Outfit | null;
}) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="animate-ns-float">
        <Hornbill size={size} mood={mood} pose={pose} outfit={outfit} branch={false} label="NextScholar hornbill" />
      </div>
      <div className="grow">
        <Bubble>{children}</Bubble>
      </div>
    </div>
  );
}

/** Mascot plus text on a tinted panel. */
export function MascotCard({
  children,
  size = 64,
  mood = "normal",
  pose,
  outfit,
  tone = "amber",
}: {
  children: ReactNode;
  size?: number;
  mood?: Mood;
  pose?: Pose;
  outfit?: Outfit | null;
  tone?: "amber" | "sunken";
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-2xl py-3 pr-3.5 pl-2",
        tone === "amber" ? "bg-ns-amber-soft" : "bg-ns-sunken",
      )}
    >
      <div className="shrink-0 animate-ns-float">
        <Hornbill size={size} mood={mood} pose={pose} outfit={outfit} branch={false} />
      </div>
      <div className="grow text-[15px] leading-[22px] font-semibold text-ns-ink">{children}</div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Quests                                                              */
/* ------------------------------------------------------------------ */

const QUEST_ICON = { check: Check, rotate: RotateCcw, book: BookOpen, target: Target, file: FileText };

export function QuestRow({ quest }: { quest: Quest }) {
  const done = quest.progress >= quest.target;
  const Icon = QUEST_ICON[quest.icon];
  const pct = Math.round((Math.min(quest.progress, quest.target) / quest.target) * 100);
  return (
    <div className="flex items-center gap-3">
      <span
        className={cn(
          "inline-flex size-11 shrink-0 items-center justify-center rounded-[14px]",
          done ? "bg-ns-success-soft text-ns-success" : "bg-ns-amber-soft text-ns-amber-text",
        )}
      >
        <Icon size={20} aria-hidden />
      </span>
      <div className="flex min-w-0 grow flex-col gap-1.5">
        <span className={cn("text-[15px] font-bold", done && "text-ns-muted line-through")}>{quest.title}</span>
        <div className="flex items-center gap-2">
          <div className="grow">
            <Bar pct={pct} fill={done ? "success" : "amber"} />
          </div>
          <span className="w-12 text-right text-xs text-ns-muted tabular-nums">
            {quest.progress}/{quest.target}
          </span>
        </div>
      </div>
      {done ? (
        <span className="inline-flex size-7 items-center justify-center rounded-full bg-ns-success text-white">
          <Check size={16} aria-label="Done" />
        </span>
      ) : (
        <span className="inline-flex items-center gap-0.5 text-[13px] font-extrabold text-ns-amber-text">
          <GameIcon name="bolt" size={14} className="text-ns-amber" />+{quest.xp}
        </span>
      )}
    </div>
  );
}

export function BonusChest({ board }: { board: QuestBoard }) {
  const done = board.quests.filter((q) => q.progress >= q.target).length;
  const total = board.quests.length;
  return (
    <div className="flex items-center gap-3 rounded-[14px] bg-ns-ink px-3.5 py-3 text-ns-on-brand">
      <span className="inline-flex size-10 animate-ns-glow items-center justify-center rounded-xl bg-ns-gold text-ns-ink">
        <GameIcon name="star" size={22} />
      </span>
      <div className="flex min-w-0 grow flex-col gap-0.5">
        <span className="text-sm font-extrabold">
          All {total} quests: +{board.bonusXp} XP bonus
        </span>
        <span className="text-xs text-ns-on-dark-muted">
          {done === total ? "Bonus claimed" : `${total - done} to go`} · resets in {board.resetsIn}
        </span>
      </div>
      <span className="text-xl font-extrabold text-ns-gold">
        {done}/{total}
      </span>
    </div>
  );
}

export function QuestsCard({
  board,
  title = "Daily quests",
  seeAllHref,
}: {
  board: QuestBoard;
  title?: string;
  seeAllHref?: Href;
}) {
  return (
    <Card className="gap-4">
      <div className="flex items-center justify-between gap-3">
        <H3>{title}</H3>
        {seeAllHref ? (
          <Link href={seeAllHref} className="text-sm font-bold text-ns-amber-text">
            See all
          </Link>
        ) : null}
      </div>
      {board.quests.map((quest) => (
        <QuestRow key={quest.id} quest={quest} />
      ))}
      <BonusChest board={board} />
    </Card>
  );
}

export function QuestToast({ quest }: { quest: Quest }) {
  return (
    <div className="flex animate-ns-pop items-center gap-2.5 rounded-xl border border-ns-line bg-ns-raised px-3 py-2.5 shadow-ns-md">
      <span className="inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-ns-success text-white">
        <Check size={16} aria-hidden />
      </span>
      <span className="grow text-sm font-bold">Quest: {quest.title}</span>
      <b className="text-sm">
        {quest.progress}/{quest.target}
      </b>
      <XpPill xp={quest.xp} />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Streak                                                              */
/* ------------------------------------------------------------------ */

const DAY_LETTERS = ["M", "T", "W", "T", "F", "S", "S"];

export function WeekDots({ week }: { week: StreakWeek }) {
  return (
    <div className="flex justify-between">
      {week.days.map((day, i) => (
        <div key={i} className="flex flex-col items-center gap-1">
          {day === "done" ? (
            <span className="inline-flex size-[34px] items-center justify-center rounded-full bg-[linear-gradient(180deg,#F6C063_0%,#E3A44B_45%,#C87A1E_100%)] text-white">
              <GameIcon name="flame" size={18} />
            </span>
          ) : day === "freeze" ? (
            <span className="inline-flex size-[34px] items-center justify-center rounded-full bg-ns-success-soft text-ns-success">
              <GameIcon name="snow" size={18} />
            </span>
          ) : day === "today" ? (
            <span className="inline-flex size-[34px] animate-ns-glow items-center justify-center rounded-full border-[2.5px] border-dashed border-ns-amber text-ns-amber">
              <GameIcon name="flame" size={16} />
            </span>
          ) : (
            <span className="size-[34px] rounded-full bg-ns-sunken" />
          )}
          <span className={cn("text-xs", i === week.todayIndex ? "font-extrabold text-ns-ink" : "text-ns-muted")}>
            {DAY_LETTERS[i]}
          </span>
        </div>
      ))}
    </div>
  );
}

export function StreakCard({ player, week }: { player: Player; week: StreakWeek }) {
  return (
    <Card className="gap-3.5 shadow-ns-md">
      <div className="flex items-center gap-3">
        <span className="inline-flex animate-ns-flame text-ns-amber">
          <GameIcon name="flame" size={40} />
        </span>
        <div className="flex grow flex-col gap-0.5">
          <span className="text-[26px] leading-[30px] font-black">{player.streakDays} day streak</span>
          <span className="text-[13px] text-ns-muted">Practise today to make it {player.streakDays + 1}</span>
        </div>
        <span
          className="inline-flex h-7 items-center gap-1 rounded-full bg-ns-success-soft px-2.5 text-[13px] font-extrabold text-ns-success"
          aria-label={`${player.streakFreezes} streak freeze`}
        >
          <GameIcon name="snow" size={14} />
          {player.streakFreezes}
        </span>
      </div>
      <WeekDots week={week} />
    </Card>
  );
}

/** Small flame message: "your streak is safe". */
export function StreakSafe({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-center gap-2.5 rounded-xl bg-ns-amber-soft px-3.5 py-3">
      <span className="inline-flex animate-ns-flame text-ns-amber">
        <GameIcon name="flame" size={24} />
      </span>
      <p className="m-0 text-sm leading-5 font-semibold text-ns-ink">{children}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Badges                                                              */
/* ------------------------------------------------------------------ */

const RING: Record<Tier, [string, string]> = {
  gold: ["#E3A44B", "#C87A1E"],
  silver: ["#9FB3B4", "#6E8586"],
  bronze: ["#C87A1E", "#94560F"],
};

export function Medal({
  icon,
  tier,
  size = 64,
  locked,
  pop,
}: {
  icon: BadgeIcon;
  tier: Tier;
  size?: number;
  locked?: boolean;
  pop?: boolean;
}) {
  if (locked) {
    return (
      <span
        className="inline-flex items-center justify-center rounded-full border-[3px] border-dashed border-ns-line bg-ns-sunken text-ns-muted"
        style={{ width: size, height: size }}
      >
        <GameIcon name="lock" size={Math.round(size * 0.36)} />
      </span>
    );
  }
  const [ring, edge] = RING[tier];
  return (
    <span
      className={cn("relative inline-flex shrink-0 items-center justify-center rounded-full", pop && "animate-ns-pop")}
      style={{
        width: size,
        height: size,
        background: `radial-gradient(circle at 35% 30%, #FFFFFF 0%, ${ring} 55%, ${edge} 100%)`,
        boxShadow: "inset 0 -4px 0 rgba(0,0,0,0.15), 0 4px 10px rgba(10,42,44,0.2)",
      }}
    >
      <span
        className="inline-flex items-center justify-center rounded-full bg-ns-ink text-ns-gold"
        style={{ width: Math.round(size * 0.7), height: Math.round(size * 0.7) }}
      >
        <GameIcon name={icon} size={Math.round(size * 0.4)} />
      </span>
    </span>
  );
}

export function BadgeTile({ badge }: { badge: Badge }) {
  return (
    <div className="flex flex-col items-center gap-1.5 text-center">
      <div className={cn(!badge.earned && "opacity-45 grayscale-[0.6]")}>
        <Medal icon={badge.icon} tier={badge.tier} size={68} />
      </div>
      <span className="text-[13px] leading-4 font-extrabold">{badge.name}</span>
      {!badge.earned && badge.progress ? (
        <>
          <div className="w-4/5">
            <Bar pct={(badge.progress.current / badge.progress.target) * 100} height={6} />
          </div>
          <span className="text-[11px] text-ns-muted">
            {badge.progress.current}/{badge.progress.target}
          </span>
        </>
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Celebration bits                                                    */
/* ------------------------------------------------------------------ */

const CONFETTI_COLOURS = ["#C87A1E", "#E3A44B", "#F6C063", "#1F6F8B", "#8FD3C8", "#FBFAF7", "#E98F6B"];

function confettiPieces(count: number, seed: number) {
  const out = [];
  let state = seed * 9301 + 49297;
  for (let i = 0; i < count; i += 1) {
    const next = () => {
      state = (state * 9301 + 49297) % 233280;
      return state / 233280;
    };
    const size = 6 + Math.floor(next() * 7);
    out.push({
      left: `${Math.floor(next() * 100)}%`,
      width: size,
      height: i % 2 ? Math.round(size / 2) : size,
      duration: 3.2 + next() * 3.3,
      delay: -next() * 6.5,
      round: i % 3 === 0,
      colour: CONFETTI_COLOURS[i % CONFETTI_COLOURS.length],
    });
  }
  return out;
}

/** Deterministic confetti (same layout on server and client). Decorative. */
export function Confetti({ count = 30, seed = 3 }: { count?: number; seed?: number }) {
  const pieces = confettiPieces(count, seed);
  return (
    <div aria-hidden="true" className="ns-confetti pointer-events-none absolute inset-0 overflow-hidden">
      {pieces.map((piece, i) => (
        <span
          key={i}
          className="absolute top-0"
          style={{
            left: piece.left,
            width: piece.width,
            height: piece.height,
            background: piece.colour,
            borderRadius: piece.round ? 999 : 2,
            animation: `ns-fall ${piece.duration.toFixed(2)}s linear ${piece.delay.toFixed(2)}s infinite`,
          }}
        />
      ))}
    </div>
  );
}

export function Tally({ lines, className }: { lines: XpLine[]; className?: string }) {
  const total = lines.reduce((sum, line) => sum + line.xp, 0);
  return (
    <div className={cn("flex flex-col gap-2.5", className)}>
      {lines.map((line) => (
        <div key={line.label} className="flex items-center gap-2">
          <span className="grow text-[15px]">{line.label}</span>
          <span className="text-[15px] font-extrabold text-ns-amber-text tabular-nums">+{line.xp}</span>
        </div>
      ))}
      <div className="h-px bg-ns-line" />
      <div className="flex items-center gap-2">
        <span className="grow text-[17px] font-black">Total</span>
        <span className="inline-flex animate-ns-pop items-center gap-1 text-[26px] font-black text-ns-amber-text [animation-delay:.3s]">
          <GameIcon name="bolt" size={24} className="text-ns-amber" />+{total}
        </span>
      </div>
    </div>
  );
}

export function RewardLine({
  icon,
  title,
  sub,
  right,
}: {
  icon: ReactNode;
  title: ReactNode;
  sub?: ReactNode;
  right?: ReactNode;
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-ns-amber-soft text-ns-amber-text">
        {icon}
      </span>
      <div className="flex min-w-0 grow flex-col gap-0.5">
        <span className="text-[15px] leading-5 font-bold">{title}</span>
        {sub ? <span className="text-[13px] leading-[18px] text-ns-muted">{sub}</span> : null}
      </div>
      {right}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Answer feedback                                                     */
/* ------------------------------------------------------------------ */

/** Right or wrong answer panel with the hornbill. */
export function Feedback({
  kind,
  title,
  children,
  xp,
  note,
}: {
  kind: "right" | "wrong";
  title?: string;
  children: ReactNode;
  xp?: number;
  note?: ReactNode;
}) {
  const right = kind === "right";
  const shownNote = note ?? (right ? undefined : "Mistakes never cost XP. Get it right to earn +6 XP.");
  return (
    <div
      role="status"
      className={cn(
        "flex animate-ns-pop items-center gap-2.5 rounded-2xl border-[1.5px] py-3 pr-3.5 pl-2",
        right ? "border-ns-success bg-ns-success-soft" : "border-ns-amber-text bg-ns-amber-soft",
      )}
    >
      <div className="shrink-0">
        {right ? (
          <Hornbill size={64} mood="happy" pose="cheer" branch={false} />
        ) : (
          <Hornbill size={60} mood="kind" pose="point" branch={false} />
        )}
      </div>
      <div className="flex min-w-0 grow flex-col gap-0.5">
        <span className={cn("text-lg leading-6 font-black", right ? "text-ns-success" : "text-ns-amber-text")}>
          {title ?? (right ? "Brilliant!" : "Not yet. So close!")}
        </span>
        <div className="text-sm leading-5 text-ns-ink">{children}</div>
        {shownNote ? <span className="text-xs leading-4 font-bold text-ns-muted">{shownNote}</span> : null}
      </div>
      {right && xp ? (
        <span className="inline-flex animate-ns-pop items-center gap-1 text-xl font-black text-ns-amber-text [animation-delay:.15s]">
          <GameIcon name="bolt" size={20} className="text-ns-amber" />+{xp}
        </span>
      ) : null}
    </div>
  );
}

/** "Added to your Try again list" note, shown after a solution is revealed. */
export function ReviewNote({
  children = "Back in 2 days. Clear it then for double XP (+20) and a step toward the Comeback kid badge.",
}: {
  children?: ReactNode;
}) {
  return (
    <div
      role="status"
      className="flex items-center gap-2.5 rounded-2xl border border-ns-amber-line bg-ns-amber-soft py-3 pr-3.5 pl-1.5"
    >
      <Hornbill size={58} mood="think" branch={false} />
      <div className="flex min-w-0 grow flex-col gap-1">
        <DoubleXpPill />
        <b className="text-[15px] leading-5">Added to your Try again list</b>
        <p className="m-0 text-[13px] leading-[18px] text-ns-ink">{children}</p>
      </div>
    </div>
  );
}

/** Small amber line with a bolt: "Right first try: +10 XP". */
export function XpNote({ children, center }: { children: ReactNode; center?: boolean }) {
  return (
    <div
      className={cn(
        "flex items-center gap-1.5 text-[13px] leading-[18px] font-bold text-ns-amber-text",
        center && "justify-center",
      )}
    >
      <GameIcon name="bolt" size={14} className="text-ns-amber" />
      <span>{children}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* League and level cards                                              */
/* ------------------------------------------------------------------ */

export function LeagueMini({ league, href }: { league: League; href: Href }) {
  const you = league.entries.find((entry) => entry.isYou);
  return (
    <Link href={href} className={cn("block rounded-2xl text-inherit no-underline", focusRing)}>
      <Card className="flex-row items-center gap-3 p-4">
        <span className="inline-flex size-11 items-center justify-center rounded-[14px] bg-ns-brand-soft text-ns-ink">
          <GameIcon name="trophy" size={24} />
        </span>
        <div className="flex grow flex-col gap-0.5">
          <span className="text-base font-extrabold">
            #{you?.rank ?? "-"} in the {league.name}
          </span>
          <span className="text-[13px] text-ns-muted">
            {league.chase ? `${league.chase.xpBehind} XP behind ${league.chase.name} · ` : ""}ends in {league.endsIn}
          </span>
        </div>
        <ChevronRight size={20} className="text-ns-muted" aria-hidden />
      </Card>
    </Link>
  );
}

export function LeagueTable({ league, compact }: { league: League; compact?: boolean }) {
  const medal = ["bg-ns-gold", "bg-ns-silver", "bg-ns-bronze"];
  return (
    <div className="flex flex-col gap-1">
      {league.entries.map((entry) => (
        <div key={entry.rank}>
          <div
            className={cn(
              "flex items-center gap-3 rounded-xl px-3",
              compact ? "py-1.5" : "py-2.5",
              entry.isYou && "border-[1.5px] border-ns-amber-line bg-ns-amber-soft",
            )}
          >
            {entry.rank <= league.crownPlaces ? (
              <span
                className={cn(
                  "inline-flex size-7 items-center justify-center rounded-full text-sm font-black text-ns-ink",
                  medal[entry.rank - 1],
                )}
              >
                {entry.rank}
              </span>
            ) : (
              <span className="w-7 text-center text-[15px] font-extrabold text-ns-muted">{entry.rank}</span>
            )}
            <span
              aria-hidden="true"
              className="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-ns-brand-soft text-[13px] font-bold"
            >
              {entry.initials}
            </span>
            <div className="flex min-w-0 grow flex-col">
              <span className={cn("text-[15px]", entry.isYou ? "font-extrabold" : "font-bold")}>
                {entry.name}
                {entry.isYou ? " (you)" : ""}
              </span>
              {entry.note ? <span className="text-xs font-bold text-ns-success">{entry.note}</span> : null}
            </div>
            <span className="text-[15px] font-extrabold tabular-nums">{entry.xp} XP</span>
          </div>
          {!compact && entry.rank === league.crownPlaces ? (
            <div className="flex items-center gap-2.5 px-3 py-1 text-xs font-extrabold tracking-[0.06em] text-ns-amber-text">
              <span className="h-px grow bg-ns-amber-line" />
              CROWN ZONE ENDS
              <span className="h-px grow bg-ns-amber-line" />
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}

export function LevelCard({ player, routes = PREVIEW_ROUTES }: { player: Player; routes?: KitRoutes }) {
  return (
    <Card className="gap-2.5">
      <div className="flex items-center gap-3">
        <LevelRing size={56} level={player.level} pct={levelPct(player)} outfit={player.equippedOutfit} />
        <div className="flex grow flex-col gap-1">
          <div className="flex items-center gap-2">
            <b className="text-[17px]">Level {player.level}</b>
            <span className="inline-flex h-6 items-center rounded-full bg-ns-amber-soft px-2.5 text-xs font-semibold text-ns-amber-text">
              {player.rankTitle}
            </span>
          </div>
          <p className="m-0 text-[13px] leading-[18px] text-ns-muted">Level {player.level + 1} unlocks headphones for your hornbill.</p>
        </div>
      </div>
      <XpBar level={player.level} current={player.xpIntoLevel} needed={player.xpForLevel} showLabel={false} />
      <div className="flex justify-between">
        <span className="text-[13px] text-ns-muted tabular-nums">
          {player.xpIntoLevel} / {player.xpForLevel} XP
        </span>
        <Link href={routes.profile} className="text-[13px] font-bold text-ns-amber-text">
          See my hornbill
        </Link>
      </div>
    </Card>
  );
}
