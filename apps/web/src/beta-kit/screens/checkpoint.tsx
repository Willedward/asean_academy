/**
 * Unit checkpoint and lesson recheck screens.
 *
 * The learning API has no checkpoint or recheck endpoints yet. Today it only
 * exposes CourseUnitMap.checkpoint_question_count and
 * CourseUnitMap.checkpoint_available, plus LessonProgressResponse.checkpoint_passed.
 * Everything else in these props is NEW backend work (see HANDOFF.md).
 */
import Link from "next/link";
import { useId, type ReactNode } from "react";
import {
  AlertCircle,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronLeft,
  Clock,
  Lightbulb,
  List,
  RotateCcw,
  RotateCw,
  Target,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { GameIcon } from "../components/icons";
import { LessonStateTag } from "../components/lesson-row";
import { ComboChip, Confetti, Feedback, Medal, MascotSays, RewardLine, StreakChip, XpNote, XpPill, XpTag } from "../components/rewards";
import {
  Bar,
  Button,
  Callout,
  Card,
  Eyebrow,
  H1,
  H2,
  H3,
  IconCircle,
  IconButton,
  Muted,
  Sheet,
  Steps,
  Tag,
  focusRing,
} from "../components/ui";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import { FocusShell, FooterBar, TopBar } from "../shell/app-shell";
import type { BadgeIcon, Href, LessonUiState, Player, Stars, Tier, XpLine } from "../types";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

/** NEW. The badge a checkpoint pass unlocks. */
export interface CheckpointBadge {
  name: string;
  icon: BadgeIcon;
  tier: Tier;
  /** NEW. "Only 4 of 18 beta students have it." Omit to hide. */
  holders?: { count: number; of: number };
}

/** What the checkpoint intro needs to know about the unit's checkpoint. */
export interface CheckpointInfo {
  /** Display code, e.g. "N1". API: derived from CourseUnitMap.stable_key / title. */
  unitCode: string;
  /** API: CourseUnitMap.lessons.length */
  lessonCount: number;
  /** API: CourseUnitMap.checkpoint_question_count */
  questionCount: number;
  /** NEW */
  minutes: number;
  /** NEW. Right answers needed to pass. */
  passMark: number;
  /** NEW. Bonus for passing (mastering the unit). */
  rewardXp: number;
  /** NEW. XP per right answer, added when the checkpoint is marked. */
  xpPerRight: number;
  /** NEW */
  badge: CheckpointBadge;
}

/** One checkpoint or recheck question. Single-part questions only. */
export interface CheckpointQuestion {
  /** API: PublicQuestionResponse.primary_outcome, e.g. "1.7" */
  outcome: string;
  /** API: PublicQuestionResponse.total_marks */
  marks: number;
  /** API: PublicQuestionResponse.stem. Pass the app's <MathContent />. */
  stem: ReactNode;
}

/** NEW. One tile on the "check before you submit" grid. */
export interface CheckpointAnswerTile {
  /** 1-based question number. */
  position: number;
  /** NEW. The learner saved an answer for this question. */
  answered: boolean;
  href: Href;
}

/** How an outcome or lesson ended up after a checkpoint or recheck. */
export type OutcomeState = LessonUiState | "needs_review";

/** One row of the "By outcome" / "N1 by lesson" lists. */
export interface OutcomeResult {
  /** API: CourseLessonMap.outcomes[0], e.g. "1.5" */
  code: string;
  /** API: CourseLessonMap.title */
  title: string;
  /** API: LessonProgressResponse.state mapped with toLessonUiState(); "needs_review" is NEW. */
  state: OutcomeState;
}

/** A lesson covered by a recheck. */
export interface RecheckLesson {
  /** API: CourseLessonMap.position */
  position: number;
  /** API: CourseLessonMap.title */
  title: string;
}

/** NEW. Everything about a recheck quiz before it starts. */
export interface RecheckInfo {
  lessons: RecheckLesson[];
  questionCount: number;
  minutes: number;
  passMark: number;
  /** When the lessons reached proficient, e.g. "2 weeks ago". */
  proficientSince: string;
  /** Bonus XP for passing. */
  rewardXp: number;
  /** Stars each lesson has after a pass (3 = mastered). */
  starsOnPass: Stars;
}

/** NEW. One question result on the recheck results screen. */
export interface RecheckQuestionResult {
  position: number;
  right: boolean;
  xp: number;
}

/* ------------------------------------------------------------------ */
/* Copy helpers                                                        */
/* ------------------------------------------------------------------ */

function joinList(items: (string | number)[]): string {
  if (items.length <= 1) return String(items[0] ?? "");
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

function lessonsLabel(lessons: RecheckLesson[]): string {
  const positions = lessons.map((lesson) => lesson.position);
  return `${positions.length === 1 ? "Lesson" : "Lessons"} ${joinList(positions)}`;
}

function questionsLabel(positions: number[]): string {
  return `${positions.length === 1 ? "Question" : "Questions"} ${joinList(positions)}`;
}

function ordinal(n: number): string {
  const suffix = n % 10 === 1 && n % 100 !== 11 ? "st" : n % 10 === 2 && n % 100 !== 12 ? "nd" : n % 10 === 3 && n % 100 !== 13 ? "rd" : "th";
  return `${n}${suffix}`;
}

function plural(count: number, one: string, many: string = `${one}s`): string {
  return count === 1 ? one : many;
}

function firstName(player: Player): string {
  return player.displayName.split(" ")[0] ?? player.displayName;
}

const TIER_LABEL: Record<Tier, string> = { gold: "Gold", silver: "Silver", bronze: "Bronze" };

/* ------------------------------------------------------------------ */
/* Shared pieces (exported for reuse, e.g. checkpoint-resume)          */
/* ------------------------------------------------------------------ */

type RuleIcon = "list" | "clock" | "bulb" | "refresh" | "target";

const RULE_ICON = { list: List, clock: Clock, bulb: Lightbulb, refresh: RotateCw, target: Target };

/** "Before you start" rules card: icon circle plus one line each. */
export function RuleList({ rules }: { rules: { icon: RuleIcon; text: string }[] }) {
  return (
    <Card className="gap-3.5">
      <ul className="m-0 flex list-none flex-col gap-3.5 p-0">
        {rules.map((rule) => (
          <li key={rule.text} className="flex items-center gap-3">
            <IconCircle icon={RULE_ICON[rule.icon]} tone="brand" size={36} />
            <span className="text-base leading-6 text-ns-ink">{rule.text}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

/** Lesson state tag, plus the checkpoint-only "Needs review" state. */
export function OutcomeStateTag({ state }: { state: OutcomeState }) {
  if (state === "needs_review") {
    return (
      <Tag tone="danger" icon={AlertCircle}>
        Needs review
      </Tag>
    );
  }
  return <LessonStateTag state={state} />;
}

/** Outcome code, title and state tag, one row each. */
export function OutcomeList({ title, rows }: { title: string; rows: OutcomeResult[] }) {
  return (
    <Card className="gap-4">
      <H3>{title}</H3>
      <ul className="m-0 flex list-none flex-col gap-3.5 p-0">
        {rows.map((row) => (
          <li key={row.code} className="flex items-center gap-2.5">
            <span className="w-[30px] shrink-0 text-[13px] font-bold text-ns-muted tabular-nums">{row.code}</span>
            <span className="min-w-0 grow text-[15px] leading-[22px] font-semibold">{row.title}</span>
            <OutcomeStateTag state={row.state} />
          </li>
        ))}
      </ul>
    </Card>
  );
}

/** Amber "Pass to win" prize card. */
function PrizeCard({ xp, children }: { xp: number; children: ReactNode }) {
  return (
    <Card tone="amber" className="gap-3">
      <div className="flex items-center justify-between gap-2">
        <H3>Pass to win</H3>
        <XpPill xp={xp} />
      </div>
      {children}
    </Card>
  );
}

/** Amber "You won +170" card with the tally lines. */
function YouWonCard({
  lines,
  xpTags,
  children,
}: {
  lines: XpLine[];
  /** Show each line as "+50 XP" with a bolt instead of a plain "+50". */
  xpTags?: boolean;
  children?: ReactNode;
}) {
  const total = lines.reduce((sum, line) => sum + line.xp, 0);
  return (
    <Card tone="amber" className={cn("shadow-ns-sm", xpTags ? "gap-2.5" : "gap-3")}>
      <div className="flex items-center justify-between gap-2">
        <H3>You won</H3>
        <span
          className={cn(
            "inline-flex animate-ns-pop items-center gap-1 font-black text-ns-amber-text tabular-nums [animation-delay:.4s]",
            xpTags ? "text-2xl" : "text-[26px]",
          )}
        >
          <GameIcon name="bolt" size={xpTags ? 22 : 24} className="text-ns-amber" />+{total}
        </span>
      </div>
      <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
        {lines.map((line) => (
          <li key={line.label} className="flex items-center gap-2">
            {xpTags ? (
              <>
                <span className="grow text-sm leading-5 text-ns-muted">{line.label}</span>
                <XpTag xp={line.xp} size={14} />
              </>
            ) : (
              <>
                <span className="grow text-[15px]">{line.label}</span>
                <span className="text-[15px] font-extrabold text-ns-amber-text tabular-nums">+{line.xp}</span>
              </>
            )}
          </li>
        ))}
      </ul>
      {children}
    </Card>
  );
}

/** "Your answer" box. Uncontrolled; the app owns saving. */
function AnswerField({
  value,
  hint,
  placeholder,
  status = "editing",
}: {
  value?: string;
  hint?: string;
  placeholder?: string;
  status?: "editing" | "right" | "wrong";
}) {
  const id = useId();
  const hintId = `${id}-hint`;
  const locked = status !== "editing";
  return (
    <Card>
      <div className="flex min-w-0 flex-col gap-2">
        <label htmlFor={id} className="text-[15px] leading-5 font-bold">
          Your answer
        </label>
        <input
          id={id}
          name="answer"
          type="text"
          inputMode="text"
          autoComplete="off"
          defaultValue={value}
          placeholder={placeholder}
          readOnly={locked}
          aria-invalid={status === "wrong" ? true : undefined}
          aria-describedby={hint ? hintId : undefined}
          className={cn(
            "h-[52px] w-full min-w-0 rounded-lg border-[1.5px] px-4 font-ns-math text-xl text-ns-ink",
            status === "right" && "border-ns-success bg-ns-sunken",
            status === "wrong" && "border-ns-danger bg-ns-sunken",
            status === "editing" && "border-ns-line-strong bg-ns-raised",
            focusRing,
          )}
        />
        {hint ? (
          <span id={hintId} className="text-sm leading-5 text-ns-muted">
            {hint}
          </span>
        ) : null}
      </div>
    </Card>
  );
}

/** Question stem card with outcome tags and marks. */
function StemCard({ tags, marks, stem }: { tags: string[]; marks?: number; stem: ReactNode }) {
  return (
    <Card className="gap-3.5">
      <div className="flex flex-wrap items-center gap-2">
        {tags.map((tag) => (
          <Tag key={tag}>{tag}</Tag>
        ))}
        {marks !== undefined ? (
          <span className="ml-auto text-[13px] text-ns-muted">
            {marks} {plural(marks, "mark")}
          </span>
        ) : null}
      </div>
      <div className="text-lg leading-7 text-ns-ink">{stem}</div>
    </Card>
  );
}

/** Checkpoint question header: like QuestionHeader, with "Save and leave" instead of a close button. */
function CheckpointQuestionHeader({
  label,
  questionLabel,
  done,
  current,
  total,
  right,
}: {
  label: string;
  questionLabel: string;
  done: number;
  current: number;
  total: number;
  right: ReactNode;
}) {
  return (
    <header className="flex shrink-0 flex-col gap-2 border-b border-ns-line bg-ns-surface px-4 pt-2 pb-3 lg:border-b-0 lg:px-0 lg:pt-0 lg:pb-4">
      <div className="flex min-h-11 items-center gap-2">
        <div className="flex min-w-0 grow flex-col">
          <span className="text-xs font-semibold text-ns-muted">{label}</span>
          <span className="text-base font-bold lg:text-[28px] lg:leading-9">{questionLabel}</span>
        </div>
        {right}
      </div>
      <Steps done={done} current={current} total={total} />
    </header>
  );
}

/** 4 x 2 grid of question tiles; blanks are dashed amber. */
export function AnswerGrid({ answers }: { answers: CheckpointAnswerTile[] }) {
  return (
    <ul className="m-0 grid list-none grid-cols-4 gap-2.5 p-0 lg:grid-cols-8">
      {answers.map((tile) => (
        <li key={tile.position}>
          <Link
            href={tile.href}
            aria-label={`Question ${tile.position}, ${tile.answered ? "answered" : "no answer"}`}
            className={cn(
              "flex h-16 flex-col items-center justify-center gap-0.5 rounded-xl border-[1.5px] no-underline",
              tile.answered
                ? "border-ns-brand-soft bg-ns-brand-soft text-ns-ink hover:border-ns-line-strong"
                : "border-dashed border-ns-amber bg-ns-amber-soft text-ns-amber-text",
              focusRing,
            )}
          >
            <span className="text-lg leading-6 font-bold">{tile.position}</span>
            {tile.answered ? <Check size={16} aria-hidden /> : <AlertCircle size={16} aria-hidden />}
          </Link>
        </li>
      ))}
    </ul>
  );
}

function AnswerLegend() {
  return (
    <div className="flex flex-wrap items-center gap-4 text-[13px] leading-[18px] text-ns-muted">
      <span className="inline-flex items-center gap-1.5">
        <span aria-hidden="true" className="size-3.5 rounded bg-ns-brand-soft" />
        Answered
      </span>
      <span className="inline-flex items-center gap-1.5">
        <span aria-hidden="true" className="size-3.5 rounded border-[1.5px] border-dashed border-ns-amber bg-ns-amber-soft" />
        No answer yet
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* 1. Checkpoint intro                                                 */
/* ------------------------------------------------------------------ */

export interface CheckpointIntroProps {
  player: Player;
  checkpoint: CheckpointInfo;
  /** Starts (or creates) the checkpoint attempt. NEW endpoint. */
  startHref: Href;
  /** Back to the unit page. */
  backHref: Href;
  routes?: KitRoutes;
}

/** Canvas: CheckpointIntro.m, CheckpointIntro.d */
export function CheckpointIntroScreen({ player, checkpoint, startHref, backHref, routes = PREVIEW_ROUTES }: CheckpointIntroProps) {
  const { unitCode, lessonCount, questionCount, minutes, passMark, rewardXp, xpPerRight, badge } = checkpoint;
  const badgeSub = `${TIER_LABEL[badge.tier]}.${badge.holders ? ` Only ${badge.holders.count} of ${badge.holders.of} beta students have it.` : ""}`;

  return (
    <FocusShell player={player} routes={routes} maxWidth={600} top={<TopBar title="Checkpoint" backHref={backHref} />}>
      <div className="flex flex-col gap-2.5">
        <Eyebrow>Unit {unitCode} checkpoint</Eyebrow>
        <H1 className="lg:text-[30px] lg:leading-[38px]">Show what you have learned</H1>
        <Muted className="text-base leading-6">
          All {lessonCount} lessons are proficient, so the checkpoint is open. Passing it marks the whole unit as mastered.
        </Muted>
      </div>

      <RuleList
        rules={[
          { icon: "list", text: `${questionCount} questions from all ${lessonCount} lessons.` },
          { icon: "clock", text: `About ${minutes} minutes. There is no timer.` },
          { icon: "bulb", text: "No hints during the checkpoint." },
          { icon: "refresh", text: "Each answer is saved. You can leave and come back." },
          { icon: "target", text: `Get ${passMark} of ${questionCount} right to master ${unitCode}.` },
        ]}
      />

      <Callout tone="brand" icon={RotateCcw}>
        Anything you miss becomes a short review, not a fail. You can take the checkpoint again after reviewing.
      </Callout>

      <PrizeCard xp={rewardXp}>
        <RewardLine icon={<Medal icon={badge.icon} tier={badge.tier} size={40} />} title={`${badge.name} badge`} sub={badgeSub} />
        <RewardLine
          icon={<GameIcon name="bolt" size={20} className="text-ns-amber" />}
          title={`+${xpPerRight} XP for each right answer`}
          sub="Added when you finish. Nothing is taken for wrong ones."
        />
        <RewardLine
          icon={<GameIcon name="star" size={20} className="text-ns-gold" />}
          title={`Every ${unitCode} lesson turns gold`}
          sub={`3 stars on all ${lessonCount} lessons.`}
        />
      </PrizeCard>

      <MascotSays mood="happy" pose="cheer" outfit={player.equippedOutfit} size={60}>
        You have got this, {firstName(player)}. No timer, no stress.
      </MascotSays>

      <Button variant="primary" full href={startHref} iconRight={ArrowRight}>
        Start checkpoint
      </Button>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* 2. Checkpoint question                                              */
/* ------------------------------------------------------------------ */

export interface CheckpointActiveProps {
  player: Player;
  /** e.g. "N1" */
  unitCode: string;
  /** 1-based. API (practice today): NextQuestionResponse.position. NEW for checkpoints. */
  position: number;
  /** API: CourseUnitMap.checkpoint_question_count */
  questionCount: number;
  question: CheckpointQuestion;
  /** NEW. The learner's saved answer, if any. */
  answer?: string;
  /** e.g. "Write the number only." Could come from QuestionPartResponse.input_placeholder. */
  answerHint?: string;
  /** NEW */
  xpPerRight: number;
  /** Saves and returns to the unit. NEW endpoint. */
  saveAndLeaveHref: Href;
  /** Previous question. Omit on question 1. */
  previousHref?: Href;
  /** Saves the answer and moves on (the last question goes to the review grid). NEW endpoint. */
  nextHref: Href;
  routes?: KitRoutes;
}

/** Canvas: CheckpointActive.m */
export function CheckpointActiveScreen({
  player,
  unitCode,
  position,
  questionCount,
  question,
  answer,
  answerHint,
  xpPerRight,
  saveAndLeaveHref,
  previousHref,
  nextHref,
  routes = PREVIEW_ROUTES,
}: CheckpointActiveProps) {
  const header = (
    <CheckpointQuestionHeader
      label={`${unitCode} checkpoint · no hints`}
      questionLabel={`Question ${position} of ${questionCount}`}
      done={position - 1}
      current={position - 1}
      total={questionCount}
      right={
        <>
          <StreakChip small days={player.streakDays} href={routes.streak} />
          <Button variant="ghost" size="sm" href={saveAndLeaveHref} className="h-11 px-3">
            Save and leave
          </Button>
        </>
      }
    />
  );

  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={720}
      top={header}
      desktopTop={header}
      footer={
        <FooterBar>
          <div className="mx-auto flex w-full max-w-[720px] gap-2">
            <Button variant="secondary" href={previousHref} disabled={!previousHref} icon={ChevronLeft}>
              Back
            </Button>
            <Button variant="primary" full href={nextHref} iconRight={ArrowRight} className="grow">
              Save and next
            </Button>
          </div>
        </FooterBar>
      }
    >
      <StemCard tags={[`Outcome ${question.outcome}`]} marks={question.marks} stem={question.stem} />
      <AnswerField value={answer} hint={answerHint} />
      <div className="flex flex-col gap-3">
        <Muted>Answers are checked at the end. You will not see right or wrong until you finish.</Muted>
        <XpNote>Each right answer: +{xpPerRight} XP, added when you finish</XpNote>
      </div>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* 3. Check before you submit (and the submit sheet)                   */
/* ------------------------------------------------------------------ */

export interface CheckpointReviewProps {
  player: Player;
  unitCode: string;
  /** NEW. One tile per question, in order. */
  answers: CheckpointAnswerTile[];
  /** NEW */
  xpPerRight: number;
  /** "reviewing" shows the grid; "confirm" opens the submit sheet over it. */
  state: "reviewing" | "confirm";
  /** Opens the confirm sheet (state "confirm"). */
  confirmHref: Href;
  /** Final submit. NEW endpoint. */
  submitHref: Href;
  /** Usually the last question. */
  back: { label: string; href: Href };
  routes?: KitRoutes;
}

/** Canvas: CheckpointReview.m, CheckpointSubmit.m (state "confirm") */
export function CheckpointReviewScreen({
  player,
  unitCode,
  answers,
  xpPerRight,
  state,
  confirmHref,
  submitHref,
  back,
  routes = PREVIEW_ROUTES,
}: CheckpointReviewProps) {
  const titleId = useId();
  const blanks = answers.filter((tile) => !tile.answered);
  const blankNumbers = blanks.map((tile) => tile.position);
  const firstBlank = blanks[0];
  const top = (
    <TopBar title={`${unitCode} checkpoint`} right={<StreakChip small days={player.streakDays} href={routes.streak} />} />
  );

  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={640}
      top={top}
      className="gap-5 lg:gap-6"
      footer={
        <FooterBar>
          <div className="mx-auto flex w-full max-w-[640px] flex-col gap-2">
            <Button variant="primary" full href={confirmHref}>
              Submit checkpoint
            </Button>
            <Button variant="ghost" full href={back.href} icon={ChevronLeft}>
              {back.label}
            </Button>
          </div>
        </FooterBar>
      }
    >
      <div className="flex flex-col gap-1.5">
        <div className="hidden lg:block">
          <Eyebrow>{unitCode} checkpoint</Eyebrow>
        </div>
        <H1 className="text-2xl leading-[30px]">Check before you submit</H1>
        <Muted className="text-[15px] leading-[22px]">No time limit. Go back to any question you want.</Muted>
      </div>

      <AnswerGrid answers={answers} />
      <AnswerLegend />

      {blanks.length > 0 ? (
        <Callout tone="amber" icon={AlertCircle}>
          <b className="text-[15px] leading-[22px] text-ns-amber-text">
            {questionsLabel(blankNumbers)} {plural(blanks.length, "has", "have")} no answer.
          </b>
          <span>
            A blank counts as not right. A best guess is worth a try: a right one is +{xpPerRight} XP, a wrong one costs nothing.
          </span>
        </Callout>
      ) : null}

      {state === "confirm" ? (
        <Sheet titleId={titleId}>
          <H2 className="lg:text-[22px]">
            <span id={titleId}>
              {blanks.length > 0
                ? `Submit with ${blanks.length} ${plural(blanks.length, "question")} blank?`
                : "Submit your checkpoint?"}
            </span>
          </H2>
          <Muted className="text-[15px] leading-[22px]">
            {blanks.length > 0
              ? `${questionsLabel(blankNumbers)} ${plural(blanks.length, "has", "have")} no answer, so ${plural(blanks.length, "it", "they")} will count as not right. `
              : ""}
            You cannot change answers after you submit.
          </Muted>
          <div className="flex flex-col gap-2">
            <Button variant="primary" full href={submitHref}>
              Submit checkpoint
            </Button>
            {firstBlank ? (
              <Button variant="secondary" full href={firstBlank.href}>
                Go to question {firstBlank.position}
              </Button>
            ) : (
              <Button variant="secondary" full href={back.href}>
                {back.label}
              </Button>
            )}
          </div>
        </Sheet>
      ) : null}
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* 4. Marking                                                          */
/* ------------------------------------------------------------------ */

export interface CheckpointMarkingProps {
  player: Player;
  unitCode: string;
  /** NEW. Answers marked so far. */
  checked: number;
  /** API: CourseUnitMap.checkpoint_question_count */
  total: number;
  /** NEW. Answers saved at submit. */
  answersSaved: number;
  /** NEW. Local time label, e.g. "10:42". */
  submittedAt: string;
  dashboardHref: Href;
  routes?: KitRoutes;
}

/** Canvas: CheckpointMarking.m */
export function CheckpointMarkingScreen({
  player,
  unitCode,
  checked,
  total,
  answersSaved,
  submittedAt,
  dashboardHref,
  routes = PREVIEW_ROUTES,
}: CheckpointMarkingProps) {
  const pct = total > 0 ? (checked / total) * 100 : 0;
  const checklist = [
    `Submitted at ${submittedAt}`,
    answersSaved === total ? `All ${total} answers saved` : `${answersSaved} of ${total} answers saved`,
    "Your XP and any new badge are on the way",
  ];
  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={600}
      top={<TopBar title={`${unitCode} checkpoint`} right={<StreakChip small days={player.streakDays} href={routes.streak} />} />}
    >
      <div className="flex flex-col gap-3.5 pt-8 lg:pt-0">
        <div className="animate-ns-float self-start">
          <Hornbill size={110} mood="think" branch={false} />
        </div>
        <H1>Submitted. Checking your answers.</H1>
        <Muted className="text-base leading-6">
          This usually takes under a minute. You can close this page. Your results will wait on your dashboard.
        </Muted>
      </div>

      <div role="status" aria-label={`Checking ${checked} of ${total} answers`} className="flex flex-col gap-2">
        <Bar pct={pct} height={10} fill="success" />
        <span className="text-sm text-ns-muted">
          {checked} of {total} checked
        </span>
      </div>

      <Card>
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {checklist.map((line) => (
            <li key={line} className="flex items-start gap-2.5">
              <CheckCircle2 size={20} aria-hidden className="mt-px shrink-0 text-ns-success" />
              <span className="text-[15px] leading-[22px] text-ns-ink">{line}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Button variant="secondary" full href={dashboardHref}>
        Back to dashboard
      </Button>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* 5. Checkpoint result (passed)                                       */
/* ------------------------------------------------------------------ */

export interface CheckpointResultProps {
  player: Player;
  unitCode: string;
  /** NEW. Right answers. */
  right: number;
  /** API: CourseUnitMap.checkpoint_question_count */
  total: number;
  /** NEW */
  passMark: number;
  /** NEW. e.g. [{ label: "Unit mastered", xp: 100 }, { label: "7 right answers", xp: 70 }]. The total is summed. */
  xpLines: XpLine[];
  /** NEW. Badge unlocked by this pass. */
  badge?: { name: string; icon: BadgeIcon; tier: Tier };
  /** NEW. Set when the XP took the learner up a level. */
  newLevel?: number;
  /** One row per outcome. "needs_review" marks the ones missed. */
  outcomes: OutcomeResult[];
  /** NEW. The first missed idea and where to refresh it. */
  review?: { title: string; body: ReactNode; lessonLabel: string; href: Href };
  /** Unit mastered celebration. */
  claimHref: Href;
  /** NEW. Marked answers. */
  answersHref: Href;
  backHref: Href;
  routes?: KitRoutes;
}

/** Canvas: CheckpointResult.m, CheckpointResult.d */
export function CheckpointResultScreen({
  player,
  unitCode,
  right,
  total,
  passMark,
  xpLines,
  badge,
  newLevel,
  outcomes,
  review,
  claimHref,
  answersHref,
  backHref,
  routes = PREVIEW_ROUTES,
}: CheckpointResultProps) {
  const toReview = outcomes.filter((row) => row.state === "needs_review").length;
  const reviewSentence =
    toReview === 0 ? "" : toReview === 1 ? " One idea needs a quick review." : ` ${toReview} ideas need a quick review.`;

  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={640}
      overlay={<Confetti count={36} seed={12} />}
      top={<TopBar title="Checkpoint results" backHref={backHref} />}
    >
      <div className="flex flex-col items-center gap-2 text-center">
        <div aria-hidden="true" className="relative h-[170px] w-[200px] animate-ns-pop">
          <GameIcon name="trophy" size={140} className="absolute top-0 left-5 text-ns-gold" />
          <Hornbill size={96} mood="happy" pose="cheer" outfit="cap" branch={false} className="absolute -right-2.5 bottom-0" />
        </div>
        <Eyebrow>{unitCode} checkpoint · passed</Eyebrow>
        <H1 className="lg:text-[30px] lg:leading-[38px]">
          {right} of {total}. {unitCode} is mastered!
        </H1>
        <Muted className="text-base leading-6">
          You needed {passMark}. Well done.{reviewSentence}
        </Muted>
      </div>

      <YouWonCard lines={xpLines}>
        {badge || newLevel ? (
          <div className="flex items-center gap-3">
            {badge ? (
              <>
                <Medal icon={badge.icon} tier={badge.tier} size={44} pop />
                <div className="flex min-w-0 grow flex-col gap-0.5">
                  <Eyebrow>New badge</Eyebrow>
                  <b className="text-base">{badge.name}</b>
                </div>
              </>
            ) : (
              <span className="grow" />
            )}
            {newLevel ? <Tag tone="amber">Level {newLevel}!</Tag> : null}
          </div>
        ) : null}
      </YouWonCard>

      <OutcomeList title="By outcome" rows={outcomes} />

      {review ? (
        <Callout tone="amber" icon={RotateCcw}>
          <b className="text-[15px] leading-[22px]">{review.title}</b>
          <div>{review.body}</div>
        </Callout>
      ) : null}

      <div className="flex flex-col gap-2">
        <Button variant="primary" full href={claimHref} iconRight={ArrowRight}>
          Claim my trophy
        </Button>
        {review ? (
          <Button variant="secondary" full href={review.href} icon={RotateCcw}>
            Review {review.lessonLabel}
          </Button>
        ) : null}
        <Button variant="ghost" full href={answersHref}>
          See my answers
        </Button>
      </div>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* 6. Recheck intro                                                    */
/* ------------------------------------------------------------------ */

export interface RecheckIntroProps {
  player: Player;
  recheck: RecheckInfo;
  startHref: Href;
  backHref: Href;
  routes?: KitRoutes;
}

/** Canvas: QuizIntro.m */
export function RecheckIntroScreen({ player, recheck, startHref, backHref, routes = PREVIEW_ROUTES }: RecheckIntroProps) {
  const { lessons, questionCount, minutes, passMark, proficientSince, rewardXp, starsOnPass } = recheck;
  const label = lessonsLabel(lessons);
  const which = lessons.length === 1 ? "the lesson" : lessons.length === 2 ? "both lessons" : `all ${lessons.length} lessons`;
  const these = lessons.length === 1 ? "this lesson" : "these lessons";

  return (
    <FocusShell player={player} routes={routes} maxWidth={600} top={<TopBar title="Recheck" backHref={backHref} />}>
      <div className="flex flex-col gap-2.5">
        <Eyebrow>Recheck</Eyebrow>
        <H1 className="lg:text-[30px] lg:leading-[38px]">
          {questionCount} quick questions on {label}
        </H1>
        <Muted className="text-base leading-6">
          You got {these} to proficient {proficientSince}. Getting them right again now shows the idea has stuck.
        </Muted>
      </div>

      <RuleList
        rules={[
          { icon: "list", text: `${questionCount} questions from ${label}.` },
          { icon: "clock", text: `About ${minutes} minutes. No timer.` },
          { icon: "bulb", text: "No hints. You see right or wrong after each one." },
          { icon: "target", text: `Get ${passMark} of ${questionCount} right to mark ${which} mastered.` },
        ]}
      />

      <Card className="gap-3.5">
        <H3>What changes if you pass</H3>
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {lessons.map((lesson) => (
            <li key={lesson.position} className="flex flex-wrap items-center gap-2">
              <span className="w-full text-[15px] leading-[22px] font-semibold">
                Lesson {lesson.position} · {lesson.title}
              </span>
              <LessonStateTag state="proficient" />
              <ArrowRight size={16} aria-hidden className="text-ns-muted" />
              <span className="sr-only">becomes</span>
              <LessonStateTag state="mastered" />
            </li>
          ))}
        </ul>
      </Card>

      <Callout tone="brand" icon={RotateCcw}>
        Not passing is fine. The {lessons.length === 1 ? "lesson stays" : "lessons stay"} proficient and the questions you miss go to your
        Try again list.
      </Callout>

      <PrizeCard xp={rewardXp}>
        <RewardLine
          icon={<GameIcon name="star" size={20} className="text-ns-gold" />}
          title={`${ordinal(starsOnPass)} star on ${label}`}
          sub={`${lessons.length === 1 ? "The lesson turns" : lessons.length === 2 ? "Both lessons turn" : "All the lessons turn"} gold on your unit map.`}
        />
      </PrizeCard>

      <Button variant="primary" full href={startHref} iconRight={ArrowRight}>
        Start recheck · +{rewardXp} XP
      </Button>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* 7. Recheck question                                                 */
/* ------------------------------------------------------------------ */

export interface RecheckActiveProps {
  player: Player;
  /** 1-based question number. NEW */
  position: number;
  questionCount: number;
  question: CheckpointQuestion & {
    /** Lesson the question comes from. API: CourseLessonMap.position for the question's outcome. */
    lessonPosition: number;
  };
  /** "answering" before Check answer; "right" or "wrong" after it. */
  state: "answering" | "right" | "wrong";
  answer?: string;
  answerHint?: string;
  /** Worked explanation shown with the right/wrong panel. API: SolutionPartResponse.steps, via <MathContent />. */
  explanation?: ReactNode;
  /** NEW. XP for this answer when right. */
  xp: number;
  /** NEW. Right answers in a row, including this one. The chip shows from 2. */
  combo?: number;
  /** Leave the recheck. Place is saved. */
  closeHref: Href;
  /** "Check answer" while answering, "Next question" after. */
  actionHref: Href;
  routes?: KitRoutes;
}

/** Canvas: QuizActive.m */
export function RecheckActiveScreen({
  player,
  position,
  questionCount,
  question,
  state,
  answer,
  answerHint,
  explanation,
  xp,
  combo = 0,
  closeHref,
  actionHref,
  routes = PREVIEW_ROUTES,
}: RecheckActiveProps) {
  const answered = state !== "answering";
  const header = (
    <CheckpointQuestionHeader
      label="Recheck · no hints"
      questionLabel={`Question ${position} of ${questionCount}`}
      done={position - 1}
      current={position - 1}
      total={questionCount}
      right={
        <>
          {state === "right" && combo >= 2 ? <ComboChip label={`${combo} IN A ROW`} /> : null}
          <IconButton icon={X} label="Leave recheck. Your place is saved" href={closeHref} />
        </>
      }
    />
  );

  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={720}
      top={header}
      desktopTop={header}
      footer={
        <FooterBar>
          <div className="mx-auto w-full max-w-[720px]">
            <Button variant="primary" full href={actionHref} iconRight={answered ? ArrowRight : undefined}>
              {answered ? "Next question" : "Check answer"}
            </Button>
          </div>
        </FooterBar>
      }
    >
      {state === "right" ? (
        <Feedback kind="right" xp={xp}>
          {explanation}
        </Feedback>
      ) : null}
      {state === "wrong" ? (
        <Feedback kind="wrong" note="It goes to your Try again list.">
          {explanation}
        </Feedback>
      ) : null}
      <StemCard tags={[`Lesson ${question.lessonPosition}`, `Outcome ${question.outcome}`]} stem={question.stem} />
      <AnswerField value={answer} hint={answered ? undefined : answerHint} status={state === "answering" ? "editing" : state} />
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* 8. Recheck result (passed)                                          */
/* ------------------------------------------------------------------ */

export interface RecheckResultProps {
  player: Player;
  /** The rechecked lessons. */
  lessons: RecheckLesson[];
  /** NEW */
  right: number;
  total: number;
  /** NEW. Stars on the rechecked lessons now. */
  stars: Stars;
  /** NEW. e.g. [{ label: "Recheck passed", xp: 50 }, { label: "4 right answers", xp: 40 }] */
  xpLines: XpLine[];
  /** NEW */
  questions: RecheckQuestionResult[];
  unitCode: string;
  /** Every lesson in the unit after the recheck. */
  unitLessons: OutcomeResult[];
  unitHref: Href;
  /** NEW. Marked answers. */
  answersHref: Href;
  backHref: Href;
  routes?: KitRoutes;
}

/** Canvas: QuizResult.m, QuizResult.d */
export function RecheckResultScreen({
  player,
  lessons,
  right,
  total,
  stars,
  xpLines,
  questions,
  unitCode,
  unitLessons,
  unitHref,
  answersHref,
  backHref,
  routes = PREVIEW_ROUTES,
}: RecheckResultProps) {
  const label = lessonsLabel(lessons);
  const missed = questions.filter((q) => !q.right).map((q) => q.position);

  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={600}
      overlay={<Confetti count={28} seed={21} />}
      top={<TopBar title="Recheck results" backHref={backHref} />}
    >
      <div className="flex flex-col gap-2.5">
        <div className="flex items-center gap-3">
          <Hornbill size={96} mood="happy" pose="cheer" outfit={player.equippedOutfit ?? "scarf"} branch={false} />
          <div className="flex flex-col gap-1.5">
            <span role="img" aria-label={`${stars} of 3 stars`} className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <span key={i} className="inline-flex animate-ns-pop" style={{ animationDelay: `${0.2 + i * 0.2}s` }}>
                  <GameIcon name="star" size={34} className={i < stars ? "text-ns-gold" : "text-ns-line"} />
                </span>
              ))}
            </span>
            <span className="text-[13px] leading-[18px] font-bold text-ns-amber-text">
              {ordinal(stars)} star on {label}
            </span>
          </div>
        </div>
        <Eyebrow>Recheck done</Eyebrow>
        <H1 className="lg:text-[30px] lg:leading-[38px]">
          {right} of {total}. {label} {lessons.length === 1 ? "is" : "are"} mastered!
        </H1>
      </div>

      <YouWonCard lines={xpLines} xpTags />

      <Card>
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {questions.map((q) => (
            <li key={q.position} className="flex items-center gap-2">
              <span className="grow text-[15px] font-semibold">Question {q.position}</span>
              {q.right ? (
                <Tag tone="success" icon={Check}>
                  Right
                </Tag>
              ) : (
                <Tag tone="danger" icon={X}>
                  Not right
                </Tag>
              )}
              <span
                className={cn(
                  "w-11 text-right text-[13px] font-extrabold tabular-nums",
                  q.right ? "text-ns-amber-text" : "text-ns-muted",
                )}
              >
                +{q.xp}
              </span>
            </li>
          ))}
        </ul>
      </Card>

      <OutcomeList title={`${unitCode} by lesson`} rows={unitLessons} />

      {missed.length > 0 ? (
        <Callout tone="brand" icon={RotateCcw}>
          <p className="m-0">
            <b>
              {questionsLabel(missed)} went to your Try again list.
            </b>{" "}
            {missed.length === 1 ? "It comes" : "They come"} back in a few days for double XP.
          </p>
        </Callout>
      ) : null}

      <div className="flex flex-col gap-2">
        <Button variant="primary" full href={unitHref}>
          Back to the unit
        </Button>
        <Button variant="ghost" full href={answersHref}>
          See my answers
        </Button>
      </div>
    </FocusShell>
  );
}
