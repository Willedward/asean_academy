/**
 * View models for the NextScholar beta kit.
 *
 * Every screen in src/beta-kit/screens takes plain data shaped like these
 * types. Screens never fetch. The page (server component) loads data from the
 * learning API, maps it with src/beta-kit/adapters.ts, and passes it in.
 *
 * Types marked NEW have no backend yet. HANDOFF.md lists what each needs.
 */
import type { components } from "@/lib/api/schema";

type Schemas = components["schemas"];

export type Href = string;

/* ------------------------------------------------------------------ */
/* Mascot                                                              */
/* ------------------------------------------------------------------ */

export type Mood = "normal" | "happy" | "sleepy" | "think" | "wow" | "kind";
export type Pose = "perch" | "cheer" | "point";
export type Outfit = "scarf" | "cap" | "headphones" | "glasses" | "crown";

/* ------------------------------------------------------------------ */
/* Player and rewards (NEW: gamification service)                      */
/* ------------------------------------------------------------------ */

export type RankTitle = "Applicant" | "Test-taker" | "Shortlisted" | "Interviewee" | "Scholar";

/** NEW. One row per learner. */
export interface Player {
  displayName: string;
  initials: string;
  intake: string;
  level: number;
  rankTitle: RankTitle;
  xpTotal: number;
  xpThisWeek: number;
  /** XP earned inside the current level. */
  xpIntoLevel: number;
  /** XP needed to finish the current level. */
  xpForLevel: number;
  streakDays: number;
  bestStreakDays: number;
  /** Earned, never sold. Max 2. */
  streakFreezes: number;
  /** Null when the learner hides themselves from the league. */
  leagueRank: number | null;
  equippedOutfit: Outfit | null;
}

export type QuestIcon = "check" | "rotate" | "book" | "target" | "file";

/** NEW. Three quests a day plus an all-three bonus. */
export interface Quest {
  id: string;
  title: string;
  icon: QuestIcon;
  progress: number;
  target: number;
  xp: number;
}

export interface QuestBoard {
  quests: Quest[];
  bonusXp: number;
  resetsIn: string;
}

/** NEW. Monday first. */
export type StreakDay = "done" | "freeze" | "today" | "empty";

export interface StreakWeek {
  days: StreakDay[];
  todayIndex: number;
}

export interface StreakMilestone {
  days: number;
  reward: string;
  reached: boolean;
}

/** NEW. Weekly league. */
export interface LeagueEntry {
  rank: number;
  name: string;
  initials: string;
  xp: number;
  isYou?: boolean;
  /** e.g. "+60 today" */
  note?: string;
}

export interface League {
  name: string;
  weekLabel: string;
  endsIn: string;
  entries: LeagueEntry[];
  /** How many at the top win the golden crown. */
  crownPlaces: number;
  chase?: { name: string; xpBehind: number };
}

export type BadgeIcon = "star" | "bolt" | "flame" | "target" | "snow" | "trophy";
export type Tier = "gold" | "silver" | "bronze";

/** NEW. */
export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: BadgeIcon;
  tier: Tier;
  earned: boolean;
  progress?: { current: number; target: number };
}

/** NEW. Wardrobe items unlocked by level or achievements. */
export interface OutfitItem {
  outfit: Outfit | "flame-scarf";
  name: string;
  unlocked: boolean;
  equipped: boolean;
  requirement: string;
}

/** One line of an XP tally, for example "2 right first try: +20". */
export interface XpLine {
  label: string;
  xp: number;
}

/* ------------------------------------------------------------------ */
/* Course, units, lessons                                              */
/* ------------------------------------------------------------------ */

/** Existing API progress state (LessonProgressResponse.state). */
export type ApiLessonState = Schemas["LessonProgressResponse"]["state"];

/**
 * What the lesson row shows. Map from the API with toLessonUiState() in
 * adapters.ts.
 */
export type LessonUiState = "locked" | "ready" | "practising" | "proficient" | "mastered" | "in_review";

export type Stars = 0 | 1 | 2 | 3;

export interface LessonSummary {
  key: string;
  position: number;
  title: string;
  minutes: number;
  questionCount: number;
  state: LessonUiState;
  /** NEW. 1 = any right answer, 2 = proficient, 3 = mastered. */
  stars: Stars;
  /** NEW. XP still available in this lesson. */
  xpAvailable?: number;
  href: Href;
  lockedReason?: string;
}

export interface UnitSummary {
  key: string;
  code: string;
  title: string;
  description: string;
  lessons: LessonSummary[];
  lessonsProficient: number;
  /** NEW */
  starsEarned: number;
  /** NEW */
  starsTotal: number;
  /** NEW */
  xpEarned: number;
  /** NEW */
  xpTotal: number;
  checkpoint: {
    questionCount: number;
    minutes: number;
    passMark: number;
    open: boolean;
    href: Href;
    rewardXp: number;
    rewardBadge: string;
  };
  href: Href;
}

/** Existing API next action (NextActionResponse), plus reward info. */
export interface ContinueCard {
  title: string;
  lessonLabel: string;
  description: string;
  progressLabel: string;
  progressPct: number;
  primary: { label: string; href: Href };
  secondary?: { label: string; href: Href };
  /** NEW */
  xp: number;
  /** NEW */
  stars: Stars;
}

/** NEW. Spaced repetition "Try again" list. */
export interface ReviewItem {
  questionKey: string;
  title: string;
  reason: string;
  /** Double XP on reviews. */
  xp: number;
  href: Href;
  tag?: { label: string; tone: Tone };
}

export interface LaterReviewItem {
  questionKey: string;
  title: string;
  reason: string;
  dueLabel: string;
}

/* ------------------------------------------------------------------ */
/* Shared UI enums                                                     */
/* ------------------------------------------------------------------ */

export type Tone = "neutral" | "brand" | "amber" | "success" | "danger";

export type NavKey = "learn" | "course" | "league" | "progress" | "me";
