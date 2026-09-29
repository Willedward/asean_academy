import type { ReactNode } from "react";

import { Hornbill } from "../components/hornbill";
import {
  BonusChest,
  ComboChip,
  DoubleXpPill,
  Feedback,
  LeagueChip,
  LevelRing,
  MascotSays,
  Medal,
  QuestRow,
  ReviewNote,
  Stars,
  StreakChip,
  WeekDots,
  XpBar,
  XpChip,
  XpPill,
  XpTag,
  levelPct,
} from "../components/rewards";
import { Card, H1, H2, H3, Muted } from "../components/ui";
import { BareShell, Logo } from "../shell/app-shell";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import type { Mood, Outfit, Player, Pose, QuestBoard, StreakWeek } from "../types";

const MOODS: { name: string; use: string; mood: Mood; pose: Pose }[] = [
  { name: "Default", use: "Lessons, empty states", mood: "normal", pose: "perch" },
  { name: "Cheering", use: "Right answers, level up", mood: "happy", pose: "cheer" },
  { name: "Thinking", use: "Hints, Try again list", mood: "think", pose: "perch" },
  { name: "Kind", use: "Wrong answers", mood: "kind", pose: "point" },
  { name: "Sleepy", use: "Streak at risk", mood: "sleepy", pose: "perch" },
  { name: "Amazed", use: "Badges, milestones", mood: "wow", pose: "cheer" },
];

const OUTFITS: { name: string; unlock: string; outfit: Outfit }[] = [
  { name: "Batik scarf", unlock: "Level 3", outfit: "scarf" },
  { name: "Scholar cap", unlock: "Level 5", outfit: "cap" },
  { name: "Headphones", unlock: "Level 8", outfit: "headphones" },
  { name: "Glasses", unlock: "Level 10", outfit: "glasses" },
  { name: "Golden crown", unlock: "Top 3 in the weekly league", outfit: "crown" },
];

function Tile({ name, sub, children }: { name: string; sub: string; children: ReactNode }) {
  return (
    <figure className="m-0 flex min-w-0 flex-col gap-1.5">
      <div className="flex h-[150px] items-center justify-center rounded-[20px] border border-ns-line bg-ns-raised lg:h-[190px]">
        {children}
      </div>
      <figcaption className="flex flex-col gap-0.5">
        <span className="text-base font-extrabold">{name}</span>
        <span className="text-[13px] text-ns-muted">{sub}</span>
      </figcaption>
    </figure>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-4">
      <H2 className="text-2xl leading-8">{title}</H2>
      {children}
    </section>
  );
}

function Spec({ title, children, note }: { title: string; children: ReactNode; note?: string }) {
  return (
    <Card className="gap-3.5">
      <H3>{title}</H3>
      {children}
      {note ? <Muted className="text-[13px] leading-[18px]">{note}</Muted> : null}
    </Card>
  );
}

export interface KitSheetProps {
  /** Sample learner shown in the chips, level ring and XP bar. */
  player: Player;
  quests: QuestBoard;
  week: StreakWeek;
  routes?: KitRoutes;
}

/** Canvas: GameKit. Reference page for the hornbill and every reward piece. */
export function KitSheetScreen({ player, quests, week, routes = PREVIEW_ROUTES }: KitSheetProps) {
  const firstQuest = quests.quests[0];
  return (
    <BareShell>
      <main className="flex flex-col gap-9 px-4 pt-10 pb-14 lg:px-[72px] lg:pt-16 lg:pb-[72px]">
        <header className="flex flex-col gap-3.5">
          <Logo height={26} />
          <H1 className="lg:text-[40px] lg:leading-[48px]">The hornbill and the reward kit</H1>
          <p className="m-0 max-w-[820px] text-[17px] leading-[26px] text-ns-muted">
            The hornbill appears across the app with six moods. Outfits unlock as students level up. Below are the reusable reward
            pieces used on every gamified screen.
          </p>
        </header>

        <Section title="Moods">
          <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-6">
            {MOODS.map((item) => (
              <Tile key={item.name} name={item.name} sub={item.use}>
                <Hornbill
                  size={160}
                  mood={item.mood}
                  pose={item.pose}
                  label={`${item.name} hornbill`}
                  className="size-[120px] lg:size-40"
                />
              </Tile>
            ))}
          </div>
        </Section>

        <Section title="Outfits students unlock">
          <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-5">
            {OUTFITS.map((item) => (
              <Tile key={item.name} name={item.name} sub={item.unlock}>
                <Hornbill
                  size={160}
                  mood={item.outfit === "crown" ? "happy" : "normal"}
                  outfit={item.outfit}
                  label={`Hornbill wearing the ${item.name.toLowerCase()}`}
                  className="size-[120px] lg:size-40"
                />
              </Tile>
            ))}
          </div>
        </Section>

        <Section title="Avatar with level ring, and app icon">
          <div className="flex flex-wrap items-end gap-7">
            {[72, 48, 36].map((size) => (
              <figure key={size} className="m-0 flex flex-col items-center gap-2">
                <LevelRing size={size} level={player.level} pct={levelPct(player)} outfit={player.equippedOutfit} />
                <figcaption className="text-xs text-ns-muted">{size}px</figcaption>
              </figure>
            ))}
            <span className="inline-flex size-[88px] items-center justify-center rounded-[22px] bg-ns-ink">
              <Hornbill size={76} crop="head" label="App icon" />
            </span>
          </div>
        </Section>

        <Section title="Reward pieces">
          <div className="grid items-start gap-6 md:grid-cols-2 lg:grid-cols-3">
            <Spec title="Top bar chips" note="Tap each to open the streak, quests or league.">
              <div className="flex flex-wrap gap-2">
                <StreakChip days={player.streakDays} href={routes.streak} />
                <XpChip xp={player.xpTotal} href={routes.quests} />
                <LeagueChip rank={player.leagueRank} href={routes.league} />
              </div>
            </Spec>
            <Spec title="Level bar">
              <XpBar level={player.level} current={player.xpIntoLevel} needed={player.xpForLevel} />
              <div>
                <ComboChip label="3 IN A ROW" />
              </div>
            </Spec>
            <Spec title="Daily quests">
              {firstQuest ? <QuestRow quest={firstQuest} /> : null}
              <BonusChest board={quests} />
            </Spec>
            <Spec title="Streak week">
              <WeekDots week={week} />
            </Spec>
            <Spec title="Badges">
              <div className="flex flex-wrap gap-3">
                <Medal icon="star" tier="gold" />
                <Medal icon="bolt" tier="silver" />
                <Medal icon="target" tier="bronze" />
                <Medal icon="star" tier="gold" locked />
              </div>
            </Spec>
            <Spec title="Mascot talking">
              <MascotSays size={64} mood="happy">
                Two more questions for your daily quest!
              </MascotSays>
            </Spec>
            <Spec title="XP amounts">
              <div className="flex flex-wrap items-center gap-2.5">
                <XpTag xp={10} />
                <XpPill xp={40} />
                <DoubleXpPill />
              </div>
            </Spec>
            <Spec title="Stars on lessons">
              <div className="flex flex-wrap gap-4">
                {[0, 1, 2, 3].map((count) => (
                  <Stars key={count} count={count} size={18} />
                ))}
              </div>
            </Spec>
          </div>
        </Section>

        <Section title="Answer feedback">
          <div className="grid items-start gap-6 md:grid-cols-2 lg:grid-cols-3">
            <Spec title="Right answer">
              <Feedback kind="right" xp={10}>
                Right on your first try.
              </Feedback>
            </Spec>
            <Spec title="Wrong answer">
              <Feedback kind="wrong">Part (b) is not yet.</Feedback>
            </Spec>
            <Spec title="Try again note">
              <ReviewNote />
            </Spec>
          </div>
        </Section>
      </main>
    </BareShell>
  );
}
