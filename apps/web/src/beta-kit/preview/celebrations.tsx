import { Card, M } from "../components/ui";
import { preview } from "../routes";
import { sampleBadges } from "../sample-data";
import { BadgeUnlockedScreen, LevelUpScreen, StreakMilestoneScreen, UnitMasteredScreen } from "../screens/celebrations";
import type { Badge } from "../types";
import type { PreviewEntry } from "./registry";

const GROUP = "Celebrations";

const comebackKid: Badge = sampleBadges.find((badge) => badge.id === "comeback-kid") ?? {
  id: "comeback-kid",
  name: "Comeback kid",
  description: "Clear a question you gave up on",
  icon: "bolt",
  tier: "silver",
  earned: true,
};

export const celebrationEntries: PreviewEntry[] = [
  {
    key: "level-up",
    title: "Level up",
    group: GROUP,
    canvas: ["LevelUp.m"],
    render: () => (
      <LevelUpScreen
        level={8}
        rankTitle="Test-taker"
        xpTotal={1285}
        unlocked={{ outfit: "headphones", name: "Headphones" }}
        xpIntoLevel={5}
        xpForLevel={180}
        nextUnlock={{ level: 10, itemName: "Glasses", rankTitle: "Shortlisted" }}
        primary={{ label: "Equip headphones", href: preview("me") }}
        secondary={{ label: "Share with my parent", href: preview("progress") }}
      />
    ),
  },
  {
    key: "streak-milestone",
    title: "7-day streak",
    group: GROUP,
    canvas: ["StreakMilestone.m"],
    render: () => (
      <StreakMilestoneScreen
        days={7}
        week={{ days: ["done", "done", "done", "done", "done", "done", "done"], todayIndex: 6 }}
        badge={{ name: "On fire", icon: "flame", tier: "gold" }}
        bonus="+ 1 streak freeze for a busy day"
        nextMilestone={14}
        continueHref={preview("streak")}
      />
    ),
  },
  {
    key: "unit-mastered",
    title: "Unit mastered",
    group: GROUP,
    canvas: ["UnitMastered.m"],
    render: () => (
      <UnitMasteredScreen
        unitCode="N1"
        unitTitle="Numbers and their operations"
        checkpoint={{ correct: 7, total: 8 }}
        xpEarned={100}
        lessonCount={7}
        badge={{ name: "Number master", icon: "trophy", tier: "gold", rarity: "Only 4 of 18 beta students have this" }}
        primary={{ label: "Continue", href: preview("level-up") }}
        secondary={{ label: "Share with my parent", href: preview("progress") }}
      />
    ),
  },
  {
    key: "badge-unlocked",
    title: "New badge",
    group: GROUP,
    canvas: ["BadgeUnlocked.m"],
    render: () => (
      <BadgeUnlockedScreen
        badge={comebackKid}
        reason="You cleared a question you gave up on 4 days ago. That is exactly how learning works."
        xp={25}
        continueHref={preview("review")}
        background={
          <Card className="text-[17px] leading-[26px]">
            <p className="m-0">
              Find the smallest positive integer <M>k</M> such that <M>360k</M> is a perfect square.
            </p>
          </Card>
        }
      />
    ),
  },
];
