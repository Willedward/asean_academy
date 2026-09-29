import type { ReactNode } from "react";

import { M, Sup } from "../components/ui";
import { preview } from "../routes";
import { samplePlayer, sampleQuests } from "../sample-data";
import {
  PracticeDoneScreen,
  PracticeKeyboardScreen,
  PracticeQuestionScreen,
  type PartStatus,
  type PracticeHint,
  type PracticePart,
  type PracticeQuestion,
  type PracticeQuestionProps,
  type PracticeSessionInfo,
  type PracticeSolution,
} from "../screens/practice";
import type { Quest } from "../types";
import type { PreviewEntry } from "./registry";

/* ------------------------------------------------------------------ */
/* Sample question: Lesson 1, question 2                               */
/* ------------------------------------------------------------------ */

const session: PracticeSessionInfo = {
  lessonPosition: 1,
  lessonTitle: "Primes and prime factorisation",
  lessonHref: preview("lesson"),
  stageLabel: "Guided practice",
  position: 2,
  total: 3,
  leaveHref: preview("lesson"),
};

const stem: ReactNode = (
  <>
    Express 360 as a product of its prime factors in index notation. Hence find
    the smallest positive integer{" "}
    <M>
      <i>k</i>
    </M>{" "}
    such that{" "}
    <M>
      360<i>k</i>
    </M>{" "}
    is a perfect square.
  </>
);

function parts(
  values: [string, string],
  status: [PartStatus, PartStatus],
): PracticePart[] {
  return [
    {
      position: 1,
      label: "a",
      prompt: "360 in index notation",
      marks: 2,
      placeholder: "e.g. 2^2 × 3",
      responseType: "algebraic_expression",
      help: (
        <>
          Type powers with ^. We read 2^3 as <Sup base="2" exp="3" />.
        </>
      ),
      value: values[0],
      status: status[0],
    },
    {
      position: 2,
      label: "b",
      prompt: "the value of k",
      marks: 1,
      placeholder: "A whole number",
      responseType: "numeric",
      help: "Numbers only.",
      value: values[1],
      status: status[1],
    },
  ];
}

const question = (
  values: [string, string],
  status: [PartStatus, PartStatus],
): PracticeQuestion => ({
  key: "n1-l1-02",
  difficulty: 2,
  outcome: "1.1",
  totalMarks: 3,
  stem,
  parts: parts(values, status),
});

const hint1: PracticeHint = {
  stage: 1,
  content: "Divide 360 by 2 as many times as you can. Then try 3, then 5.",
};

const answerQuest: Quest = sampleQuests.quests[0] ?? {
  id: "answer-5",
  title: "Answer 5 questions",
  icon: "check",
  progress: 4,
  target: 5,
  xp: 15,
};

const index360 = (
  <>
    <Sup base="2" exp="3" /> × <Sup base="3" exp="2" /> × 5
  </>
);

const solution: PracticeSolution = {
  answers: [
    { label: "a", value: index360 },
    {
      label: "b",
      value: (
        <>
          <i>k</i> = 10
        </>
      ),
    },
  ],
  steps: [
    // Long lines set `wide`: they scroll sideways in their own labelled box.
    {
      text: "Divide by 2 while you can.",
      math: "360 = 2 × 180 = 2 × 2 × 90 = 2 × 2 × 2 × 45",
      wide: true,
    },
    { text: "45 is odd. Divide by 3, twice.", math: "45 = 3 × 15 = 3 × 3 × 5" },
    { text: "Group the repeated factors.", math: <>360 = {index360}</> },
    {
      text: "For a perfect square every index must be even. 2 has index 3 and 5 has index 1, so each needs one more.",
      math: (
        <>
          <i>k</i> = 2 × 5 = 10
        </>
      ),
    },
    {
      text: "Check.",
      math: (
        <>
          360 × 10 = 3600 = <Sup base="60" exp="2" />
        </>
      ),
    },
  ],
};

const base: Omit<PracticeQuestionProps, "state" | "question"> = {
  player: samplePlayer,
  session,
  hints: [],
  hintsTotal: 2,
  wrongTries: 0,
  solutionAvailable: false,
  solutionAfterTries: 2,
  xp: { firstTry: 10, afterHelp: 6, review: 20 },
  review: { inDays: 2, badge: "Comeback kid" },
  lessonStars: 0,
  quest: answerQuest,
  links: {
    hint: preview("practice-wrong-1"),
    giveUp: preview("practice-give-up"),
    showSolution: preview("practice-solution"),
    keepTrying: preview("practice-wrong-2"),
    next: preview("practice-correct"),
  },
};

const afterTwoTries = {
  ...base,
  question: question(["2^3 × 3^2 × 5", "2"], ["correct", "wrong"]),
  hints: [hint1],
  wrongTries: 2,
  solutionAvailable: true,
};

/* ------------------------------------------------------------------ */
/* Entries                                                             */
/* ------------------------------------------------------------------ */

export const practiceEntries: PreviewEntry[] = [
  {
    key: "practice-answer",
    title: "Practice: answering",
    group: "Practice",
    canvas: ["PracticeAnswer.m", "PracticeAnswer.d"],
    render: () => (
      <PracticeQuestionScreen
        {...base}
        state="answering"
        question={question(["2^3 × 3^2 × 5", ""], ["none", "none"])}
        answerAction={preview("practice-wrong-1")}
      />
    ),
  },
  {
    key: "practice-wrong-1",
    title: "Practice: first wrong try, hint open",
    group: "Practice",
    canvas: ["PracticeWrong1.m", "Practice.t"],
    render: () => (
      <PracticeQuestionScreen
        {...base}
        state="wrong"
        question={question(["2^3 × 3^2 × 5", "5"], ["correct", "wrong"])}
        hints={[hint1]}
        wrongTries={1}
        feedback={{
          body: "Part (a) is right. Part (b) is not yet. Change it and check again.",
        }}
        answerAction={preview("practice-wrong-2")}
      />
    ),
  },
  {
    key: "practice-wrong-2",
    title: "Practice: second wrong try",
    group: "Practice",
    canvas: ["PracticeWrong2.m", "PracticeWrong2.d"],
    render: () => (
      <PracticeQuestionScreen
        {...afterTwoTries}
        state="wrong"
        feedback={{
          title: "Still not yet",
          body: "Part (b) is still not right. Keep trying, open Hint 2, or see the solution.",
          note: "Your streak and XP are safe. The solution is open if you need it.",
        }}
        answerAction={preview("practice-correct")}
      />
    ),
  },
  {
    key: "practice-give-up",
    title: "Practice: give up sheet",
    group: "Practice",
    canvas: ["PracticeGiveUpDialog.m"],
    render: () => (
      <PracticeQuestionScreen {...afterTwoTries} state="confirm-give-up" />
    ),
  },
  {
    key: "practice-solution",
    title: "Practice: solution shown",
    group: "Practice",
    canvas: ["PracticeSolution.m", "PracticeSolution.d", "PracticeLongMath.m"],
    render: () => (
      <PracticeQuestionScreen
        {...afterTwoTries}
        state="solution"
        solution={solution}
      />
    ),
  },
  {
    key: "practice-correct",
    title: "Practice: right first try",
    group: "Practice",
    canvas: ["PracticeCorrect.m"],
    render: () => (
      <PracticeQuestionScreen
        {...base}
        state="correct"
        session={{ ...session, position: 3 }}
        combo="FIRST TRY"
        lessonStars={1}
        question={{
          key: "n1-l1-03",
          difficulty: 1,
          outcome: "1.1",
          totalMarks: 1,
          stem: "Which of these numbers is prime: 21, 27, 29, 33?",
          parts: [
            {
              position: 1,
              label: null,
              prompt: null,
              marks: 1,
              placeholder: "A whole number",
              responseType: "numeric",
              value: "29",
              status: "correct",
            },
          ],
        }}
        result={{
          xp: 10,
          title: "Brilliant!",
          body: "Right on your first try. 29 has only two factors, 1 and 29.",
          stars: 1,
          starNote: "First star won for Lesson 1 practice",
          quest: { ...answerQuest, progress: 5 },
          finish: { label: "Finish practice", href: preview("practice-done") },
        }}
      />
    ),
  },
  {
    key: "practice-done",
    title: "Practice done",
    group: "Practice",
    canvas: ["PracticeDone.m", "PracticeDone.d"],
    render: () => (
      <PracticeDoneScreen
        player={samplePlayer}
        title="Lesson 1 practice"
        subtitle="Lesson 1 · Guided practice"
        backHref={preview("unit")}
        stars={1}
        tally={[
          { label: "2 right first try", xp: 20 },
          { label: "Practice set finished", xp: 10 },
          { label: "Quest: Answer 5 questions", xp: 15 },
          { label: "All 3 quests done", xp: 30 },
        ]}
        level={{
          level: 7,
          current: 155,
          needed: 160,
          note: "Clear your review question to level up and unlock headphones.",
        }}
        streak={{ days: 13, note: "1 more day to the 14-day milestone." }}
        results={[
          { label: "Question 1", outcome: "first_try", xp: 10 },
          {
            label: "Question 2",
            outcome: "solution_shown",
            note: "Back in 2 days",
          },
          { label: "Question 3", outcome: "first_try", xp: 10 },
        ]}
        nextStar={{
          title: "Star 2 is one answer away.",
          body: "Get the missed question right without the solution to reach proficient and open Lesson 2.",
        }}
        primary={{
          label: "Retry the missed question · +20 XP",
          href: preview("review"),
        }}
        secondary={{ label: "Back to the unit", href: preview("unit") }}
      />
    ),
  },
  {
    key: "practice-keyboard",
    title: "Practice: typing on a phone",
    group: "Practice",
    canvas: ["PracticeKeyboard.m"],
    render: () => (
      <PracticeKeyboardScreen
        player={samplePlayer}
        session={session}
        shortStem="Express 360 as a product of its prime factors in index notation."
        fullStem={stem}
        part={{
          ...parts(["2^3 × 3^2 ×", ""], ["none", "none"])[0]!,
          help: undefined,
        }}
        readsAs={
          <>
            <Sup base="2" exp="3" /> × <Sup base="3" exp="2" /> ×
          </>
        }
        hintsOpen={0}
        hintsTotal={2}
        links={{ hint: preview("practice-wrong-1") }}
        answerAction={preview("practice-wrong-1")}
      />
    ),
  },
];
