/**
 * Sample data for the /beta-kit preview: one beta student, Dimas, midway
 * through unit N1. Replace with real data from the learning API. Keys and
 * titles match src/fixtures/course-map.json.
 */
import { preview } from "./routes";
import type {
  Badge,
  ContinueCard,
  LaterReviewItem,
  League,
  LessonSummary,
  OutfitItem,
  Player,
  QuestBoard,
  ReviewItem,
  StreakMilestone,
  StreakWeek,
  UnitSummary,
} from "./types";

export const samplePlayer: Player = {
  displayName: "Dimas Saputra",
  initials: "DS",
  intake: "Sec 3 entry",
  level: 7,
  rankTitle: "Test-taker",
  xpTotal: 1240,
  xpThisWeek: 350,
  xpIntoLevel: 80,
  xpForLevel: 160,
  streakDays: 12,
  bestStreakDays: 12,
  streakFreezes: 1,
  leagueRank: 3,
  equippedOutfit: "scarf",
};

/** A brand new student straight after onboarding. */
export const newPlayer: Player = {
  ...samplePlayer,
  level: 1,
  rankTitle: "Applicant",
  xpTotal: 50,
  xpThisWeek: 50,
  xpIntoLevel: 50,
  xpForLevel: 160,
  streakDays: 0,
  bestStreakDays: 0,
  streakFreezes: 0,
  leagueRank: null,
  equippedOutfit: null,
};

export const sampleQuests: QuestBoard = {
  quests: [
    { id: "answer-5", title: "Answer 5 questions", icon: "check", progress: 4, target: 5, xp: 15 },
    { id: "clear-2", title: "Clear 2 Try again questions", icon: "rotate", progress: 2, target: 2, xp: 15 },
    { id: "section-1", title: "Finish a lesson section", icon: "book", progress: 1, target: 1, xp: 15 },
  ],
  bonusXp: 30,
  resetsIn: "6h 12m",
};

export const newQuests: QuestBoard = {
  quests: [
    { id: "section-1", title: "Finish a lesson section", icon: "book", progress: 0, target: 1, xp: 15 },
    { id: "answer-5", title: "Answer 5 questions", icon: "check", progress: 0, target: 5, xp: 15 },
    { id: "first-try-3", title: "Get 3 right first try", icon: "target", progress: 0, target: 3, xp: 15 },
  ],
  bonusXp: 30,
  resetsIn: "6h 12m",
};

export const sampleWeek: StreakWeek = { days: ["done", "done", "done", "freeze", "done", "today", "empty"], todayIndex: 5 };

export const sampleMilestones: StreakMilestone[] = [
  { days: 3, reward: "+20 XP", reached: true },
  { days: 7, reward: "On fire badge", reached: true },
  { days: 14, reward: "+100 XP", reached: false },
  { days: 30, reward: "Flame scarf", reached: false },
  { days: 60, reward: "Legend badge", reached: false },
];

export const sampleLeague: League = {
  name: "Beta League",
  weekLabel: "Week 3",
  endsIn: "2 days",
  crownPlaces: 3,
  chase: { name: "Kevin", xpBehind: 45 },
  entries: [
    { rank: 1, name: "Nadia P.", initials: "NP", xp: 420 },
    { rank: 2, name: "Kevin T.", initials: "KT", xp: 395 },
    { rank: 3, name: "Dimas S.", initials: "DS", xp: 350, isYou: true, note: "+60 today" },
    { rank: 4, name: "Putri A.", initials: "PA", xp: 310, note: "+40 today" },
    { rank: 5, name: "Rizky P.", initials: "RP", xp: 280 },
    { rank: 6, name: "Bella W.", initials: "BW", xp: 240 },
    { rank: 7, name: "Aisyah R.", initials: "AR", xp: 190 },
    { rank: 8, name: "Jonathan T.", initials: "JT", xp: 150 },
  ],
};

export const sampleBadges: Badge[] = [
  { id: "first-try-ace", name: "First-try ace", description: "Get 10 questions right first try", icon: "star", tier: "gold", earned: true },
  { id: "comeback-kid", name: "Comeback kid", description: "Clear a question you gave up on", icon: "bolt", tier: "silver", earned: true },
  { id: "on-fire", name: "On fire", description: "Reach a 7-day streak", icon: "flame", tier: "gold", earned: true },
  { id: "prime-time", name: "Prime time", description: "Get Lesson 1 to proficient", icon: "target", tier: "bronze", earned: true },
  { id: "review-master", name: "Review master", description: "Clear 20 Try again questions", icon: "snow", tier: "silver", earned: false, progress: { current: 12, target: 20 } },
  { id: "quest-hunter", name: "Quest hunter", description: "Finish 30 daily quests", icon: "star", tier: "bronze", earned: false, progress: { current: 19, target: 30 } },
  { id: "number-master", name: "Number master", description: "Master unit N1", icon: "trophy", tier: "gold", earned: false, progress: { current: 2, target: 7 } },
  { id: "two-weeks", name: "Two weeks strong", description: "Reach a 14-day streak", icon: "flame", tier: "gold", earned: false, progress: { current: 12, target: 14 } },
  { id: "essay-starter", name: "Essay starter", description: "Submit your first essay", icon: "star", tier: "bronze", earned: false, progress: { current: 0, target: 1 } },
];

export const sampleWardrobe: OutfitItem[] = [
  { outfit: "scarf", name: "Batik scarf", unlocked: true, equipped: true, requirement: "Level 3" },
  { outfit: "cap", name: "Scholar cap", unlocked: true, equipped: false, requirement: "Level 5" },
  { outfit: "headphones", name: "Headphones", unlocked: false, equipped: false, requirement: "Level 8" },
  { outfit: "glasses", name: "Glasses", unlocked: false, equipped: false, requirement: "Level 10" },
  { outfit: "crown", name: "Golden crown", unlocked: false, equipped: false, requirement: "Top 3 weekly" },
  { outfit: "flame-scarf", name: "Flame scarf", unlocked: false, equipped: false, requirement: "30-day streak" },
];

const lessonHref = preview("lesson");

export const sampleLessons: LessonSummary[] = [
  { key: "n1-lesson-01", position: 1, title: "Primes and prime factorisation", minutes: 25, questionCount: 3, state: "proficient", stars: 2, href: lessonHref },
  { key: "n1-lesson-02", position: 2, title: "HCF, LCM, squares, cubes and roots", minutes: 35, questionCount: 4, state: "practising", stars: 1, href: lessonHref },
  { key: "n1-lesson-03", position: 3, title: "Number sets and operations", minutes: 35, questionCount: 4, state: "ready", stars: 0, xpAvailable: 60, href: preview("lesson-in-review") },
  { key: "n1-lesson-04", position: 4, title: "Calculator calculations", minutes: 20, questionCount: 2, state: "locked", stars: 0, href: lessonHref, lockedReason: "Finish Lesson 3 to open" },
  { key: "n1-lesson-05", position: 5, title: "Number lines and ordering", minutes: 25, questionCount: 2, state: "locked", stars: 0, href: lessonHref, lockedReason: "Finish Lesson 3 to open" },
  { key: "n1-lesson-06", position: 6, title: "Inequalities", minutes: 20, questionCount: 1, state: "locked", stars: 0, href: lessonHref, lockedReason: "Finish Lesson 3 to open" },
  { key: "n1-lesson-07", position: 7, title: "Approximation and estimation", minutes: 30, questionCount: 3, state: "locked", stars: 0, href: lessonHref, lockedReason: "Finish Lesson 3 to open" },
];

export const sampleUnit: UnitSummary = {
  key: "g3-sec1-n1",
  code: "N1",
  title: "Numbers and their operations",
  description: "Primes, HCF and LCM, number sets, calculators, number lines, inequalities and estimation.",
  lessons: sampleLessons,
  lessonsProficient: 1,
  starsEarned: 3,
  starsTotal: 21,
  xpEarned: 145,
  xpTotal: 700,
  checkpoint: {
    questionCount: 8,
    minutes: 25,
    passMark: 6,
    open: false,
    href: preview("checkpoint-intro"),
    rewardXp: 100,
    rewardBadge: "Number master",
  },
  href: preview("unit"),
};

export const sampleContinue: ContinueCard = {
  title: "HCF, LCM, squares, cubes and roots",
  lessonLabel: "Lesson 2 of 7 · N1",
  description: "Halfway there. 2 more questions to win your first star.",
  progressLabel: "2 of 4 questions",
  progressPct: 50,
  primary: { label: "Resume practice", href: preview("practice-answer") },
  secondary: { label: "Review the lesson", href: lessonHref },
  xp: 40,
  stars: 0,
};

export const sampleReviewNow: ReviewItem[] = [
  { questionKey: "n1-l1-02", title: "Lesson 1 · Question 2", reason: "You saw the solution on Tue", xp: 20, href: preview("practice-answer"), tag: { label: "Solution shown", tone: "neutral" } },
  { questionKey: "n1-l2-03", title: "Lesson 2 · Question 3", reason: "Two wrong tries, then Give up, on Wed", xp: 20, href: preview("practice-answer"), tag: { label: "Gave up", tone: "neutral" } },
  { questionKey: "n1-l2-01", title: "Lesson 2 · Question 1", reason: "Right after a hint, 5 days ago", xp: 20, href: preview("practice-answer"), tag: { label: "Keep it fresh", tone: "brand" } },
];

export const sampleReviewLater: LaterReviewItem[] = [
  { questionKey: "n1-l1-03", title: "Lesson 1 · Question 3", reason: "Right after 2 hints", dueLabel: "Fri 3 Oct" },
  { questionKey: "cp-n1-05", title: "Checkpoint · Question 5", reason: "Missed in the checkpoint", dueLabel: "Mon 6 Oct" },
];
