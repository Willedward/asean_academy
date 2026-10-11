import { preview } from "../routes";
import { newPlayer, samplePlayer } from "../sample-data";
import type { PracticePart } from "../screens/practice";
import {
  DashboardReadinessScreen,
  ParentReportScreen,
  ReadinessCard,
  ReadinessCompareScreen,
  ReadinessIntroScreen,
  ReadinessPendingScreen,
  ReadinessQuestionScreen,
  ReadinessResultScreen,
  ReadinessReviewScreen,
  type ReadinessOutcome,
  type ReadinessResultData,
  type ShareLink,
} from "../screens/readiness";
import { AppShell, StatBar } from "../shell/app-shell";
import { MascotSays } from "../components/rewards";
import type { PreviewEntry } from "./registry";

const G = "Readiness check";
const OUT: ReadinessOutcome[] = [
  { code: "1.1", title: "Primes and prime factorisation", score: 4, max: 4, after: 4 },
  { code: "1.2", title: "HCF and LCM", score: 3, max: 4, after: 4 },
  { code: "1.3", title: "Squares, cubes and roots", score: 2, max: 4, after: 4 },
  { code: "1.4", title: "Integers and number sets", score: 3, max: 4, after: 3 },
  { code: "1.5", title: "Ordering on a number line", score: 1, max: 4, after: 3 },
  { code: "1.6", title: "Estimation and calculators", score: 1, max: 4, after: 2 },
];
const strip = (o: ReadinessOutcome): ReadinessOutcome => ({ code: o.code, title: o.title, score: o.score, max: o.max });
const at = (code: string) => strip(OUT.find((o) => o.code === code) as ReadinessOutcome);

const result: ReadinessResultData = {
  purpose: "baseline",
  band: "on_track",
  score: 14,
  max: 24,
  dateLabel: "9 October",
  strengths: [at("1.1"), at("1.2"), at("1.4")],
  focus: [at("1.5"), at("1.6"), at("1.3")],
  outcomes: OUT.map(strip),
  summary: "You already have a solid base. A few topics need practice before the test.",
  reward: { xp: 50, badge: "Starting line", badgeNote: "For finishing your readiness check." },
  start: { label: "Lesson 1", href: preview("lesson") },
};

const share: ShareLink = {
  url: "nextscholar.id/r/7Kq2-Wm9x",
  expiresLabel: "8 November",
  whatsappHref: preview("readiness-parent"),
  pdfHref: preview("readiness-parent"),
};

const part: PracticePart = {
  position: 1,
  label: null,
  prompt: null,
  marks: 1,
  placeholder: "A number",
  responseType: "numeric",
  help: "Enter a number. Fractions like −3/4 are fine too.",
  value: "−0.75",
  status: "none",
};

const q = (n: number) => preview(n === 12 ? "readiness-review" : "readiness-question");

export const readinessEntries: PreviewEntry[] = [
  {
    key: "readiness-intro",
    title: "Readiness check · after onboarding",
    group: G,
    canvas: ["ReadinessIntro.m"],
    render: () => (
      <ReadinessIntroScreen
        questionCount={12}
        minutes={25}
        reward={{ xp: 50, badge: "Starting line" }}
        startHref={preview("readiness-question")}
        laterHref={preview("dashboard-readiness")}
      />
    ),
  },
  {
    key: "dashboard-readiness",
    title: "Dashboard · readiness check not done yet",
    group: G,
    canvas: ["DashboardReadiness.m"],
    render: () => (
      <DashboardReadinessScreen
        player={newPlayer}
        card={{ kind: "baseline", questionCount: 12, minutes: 25, xp: 50, href: preview("readiness-question") }}
        firstLesson={{ title: "Primes and prime factorisation", label: "Lesson 1 of 7", href: preview("lesson") }}
      />
    ),
  },
  {
    key: "readiness-question",
    title: "Readiness check · answering",
    group: G,
    canvas: ["ReadinessQuestion.m", "ReadinessQuestion.d"],
    render: () => (
      <ReadinessQuestionScreen
        player={samplePlayer}
        purpose="baseline"
        position={6}
        total={12}
        answered={[1, 2, 3, 4, 5]}
        outcome="1.5"
        calculatorAllowed={false}
        marks={1}
        stem={
          <div className="flex flex-col gap-3">
            <span>
              Here are five numbers. Write down the <b>second smallest</b>.
            </span>
            <span className="flex flex-wrap gap-2.5 font-ns-math text-[22px]">
              {["−3", "0.4", "−0.5", "−¾", "1"].map((v) => (
                <span key={v} className="rounded-[10px] bg-ns-sunken px-3 py-1.5">
                  {v}
                </span>
              ))}
            </span>
          </div>
        }
        parts={[part]}
        savedLabel="Saved"
        minutesLeft={15}
        questionHref={q}
        previousHref={preview("readiness-question")}
        nextHref={preview("readiness-review")}
        skipHref={preview("readiness-question")}
        leaveHref={preview("dashboard-readiness-resume")}
      />
    ),
  },
  {
    key: "readiness-review",
    title: "Readiness check · review and finish",
    group: G,
    canvas: ["ReadinessReview.m"],
    render: () => (
      <ReadinessReviewScreen
        player={samplePlayer}
        total={12}
        answered={[1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12]}
        reward={{ xp: 50, badge: "Starting line" }}
        questionHref={q}
        submitAction={preview("readiness-result")}
        backHref={preview("readiness-question")}
      />
    ),
  },
  {
    key: "readiness-result",
    title: "Readiness check · results, strengths first",
    group: G,
    canvas: ["ReadinessResult.m", "ReadinessResult.d"],
    render: () => <ReadinessResultScreen player={samplePlayer} data={result} shareHref={preview("readiness-share")} backHref={preview("dashboard")} />,
  },
  {
    key: "readiness-share",
    title: "Readiness check · share with a parent",
    group: G,
    canvas: ["ReadinessShare.m"],
    render: () => (
      <ReadinessResultScreen
        player={samplePlayer}
        data={{ ...result, reward: undefined }}
        shareHref={preview("readiness-share")}
        share={share}
        shareCloseHref={preview("readiness-result")}
        backHref={preview("dashboard")}
      />
    ),
  },
  {
    key: "readiness-parent",
    title: "Readiness check · what the parent sees",
    group: G,
    canvas: ["ReadinessParent.m"],
    render: () => <ParentReportScreen studentFirstName="Dimas" courseLabel="Sec 1 entry mathematics" data={result} expiresLabel="8 November 2026" />,
  },
  {
    key: "readiness-compare",
    title: "Readiness check · end of beta, start and now",
    group: G,
    canvas: ["ReadinessCompare.m", "ReadinessCompare.d"],
    render: () => (
      <ReadinessCompareScreen
        player={samplePlayer}
        start={{ score: 14, band: "on_track", dateLabel: "9 Oct" }}
        now={{ score: 20, band: "ahead", dateLabel: "12 Dec" }}
        max={24}
        outcomes={OUT}
        biggest={{ title: "Ordering on a number line", from: 1, to: 3, xp: 50, badge: "Glow up" }}
        shareHref={preview("readiness-share")}
        backHref={preview("progress")}
      />
    ),
  },
  {
    key: "dashboard-readiness-end",
    title: "Dashboard · end-of-beta check",
    group: G,
    canvas: ["DashboardReadinessEnd.m"],
    render: () => (
      <AppShell active="learn" player={samplePlayer} top={<StatBar player={samplePlayer} />} maxWidth={720}>
        <MascotSays mood="happy" pose="cheer">
          The beta ends on 19 December. One last thing: see how far you’ve come!
        </MascotSays>
        <ReadinessCard kind="endline" questionCount={12} minutes={25} xp={50} href={preview("readiness-question")} />
      </AppShell>
    ),
  },
  {
    key: "dashboard-readiness-resume",
    title: "Dashboard · readiness check half done",
    group: G,
    canvas: ["(state of DashboardReadiness.m)"],
    render: () => (
      <AppShell active="learn" player={samplePlayer} top={<StatBar player={samplePlayer} />} maxWidth={720}>
        <ReadinessCard kind="resume" questionCount={12} minutes={25} answered={5} xp={50} href={preview("readiness-question")} />
      </AppShell>
    ),
  },
  {
    key: "readiness-pending",
    title: "Readiness check · questions still in review",
    group: G,
    canvas: ["ReadinessPending.m"],
    render: () => <ReadinessPendingScreen player={samplePlayer} lessonHref={preview("lesson")} backHref={preview("dashboard")} />,
  },
];
