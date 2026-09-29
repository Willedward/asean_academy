import { preview } from "../routes";
import { sampleBadges, sampleLeague, samplePlayer, sampleReviewNow, sampleUnit, sampleWardrobe } from "../sample-data";
import { BadgesScreen, LeagueScreen, ProfileScreen, ProgressScreen, SettingsScreen, type SettingsProps } from "../screens/me";
import type { Badge, XpLine } from "../types";
import type { PreviewEntry } from "./registry";

/* Extra sample data for Progress, league and me --------------------- */

const climbRules: XpLine[] = [
  { label: "Right first try", xp: 10 },
  { label: "Right after a hint", xp: 6 },
  { label: "Clear a Try again question", xp: 20 },
  { label: "Finish all 3 daily quests", xp: 30 },
];

const firstReview = sampleReviewNow[0];

const settingsBase: Omit<SettingsProps, "deleteDialog"> = {
  player: samplePlayer,
  profile: { displayName: "Dimas", email: "dimas@example.com" },
  gameSettings: { sounds: true, celebrations: true, showInLeague: true, streakReminder: true, reminderTime: "19:30" },
  course: { title: "Singapore Secondary 1 G3 Mathematics", intake: "Sec 3 entry" },
  deleteHref: preview("settings-delete"),
};

const earnedBadges = sampleBadges.filter((badge) => badge.earned).length;
const twoWeeks = sampleBadges.find((badge) => badge.id === "two-weeks") as Badge;

export const meEntries: PreviewEntry[] = [
  {
    key: "progress",
    title: "Progress",
    group: "Progress, league and me",
    canvas: ["Progress.m", "Progress.d"],
    render: () => (
      <ProgressScreen
        player={samplePlayer}
        courseTitle="Singapore Secondary 1 G3 Mathematics"
        league={sampleLeague}
        unit={sampleUnit}
        badges={sampleBadges}
        stats={{
          lessonsProficient: 1,
          lessonCount: 7,
          firstTryPct: 62,
          firstTryRight: 5,
          answered: 8,
          eventualPct: 88,
          questionsDone: 9,
          solutionsShown: 1,
        }}
        retry={firstReview ? { ...firstReview, dueNote: "Solution shown 2 days ago", href: preview("review") } : null}
        outcomes={sampleUnit.lessons.map((lesson) => ({ code: `1.${lesson.position}`, title: lesson.title, state: lesson.state }))}
        recent={[
          { id: "r1", title: "Lesson 2 · Question 2", when: "Today", result: { label: "Right first try", tone: "success" }, xp: 10 },
          { id: "r2", title: "Lesson 2 · Question 1", when: "Today", result: { label: "Right after 1 hint", tone: "brand" }, xp: 6 },
          { id: "r3", title: "Lesson 1 practice", when: "Tue", result: { label: "Proficient", tone: "success" }, xp: 10 },
          { id: "r4", title: "Lesson 1 · Question 2", when: "Tue", result: { label: "Solution shown", tone: "neutral" }, xp: 0 },
        ]}
      />
    ),
  },
  {
    key: "settings",
    title: "Settings",
    group: "Progress, league and me",
    canvas: ["Settings.m", "Settings.d"],
    render: () => <SettingsScreen {...settingsBase} />,
  },
  {
    key: "settings-delete",
    title: "Settings · delete account",
    group: "Progress, league and me",
    canvas: ["SettingsDelete.m"],
    render: () => <SettingsScreen {...settingsBase} deleteDialog={{ badgesEarned: earnedBadges, cancelHref: preview("settings"), typed: "DELETE" }} />,
  },
  {
    key: "me",
    title: "Me · hornbill and wardrobe",
    group: "Progress, league and me",
    canvas: ["Profile.m", "Profile.d"],
    render: () => (
      <ProfileScreen player={samplePlayer} wardrobe={sampleWardrobe} badges={sampleBadges} nextUnlockLabel="Headphones unlock in 80 XP" />
    ),
  },
  {
    key: "league",
    title: "League",
    group: "Progress, league and me",
    canvas: ["League.m", "League.d"],
    render: () => (
      <LeagueScreen
        player={samplePlayer}
        league={{ ...sampleLeague, endsIn: "2 days 5 hours" }}
        endsInShort="2d 5h"
        climbRules={climbRules}
        practiseHref={preview("practice-answer")}
      />
    ),
  },
  {
    key: "badges",
    title: "Badges",
    group: "Progress, league and me",
    canvas: ["Badges.m"],
    render: () => <BadgesScreen player={samplePlayer} badges={sampleBadges} almost={{ badge: twoWeeks, hint: "2 more days of practice" }} />,
  },
];
