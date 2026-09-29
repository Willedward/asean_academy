import type { ReactNode } from "react";
import { ArrowRight, Check, RefreshCw } from "lucide-react";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { Medal, MiniChips, StreakSafe } from "../components/rewards";
import { Button, Callout, Card, Eyebrow, H1, Muted, Sheet, Steps, Tag, focusRing } from "../components/ui";
import { AppShell, BareShell, FocusShell, FooterBar, Logo, QuestionHeader, TopBar } from "../shell/app-shell";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import type { Href, Mood, Player } from "../types";
import type { FormAction } from "./entry";

/* ------------------------------------------------------------------ */
/* Shared pieces                                                       */
/* ------------------------------------------------------------------ */

/**
 * One grey loading shape. `w` is any CSS length (default full width), `h` is px.
 * For sizes that change at a breakpoint, leave w/h out and pass classes.
 */
export function Skel({ w, h, round, className }: { w?: string; h?: number; round?: boolean; className?: string }) {
  return (
    <div
      className={cn("w-full shrink-0 animate-pulse bg-ns-sunken", round ? "rounded-full" : "rounded-lg", className)}
      style={{ width: w, height: h }}
    />
  );
}

/** Hidden status line so screen readers hear what is loading. */
function LoadingStatus({ children }: { children: string }) {
  return (
    <span role="status" className="sr-only">
      {children}
    </span>
  );
}

function SkelCard({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <Card shadow={false} className={className}>
      {children}
    </Card>
  );
}

export interface StateScreenProps {
  mood: Mood;
  title: string;
  text: ReactNode;
  /** Buttons. Stacked on phones. */
  actions: ReactNode;
  /** Put the actions in a row from 1024px up. */
  inlineActions?: boolean;
  /** Panels between the text and the actions. */
  extra?: ReactNode;
  /** Small print under the actions, e.g. an error code. */
  footnote?: ReactNode;
}

/** Hornbill, title, text, optional panels and actions. Used by every system state. */
export function StateScreen({ mood, title, text, actions, inlineActions, extra, footnote }: StateScreenProps) {
  return (
    <section className="flex flex-col gap-4 pt-6">
      <div className="animate-ns-float self-start">
        <Hornbill size={120} mood={mood} outfit="scarf" />
      </div>
      <H1 className="text-[26px] leading-8 lg:text-[26px] lg:leading-8">{title}</H1>
      <p className="m-0 text-base leading-6 text-ns-muted">{text}</p>
      {extra}
      <div className={cn("flex flex-col gap-2", inlineActions && "lg:flex-row lg:flex-wrap")}>{actions}</div>
      {footnote}
    </section>
  );
}

/** Logo bar plus a centred column. For states shown without the app chrome. */
function BareState({ children }: { children: ReactNode }) {
  return (
    <BareShell>
      <header className="flex h-[60px] items-center border-b border-ns-line px-4 lg:h-20 lg:px-14">
        <Logo height={22} />
      </header>
      <main className="flex justify-center px-6 pb-10 lg:pt-10">
        <div className="w-full max-w-[520px]">{children}</div>
      </main>
    </BareShell>
  );
}

function ErrorCode({ code, requestId, center, mono }: { code: string; requestId: string; center?: boolean; mono?: boolean }) {
  return (
    <p className={cn("m-0 text-[13px] leading-[18px] text-ns-muted", center && "pt-2 text-center", mono && "font-mono")}>
      Error code: {code} · {requestId}
    </p>
  );
}

/** A labelled multi-line text box. `name` is the form field name. */
export function TextArea({
  id,
  name,
  label,
  value,
  placeholder,
  rows = 2,
}: {
  id: string;
  name: string;
  label: string;
  value?: string;
  placeholder?: string;
  rows?: number;
}) {
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <label htmlFor={id} className="text-[15px] leading-5 font-semibold">
        {label}
      </label>
      <textarea
        id={id}
        name={name}
        rows={rows}
        defaultValue={value}
        placeholder={placeholder}
        className={cn(
          "w-full min-w-0 resize-y rounded-lg border-[1.5px] border-ns-line-strong bg-ns-raised px-4 py-3 text-base leading-6 text-ns-ink placeholder:text-ns-muted",
          focusRing,
        )}
      />
    </div>
  );
}

function RadioDot() {
  return (
    <span className="inline-flex size-5 shrink-0 items-center justify-center rounded-full border-2 border-ns-line-strong group-has-checked:border-ns-ink">
      <span className="size-2.5 rounded-full bg-ns-ink opacity-0 group-has-checked:opacity-100" />
    </span>
  );
}

const radioFocus = "has-focus-visible:outline-3 has-focus-visible:outline-offset-2 has-focus-visible:outline-ns-success";

/* ------------------------------------------------------------------ */
/* Loading and skeletons                                               */
/* ------------------------------------------------------------------ */

export interface LoadingProps {
  player: Player;
  /** e.g. "Loading your streak and quests…" */
  message: string;
  routes?: KitRoutes;
}

/** Canvas: Loading.m. Dashboard skeleton with a small hornbill status line. */
export function LoadingScreen({ player, message, routes = PREVIEW_ROUTES }: LoadingProps) {
  return (
    <AppShell
      active="learn"
      player={player}
      routes={routes}
      top={<TopBar logo right={<MiniChips player={player} routes={routes} />} />}
    >
      <div className="flex flex-col gap-2.5">
        <Skel w="40%" h={16} />
        <Skel w="80%" h={28} />
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-6">
        <div className="flex flex-col gap-4">
          <SkelCard className="gap-3.5 p-6">
            <Skel w="30%" h={22} round />
            <Skel w="90%" h={24} />
            <Skel w="70%" h={16} />
            <Skel h={10} round />
            <Skel h={44} round />
          </SkelCard>
          <SkelCard>
            <Skel w="50%" h={20} />
            <Skel h={14} />
            <Skel w="60%" h={14} />
          </SkelCard>
          <SkelCard className="p-6">
            <div className="grid grid-cols-3 gap-4">
              {[0, 1, 2].map((i) => (
                <div key={i} className="flex flex-col gap-1.5">
                  <Skel w="60%" h={28} />
                  <Skel w="90%" h={12} />
                </div>
              ))}
            </div>
          </SkelCard>
        </div>
        <div className="hidden flex-col gap-4 lg:flex">
          <SkelCard className="gap-3.5">
            <Skel w="50%" h={28} />
            <Skel h={34} round />
          </SkelCard>
          <SkelCard>
            <Skel w="40%" h={20} />
            <Skel h={44} />
            <Skel h={44} />
            <Skel h={44} />
          </SkelCard>
        </div>
      </div>
      <div role="status" className="flex items-center gap-2.5 self-center">
        <div className="animate-ns-float">
          <Hornbill size={56} branch={false} />
        </div>
        <span className="text-sm font-bold text-ns-muted">{message}</span>
      </div>
    </AppShell>
  );
}

export interface SkeletonUnitProps {
  player: Player;
  /** e.g. "Unit N1". Known from the link, before the unit loads. */
  unitLabel: string;
  backHref: Href;
  routes?: KitRoutes;
}

/** Canvas: SkeletonUnit.m */
export function SkeletonUnitScreen({ player, unitLabel, backHref, routes = PREVIEW_ROUTES }: SkeletonUnitProps) {
  return (
    <AppShell
      active="course"
      player={player}
      routes={routes}
      top={<TopBar title={unitLabel} backHref={backHref} right={<MiniChips player={player} routes={routes} />} />}
    >
      <div className="flex flex-col gap-3">
        <Skel w="55%" h={12} />
        <Skel className="h-[26px] w-[90%] lg:w-[60%]" />
        <div className="flex gap-2">
          <Skel w="96px" h={24} round />
          <Skel w="110px" h={24} round />
        </div>
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] lg:gap-6">
        <SkelCard className="gap-5">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-3.5">
              <Skel w="36px" h={36} round />
              <div className="flex grow flex-col gap-2">
                <Skel w="75%" h={16} />
                <Skel w="45%" h={12} />
              </div>
              <Skel w="72px" h={24} round />
            </div>
          ))}
        </SkelCard>
        <SkelCard>
          <Skel w="40%" h={20} />
          <Skel h={14} />
          <Skel w="70%" h={14} />
          <Skel h={44} round />
        </SkelCard>
      </div>
      <LoadingStatus>{`Loading ${unitLabel}`}</LoadingStatus>
    </AppShell>
  );
}

function SkelQuestionHeader() {
  return (
    <header className="flex flex-col gap-2.5 border-b border-ns-line bg-ns-surface px-4 py-3 lg:border-b-0 lg:px-0 lg:py-0">
      <div className="flex items-center gap-2">
        <div className="flex grow flex-col gap-1.5">
          <Skel className="h-3 w-[45%] lg:w-[220px]" />
          <Skel className="h-[18px] w-[35%] lg:h-8 lg:w-[260px]" />
        </div>
        <Skel w="32px" h={32} round />
      </div>
      <Skel h={6} round />
    </header>
  );
}

export interface SkeletonPracticeProps {
  player: Player;
  routes?: KitRoutes;
}

/** Canvas: SkeletonPractice.m */
export function SkeletonPracticeScreen({ player, routes = PREVIEW_ROUTES }: SkeletonPracticeProps) {
  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={760}
      top={<SkelQuestionHeader />}
      desktopTop={<SkelQuestionHeader />}
      footer={
        <FooterBar>
          <div className="flex gap-2 lg:justify-end">
            <Skel w="120px" h={44} round />
            <div className="grow lg:w-[220px] lg:grow-0">
              <Skel h={44} round />
            </div>
          </div>
        </FooterBar>
      }
    >
      <SkelCard>
        <div className="flex gap-2">
          <Skel w="64px" h={24} round />
          <Skel w="88px" h={24} round />
        </div>
        <Skel h={16} />
        <Skel w="95%" h={16} />
        <Skel w="60%" h={16} />
      </SkelCard>
      <SkelCard className="gap-5">
        <div className="flex flex-col gap-2">
          <Skel w="30%" h={16} />
          <Skel h={52} />
          <Skel w="70%" h={12} />
        </div>
        <div className="flex flex-col gap-2">
          <Skel w="30%" h={16} />
          <Skel h={52} />
        </div>
      </SkelCard>
      <LoadingStatus>Loading question</LoadingStatus>
    </FocusShell>
  );
}

export interface SkeletonLessonProps {
  player: Player;
  backHref: Href;
  routes?: KitRoutes;
}

/** Canvas: SkeletonLesson.d */
export function SkeletonLessonScreen({ player, backHref, routes = PREVIEW_ROUTES }: SkeletonLessonProps) {
  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={1040}
      top={<TopBar backHref={backHref} right={<Skel w="120px" h={32} round />} />}
    >
      <div className="flex flex-col gap-3">
        <Skel w="220px" h={14} />
        <div className="flex gap-2">
          <Skel w="96px" h={24} round />
          <Skel w="72px" h={24} round />
        </div>
        <Skel className="h-9 w-[85%] lg:w-[60%]" />
      </div>
      <div className="grid items-start gap-7 lg:grid-cols-[minmax(0,680px)_300px] lg:gap-14">
        <div className="flex min-w-0 flex-col gap-7">
          <SkelCard>
            <Skel w="40%" h={18} />
            <Skel w="90%" h={14} />
            <Skel w="80%" h={14} />
          </SkelCard>
          <Skel className="h-[220px] rounded-2xl lg:h-[360px]" />
          <div className="flex flex-col gap-2.5">
            <Skel h={16} />
            <Skel w="96%" h={16} />
            <Skel w="70%" h={16} />
          </div>
        </div>
        <SkelCard className="hidden gap-4 lg:flex">
          <div className="flex flex-col gap-3.5">
            {[0, 1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="flex items-center gap-2.5">
                <Skel w="8px" h={8} round />
                <Skel w="70%" h={12} />
              </div>
            ))}
          </div>
          <Skel h={120} className="rounded-xl" />
        </SkelCard>
      </div>
      <LoadingStatus>Loading lesson</LoadingStatus>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Error and interruption states                                       */
/* ------------------------------------------------------------------ */

export interface OfflineProps {
  /** NEW: Player.streakDays */
  streakDays: number;
  /** True when a typed answer is waiting to be sent. */
  answerKept: boolean;
  retryHref: Href;
  routes?: KitRoutes;
}

/** Canvas: Offline.m */
export function OfflineScreen({ streakDays, answerKept, retryHref, routes = PREVIEW_ROUTES }: OfflineProps) {
  return (
    <BareState>
      <StateScreen
        mood="sleepy"
        title="You are offline"
        text="We could not reach NextScholar. Check your Wi-Fi or mobile data, then try again."
        extra={
          <>
            {answerKept ? (
              <Callout tone="brand" icon={Check}>
                <p className="m-0">
                  <b>Your typed answer is still here.</b> Nothing was sent, so nothing was lost.
                </p>
              </Callout>
            ) : null}
            {streakDays > 0 ? (
              <StreakSafe>Your {streakDays}-day streak is safe. Practise any time before midnight.</StreakSafe>
            ) : null}
          </>
        }
        actions={
          <>
            <Button variant="primary" full icon={RefreshCw} href={retryHref}>
              Try again
            </Button>
            <Button variant="ghost" full href={routes.nav.learn}>
              Back to dashboard
            </Button>
          </>
        }
      />
    </BareState>
  );
}

export interface NotFoundProps {
  /** API: ErrorDetail.code, e.g. "content_unavailable" */
  errorCode: string;
  /** API: ErrorDetail.request_id */
  requestId: string;
  routes?: KitRoutes;
}

/** Canvas: NotFound.m */
export function NotFoundScreen({ errorCode, requestId, routes = PREVIEW_ROUTES }: NotFoundProps) {
  return (
    <BareState>
      <StateScreen
        mood="think"
        title="This page is not available"
        text="It may have moved, or the lesson is still being reviewed. Your progress is safe."
        actions={
          <Button variant="primary" full href={routes.nav.learn}>
            Go to my dashboard
          </Button>
        }
        footnote={<ErrorCode code={errorCode} requestId={requestId} center />}
      />
    </BareState>
  );
}

export interface SessionExpiredProps {
  signInHref: Href;
}

/** Canvas: SessionExpired.m */
export function SessionExpiredScreen({ signInHref }: SessionExpiredProps) {
  return (
    <BareState>
      <StateScreen
        mood="kind"
        title="Please sign in again"
        text="You were signed out to keep your account safe. Your answers and progress are saved."
        extra={<StreakSafe>Your streak, XP and badges are all saved.</StreakSafe>}
        actions={
          <Button variant="primary" full href={signInHref}>
            Sign in
          </Button>
        }
      />
    </BareState>
  );
}

export interface ServerErrorProps {
  player: Player;
  /** API: ErrorDetail.code */
  errorCode: string;
  /** API: ErrorDetail.request_id */
  requestId: string;
  retryHref: Href;
  routes?: KitRoutes;
}

/** Canvas: Error.d */
export function ServerErrorScreen({ player, errorCode, requestId, retryHref, routes = PREVIEW_ROUTES }: ServerErrorProps) {
  return (
    <AppShell active="learn" player={player} routes={routes} top={<TopBar logo />}>
      <div className="max-w-[520px]">
        <StateScreen
          mood="think"
          title="Something went wrong on our side"
          text="This is our fault, not yours. Try again in a moment. If it keeps happening, send us the code below."
          extra={<ErrorCode code={errorCode} requestId={requestId} mono />}
          inlineActions
          actions={
            <>
              <Button variant="primary" full icon={RefreshCw} href={retryHref} className="lg:w-auto">
                Try again
              </Button>
              <Button variant="secondary" full href={routes.nav.learn} className="lg:w-auto">
                Back to dashboard
              </Button>
            </>
          }
        />
      </div>
    </AppShell>
  );
}

export interface CheckpointResumeProps {
  /** e.g. "N1 checkpoint" */
  checkpointTitle: string;
  /** NEW: checkpoint attempt, answers saved so far. */
  answeredCount: number;
  /** NEW */
  questionCount: number;
  /** NEW, e.g. "Left yesterday at 20:41" (format from the attempt's last_activity_at). */
  leftAtLabel: string;
  /** NEW. What finishing today earns. */
  reward?: { streakDays: number; badgeName: string };
  continueHref: Href;
  routes?: KitRoutes;
}

/** Canvas: CheckpointResume.m */
export function CheckpointResumeScreen({
  checkpointTitle,
  answeredCount,
  questionCount,
  leftAtLabel,
  reward,
  continueHref,
  routes = PREVIEW_ROUTES,
}: CheckpointResumeProps) {
  const next = answeredCount + 1;
  return (
    <BareState>
      <StateScreen
        mood="normal"
        title="Pick up your checkpoint"
        text={`You left at question ${next} of ${questionCount}. Your first ${answeredCount} answers are saved, and nothing is marked until you finish.`}
        extra={
          <>
            <Card className="gap-2.5 p-4">
              <div className="flex items-center gap-2">
                <span className="grow text-[15px] font-semibold">{checkpointTitle}</span>
                <Tag tone="amber">
                  {answeredCount} of {questionCount} answered
                </Tag>
              </div>
              <Steps done={answeredCount} current={-1} total={questionCount} />
              <Muted className="text-[13px] leading-[18px]">{leftAtLabel}</Muted>
            </Card>
            {reward ? (
              <StreakSafe>
                Finish today to keep your streak at {reward.streakDays} and win the {reward.badgeName} badge.
              </StreakSafe>
            ) : null}
          </>
        }
        actions={
          <>
            <Button variant="primary" full iconRight={ArrowRight} href={continueHref}>
              Continue from question {next}
            </Button>
            <Button variant="ghost" full href={routes.nav.learn}>
              Back to dashboard
            </Button>
          </>
        }
      />
    </BareState>
  );
}

export interface PracticeExpiredProps {
  /** e.g. "Lesson 1" */
  lessonLabel: string;
  /** API: PracticeSessionSummary.resolved_count */
  answeredCount: number;
  /** NEW. XP earned in the closed session. */
  xpKept: number;
  newSessionHref: Href;
  lessonHref: Href;
}

/** Canvas: PracticeExpired.m. Needs a new "expired" PracticeSessionSummary.status. */
export function PracticeExpiredScreen({ lessonLabel, answeredCount, xpKept, newSessionHref, lessonHref }: PracticeExpiredProps) {
  return (
    <BareState>
      <StateScreen
        mood="normal"
        title="This practice session has closed"
        text="Sessions close after a week without activity, so your questions stay fresh. Start a new one to keep going."
        extra={
          <Callout tone="brand" icon={Check}>
            <p className="m-0">
              <b>Nothing is lost.</b> The {answeredCount} question{answeredCount === 1 ? "" : "s"} you answered still count toward{" "}
              {lessonLabel}
              {xpKept > 0 ? `, and the +${xpKept} XP you earned stays with you` : ""}.
            </p>
          </Callout>
        }
        actions={
          <>
            <Button variant="primary" full icon={RefreshCw} href={newSessionHref}>
              Start a new session
            </Button>
            <Button variant="ghost" full href={lessonHref}>
              Back to {lessonLabel}
            </Button>
          </>
        }
      />
    </BareState>
  );
}

/* ------------------------------------------------------------------ */
/* Report a problem                                                    */
/* ------------------------------------------------------------------ */

/** NEW: problem report reason codes. */
export interface ReportReason {
  value: string;
  label: string;
}

export interface ReportProblemSheetProps {
  /** API: PublicQuestionResponse.question_key, sent with the report. */
  questionKey: string;
  reasons: ReportReason[];
  selectedReason?: string;
  details?: string;
  /** NEW. Reward if the report is confirmed. */
  reward?: { xp: number; badgeName: string };
  /** NEW endpoint: POST a question report. */
  action?: FormAction;
}

/** The dialog alone, to open over any practice or checkpoint question. */
export function ReportProblemSheet({ questionKey, reasons, selectedReason, details, reward, action }: ReportProblemSheetProps) {
  const titleId = "report-problem-title";
  return (
    <Sheet titleId={titleId}>
      <h2 id={titleId} className="m-0 text-xl leading-7 font-semibold">
        Report a problem with this question
      </h2>
      <form action={action} className="flex flex-col gap-3.5">
        <input type="hidden" name="question_key" defaultValue={questionKey} />
        <fieldset className="m-0 flex flex-col border-0 p-0">
          <legend className="sr-only">What is wrong?</legend>
          {reasons.map((reason) => (
            <label
              key={reason.value}
              className={cn("group flex min-h-11 cursor-pointer items-center gap-3 rounded-lg text-[15px]", radioFocus)}
            >
              <input
                type="radio"
                name="reason"
                value={reason.value}
                defaultChecked={reason.value === selectedReason}
                className="sr-only"
              />
              <RadioDot />
              {reason.label}
            </label>
          ))}
        </fieldset>
        <TextArea id="report-details" name="details" label="Tell us more (optional)" value={details} />
        <Muted className="text-[13px] leading-[18px]">
          A former scholar checks every report within 2 days. If the question is wrong, we fix your score.
        </Muted>
        {reward ? (
          <div className="flex items-center gap-3">
            <Medal icon="target" tier="bronze" size={36} />
            <div className="flex min-w-0 flex-col gap-0.5">
              <span className="text-[15px] leading-5 font-bold">
                {reward.badgeName} badge and +{reward.xp} XP
              </span>
              <span className="text-[13px] leading-[18px] text-ns-muted">
                If we confirm the problem. Thank you for making it better.
              </span>
            </div>
          </div>
        ) : null}
        <Button type="submit" variant="primary" full>
          Send report
        </Button>
      </form>
    </Sheet>
  );
}

export interface ReportProblemProps extends ReportProblemSheetProps {
  player: Player;
  /** e.g. "Lesson 1 · Guided practice" */
  contextLabel: string;
  /** e.g. "Question 2 of 3" */
  questionLabel: string;
  done: number;
  current: number;
  total: number;
  /** The question under the dialog (MathContent in the app). */
  question: ReactNode;
  closeHref: Href;
  routes?: KitRoutes;
}

/** Canvas: ReportProblem.m */
export function ReportProblemScreen({
  player,
  contextLabel,
  questionLabel,
  done,
  current,
  total,
  question,
  closeHref,
  routes = PREVIEW_ROUTES,
  ...sheet
}: ReportProblemProps) {
  const header = (
    <QuestionHeader
      label={contextLabel}
      questionLabel={questionLabel}
      done={done}
      current={current}
      total={total}
      closeHref={closeHref}
    />
  );
  return (
    <FocusShell player={player} routes={routes} maxWidth={760} top={header} desktopTop={header}>
      <div inert className="opacity-35">
        <Card className="gap-4 p-5">{question}</Card>
      </div>
      <ReportProblemSheet {...sheet} />
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Weekly check-in                                                     */
/* ------------------------------------------------------------------ */

export interface WeeklyCheckinSheetProps {
  /** NEW. 1 to 5, null before the learner picks. */
  rating: number | null;
  confusing?: string;
  suggestion?: string;
  /** NEW. XP for sending the check-in. */
  xp: number;
  /** NEW endpoint: POST a weekly check-in. */
  action?: FormAction;
  skipHref: Href;
}

/** The dialog alone, to open over the dashboard once a week. */
export function WeeklyCheckinSheet({ rating, confusing, suggestion, xp, action, skipHref }: WeeklyCheckinSheetProps) {
  const titleId = "weekly-checkin-title";
  return (
    <Sheet titleId={titleId}>
      <form action={action} className="flex flex-col gap-3.5">
        <div className="flex flex-col gap-1">
          <Eyebrow>Weekly check-in · 1 minute</Eyebrow>
          <h2 id={titleId} className="m-0 text-xl leading-7 font-semibold">
            How helpful was NextScholar this week?
          </h2>
        </div>
        <fieldset className="m-0 flex flex-col gap-1.5 border-0 p-0">
          <legend className="sr-only">Rate from 1, not helpful, to 5, very helpful</legend>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((value) => (
              <label
                key={value}
                className={cn(
                  "flex h-12 flex-1 cursor-pointer items-center justify-center rounded-xl border-[1.5px] border-ns-line-strong bg-ns-raised text-[17px] font-bold text-ns-ink has-checked:border-ns-ink has-checked:bg-ns-ink has-checked:text-ns-on-brand",
                  radioFocus,
                )}
              >
                <input type="radio" name="rating" value={value} defaultChecked={value === rating} className="sr-only" />
                {value}
                <span className="sr-only"> of 5</span>
              </label>
            ))}
          </div>
          <div aria-hidden="true" className="flex justify-between text-xs text-ns-muted">
            <span>Not helpful</span>
            <span>Very helpful</span>
          </div>
        </fieldset>
        <TextArea id="checkin-confusing" name="confusing" label="What was confusing or annoying?" value={confusing} />
        <TextArea
          id="checkin-suggestion"
          name="suggestion"
          label="What should we add?"
          value={suggestion}
          placeholder="Anything at all"
        />
        <div className="flex flex-col gap-1.5">
          <Button type="submit" variant="primary" full>
            Send to the team · +{xp} XP
          </Button>
          <Button variant="ghost" full href={skipHref}>
            Skip this week
          </Button>
        </div>
      </form>
    </Sheet>
  );
}

export interface WeeklyCheckinProps extends WeeklyCheckinSheetProps {
  player: Player;
  /** The page under the dialog, usually the dashboard. */
  background: ReactNode;
  routes?: KitRoutes;
}

/** Canvas: WeeklyCheckin.m */
export function WeeklyCheckinScreen({ player, background, routes = PREVIEW_ROUTES, ...sheet }: WeeklyCheckinProps) {
  return (
    <AppShell
      active="learn"
      player={player}
      routes={routes}
      top={<TopBar logo right={<MiniChips player={player} routes={routes} />} />}
    >
      <div inert className="flex flex-col gap-4 opacity-35">
        {background}
      </div>
      <WeeklyCheckinSheet {...sheet} />
    </AppShell>
  );
}
