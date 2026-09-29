import { preview } from "../routes";
import {
  newPlayer,
  newQuests,
  sampleBadges,
  sampleContinue,
  sampleLeague,
  sampleLessons,
  sampleMilestones,
  samplePlayer,
  sampleQuests,
  sampleReviewLater,
  sampleReviewNow,
  sampleUnit,
  sampleWeek,
} from "../sample-data";
import { DashboardScreen } from "../screens/dashboard";
import {
  CourseMapScreen,
  DashboardNewScreen,
  DashboardReviewScreen,
  DashboardUnitDoneScreen,
  QuestsScreen,
  ReviewScreen,
  StreakScreen,
  UnitScreen,
  type StreakMonth,
} from "../screens/learn";
import type { Badge, StreakDay, UnitSummary, XpLine } from "../types";
import type { PreviewEntry } from "./registry";

/* Extra sample data for the Learn group ----------------------------- */

export const sampleXpRules: XpLine[] = [
  { label: "Right first try", xp: 10 },
  { label: "Right after a hint", xp: 6 },
  { label: "Finish a lesson section", xp: 10 },
  { label: "Clear a Try again question", xp: 20 },
  { label: "Finish all 3 daily quests", xp: 30 },
];

const reviewMaster = sampleBadges.find((badge) => badge.id === "review-master") as Badge;

const courseTitle = "Singapore Secondary 1 G3 Mathematics";

/** Unit N1 later on: every lesson proficient, two mastered, checkpoint open. */
const recheckUnit: UnitSummary = {
  ...sampleUnit,
  lessons: sampleLessons.map((lesson) => ({
    ...lesson,
    state: lesson.position <= 2 ? "mastered" : "proficient",
    stars: lesson.position <= 2 ? 3 : 2,
    xpAvailable: undefined,
    lockedReason: undefined,
    href: preview("lesson"),
  })),
  lessonsProficient: 7,
  checkpoint: { ...sampleUnit.checkpoint, open: true },
};

/** October: 7 days, a freeze on the 8th, 4 more days, today is the 13th. */
const october: StreakMonth = {
  name: "October",
  note: "Freeze used on the 8th",
  days: Array.from({ length: 30 }, (_, i): StreakDay => {
    const date = i + 1;
    if (date === 8) return "freeze";
    if (date < 13) return "done";
    if (date === 13) return "today";
    return "empty";
  }),
};

export const learnEntries: PreviewEntry[] = [
  {
    key: "dashboard",
    title: "Dashboard",
    group: "Learn",
    canvas: ["Dashboard.m", "Dashboard.d", "Dashboard.t"],
    render: () => (
      <DashboardScreen
        player={samplePlayer}
        greeting="Selamat pagi"
        continueCard={sampleContinue}
        quests={sampleQuests}
        week={sampleWeek}
        league={sampleLeague}
        unit={sampleUnit}
        reviewDue={{ count: 1, xp: 20, href: preview("review") }}
      />
    ),
  },
  {
    key: "dashboard-new",
    title: "Dashboard · new student",
    group: "Learn",
    canvas: ["DashboardNew.m"],
    render: () => (
      <DashboardNewScreen
        player={newPlayer}
        welcomeBonusXp={50}
        start={{
          lessonLabel: "Lesson 1 of 7 · 25 min",
          title: "Primes and prime factorisation",
          description: "Learn what makes a number prime, then break any number into its prime factors.",
          ctaLabel: "Start Lesson 1",
          href: preview("lesson"),
          xp: 60,
        }}
        quests={newQuests}
        xpRules={sampleXpRules}
        nextUnlock={{ level: 3, outfit: "scarf", description: "A batik scarf for your hornbill. About 2 lessons away." }}
      />
    ),
  },
  {
    key: "dashboard-review",
    title: "Dashboard · reviews waiting",
    group: "Learn",
    canvas: ["DashboardReview.m"],
    render: () => (
      <DashboardReviewScreen
        player={samplePlayer}
        greeting="Welcome back"
        review={{
          items: sampleReviewNow,
          minutes: 6,
          badge: reviewMaster,
          startHref: preview("review"),
          later: { label: "Later. Go to Lesson 2", href: preview("practice-answer") },
        }}
        continueCard={{ ...sampleContinue, secondary: undefined }}
        quests={sampleQuests}
        week={sampleWeek}
      />
    ),
  },
  {
    key: "dashboard-unit-done",
    title: "Dashboard · unit finished",
    group: "Learn",
    canvas: ["DashboardUnitDone.m"],
    render: () => (
      <DashboardUnitDoneScreen
        player={{ ...samplePlayer, level: 9, streakDays: 13, bestStreakDays: 13, xpTotal: 1535, leagueRank: 1, equippedOutfit: "cap" }}
        greeting="Well done"
        unit={{ code: "N1", title: "Numbers and their operations" }}
        results={{ starsEarned: 21, starsTotal: 21, bonusXp: 100, firstTryPct: 71 }}
        badge={{ name: "Number master", note: "Only 4 of 18 beta students have it" }}
        resultsHref={preview("checkpoint-result")}
        recheck={{
          xp: 50,
          description: "5 mixed questions every 2 weeks. About 8 minutes. Keeps your streak alive while N2 is checked.",
          href: preview("recheck-intro"),
        }}
        quests={sampleQuests}
        nextUnit={{ code: "N2" }}
      />
    ),
  },
  {
    key: "course-map",
    title: "Course map",
    group: "Learn",
    canvas: ["CourseMap.m", "CourseMap.d"],
    render: () => (
      <CourseMapScreen
        player={samplePlayer}
        course={{
          title: courseTitle,
          description: "A step-by-step path for the Sec 3 entry Mathematics test, starting with N1.",
        }}
        units={[sampleUnit]}
        badgeHolderCount={4}
        moreUnitsComing
      />
    ),
  },
  {
    key: "unit",
    title: "Unit",
    group: "Learn",
    canvas: ["Unit.m", "Unit.d"],
    render: () => (
      <UnitScreen
        player={samplePlayer}
        courseTitle={courseTitle}
        unit={sampleUnit}
        timeLabel="About 3.5 hours"
        nudge="Lesson 2 is 2 questions away from its first star!"
        legend="stars"
      />
    ),
  },
  {
    key: "unit-recheck",
    title: "Unit · recheck ready",
    group: "Learn",
    canvas: ["UnitRecheck.m"],
    render: () => (
      <UnitScreen
        player={samplePlayer}
        courseTitle={courseTitle}
        unit={recheckUnit}
        timeLabel="About 3.5 hours"
        recheck={{
          title: "Recheck ready: Lessons 3 and 4",
          description: "5 questions, no hints. Get 4 right to mark both lessons mastered.",
          xp: 50,
          starNote: "3rd star for both",
          href: preview("recheck-intro"),
        }}
        legend="labels"
      />
    ),
  },
  {
    key: "review",
    title: "Try again list",
    group: "Learn",
    canvas: ["Review.m", "Review.d"],
    render: () => (
      <ReviewScreen
        player={samplePlayer}
        now={sampleReviewNow}
        later={sampleReviewLater}
        clearedCount={4}
        tab="ready"
        tabHrefs={{ ready: preview("review"), later: preview("review"), cleared: preview("review") }}
        badge={reviewMaster}
        questNote="Clearing all 3 now also finishes today’s quest."
        startHref={preview("practice-answer")}
      />
    ),
  },
  {
    key: "quests",
    title: "Daily quests",
    group: "Learn",
    canvas: ["Quests.m"],
    render: () => (
      <QuestsScreen
        player={samplePlayer}
        quests={sampleQuests}
        weeklyGoal={{ daysDone: 4, target: 5 }}
        challenge={{
          label: "October challenge",
          title: "Finish 30 quests",
          reward: "Reward: the golden batik scarf, only this month.",
          progressLabel: "Quests finished",
          progress: 19,
          target: 30,
        }}
      />
    ),
  },
  {
    key: "streak",
    title: "Streak",
    group: "Learn",
    canvas: ["Streak.m"],
    render: () => <StreakScreen player={samplePlayer} month={october} milestones={sampleMilestones} maxFreezes={2} />,
  },
];
