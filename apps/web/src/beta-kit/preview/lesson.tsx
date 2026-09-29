import { AlertCircle } from "lucide-react";

import { Callout, M, Sup } from "../components/ui";
import { preview } from "../routes";
import { samplePlayer, sampleUnit } from "../sample-data";
import {
  CheckYourself,
  LessonInReviewScreen,
  LessonMath,
  LessonScreen,
  LessonVideoScreen,
  WorkedExample,
  type LessonMeta,
  type LessonPracticeCta,
  type LessonSection,
} from "../screens/lesson";
import type { PreviewEntry } from "./registry";

const lesson1: LessonMeta = {
  position: 1,
  lessonCount: 7,
  title: "Primes and prime factorisation",
  minutes: 25,
  state: "proficient",
  stars: 2,
  unitCode: sampleUnit.code,
  unitTitle: sampleUnit.title,
  unitHref: sampleUnit.href,
};

const lesson1Practice: LessonPracticeCta = {
  questionCount: 3,
  available: true,
  stars: 0,
  xp: 40,
  quest: { title: "Answer 5 questions", progress: 4, target: 5 },
  href: preview("practice-answer"),
};

const sections: LessonSection[] = [
  {
    id: "prime-numbers",
    title: "Prime numbers",
    xp: 10,
    done: true,
    content: (
      <>
        <p>
          A <b>prime number</b> has exactly two factors: 1 and itself. The first
          primes are 2, 3, 5, 7, 11 and 13.
        </p>
        <p>
          A number with more than two factors is <b>composite</b>. 12 is
          composite because 2, 3, 4 and 6 also divide it.
        </p>
        <Callout tone="amber" icon={AlertCircle}>
          <span className="text-ns-amber-text">
            <b>1 is not prime.</b> It has only one factor. 2 is the only even
            prime.
          </span>
        </Callout>
      </>
    ),
  },
  {
    id: "prime-factorisation",
    title: "Prime factorisation",
    xp: 10,
    done: true,
    content: (
      <>
        <p>
          Every whole number greater than 1 can be written as a product of
          primes in exactly one way. Repeated factors are written with an index.
        </p>
        <LessonMath>
          2 × 2 × 2 = <Sup base="2" exp="3" />
        </LessonMath>
        <p>
          Read{" "}
          <M>
            <Sup base="2" exp="3" />
          </M>{" "}
          as &quot;2 to the power of 3&quot;. The small 3 is the <b>index</b>.
        </p>
      </>
    ),
  },
  {
    id: "worked-example",
    title: "Worked example",
    xp: 10,
    done: false,
    content: (
      <WorkedExample
        title="Write 84 as a product of prime factors"
        steps={[
          { text: "84 is even, so divide by 2.", math: "84 = 2 × 42" },
          { text: "42 is even too.", math: "84 = 2 × 2 × 21" },
          {
            text: "21 is not even. Try the next prime, 3.",
            math: "84 = 2 × 2 × 3 × 7",
          },
          {
            text: "7 is prime, so stop. Group the repeated 2s.",
            math: (
              <>
                84 = <Sup base="2" exp="2" /> × 3 × 7
              </>
            ),
          },
        ]}
      />
    ),
  },
  {
    id: "check-yourself",
    title: "Check yourself",
    xp: 5,
    done: false,
    content: (
      <CheckYourself
        question="Is 51 a prime number?"
        options={["Yes", "No"]}
        chosen={1}
        feedback={{
          correct: true,
          body: "51 = 3 × 17, so it has more than two factors.",
        }}
        xp={5}
      />
    ),
  },
];

const videoSteps = [
  "Before you start",
  "Video",
  "Prime numbers",
  "Prime factorisation",
  "Worked example",
  "Check yourself",
  "Summary",
];

export const lessonEntries: PreviewEntry[] = [
  {
    key: "lesson",
    title: "Lesson",
    group: "Lesson",
    canvas: ["Lesson.m", "Lesson.d", "Lesson.t"],
    render: () => (
      <LessonScreen
        player={samplePlayer}
        lesson={lesson1}
        objectives={[
          "Tell whether a whole number is prime or composite.",
          "Write a whole number as a product of prime factors using index notation.",
        ]}
        video={{
          title: "[Video poster: Lesson 1]",
          duration: "6:12",
          minutes: 6,
          xp: 10,
          done: true,
          href: preview("lesson-video"),
          transcriptHref: preview("lesson-video"),
        }}
        recall={
          <>
            <b>Quick recall.</b> A <i>factor</i> of 12 is a number that divides
            12 exactly. The factors of 12 are 1, 2, 3, 4, 6 and 12.
          </>
        }
        sections={sections}
        summary={[
          "A prime has exactly two factors. 1 is not prime.",
          "Divide by the smallest prime that works, again and again.",
          <>
            Write repeated factors with an index: 2 × 2 × 2 ={" "}
            <Sup base="2" exp="3" />.
          </>,
        ]}
        practice={lesson1Practice}
        currentSectionId="prime-numbers"
      />
    ),
  },
  {
    key: "lesson-in-review",
    title: "Lesson being checked",
    group: "Lesson",
    canvas: ["LessonPending.m"],
    render: () => (
      <LessonInReviewScreen
        player={samplePlayer}
        lesson={{
          ...lesson1,
          position: 3,
          title: "Number sets and operations",
          minutes: 35,
          state: "in_review",
          stars: 0,
        }}
        objectives={[
          "Tell integers, rational numbers and real numbers apart.",
          "Add, subtract, multiply and divide signed and rational numbers.",
        ]}
        reviewDue={{ count: 2, xp: 40, href: preview("review") }}
        practiceXp={40}
        previous={{ label: "Back to Lesson 2", href: sampleUnit.href }}
      />
    ),
  },
  {
    key: "lesson-video",
    title: "Lesson video",
    group: "Lesson",
    canvas: ["LessonVideo.m", "LessonVideo.d"],
    render: () => (
      <LessonVideoScreen
        player={samplePlayer}
        lesson={{
          position: 1,
          title: "Primes and prime factorisation",
          href: preview("lesson"),
        }}
        video={{
          title: "Video: breaking a number into primes",
          minutes: 6,
          xp: 10,
          media: (
            <div className="relative h-full w-full">
              <span className="absolute top-3 left-4 text-xs font-semibold text-ns-on-brand/70">
                [Lesson video]
              </span>
              <span className="absolute top-[34%] left-1/2 -translate-x-1/2 -translate-y-1/2 font-ns-math text-[26px] whitespace-nowrap text-ns-on-brand lg:top-[38%] lg:text-[44px]">
                84 = 2 × 2 × 21
              </span>
            </div>
          ),
          caption: "And 42 is even too, so we keep going.",
          captionsOn: true,
          playing: true,
          speed: 1,
          positionSeconds: 134,
          durationSeconds: 372,
        }}
        steps={videoSteps}
        stepIndex={1}
        transcript={{
          lines: [
            {
              time: "1:48",
              text: "Let us break 84 into primes. 84 is even, so we start with 2.",
            },
            { time: "2:02", text: "84 is 2 times 42." },
            {
              time: "2:14",
              text: "And 42 is even too, so we keep going. 42 is 2 times 21.",
            },
            {
              time: "2:31",
              text: "21 is odd, so 2 will not work. Try the next prime, which is 3.",
            },
            {
              time: "2:44",
              text: "21 is 3 times 7, and 7 is prime. So we stop.",
            },
            {
              time: "2:58",
              text: "Now group the repeated 2s. 84 is 2 squared, times 3, times 7.",
            },
          ],
          currentIndex: 2,
          followVideo: true,
          downloadHref: preview("lesson-video"),
          language: "English captions",
        }}
        doneHref={preview("lesson")}
      />
    ),
  },
];
