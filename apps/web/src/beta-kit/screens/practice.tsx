import { useId, type ReactNode } from "react";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  Eye,
  Flag,
  Lightbulb,
  Lock,
  RotateCcw,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { GameIcon } from "../components/icons";
import {
  ComboChip,
  Confetti,
  Feedback,
  MiniChips,
  QuestRow,
  QuestToast,
  ReviewNote,
  RewardLine,
  Stars,
  StreakChip,
  Tally,
  XpBar,
  XpNote,
  XpPill,
  XpPop,
  XpTag,
} from "../components/rewards";
import {
  Button,
  Callout,
  Card,
  Divider,
  Eyebrow,
  H3,
  Muted,
  Sheet,
  Steps,
  Tag,
  focusRing,
} from "../components/ui";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import {
  FocusShell,
  FooterBar,
  QuestionHeader,
  TopBar,
} from "../shell/app-shell";
import type {
  Href,
  Player,
  Quest,
  Stars as StarCount,
  Tone,
  XpLine,
} from "../types";
import { BackLink, NumberedSteps, type NumberedStep } from "./lesson";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

/** Per-part result after "Check answer". API: AttemptPartResult.correct. */
export type PartStatus = "none" | "correct" | "wrong";

export interface PracticePart {
  /** API: QuestionPartResponse.position. Input name is `answer-<position>`. */
  position: number;
  /** API: QuestionPartResponse.label ("a", "b" or null for a single part) */
  label: string | null;
  /** API: QuestionPartResponse.prompt, rendered with MathContent */
  prompt: ReactNode;
  /** API: QuestionPartResponse.marks */
  marks: number;
  /** API: QuestionPartResponse.input_placeholder */
  placeholder: string;
  /** API: QuestionPartResponse.response_type */
  responseType: "numeric" | "algebraic_expression";
  /** Typing help under the box, e.g. "Numbers only." Derived from response_type. */
  help?: ReactNode;
  /** The learner's current answer (client state). */
  value: string;
  /** API: AttemptPartResult.correct, "none" before the first check */
  status: PartStatus;
  /** API: AttemptPartResult.error (e.g. the answer could not be read) */
  error?: string | null;
}

export interface PracticeQuestion {
  /** API: PublicQuestionResponse.stable_key */
  key: string;
  /** API: PublicQuestionResponse.difficulty, shown as "Level 2" */
  difficulty: number;
  /** API: PublicQuestionResponse.primary_outcome, shown as "Outcome 1.1" */
  outcome: string;
  /** API: PublicQuestionResponse.total_marks */
  totalMarks: number;
  /** API: PublicQuestionResponse.stem, rendered with MathContent */
  stem: ReactNode;
  /** API: PublicQuestionResponse.parts */
  parts: PracticePart[];
}

export interface PracticeSessionInfo {
  /** e.g. 1, for "Lesson 1 · Guided practice". API: LessonResponse.position */
  lessonPosition: number;
  /** API: LessonResponse.title */
  lessonTitle: string;
  lessonHref: Href;
  /** API: NextQuestionResponse.stage, e.g. "guided" shown as "Guided practice" */
  stageLabel: string;
  /** API: NextQuestionResponse.position */
  position: number;
  /** API: PracticeSessionSummary.question_count */
  total: number;
  /** Save and leave. The session keeps its place (PracticeSessionSummary.status stays "active"). */
  leaveHref: Href;
}

/** API: HintResponse. `content` is HintResponse.parts rendered with MathContent. */
export interface PracticeHint {
  stage: 1 | 2;
  content: ReactNode;
}

/** API: SolutionResponse, from GiveUpResponse.solution. */
export interface PracticeSolution {
  /** One per part. API: SolutionPartResponse.label + canonical_latex */
  answers: { label: string | null; value: ReactNode }[];
  /** API: SolutionPartResponse.steps. Set `wide` on lines that can be long. */
  steps: NumberedStep[];
}

/** NEW. XP rules shown on the question. */
export interface PracticeXp {
  firstTry: number;
  afterHelp: number;
  /** Clearing it later from the Try again list (double XP). */
  review: number;
}

export type PracticeState =
  "answering" | "wrong" | "confirm-give-up" | "solution" | "correct";

export interface PracticeLinks {
  /** Opens the next hint (revealHint). */
  hint?: Href;
  /** Opens the give up sheet. */
  giveUp?: Href;
  /** Confirms give up (giveUp) and shows the solution. */
  showSolution?: Href;
  /** Closes the give up sheet. */
  keepTrying?: Href;
  /** Next question (getNextQuestion). */
  next?: Href;
}

export interface PracticeQuestionProps {
  player: Player;
  state: PracticeState;
  session: PracticeSessionInfo;
  question: PracticeQuestion;
  /** Hints opened so far. API: HintResponse[], NextQuestionResponse.highest_hint_stage */
  hints: PracticeHint[];
  /** Hint stages authored for the question (2 today). */
  hintsTotal: number;
  /** Wrong checks so far. API: AttemptResponse.attempt_number (or NextQuestionResponse.attempt_count) */
  wrongTries: number;
  /** API: AttemptResponse.solution_available */
  solutionAvailable: boolean;
  /** Tries before the solution opens (2 today). */
  solutionAfterTries: number;
  /** Shown when state is "wrong". The app writes it from AttemptResponse.parts. */
  feedback?: { title?: string; body: ReactNode; note?: string };
  /** Shown when state is "solution". */
  solution?: PracticeSolution;
  /** Shown when state is "correct". */
  result?: {
    /** NEW */
    xp: number;
    title: string;
    body: ReactNode;
    /** NEW. Stars the lesson has after this answer. */
    stars: StarCount;
    /** NEW. e.g. "First star won for Lesson 1 practice" */
    starNote?: string;
    /** NEW. Quest finished by this answer. */
    quest?: Quest;
    finish: { label: string; href: Href };
  };
  /** NEW */
  xp: PracticeXp;
  /** NEW. When a given-up question comes back (spaced repetition). */
  review: { inDays: number; badge: string };
  /** NEW. Stars the lesson has now. */
  lessonStars: StarCount;
  /** NEW. The quest this question counts toward. */
  quest?: Quest;
  /** NEW. Combo label, e.g. "FIRST TRY" or "3 IN A ROW". Replaces the streak chip. */
  combo?: string;
  links?: PracticeLinks;
  /**
   * Where "Check answer" submits. Inputs are named `answer-<position>`, the
   * shape submitAttempt() takes. A server action or a URL.
   */
  answerAction?: string | ((formData: FormData) => void | Promise<void>);
  routes?: KitRoutes;
}

/* ------------------------------------------------------------------ */
/* Pieces                                                              */
/* ------------------------------------------------------------------ */

const PRIMARY_BUTTON = cn(
  "inline-flex h-11 items-center justify-center gap-2 rounded-full border-[1.5px] border-ns-ink bg-ns-ink px-6 text-[15px] font-semibold whitespace-nowrap text-ns-on-brand hover:bg-ns-dark",
  focusRing,
);

/** "Check answer": a submit button tied to the answer form by id, so it can live in the footer. */
function CheckAnswerButton({
  formId,
  full,
  small,
}: {
  formId: string;
  full?: boolean;
  small?: boolean;
}) {
  return (
    <button
      type="submit"
      form={formId}
      className={cn(
        PRIMARY_BUTTON,
        full && "w-full",
        small && "h-11 px-4 text-sm",
      )}
    >
      Check answer
    </button>
  );
}

function PracticeDesktopHead({
  player,
  session,
  combo,
  routes,
}: {
  player: Player;
  session: PracticeSessionInfo;
  combo?: string;
  routes: KitRoutes;
}) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-end gap-3">
        <div className="flex min-w-0 grow flex-col gap-1.5">
          <BackLink href={session.lessonHref}>
            Lesson {session.lessonPosition} · {session.lessonTitle}
          </BackLink>
          <h1 className="m-0 text-[28px] leading-9 font-bold">
            {session.stageLabel} · Question {session.position} of{" "}
            {session.total}
          </h1>
        </div>
        {combo ? <ComboChip label={combo} /> : null}
        <MiniChips player={player} routes={routes} />
        <Button variant="ghost" size="sm" icon={X} href={session.leaveHref}>
          Save and leave
        </Button>
      </div>
      <Steps
        done={session.position - 1}
        current={session.position - 1}
        total={session.total}
      />
    </div>
  );
}

function PracticeTop({
  player,
  session,
  combo,
  routes,
}: {
  player: Player;
  session: PracticeSessionInfo;
  combo?: string;
  routes: KitRoutes;
}) {
  return (
    <QuestionHeader
      label={`Lesson ${session.lessonPosition} · ${session.stageLabel}`}
      questionLabel={`Question ${session.position} of ${session.total}`}
      done={session.position - 1}
      current={session.position - 1}
      total={session.total}
      right={
        combo ? (
          <ComboChip label={combo} />
        ) : (
          <StreakChip small days={player.streakDays} href={routes.streak} />
        )
      }
      closeHref={session.leaveHref}
    />
  );
}

export function QuestionStemCard({ question }: { question: PracticeQuestion }) {
  return (
    <Card className="gap-3.5">
      <div className="flex flex-wrap items-center gap-2">
        <Tag>Level {question.difficulty}</Tag>
        <Tag>Outcome {question.outcome}</Tag>
        <span className="ml-auto text-[13px] text-ns-muted">
          {question.totalMarks} mark{question.totalMarks === 1 ? "" : "s"}
        </span>
      </div>
      <div className="text-[17px] leading-7 lg:text-lg">{question.stem}</div>
    </Card>
  );
}

const STATUS_TAG: Record<
  Exclude<PartStatus, "none">,
  { label: string; tone: Tone; icon: typeof Check }
> = {
  correct: { label: "Correct", tone: "success", icon: Check },
  wrong: { label: "Not yet", tone: "danger", icon: X },
};

/** One labelled answer box with its per-part result. */
export function AnswerInput({
  part,
  single,
  locked,
  finished,
  focused,
  readsAs,
}: {
  part: PracticePart;
  /** Only part of the question: label it "Your answer". */
  single?: boolean;
  /** The question is over (solution shown, sheet open): answers are read only. */
  locked?: boolean;
  /** Answered right: green box. */
  finished?: boolean;
  /** Draw as the focused field (keyboard open). */
  focused?: boolean;
  /** Live preview of the typed maths, e.g. 2³ × 3² ×. */
  readsAs?: ReactNode;
}) {
  const base = useId();
  const id = `${base}-answer`;
  const statusId = `${base}-status`;
  const helpId = `${base}-help`;
  const errorId = `${base}-error`;
  const status = part.status === "none" ? null : STATUS_TAG[part.status];
  const readOnly = locked || part.status === "correct";
  const describedBy = [
    status ? statusId : null,
    readsAs || part.help ? helpId : null,
    part.error ? errorId : null,
  ]
    .filter(Boolean)
    .join(" ");
  const title =
    single && !part.label
      ? "Your answer"
      : `Part (${part.label ?? part.position})`;

  return (
    <div className="flex min-w-0 flex-col gap-2">
      <div className="flex items-center gap-2">
        <label
          htmlFor={id}
          className="flex min-w-0 grow flex-wrap items-baseline gap-x-2 gap-y-0.5"
        >
          <span className="text-[15px] leading-5 font-bold">{title}</span>
          {part.prompt ? (
            <span className="text-sm leading-5 text-ns-muted">
              {part.prompt}
            </span>
          ) : null}
        </label>
        {status ? (
          <span id={statusId} className={cn(finished && "sr-only")}>
            <Tag tone={status.tone} icon={status.icon}>
              {status.label}
            </Tag>
          </span>
        ) : null}
      </div>
      <input
        id={id}
        name={`answer-${part.position}`}
        type="text"
        inputMode={part.responseType === "numeric" ? "decimal" : "text"}
        autoComplete="off"
        autoCapitalize="off"
        spellCheck={false}
        maxLength={500}
        defaultValue={part.value}
        placeholder={part.placeholder}
        readOnly={readOnly}
        aria-invalid={part.status === "wrong" ? true : undefined}
        aria-describedby={describedBy || undefined}
        className={cn(
          "h-[52px] w-full min-w-0 rounded-lg border-[1.5px] px-4 font-ns-math text-xl text-ns-ink placeholder:text-ns-muted/80",
          part.status === "correct" && finished
            ? "border-2 border-ns-success bg-ns-success-soft"
            : part.status === "correct"
              ? "border-ns-success bg-ns-sunken"
              : part.status === "wrong"
                ? "border-ns-danger bg-ns-raised"
                : "border-ns-line-strong bg-ns-raised",
          focused &&
            "border-2 border-ns-ink outline-3 outline-offset-2 outline-ns-ink/25",
          focusRing,
        )}
      />
      {readsAs ? (
        <div
          id={helpId}
          className="flex items-center gap-2 text-sm text-ns-muted"
        >
          Reads as{" "}
          <span className="font-ns-math text-lg text-ns-ink">{readsAs}</span>
        </div>
      ) : part.help ? (
        <div id={helpId} className="text-[13px] leading-[18px] text-ns-muted">
          {part.help}
        </div>
      ) : null}
      {part.error ? (
        <div
          id={errorId}
          className="text-[13px] leading-[18px] font-semibold text-ns-danger"
        >
          {part.error}
        </div>
      ) : null}
    </div>
  );
}

function AnswerForm({
  formId,
  question,
  action,
  locked,
  finished,
  overlay,
}: {
  formId: string;
  question: PracticeQuestion;
  action?: PracticeQuestionProps["answerAction"];
  locked?: boolean;
  finished?: boolean;
  overlay?: ReactNode;
}) {
  const single = question.parts.length === 1;
  return (
    <Card className="relative gap-5">
      {overlay}
      <form id={formId} action={action} className="flex flex-col gap-5">
        {question.parts.map((part) => (
          <AnswerInput
            key={part.position}
            part={part}
            single={single}
            locked={locked}
            finished={finished}
          />
        ))}
      </form>
    </Card>
  );
}

export function HintList({ hints }: { hints: PracticeHint[] }) {
  return (
    <div
      role="region"
      aria-label="Hints"
      className="flex flex-col gap-3 rounded-xl bg-ns-amber-soft p-4"
    >
      {hints.map((hint) => (
        <div key={hint.stage} className="flex items-start gap-2.5">
          <span className="shrink-0 pt-0.5 text-xs font-bold text-ns-amber-text">
            Hint {hint.stage}
          </span>
          <div className="text-[15px] leading-[22px] text-ns-ink">
            {hint.content}
          </div>
        </div>
      ))}
    </div>
  );
}

function hintLabel(open: number, total: number) {
  return open < total ? `Hint ${open + 1} of ${total}` : "No more hints";
}

function triesLabel(tries: number, soFar: boolean) {
  if (tries === 0) return "No tries yet";
  return `${tries} wrong ${tries === 1 ? "try" : "tries"}${soFar ? " so far" : ""}`;
}

function ThisQuestionCard({
  xp,
  stars,
  quest,
  firstTryGone,
}: {
  xp: PracticeXp;
  stars: StarCount;
  quest?: Quest;
  firstTryGone: boolean;
}) {
  const rows = [
    { label: "Right first try", xp: xp.firstTry, gone: firstTryGone },
    { label: "Right after a hint or retry", xp: xp.afterHelp, gone: false },
    { label: "Cleared later from Try again", xp: xp.review, gone: false },
  ];
  return (
    <Card className="gap-3">
      <div className="flex items-center justify-between gap-3">
        <H3>This question</H3>
        <Stars count={stars} size={18} />
      </div>
      {rows.map((row) => (
        <div key={row.label} className="flex items-center gap-2">
          <span
            className={cn(
              "grow text-sm leading-5 text-ns-muted",
              row.gone && "line-through",
            )}
          >
            {row.label}
            {row.gone ? <span className="sr-only"> (missed)</span> : null}
          </span>
          <XpTag xp={row.xp} size={14} />
        </div>
      ))}
      {quest ? (
        <>
          <Divider />
          <QuestRow quest={quest} />
        </>
      ) : null}
    </Card>
  );
}

/** Numbered worked solution with the final answers on top. */
export function SolutionCard({ solution }: { solution: PracticeSolution }) {
  return (
    <Card className="gap-4">
      <H3>Solution</H3>
      {solution.answers.length ? (
        <div className="flex flex-wrap gap-x-8 gap-y-3 rounded-xl bg-ns-sunken p-4">
          {solution.answers.map((answer, i) => (
            <div key={i} className="flex flex-col gap-0.5">
              <Eyebrow muted>
                {answer.label ? `Answer (${answer.label})` : "Answer"}
              </Eyebrow>
              <span className="font-ns-math text-[22px] text-ns-ink">
                {answer.value}
              </span>
            </div>
          ))}
        </div>
      ) : null}
      <NumberedSteps steps={solution.steps} mathSize={19} />
    </Card>
  );
}

function reviewText(review: PracticeQuestionProps["review"], xp: PracticeXp) {
  return `Back in ${review.inDays} days. Clear it then for double XP (+${xp.review}) and a step toward the ${review.badge} badge.`;
}

/** Right answer panel, footer on phones and a card on desktop. */
function ResultPanel({
  result,
  className,
  card,
}: {
  result: NonNullable<PracticeQuestionProps["result"]>;
  className?: string;
  card?: boolean;
}) {
  return (
    <div
      role="status"
      className={cn(
        "flex animate-ns-pop flex-col gap-3 bg-ns-success-soft",
        card
          ? "rounded-2xl border-[1.5px] border-ns-success p-5"
          : "border-t-2 border-ns-success px-4 pt-4 pb-5",
        className,
      )}
    >
      <div
        className={cn(
          "mx-auto flex w-full max-w-[1040px] flex-col gap-3",
          card && "max-w-none",
        )}
      >
        <div className="flex items-end gap-2.5">
          <div
            className={cn(
              "shrink-0",
              card ? "-my-2 -ml-1.5" : "-mt-10 -mb-2 -ml-1.5",
            )}
          >
            <Hornbill
              size={96}
              mood="happy"
              pose="cheer"
              outfit="scarf"
              branch={false}
            />
          </div>
          <div className="flex min-w-0 grow flex-col gap-0.5">
            <span className="text-[22px] leading-7 font-black text-ns-success">
              {result.title}
            </span>
            <p className="m-0 text-sm leading-5 text-ns-ink">{result.body}</p>
          </div>
          <span className="inline-flex shrink-0 animate-ns-pop items-center gap-1 text-xl font-black text-ns-amber-text [animation-delay:.15s]">
            <GameIcon name="bolt" size={20} className="text-ns-amber" />+
            {result.xp}
            <span className="sr-only"> XP</span>
          </span>
        </div>
        {result.starNote ? (
          <div className="flex items-center gap-2">
            <Stars count={result.stars} size={20} />
            <span className="text-[13px] leading-[18px] font-semibold text-ns-ink">
              {result.starNote}
            </span>
          </div>
        ) : null}
        <Button
          variant="primary"
          full
          href={result.finish.href}
          iconRight={ArrowRight}
        >
          {result.finish.label}
        </Button>
      </div>
    </div>
  );
}

function GiveUpSheet({
  review,
  xp,
  links,
}: {
  review: PracticeQuestionProps["review"];
  xp: PracticeXp;
  links: PracticeLinks;
}) {
  const titleId = useId();
  return (
    <Sheet titleId={titleId}>
      <div className="flex items-center gap-3">
        <Hornbill size={72} mood="kind" branch={false} />
        <div className="flex min-w-0 grow flex-col gap-1">
          <h2 id={titleId} className="m-0 text-xl leading-7 font-semibold">
            See the full solution?
          </h2>
          <Muted className="text-[15px] leading-[22px]">
            That is fine. Seeing the step you missed is how you learn it.
          </Muted>
        </div>
      </div>
      <RewardLine
        icon={<RotateCcw size={20} aria-hidden />}
        title={`It comes back in ${review.inDays} days`}
        sub={`Clear it then for double XP (+${xp.review}).`}
        right={<XpPill xp={xp.review} />}
      />
      <RewardLine
        icon={<GameIcon name="flame" size={20} className="text-ns-amber" />}
        title="Your streak and XP are safe"
        sub="Giving up never takes anything away."
      />
      <div className="flex flex-col gap-2">
        <Button variant="primary" full href={links.showSolution}>
          Show solution
        </Button>
        <Button full href={links.keepTrying}>
          Keep trying · still +{xp.afterHelp} XP
        </Button>
      </div>
    </Sheet>
  );
}

/* ------------------------------------------------------------------ */
/* Practice question                                                   */
/* ------------------------------------------------------------------ */

/**
 * Canvas: PracticeAnswer.m, PracticeAnswer.d, Practice.t, PracticeWrong1.m,
 * PracticeWrong2.m, PracticeWrong2.d, PracticeGiveUpDialog.m,
 * PracticeSolution.m, PracticeSolution.d, PracticeLongMath.m, PracticeCorrect.m
 */
export function PracticeQuestionScreen({
  player,
  state,
  session,
  question,
  hints,
  hintsTotal,
  wrongTries,
  solutionAvailable,
  solutionAfterTries,
  feedback,
  solution,
  result,
  xp,
  review,
  lessonStars,
  quest,
  combo,
  links = {},
  answerAction,
  routes = PREVIEW_ROUTES,
}: PracticeQuestionProps) {
  const formId = useId();
  const answering = state === "answering" || state === "wrong";
  const heading = `${session.stageLabel} · Question ${session.position} of ${session.total}`;
  const hintButton = (full?: boolean) => (
    <Button
      icon={Lightbulb}
      full={full}
      href={links.hint}
      disabled={hints.length >= hintsTotal}
    >
      {hintLabel(hints.length, hintsTotal)}
    </Button>
  );
  const feedbackPanel =
    state === "wrong" && feedback ? (
      <Feedback kind="wrong" title={feedback.title} note={feedback.note}>
        {feedback.body}
      </Feedback>
    ) : null;

  const footer = answering ? (
    <FooterBar className="lg:hidden">
      <XpNote>
        {wrongTries === 0
          ? `Right first try: +${xp.firstTry} XP. Keeps your combo going.`
          : `Get it right now: still +${xp.afterHelp} XP.`}
      </XpNote>
      <div className="flex gap-2">
        {hintButton()}
        <div className="grow">
          <CheckAnswerButton formId={formId} full />
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
        <span className="text-[13px] leading-[18px] text-ns-muted">
          {triesLabel(wrongTries, true)}
        </span>
        {solutionAvailable ? (
          <Button
            variant="ghost"
            size="sm"
            icon={Flag}
            href={links.giveUp}
            className="-ml-4 h-11"
          >
            Give up and see the solution
          </Button>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-[13px] leading-[18px] text-ns-muted">
            <Lock size={14} aria-hidden />
            The solution opens after {solutionAfterTries} tries
          </span>
        )}
      </div>
    </FooterBar>
  ) : state === "solution" ? (
    <FooterBar className="lg:hidden">
      <Button variant="primary" full href={links.next} iconRight={ArrowRight}>
        Next question
      </Button>
      <XpNote center>Next one is worth +{xp.firstTry} XP first try</XpNote>
    </FooterBar>
  ) : state === "correct" && result ? (
    <ResultPanel result={result} className="lg:hidden" />
  ) : undefined;

  const questionColumn = (
    <div
      className={cn(
        "flex min-w-0 flex-col gap-4",
        state === "solution" && "hidden lg:flex",
        state === "confirm-give-up" && "opacity-35",
      )}
      inert={state === "confirm-give-up" || undefined}
    >
      <QuestionStemCard question={question} />
      <AnswerForm
        formId={formId}
        question={question}
        action={answerAction}
        locked={!answering}
        finished={state === "correct"}
        overlay={
          state === "correct" && result ? (
            <XpPop text={`+${result.xp}`} className="top-3 right-6" />
          ) : undefined
        }
      />
      {state === "correct" && result?.quest ? (
        <QuestToast quest={result.quest} />
      ) : null}
      {answering ? (
        <div className="hidden items-center gap-4 lg:flex">
          <CheckAnswerButton formId={formId} />
          <span className="text-sm text-ns-muted">
            {triesLabel(wrongTries, false)}
          </span>
        </div>
      ) : null}
    </div>
  );

  let sideColumn: ReactNode = null;
  if (answering || state === "confirm-give-up") {
    sideColumn = (
      <div
        className={cn(
          "hidden min-w-0 flex-col gap-4 lg:flex",
          state === "confirm-give-up" && "opacity-35",
        )}
        inert={state === "confirm-give-up" || undefined}
      >
        {feedbackPanel}
        <ThisQuestionCard
          xp={xp}
          stars={lessonStars}
          quest={quest}
          firstTryGone={wrongTries > 0}
        />
        <Card className="gap-3.5">
          <div className="flex items-center justify-between gap-3">
            <H3>Hints</H3>
            <span className="text-[13px] text-ns-muted">
              {hints.length} of {hintsTotal} open
            </span>
          </div>
          {hints.length ? (
            <HintList hints={hints} />
          ) : (
            <Muted>
              Stuck? A hint shows the next step without giving the answer away.
              You still earn +{xp.afterHelp} XP after a hint.
            </Muted>
          )}
          {hintButton(true)}
        </Card>
        <Card className="gap-3">
          <H3>Solution</H3>
          {solutionAvailable ? (
            <>
              <Button full icon={Flag} href={links.giveUp}>
                Give up and see the solution
              </Button>
              <Muted className="text-center text-[13px] leading-[18px]">
                You can also keep trying as long as you like. Your XP is safe
                either way.
              </Muted>
            </>
          ) : (
            <span className="inline-flex items-center justify-center gap-1.5 text-[13px] text-ns-muted">
              <Lock size={14} aria-hidden />
              The solution opens after {solutionAfterTries} wrong tries
            </span>
          )}
        </Card>
      </div>
    );
  } else if (state === "solution") {
    sideColumn = (
      <div className="flex min-w-0 flex-col gap-4">
        <ReviewNote>{reviewText(review, xp)}</ReviewNote>
        {solution ? <SolutionCard solution={solution} /> : null}
        <div className="hidden lg:block">
          <Button
            variant="primary"
            full
            href={links.next}
            iconRight={ArrowRight}
          >
            Next question
          </Button>
        </div>
      </div>
    );
  } else if (state === "correct" && result) {
    sideColumn = (
      <div className="hidden min-w-0 flex-col gap-4 lg:flex">
        <ResultPanel result={result} card />
      </div>
    );
  }

  return (
    <FocusShell
      player={player}
      routes={routes}
      top={
        <PracticeTop
          player={player}
          session={session}
          combo={combo}
          routes={routes}
        />
      }
      desktopTop={
        <PracticeDesktopHead
          player={player}
          session={session}
          combo={combo}
          routes={routes}
        />
      }
      footer={footer}
      overlay={
        state === "confirm-give-up" ? (
          <GiveUpSheet review={review} xp={xp} links={links} />
        ) : state === "correct" ? (
          <Confetti count={18} seed={7} />
        ) : undefined
      }
    >
      <h1 className="sr-only lg:hidden">{heading}</h1>
      {answering ? (
        <div className="flex flex-col gap-4 lg:hidden">
          {feedbackPanel}
          {hints.length ? <HintList hints={hints} /> : null}
        </div>
      ) : null}
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-8">
        {questionColumn}
        {sideColumn}
      </div>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Practice on a phone with the keyboard open                          */
/* ------------------------------------------------------------------ */

const MATH_KEYS: { key: string; label: string }[] = [
  { key: "^", label: "Power" },
  { key: "×", label: "Times" },
  { key: "÷", label: "Divide" },
  { key: "√", label: "Square root" },
  { key: "(", label: "Open bracket" },
  { key: ")", label: "Close bracket" },
  { key: "a/b", label: "Fraction" },
  { key: "−", label: "Minus" },
];

/**
 * Maths keys that sit on top of the phone keyboard. Each button carries the
 * text it inserts in `data-insert`; the app wires the insert on the client.
 */
export function MathKeysToolbar({ controls }: { controls: string }) {
  return (
    <div
      role="toolbar"
      aria-label="Maths keys"
      aria-controls={controls}
      className="border-t border-ns-line bg-ns-sunken"
    >
      <div className="mx-auto flex max-w-[680px] gap-1.5 overflow-x-auto px-3 py-2 lg:max-w-[1040px] lg:px-0">
        {MATH_KEYS.map((item) => (
          <button
            key={item.label}
            type="button"
            aria-label={item.label}
            data-insert={item.key === "a/b" ? "/" : item.key}
            className={cn(
              "h-11 min-w-11 shrink-0 rounded-[10px] border border-ns-line bg-ns-raised px-2.5 font-ns-math text-xl text-ns-ink hover:bg-ns-sunken",
              focusRing,
            )}
          >
            {item.key}
          </button>
        ))}
      </div>
    </div>
  );
}

export interface PracticeKeyboardProps {
  player: Player;
  session: PracticeSessionInfo;
  /** First sentence of the stem, shown while typing. */
  shortStem: ReactNode;
  /** API: PublicQuestionResponse.stem, behind "Show full question". */
  fullStem: ReactNode;
  /** The part being typed in. */
  part: PracticePart;
  /** NEW. The typed answer rendered as maths, e.g. 2³ × 3² ×. */
  readsAs?: ReactNode;
  hintsOpen: number;
  hintsTotal: number;
  links?: Pick<PracticeLinks, "hint">;
  answerAction?: PracticeQuestionProps["answerAction"];
  routes?: KitRoutes;
}

/** Canvas: PracticeKeyboard.m */
export function PracticeKeyboardScreen({
  player,
  session,
  shortStem,
  fullStem,
  part,
  readsAs,
  hintsOpen,
  hintsTotal,
  links = {},
  answerAction,
  routes = PREVIEW_ROUTES,
}: PracticeKeyboardProps) {
  const formId = useId();
  const inputHint = `${formId}-part`;
  return (
    <FocusShell
      player={player}
      routes={routes}
      top={<PracticeTop player={player} session={session} routes={routes} />}
      desktopTop={
        <PracticeDesktopHead
          player={player}
          session={session}
          routes={routes}
        />
      }
      className="gap-3"
      footer={
        <div className="border-t border-ns-line bg-ns-surface">
          <div className="mx-auto flex max-w-[680px] gap-2 px-3 py-2.5 lg:max-w-[1040px] lg:px-0">
            <Button
              size="sm"
              icon={Lightbulb}
              href={links.hint}
              disabled={hintsOpen >= hintsTotal}
              className="h-11"
            >
              {hintLabel(hintsOpen, hintsTotal)}
            </Button>
            <div className="grow">
              <CheckAnswerButton formId={formId} full small />
            </div>
          </div>
          <MathKeysToolbar controls={inputHint} />
          {/*
            The phone's own keyboard opens below this bar. Keep the bar pinned to
            the top of the keyboard with the VisualViewport API (or
            `interactive-widget=resizes-content` in the viewport meta). Do not
            draw a keyboard here.
          */}
        </div>
      }
    >
      <h1 className="sr-only">
        {session.stageLabel} · Question {session.position} of {session.total}
      </h1>
      <div className="flex w-full flex-col gap-3 lg:max-w-[680px] lg:gap-4">
        <Card className="gap-2 p-4">
          <p className="m-0 text-base leading-6">{shortStem}</p>
          <details className="group">
            <summary
              className={cn(
                "mx-auto flex min-h-11 w-fit cursor-pointer list-none items-center gap-1.5 rounded-full px-4 text-sm font-semibold [&::-webkit-details-marker]:hidden",
                focusRing,
              )}
            >
              <span className="group-open:hidden">Show full question</span>
              <span className="hidden group-open:inline">
                Hide full question
              </span>
              <ChevronDown
                size={18}
                aria-hidden
                className="transition-transform group-open:rotate-180"
              />
            </summary>
            <div className="pt-1 text-base leading-6">{fullStem}</div>
          </details>
        </Card>
        <Card className="p-4">
          <form id={formId} action={answerAction}>
            <div id={inputHint}>
              <AnswerInput part={part} focused readsAs={readsAs} />
            </div>
          </form>
        </Card>
      </div>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Practice done                                                       */
/* ------------------------------------------------------------------ */

/** NEW. How each question in the set ended. */
export type QuestionOutcome = "first_try" | "with_help" | "solution_shown";

const OUTCOME: Record<
  QuestionOutcome,
  { label: string; tone: Tone; icon: typeof Check }
> = {
  first_try: { label: "Right first try", tone: "success", icon: CheckCircle2 },
  with_help: {
    label: "Right after a hint or retry",
    tone: "success",
    icon: CheckCircle2,
  },
  solution_shown: { label: "Solution shown", tone: "neutral", icon: Eye },
};

export interface PracticeResultRow {
  label: string;
  outcome: QuestionOutcome;
  /** XP earned, or a note such as "Back in 2 days". */
  xp?: number;
  note?: string;
}

export interface PracticeDoneProps {
  player: Player;
  /** Top bar title, e.g. "Lesson 1 practice". */
  title: string;
  /** e.g. "Lesson 1 · Guided practice" */
  subtitle: string;
  backHref: Href;
  /** NEW. Lesson stars after this set. */
  stars: StarCount;
  /** NEW. XP won in this set. */
  tally: XpLine[];
  /** NEW. Level after this set. */
  level: { level: number; current: number; needed: number; note?: string };
  /** NEW */
  streak: { days: number; note: string };
  /** One row per question. API: PracticeSessionSummary counts; per-question rows are NEW. */
  results: PracticeResultRow[];
  /** NEW. What the next star needs. */
  nextStar?: { title: string; body: string };
  primary: { label: string; href: Href };
  secondary: { label: string; href: Href };
  routes?: KitRoutes;
}

/** Canvas: PracticeDone.m, PracticeDone.d */
export function PracticeDoneScreen({
  player,
  title,
  subtitle,
  backHref,
  stars,
  tally,
  level,
  streak,
  results,
  nextStar,
  primary,
  secondary,
  routes = PREVIEW_ROUTES,
}: PracticeDoneProps) {
  const toNext = level.needed - level.current;
  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={560}
      top={<TopBar title={title} backHref={backHref} />}
      overlay={<Confetti count={34} seed={11} />}
    >
      <div className="flex flex-col items-center gap-1.5 text-center">
        <div className="animate-ns-pop">
          <Hornbill
            size={128}
            mood="happy"
            pose="cheer"
            outfit="scarf"
            branch={false}
          />
        </div>
        <h1 className="m-0 text-[28px] leading-[34px] font-bold">
          Practice done!
        </h1>
        <Muted className="text-[15px] leading-[22px]">{subtitle}</Muted>
        <div aria-hidden="true" className="flex gap-1.5 pt-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="animate-ns-pop"
              style={{ animationDelay: `${0.3 + i * 0.2}s` }}
            >
              <GameIcon
                name="star"
                size={40}
                className={i < stars ? "text-ns-gold" : "text-ns-line"}
              />
            </span>
          ))}
        </div>
        <p className="m-0 text-[13px] leading-[18px] font-bold text-ns-amber-text">
          {stars} of 3 stars
        </p>
      </div>

      <Card>
        <Tally lines={tally} />
      </Card>

      <Card tone="amber" className="gap-2.5 p-[18px]">
        <XpBar
          level={level.level}
          current={level.current}
          needed={level.needed}
        />
        <p className="m-0 text-[13px] leading-[18px]">
          {toNext > 0 ? (
            <b className="text-ns-amber-text">
              {toNext} XP to Level {level.level + 1}!
            </b>
          ) : null}{" "}
          {level.note}
        </p>
      </Card>

      <Card className="flex-row items-center gap-3 p-4">
        <span className="inline-flex animate-ns-flame text-ns-amber">
          <GameIcon name="flame" size={34} />
        </span>
        <div className="flex flex-col gap-0.5">
          <b className="text-lg leading-6">{streak.days} day streak!</b>
          <Muted className="text-[13px] leading-[18px]">{streak.note}</Muted>
        </div>
      </Card>

      <Card className="gap-3">
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {results.map((row) => {
            const outcome = OUTCOME[row.outcome];
            return (
              <li key={row.label} className="flex items-center gap-2">
                <span className="grow text-[15px] font-semibold">
                  {row.label}
                </span>
                <Tag tone={outcome.tone} icon={outcome.icon}>
                  {outcome.label}
                </Tag>
                <span
                  className={cn(
                    "w-[92px] shrink-0 text-right text-[13px] font-extrabold",
                    row.xp ? "text-ns-amber-text" : "text-ns-muted",
                  )}
                >
                  {row.xp ? `+${row.xp}` : row.note}
                  {row.xp ? <span className="sr-only"> XP</span> : null}
                </span>
              </li>
            );
          })}
        </ul>
      </Card>

      {nextStar ? (
        <Callout tone="amber" icon={TargetIcon}>
          <b className="text-[15px] leading-[22px]">{nextStar.title}</b>
          <span>{nextStar.body}</span>
        </Callout>
      ) : null}

      <div className="flex flex-col gap-2">
        <Button variant="primary" full icon={RotateCcw} href={primary.href}>
          {primary.label}
        </Button>
        <Button full href={secondary.href}>
          {secondary.label}
        </Button>
      </div>
    </FocusShell>
  );
}

function TargetIcon({ size = 20 }: { size?: number }) {
  return <GameIcon name="target" size={size} />;
}
