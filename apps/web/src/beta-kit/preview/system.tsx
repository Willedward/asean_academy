import { H1, M } from "../components/ui";
import { preview } from "../routes";
import { samplePlayer, sampleContinue, sampleQuests, sampleWeek } from "../sample-data";
import { ContinueCard } from "../screens/dashboard";
import { KitSheetScreen } from "../screens/kit-sheet";
import {
  CheckpointResumeScreen,
  LoadingScreen,
  NotFoundScreen,
  OfflineScreen,
  PracticeExpiredScreen,
  ReportProblemScreen,
  ServerErrorScreen,
  SessionExpiredScreen,
  SkeletonLessonScreen,
  SkeletonPracticeScreen,
  SkeletonUnitScreen,
  WeeklyCheckinScreen,
} from "../screens/system";
import type { PreviewEntry } from "./registry";

const GROUP = "System states";

const reportReasons = [
  { value: "answer_key_wrong", label: "The answer key seems wrong" },
  { value: "unclear_or_typo", label: "The question is unclear or has a typo" },
  { value: "missing_image", label: "A picture or diagram is missing" },
  { value: "other", label: "Something else" },
];

export const systemEntries: PreviewEntry[] = [
  {
    key: "loading",
    title: "Loading dashboard",
    group: GROUP,
    canvas: ["Loading.m"],
    render: () => <LoadingScreen player={samplePlayer} message="Loading your streak and quests…" />,
  },
  {
    key: "skeleton-unit",
    title: "Loading unit",
    group: GROUP,
    canvas: ["SkeletonUnit.m"],
    render: () => <SkeletonUnitScreen player={samplePlayer} unitLabel="Unit N1" backHref={preview("course-map")} />,
  },
  {
    key: "skeleton-practice",
    title: "Loading practice question",
    group: GROUP,
    canvas: ["SkeletonPractice.m"],
    render: () => <SkeletonPracticeScreen player={samplePlayer} />,
  },
  {
    key: "skeleton-lesson",
    title: "Loading lesson",
    group: GROUP,
    canvas: ["SkeletonLesson.d"],
    render: () => <SkeletonLessonScreen player={samplePlayer} backHref={preview("unit")} />,
  },
  {
    key: "offline",
    title: "Offline",
    group: GROUP,
    canvas: ["Offline.m"],
    render: () => <OfflineScreen streakDays={samplePlayer.streakDays} answerKept retryHref={preview("practice-answer")} />,
  },
  {
    key: "not-found",
    title: "Page not available",
    group: GROUP,
    canvas: ["NotFound.m"],
    render: () => <NotFoundScreen errorCode="content_unavailable" requestId="req_4c1e90" />,
  },
  {
    key: "signed-out",
    title: "Signed out",
    group: GROUP,
    canvas: ["SessionExpired.m"],
    render: () => <SessionExpiredScreen signInHref={preview("sign-in")} />,
  },
  {
    key: "server-error",
    title: "Server error",
    group: GROUP,
    canvas: ["Error.d"],
    render: () => (
      <ServerErrorScreen player={samplePlayer} errorCode="server_error" requestId="req_a91f02" retryHref={preview("dashboard")} />
    ),
  },
  {
    key: "report-problem",
    title: "Report a problem",
    group: GROUP,
    canvas: ["ReportProblem.m"],
    render: () => (
      <ReportProblemScreen
        player={samplePlayer}
        contextLabel="Lesson 1 · Guided practice"
        questionLabel="Question 2 of 3"
        done={1}
        current={1}
        total={3}
        closeHref={preview("practice-answer")}
        question={
          <p className="m-0 text-[17px] leading-[26px]">
            Find the smallest positive integer <M>k</M> such that <M>360k</M> is a perfect square.
          </p>
        }
        questionKey="n1-l1-02"
        reasons={reportReasons}
        selectedReason="answer_key_wrong"
        details="I think part (b) should accept 10 but it marked me wrong."
        reward={{ xp: 25, badgeName: "Bug hunter" }}
      />
    ),
  },
  {
    key: "checkpoint-resume",
    title: "Checkpoint interrupted",
    group: GROUP,
    canvas: ["CheckpointResume.m"],
    render: () => (
      <CheckpointResumeScreen
        checkpointTitle="N1 checkpoint"
        answeredCount={2}
        questionCount={8}
        leftAtLabel="Left yesterday at 20:41"
        reward={{ streakDays: 13, badgeName: "Number master" }}
        continueHref={preview("checkpoint-active")}
      />
    ),
  },
  {
    key: "practice-expired",
    title: "Practice session closed",
    group: GROUP,
    canvas: ["PracticeExpired.m"],
    render: () => (
      <PracticeExpiredScreen
        lessonLabel="Lesson 1"
        answeredCount={2}
        xpKept={16}
        newSessionHref={preview("practice-answer")}
        lessonHref={preview("lesson")}
      />
    ),
  },
  {
    key: "weekly-checkin",
    title: "Weekly check-in",
    group: GROUP,
    canvas: ["WeeklyCheckin.m"],
    render: () => (
      <WeeklyCheckinScreen
        player={samplePlayer}
        background={
          <>
            <H1>Pick up where you left off</H1>
            <ContinueCard data={sampleContinue} />
          </>
        }
        rating={4}
        confusing="Typing powers like 2^3 was hard on my phone."
        xp={20}
        skipHref={preview("dashboard")}
      />
    ),
  },
  {
    key: "kit",
    title: "Kit: hornbill and rewards",
    group: GROUP,
    canvas: ["GameKit.dc"],
    render: () => <KitSheetScreen player={samplePlayer} quests={sampleQuests} week={sampleWeek} />,
  },
];
