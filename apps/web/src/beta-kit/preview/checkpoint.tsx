import { M } from "../components/ui";
import { preview } from "../routes";
import { samplePlayer, sampleUnit } from "../sample-data";
import {
  CheckpointActiveScreen,
  CheckpointIntroScreen,
  CheckpointMarkingScreen,
  CheckpointResultScreen,
  CheckpointReviewScreen,
  RecheckActiveScreen,
  RecheckIntroScreen,
  RecheckResultScreen,
  type CheckpointAnswerTile,
  type CheckpointInfo,
  type OutcomeResult,
  type RecheckInfo,
} from "../screens/checkpoint";
import type { PreviewEntry } from "./registry";

const GROUP = "Checkpoint and recheck";

/* Sample data: Dimas has all 7 N1 lessons at proficient and opens the checkpoint. */

const checkpoint: CheckpointInfo = {
  unitCode: sampleUnit.code,
  lessonCount: sampleUnit.lessons.length,
  questionCount: sampleUnit.checkpoint.questionCount,
  minutes: sampleUnit.checkpoint.minutes,
  passMark: sampleUnit.checkpoint.passMark,
  rewardXp: sampleUnit.checkpoint.rewardXp,
  xpPerRight: 10,
  badge: { name: sampleUnit.checkpoint.rewardBadge, icon: "trophy", tier: "gold", holders: { count: 4, of: 18 } },
};

const answerTiles: CheckpointAnswerTile[] = Array.from({ length: checkpoint.questionCount }, (_, i) => ({
  position: i + 1,
  answered: i + 1 !== 6,
  href: preview("checkpoint-active"),
}));

const outcomeTitles = sampleUnit.lessons.map((lesson) => ({ code: `1.${lesson.position}`, title: lesson.title }));

const checkpointOutcomes: OutcomeResult[] = outcomeTitles.map((row) => ({
  ...row,
  state: row.code === "1.5" ? "needs_review" : "mastered",
}));

const recheckUnitLessons: OutcomeResult[] = outcomeTitles.map((row, i) => ({
  ...row,
  state: i < 4 ? "mastered" : "proficient",
}));

const recheck: RecheckInfo = {
  lessons: [
    { position: 3, title: "Number sets and operations" },
    { position: 4, title: "Calculator calculations" },
  ],
  questionCount: 5,
  minutes: 8,
  passMark: 4,
  proficientSince: "2 weeks ago",
  rewardXp: 50,
  starsOnPass: 3,
};

export const checkpointEntries: PreviewEntry[] = [
  {
    key: "checkpoint-intro",
    title: "Checkpoint · before you start",
    group: GROUP,
    canvas: ["CheckpointIntro.m", "CheckpointIntro.d"],
    render: () => (
      <CheckpointIntroScreen
        player={samplePlayer}
        checkpoint={checkpoint}
        startHref={preview("checkpoint-active")}
        backHref={preview("unit")}
      />
    ),
  },
  {
    key: "checkpoint-active",
    title: "Checkpoint · answering",
    group: GROUP,
    canvas: ["CheckpointActive.m"],
    render: () => (
      <CheckpointActiveScreen
        player={samplePlayer}
        unitCode={checkpoint.unitCode}
        position={3}
        questionCount={checkpoint.questionCount}
        question={{
          outcome: "1.7",
          marks: 1,
          stem: (
            <>
              Round <M>0.045 67</M> to 2 significant figures.
            </>
          ),
        }}
        answer="0.046"
        answerHint="Write the number only."
        xpPerRight={checkpoint.xpPerRight}
        saveAndLeaveHref={preview("checkpoint-resume")}
        previousHref={preview("checkpoint-active")}
        nextHref={preview("checkpoint-review")}
      />
    ),
  },
  {
    key: "checkpoint-review",
    title: "Checkpoint · check before you submit",
    group: GROUP,
    canvas: ["CheckpointReview.m"],
    render: () => (
      <CheckpointReviewScreen
        player={samplePlayer}
        unitCode={checkpoint.unitCode}
        answers={answerTiles}
        xpPerRight={checkpoint.xpPerRight}
        state="reviewing"
        confirmHref={preview("checkpoint-submit")}
        submitHref={preview("checkpoint-marking")}
        back={{ label: "Back to question 8", href: preview("checkpoint-active") }}
      />
    ),
  },
  {
    key: "checkpoint-submit",
    title: "Checkpoint · submit with a blank",
    group: GROUP,
    canvas: ["CheckpointSubmit.m"],
    render: () => (
      <CheckpointReviewScreen
        player={samplePlayer}
        unitCode={checkpoint.unitCode}
        answers={answerTiles}
        xpPerRight={checkpoint.xpPerRight}
        state="confirm"
        confirmHref={preview("checkpoint-submit")}
        submitHref={preview("checkpoint-marking")}
        back={{ label: "Back to question 8", href: preview("checkpoint-active") }}
      />
    ),
  },
  {
    key: "checkpoint-marking",
    title: "Checkpoint · being checked",
    group: GROUP,
    canvas: ["CheckpointMarking.m"],
    render: () => (
      <CheckpointMarkingScreen
        player={samplePlayer}
        unitCode={checkpoint.unitCode}
        checked={5}
        total={checkpoint.questionCount}
        answersSaved={checkpoint.questionCount}
        submittedAt="10:42"
        dashboardHref={preview("dashboard")}
      />
    ),
  },
  {
    key: "checkpoint-result",
    title: "Checkpoint · passed",
    group: GROUP,
    canvas: ["CheckpointResult.m", "CheckpointResult.d"],
    render: () => (
      <CheckpointResultScreen
        player={samplePlayer}
        unitCode={checkpoint.unitCode}
        right={7}
        total={checkpoint.questionCount}
        passMark={checkpoint.passMark}
        xpLines={[
          { label: "Unit mastered", xp: checkpoint.rewardXp },
          { label: "7 right answers", xp: 7 * checkpoint.xpPerRight },
        ]}
        badge={{ name: checkpoint.badge.name, icon: checkpoint.badge.icon, tier: checkpoint.badge.tier }}
        newLevel={samplePlayer.level + 1}
        outcomes={checkpointOutcomes}
        review={{
          title: "Review: number lines and ordering.",
          body: (
            <>
              You placed <M>−2.5</M> to the right of <M>−2</M>. Lesson 5 has a 3-minute refresher, and the question comes back for
              double XP.
            </>
          ),
          lessonLabel: "Lesson 5",
          href: preview("lesson"),
        }}
        claimHref={preview("unit-mastered")}
        answersHref={preview("checkpoint-review")}
        backHref={preview("unit")}
      />
    ),
  },
  {
    key: "recheck-intro",
    title: "Recheck · before you start",
    group: GROUP,
    canvas: ["QuizIntro.m"],
    render: () => (
      <RecheckIntroScreen
        player={samplePlayer}
        recheck={recheck}
        startHref={preview("recheck-active")}
        backHref={preview("unit-recheck")}
      />
    ),
  },
  {
    key: "recheck-active",
    title: "Recheck · answered, right",
    group: GROUP,
    canvas: ["QuizActive.m"],
    render: () => (
      <RecheckActiveScreen
        player={samplePlayer}
        position={2}
        questionCount={recheck.questionCount}
        question={{
          lessonPosition: 3,
          outcome: "1.3",
          marks: 1,
          stem: (
            <>
              Work out <M>−8 + (−3) × 4</M>.
            </>
          ),
        }}
        state="right"
        answer="−20"
        explanation={
          <>
            Multiply first: (−3) × 4 = −12. Then −8 + (−12) = −20.
          </>
        }
        xp={10}
        combo={2}
        closeHref={preview("unit-recheck")}
        actionHref={preview("recheck-result")}
      />
    ),
  },
  {
    key: "recheck-result",
    title: "Recheck · passed",
    group: GROUP,
    canvas: ["QuizResult.m", "QuizResult.d"],
    render: () => (
      <RecheckResultScreen
        player={samplePlayer}
        lessons={recheck.lessons}
        right={4}
        total={recheck.questionCount}
        stars={3}
        xpLines={[
          { label: "Recheck passed", xp: recheck.rewardXp },
          { label: "4 right answers", xp: 40 },
        ]}
        questions={[1, 2, 3, 4, 5].map((position) => ({ position, right: position !== 4, xp: position !== 4 ? 10 : 0 }))}
        unitCode={checkpoint.unitCode}
        unitLessons={recheckUnitLessons}
        unitHref={preview("unit")}
        answersHref={preview("recheck-active")}
        backHref={preview("unit")}
      />
    ),
  },
];
