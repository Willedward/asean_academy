/**
 * Previews of every tutor board on the canvas page "AI tutor (V2)", on sample
 * data. Served at /beta-kit/tutor/<key>. Not used in production.
 */
import type { ReactNode } from "react";
import { Flag, Lightbulb, Lock } from "lucide-react";

import { Feedback, ReviewNote, XpNote } from "../components/rewards";
import { Button, Card, H3, M, Muted, Sup } from "../components/ui";
import type { PreviewEntry } from "../preview/registry";
import { samplePlayer } from "../sample-data";
import { BackLink } from "../screens/lesson";
import {
  AnswerInput,
  HintList,
  QuestionStemCard,
  SolutionCard,
  type PracticeHint,
  type PracticePart,
  type PracticeQuestion,
  type PracticeSolution,
} from "../screens/practice";
import { FocusShell, FooterBar, QuestionHeader } from "../shell/app-shell";
import { AskHornbillButton, AskHornbillCard, AskHornbillNudge } from "./launcher";
import {
  SAMPLE_NOW,
  replyExactly,
  replyLocked,
  replySmaller,
  replySolution,
  replyWhy,
  sampleQuota,
  sampleSummary,
  student,
} from "./sample";
import { ReportReplySheet, TutorPlanSheet } from "./sheets";
import { TutorView, type TutorViewProps } from "./tutor-view";
import type { TutorLaunchState } from "./types";

const base = "/beta-kit/tutor";
const href = (key: string) => `${base}/${key}`;

/* ------------------------------------------------------------------ */
/* The practice screen behind the tutor                                */
/* ------------------------------------------------------------------ */

function parts(b: string): PracticePart[] {
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
      value: "2^3 × 3^2 × 5",
      status: "correct",
    },
    {
      position: 2,
      label: "b",
      prompt: "the value of k",
      marks: 1,
      placeholder: "A whole number",
      responseType: "numeric",
      help: "Numbers only.",
      value: b,
      status: "wrong",
    },
  ];
}

const question = (b: string): PracticeQuestion => ({
  key: "n1-l1-q2",
  difficulty: 2,
  outcome: "1.1",
  totalMarks: 3,
  stem: (
    <>
      Express 360 as a product of its prime factors in index notation. Hence find the smallest positive integer{" "}
      <M>
        <i>k</i>
      </M>{" "}
      such that{" "}
      <M>
        360<i>k</i>
      </M>{" "}
      is a perfect square.
    </>
  ),
  parts: parts(b),
});

const hint1: PracticeHint = { stage: 1, content: "Divide 360 by 2 as many times as you can. Then try 3, then 5." };

const solution: PracticeSolution = {
  answers: [
    {
      label: "a",
      value: (
        <>
          <Sup base="2" exp="3" /> × <Sup base="3" exp="2" /> × 5
        </>
      ),
    },
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
    { text: "Divide by 2 while you can.", math: "360 = 2 × 180 = 2 × 2 × 90 = 2 × 2 × 2 × 45", wide: true },
    { text: "45 is odd. Divide by 3, twice.", math: "45 = 3 × 15 = 3 × 3 × 5" },
    {
      text: "Group the repeated factors.",
      math: (
        <>
          360 = <Sup base="2" exp="3" /> × <Sup base="3" exp="2" /> × 5
        </>
      ),
    },
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

function PracticeBackdrop({
  launch = "available",
  solutionShown,
  overlay,
  entry,
  chatOpen,
}: {
  launch?: TutorLaunchState;
  solutionShown?: boolean;
  overlay?: ReactNode;
  /** Draws the entry point (button, nudge, desktop card). */
  entry?: boolean;
  /** The chat panel is open: on desktop the question moves left to stay clear of it. */
  chatOpen?: boolean;
}) {
  const q = question(solutionShown ? "2" : "5");
  const feedback = (
    <Feedback kind="wrong">Part (a) is right. Part (b) is not yet. Change it and check again.</Feedback>
  );
  const answers = (
    <Card className="gap-5">
      {q.parts.map((part) => (
        <AnswerInput key={part.position} part={part} locked={solutionShown} />
      ))}
    </Card>
  );
  const footer = solutionShown ? (
    <FooterBar className="lg:hidden">
      <Button variant="primary" full href={href("solution")}>
        Next question
      </Button>
    </FooterBar>
  ) : (
    <FooterBar className="lg:hidden">
      {entry ? <AskHornbillNudge /> : null}
      <XpNote>Get it right now: still +6 XP.</XpNote>
      <div className="flex gap-2">
        <Button icon={Lightbulb}>Hint 2 of 2</Button>
        <AskHornbillButton state={launch} href={launch === "locked" ? href("plan") : href("start")} className="grow" />
      </div>
      <Button variant="primary" full>
        Check answer
      </Button>
      <div className="flex flex-wrap items-center justify-between gap-2 text-[13px] text-ns-muted">
        <span>1 wrong try so far</span>
        <span className="inline-flex items-center gap-1.5">
          <Lock size={14} aria-hidden />
          Solution opens after 2 tries
        </span>
      </div>
    </FooterBar>
  );
  const side = solutionShown ? (
    <div className="flex min-w-0 flex-col gap-4 lg:hidden">
      <ReviewNote />
      <SolutionCard solution={solution} />
    </div>
  ) : (
    <div className={chatOpen ? "hidden" : "hidden min-w-0 flex-col gap-4 lg:flex"}>
      <AskHornbillCard state={launch} href={launch === "locked" ? href("plan") : href("reply")} />
      <Card className="gap-3.5">
        <div className="flex items-center justify-between gap-3">
          <H3>Hints</H3>
          <span className="text-[13px] text-ns-muted">1 of 2 open</span>
        </div>
        <HintList hints={[hint1]} />
        <Button full icon={Lightbulb}>
          Hint 2 of 2
        </Button>
      </Card>
      <Card className="gap-3">
        <H3>Solution</H3>
        <span className="inline-flex items-center justify-center gap-1.5 text-[13px] text-ns-muted">
          <Lock size={14} aria-hidden />
          Opens after 2 wrong tries
        </span>
      </Card>
    </div>
  );
  return (
    <FocusShell
      player={samplePlayer}
      top={
        <QuestionHeader
          label="Lesson 1 · Guided practice"
          questionLabel="Question 2 of 3"
          done={1}
          current={1}
          total={3}
          closeHref="/beta-kit/tutor"
        />
      }
      desktopTop={
        <div className="flex flex-col gap-1.5">
          <BackLink href="/beta-kit/tutor">Lesson 1 · Primes and prime factorisation</BackLink>
          <h1 className="m-0 text-[28px] leading-9 font-bold">Guided practice · Question 2 of 3</h1>
        </div>
      }
      footer={footer}
      overlay={overlay}
      maxWidth={1120}
      className={chatOpen ? "lg:pr-[440px]" : undefined}
    >
      <div className="flex flex-col gap-4 lg:hidden">
        {solutionShown ? null : (
          <>
            {feedback}
            <HintList hints={[hint1]} />
          </>
        )}
      </div>
      <div className={chatOpen ? "grid items-start gap-4" : "grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-8"}>
        <div className={solutionShown ? "hidden min-w-0 flex-col gap-4 lg:flex" : "flex min-w-0 flex-col gap-4"}>
          <div className="hidden lg:block">{solutionShown ? null : feedback}</div>
          <QuestionStemCard question={q} />
          {answers}
          {solutionShown ? (
            <div className="hidden flex-col gap-4 lg:flex">
              <ReviewNote />
              <SolutionCard solution={solution} />
            </div>
          ) : null}
          {solutionShown ? null : (
            <div className="hidden items-center gap-4 lg:flex">
              <Button variant="primary">Check answer</Button>
              <span className="text-sm text-ns-muted">1 wrong try</span>
            </div>
          )}
        </div>
        {side}
      </div>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Chat states                                                         */
/* ------------------------------------------------------------------ */

const chatBase: Omit<TutorViewProps, "messages"> = {
  questionLabel: "Question 2 · part (b)",
  questionSummary: sampleSummary,
  wrongTries: 1,
  solutionOpen: false,
  studentName: "Dimas",
  closeHref: href("entry"),
  nextStepHref: href("entry"),
  now: SAMPLE_NOW,
  timeZone: "Asia/Jakarta",
};

function Chat(props: Partial<TutorViewProps> & Pick<TutorViewProps, "messages">) {
  return <PracticeBackdrop chatOpen solutionShown={props.solutionOpen} overlay={<TutorView {...chatBase} {...props} />} />;
}

const reply = {
  suggestions: ["I still don’t get it", "Why do powers need to be even?", "Show me in the lesson"],
  nextStep: "Try part (b) again",
  reportHref: href("report"),
};

export const tutorEntries: PreviewEntry[] = [
  {
    key: "entry",
    title: "1 · Ask the hornbill appears after the first try",
    group: "AI tutor (V2)",
    canvas: ["TutorEntry.m", "TutorEntry.d"],
    render: () => <PracticeBackdrop entry />,
  },
  {
    key: "start",
    title: "2 · Hello and starter questions",
    group: "AI tutor (V2)",
    canvas: ["TutorStart.m"],
    render: () => <Chat messages={[]} />,
  },
  {
    key: "thinking",
    title: "3 · Thinking, send is locked",
    group: "AI tutor (V2)",
    canvas: ["TutorThinking.m"],
    render: () => <Chat messages={[student("s1", "Why is my answer wrong?", "sending")]} sending />,
  },
  {
    key: "reply",
    title: "4 · Reply with maths, suggestions and next step",
    group: "AI tutor (V2)",
    canvas: ["Tutor.m", "Tutor.d"],
    render: () => <Chat messages={[student("s1", "Why is my answer wrong?"), replyWhy]} {...reply} />,
  },
  {
    key: "still-stuck",
    title: "5 · Still stuck: a new approach",
    group: "AI tutor (V2)",
    canvas: ["TutorStillStuck.m"],
    render: () => (
      <Chat
        messages={[student("s1", "Why is my answer wrong?"), replyWhy, student("s2", "I still don’t get it"), replySmaller]}
        suggestions={["2 and 5", "Only 5", "Why is 36 a square?"]}
        reportHref={href("report")}
      />
    ),
  },
  {
    key: "answer-locked",
    title: "6 · Asks for the answer too early",
    group: "AI tutor (V2)",
    canvas: ["TutorAnswerLocked.m"],
    render: () => (
      <Chat
        messages={[student("s1", "just tell me what k is pls"), replyLocked]}
        suggestions={["How do I count the 2s?", "Open Hint 2"]}
        nextStep="Try part (b) again"
        reportHref={href("report")}
      />
    ),
  },
  {
    key: "solution",
    title: "7 · After Give up: explains the solution",
    group: "AI tutor (V2)",
    canvas: ["TutorSolution.m", "TutorSolution.d"],
    render: () => (
      <Chat
        solutionOpen
        wrongTries={2}
        messages={[student("s1", "why is k = 2 × 5 and not just 5?"), replySolution]}
        suggestions={["Why does an even power make a square?", "Give me a similar question"]}
        reportHref={href("report")}
      />
    ),
  },
  {
    key: "low-quota",
    title: "8 · 3 or fewer messages left today",
    group: "AI tutor (V2)",
    canvas: ["TutorLowQuota.m"],
    render: () => (
      <Chat
        messages={[student("s1", "ok so 2 and 5 are odd"), replyExactly]}
        nextStep="Try part (b) again"
        notice={{ kind: "quota_low", remaining: 2, resetsAt: sampleQuota(2).resets_at }}
        reportHref={href("report")}
      />
    ),
  },
  {
    key: "out-for-today",
    title: "9 · Out of messages for today",
    group: "AI tutor (V2)",
    canvas: ["TutorOutForToday.m"],
    render: () => (
      <Chat
        messages={[student("s1", "ok so 2 and 5 are odd"), replyExactly]}
        notice={{ kind: "out_for_today", resetsAt: sampleQuota(0).resets_at }}
      />
    ),
  },
  {
    key: "offline",
    title: "10 · Hornbill not reachable, explicit retry",
    group: "AI tutor (V2)",
    canvas: ["TutorOffline.m"],
    render: () => (
      <Chat
        messages={[student("s1", "What is the question asking?", "failed")]}
        notice={{ kind: "offline", requestId: "req_7f2c91a4" }}
      />
    ),
  },
  {
    key: "report",
    title: "11 · Report a reply",
    group: "AI tutor (V2)",
    canvas: ["TutorReport.m"],
    render: () => (
      <PracticeBackdrop
        chatOpen
        overlay={
          <>
            <TutorView {...chatBase} messages={[student("s1", "Why is my answer wrong?"), replyWhy]} />
            <ReportReplySheet cancelHref={href("reply")} />
          </>
        }
      />
    ),
  },
  {
    key: "plan",
    title: "12 · Free plan: the tutor is part of the Season pass",
    group: "AI tutor (V2)",
    canvas: ["TutorPlan.m"],
    render: () => (
      <PracticeBackdrop launch="locked" overlay={<TutorPlanSheet plansHref="/beta-kit" closeHref={href("entry")} />} />
    ),
  },
  {
    key: "unavailable",
    title: "Extra · Can’t help with this question yet",
    group: "AI tutor (V2)",
    canvas: ["(plan only)"],
    render: () => <Chat messages={[]} notice={{ kind: "unavailable_question" }} />,
  },
];

export function findTutorEntry(key: string) {
  return tutorEntries.find((entry) => entry.key === key);
}

/** Small legend for the index page. */
export function TutorPreviewIntro() {
  return (
    <Muted>
      The hornbill tutor (roadmap V2-15), built from the canvas page “AI tutor (V2)”. Resize the window: phones get a
      sheet over the question, desktops a panel beside it. <Flag size={12} className="inline" aria-hidden /> Every
      screen uses sample data; the live wiring is <code>TutorDock</code>.
    </Muted>
  );
}
