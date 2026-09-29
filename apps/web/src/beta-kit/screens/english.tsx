/**
 * English: grammar and vocabulary practice, and essay writing with AI
 * feedback.
 *
 * The learning API has no English endpoints yet, so every prop here is NEW
 * backend work (grammar units and questions, writing tasks, drafts, submitted
 * versions, AI feedback, the essay quota). Shapes reuse types.ts where they
 * can (Quest, Stars, LessonUiState, Player).
 */
import Link from "next/link";
import type { ReactNode } from "react";
import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  Clock,
  FileText,
  Lock,
  RefreshCw,
  RotateCcw,
  Sparkles,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { GameIcon } from "../components/icons";
import { LessonStateTag } from "../components/lesson-row";
import {
  ComboChip,
  Confetti,
  Feedback,
  Medal,
  MiniChips,
  QuestRow,
  QuestToast,
  RewardLine,
  Stars as StarRow,
  StreakChip,
  XpNote,
  XpPill,
  XpTag,
} from "../components/rewards";
import {
  Button,
  Callout,
  Card,
  Divider,
  Eyebrow,
  Field,
  H1,
  H2,
  H3,
  IconButton,
  Muted,
  Sheet,
  Tag,
  focusRing,
} from "../components/ui";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import { AppShell, FocusShell, FooterBar, TopBar } from "../shell/app-shell";
import type { BadgeIcon, Href, LessonUiState, Player, Quest, Stars, Tier, Tone } from "../types";

/* ------------------------------------------------------------------ */
/* Types (all NEW: no English API yet)                                 */
/* ------------------------------------------------------------------ */

export type Subject = "maths" | "english";

/** NEW. Links for the Maths / English switch. */
export interface SubjectLinks {
  maths: Href;
  english: Href;
}

/** NEW. One grammar or vocabulary set, e.g. "Tenses". */
export interface GrammarUnitSummary {
  key: string;
  title: string;
  questionCount: number;
  /** Same states and labels as maths lessons. */
  state: LessonUiState;
  stars: Stars;
  /** XP still available, shown when no star is earned yet. */
  xpAvailable?: number;
  href: Href;
}

export type WritingKind = "Situational writing" | "Continuous writing";

/** NEW. "draft" = a saved draft, "new" = not started, "marked" = feedback ready. */
export type WritingTaskStatus = "draft" | "new" | "marked";

/** NEW. A writing task card on the English home. */
export interface WritingTaskSummary {
  key: string;
  kind: WritingKind;
  title: string;
  words: { min: number; max: number };
  minutes: number;
  status: WritingTaskStatus;
  /** Only when status is "marked". */
  marked?: { dateLabel: string; score: number; outOf: number };
  /** XP for submitting a first version. */
  submitXp: number;
  /** XP for improving the score in a later version. */
  improveXp: number;
  href: Href;
}

/** NEW. Full writing task (prompt, purpose, audience, context, rubric). */
export interface WritingTask {
  key: string;
  kind: WritingKind;
  title: string;
  brief: string;
  purpose: string;
  audience: string;
  context: string;
  words: { min: number; max: number };
  minutes: number;
  /** What the student writes, e.g. "email", "report", "essay". */
  formatNoun: string;
  rubric: { name: string; marks: number }[];
  rubricHref: Href;
}

/* ------------------------------------------------------------------ */
/* Small shared pieces                                                 */
/* ------------------------------------------------------------------ */

/** Maths / English pill switch. A nav, with aria-current on the active subject. */
export function SubjectSwitch({ active, links }: { active: Subject; links: SubjectLinks }) {
  const items: { key: Subject; label: string }[] = [
    { key: "maths", label: "Maths" },
    { key: "english", label: "English" },
  ];
  return (
    <nav aria-label="Subject" className="flex gap-1 rounded-full border border-ns-line bg-ns-sunken p-1">
      {items.map((item) => {
        const on = item.key === active;
        return (
          <Link
            key={item.key}
            href={links[item.key]}
            aria-current={on ? "page" : undefined}
            className={cn(
              "flex h-11 flex-1 items-center justify-center rounded-full text-[15px] font-semibold no-underline",
              on ? "bg-ns-ink text-ns-on-brand" : "text-ns-ink hover:bg-ns-raised",
              focusRing,
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

/** Purpose, audience and context of a writing task. */
function TaskFrame({ task }: { task: WritingTask }) {
  const rows = [
    ["Purpose", task.purpose],
    ["Audience", task.audience],
    ["Context", task.context],
  ] as const;
  return (
    <dl className="m-0 flex flex-col gap-3">
      {rows.map(([label, text]) => (
        <div key={label} className="flex flex-col gap-0.5">
          <dt>
            <Eyebrow>{label}</Eyebrow>
          </dt>
          <dd className="m-0 text-[15px] leading-[22px] text-ns-ink">{text}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Header for grammar and vocabulary questions: topic, count, bar, close. */
export function EnglishQuestionHeader({
  topic,
  position,
  total,
  right,
  closeHref,
}: {
  topic: string;
  position: number;
  total: number;
  right?: ReactNode;
  closeHref: Href;
}) {
  const pct = Math.round((position / Math.max(1, total)) * 100);
  return (
    <header className="flex shrink-0 flex-col gap-2 border-b border-ns-line bg-ns-surface px-4 pt-2 pb-3 lg:border-b-0 lg:px-0 lg:pt-0 lg:pb-2">
      <div className="flex items-center gap-1.5">
        <div className="flex min-w-0 grow flex-col">
          <span className="truncate text-xs font-semibold text-ns-muted">English · {topic}</span>
          <span className="text-base font-bold lg:text-[28px] lg:leading-9">
            Question {position} of {total}
          </span>
        </div>
        {right}
        <IconButton icon={X} label="Leave practice. Your place is saved" href={closeHref} />
      </div>
      <div
        role="progressbar"
        aria-label="Question progress"
        aria-valuenow={position}
        aria-valuemin={0}
        aria-valuemax={total}
        className="h-1.5 overflow-hidden rounded-full bg-ns-line"
      >
        <div className="h-full rounded-full bg-ns-amber" style={{ width: `${pct}%` }} />
      </div>
    </header>
  );
}

/** The blank in a grammar sentence. Pass `value` once the answer is right. */
export function Gap({ value }: { value?: string }) {
  return (
    <span className="inline-block min-w-[72px] border-b-2 border-ns-amber px-1 text-center font-bold">
      {value ?? <span className="sr-only">blank</span>}
    </span>
  );
}

function QuestionStem({ topic, instruction, stem, hint }: { topic: string; instruction: string; stem: ReactNode; hint?: ReactNode }) {
  return (
    <Card className="gap-3.5">
      <div className="flex">
        <Tag>{topic}</Tag>
      </div>
      <Muted>{instruction}</Muted>
      <p className="m-0 text-xl leading-[30px] font-medium text-ns-ink">{stem}</p>
      {hint ? <Muted>{hint}</Muted> : null}
    </Card>
  );
}

/** Footer content, kept to the same width as the question column. */
function QuestionFooter({ children }: { children: ReactNode }) {
  return (
    <FooterBar>
      <div className="mx-auto flex w-full max-w-[680px] flex-col gap-2">{children}</div>
    </FooterBar>
  );
}

/* ------------------------------------------------------------------ */
/* English home                                                        */
/* ------------------------------------------------------------------ */

export interface EnglishHomeProps {
  player: Player;
  subjectLinks: SubjectLinks;
  /** NEW. English daily quests (no all-three bonus on this card). */
  quests: Quest[];
  questsResetIn: string;
  /** NEW. Essay marks left in the beta. Drafts are free. */
  essayMarksLeft: number;
  grammarUnits: GrammarUnitSummary[];
  writingTasks: WritingTaskSummary[];
  myEssaysHref: Href;
  routes?: KitRoutes;
}

function GrammarUnitRow({ unit, position }: { unit: GrammarUnitSummary; position: number }) {
  const done = unit.state === "proficient" || unit.state === "mastered";
  const practising = unit.state === "practising";
  const locked = unit.state === "locked";
  const inner = (
    <>
      <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-ns-brand-soft text-[15px] font-bold text-ns-ink">
        {done ? <Check size={18} aria-label="Done" /> : locked ? <Lock size={16} aria-label="Locked" /> : position}
      </span>
      <div className="flex min-w-0 grow flex-col gap-0.5">
        <span className={cn("text-base leading-[22px] font-semibold", locked ? "text-ns-muted" : "text-ns-ink")}>{unit.title}</span>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <span className="text-[13px] leading-[18px] text-ns-muted">
            {unit.questionCount} question{unit.questionCount === 1 ? "" : "s"}
          </span>
          {unit.stars > 0 || practising ? <StarRow count={unit.stars} size={13} /> : null}
          {unit.stars === 0 && !practising && unit.xpAvailable ? <XpTag xp={unit.xpAvailable} size={12} /> : null}
        </div>
      </div>
      <LessonStateTag state={unit.state} />
    </>
  );
  const rowClass = cn("flex items-center gap-3.5 rounded-xl px-4 py-3", practising && "bg-ns-amber-soft");
  if (locked) return <div className={rowClass}>{inner}</div>;
  return (
    <Link href={unit.href} className={cn(rowClass, "text-inherit no-underline", !practising && "hover:bg-ns-sunken", focusRing)}>
      {inner}
    </Link>
  );
}

const TASK_TAG: Record<WritingTaskStatus, { label: string; tone: Tone; icon?: typeof CheckCircle2 }> = {
  draft: { label: "Draft saved", tone: "amber" },
  new: { label: "Not started", tone: "neutral" },
  marked: { label: "Marked", tone: "success", icon: CheckCircle2 },
};

function WritingTaskCard({ task }: { task: WritingTaskSummary }) {
  const tag = TASK_TAG[task.status];
  const meta =
    task.status === "marked" && task.marked
      ? `Marked ${task.marked.dateLabel} · estimated ${task.marked.score} of ${task.marked.outOf}`
      : `${task.words.min} to ${task.words.max} words · about ${task.minutes} min`;
  const note =
    task.status === "draft"
      ? `Submit for +${task.submitXp} XP`
      : task.status === "new"
        ? `+${task.submitXp} XP when you submit`
        : `+${task.submitXp} XP earned · write version 2 for +${task.improveXp}`;
  return (
    <Link
      href={task.href}
      className={cn(
        "flex flex-col gap-2 rounded-xl border border-ns-line bg-ns-raised p-4 text-inherit no-underline hover:bg-ns-surface",
        focusRing,
      )}
    >
      <div className="flex items-center gap-2">
        <Eyebrow muted>{task.kind}</Eyebrow>
        <span className="ml-auto">
          <Tag tone={tag.tone} icon={tag.icon}>
            {tag.label}
          </Tag>
        </span>
      </div>
      <span className="text-[17px] leading-6 font-semibold">{task.title}</span>
      <Muted className="text-[13px] leading-[18px]">{meta}</Muted>
      <XpNote>{note}</XpNote>
    </Link>
  );
}

/** Canvas: EnglishHome.m, EnglishHome.d */
export function EnglishHomeScreen({
  player,
  subjectLinks,
  quests,
  questsResetIn,
  essayMarksLeft,
  grammarUnits,
  writingTasks,
  myEssaysHref,
  routes = PREVIEW_ROUTES,
}: EnglishHomeProps) {
  const proficient = grammarUnits.filter((u) => u.state === "proficient" || u.state === "mastered").length;
  return (
    <AppShell
      active="course"
      player={player}
      routes={routes}
      className="gap-5 lg:gap-6"
      top={<TopBar title="Course" right={<MiniChips player={player} routes={routes} />} />}
    >
      <div className="flex flex-col gap-5 lg:flex-row-reverse lg:items-end lg:gap-6">
        <div className="lg:w-[260px] lg:shrink-0">
          <SubjectSwitch active="english" links={subjectLinks} />
        </div>
        <div className="flex grow flex-col gap-1.5">
          <div className="hidden lg:block">
            <Eyebrow muted>Your course</Eyebrow>
          </div>
          <H1>English</H1>
          <Muted className="text-[15px] leading-[22px] lg:text-base lg:leading-6">
            Grammar practice and essay writing, with feedback after you submit.
          </Muted>
        </div>
      </div>

      <div className="grid items-start gap-5 lg:grid-cols-2 lg:grid-rows-[auto_1fr] lg:gap-6">
        <div className="flex flex-col gap-4 lg:col-start-2 lg:row-start-1 lg:gap-6">
          <Card className="gap-3.5">
            <div className="flex items-center justify-between gap-3">
              <H3>English quests today</H3>
              <span className="text-[13px] text-ns-muted">Resets in {questsResetIn}</span>
            </div>
            {quests.map((quest) => (
              <QuestRow key={quest.id} quest={quest} />
            ))}
          </Card>
          <Card tone="amber" className="flex-row items-start gap-3 border-ns-amber-soft">
            <span className="flex text-ns-amber-text">
              <FileText size={22} aria-hidden />
            </span>
            <div className="flex flex-col gap-0.5">
              <H3>
                {essayMarksLeft} essay mark{essayMarksLeft === 1 ? "" : "s"} left in the beta
              </H3>
              <p className="m-0 text-sm leading-5 text-ns-muted">Each essay you submit gets full feedback. Drafts are free and unlimited.</p>
            </div>
          </Card>
        </div>

        <Card className="gap-3 lg:col-start-1 lg:row-span-2 lg:row-start-1">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <H2>Grammar and vocabulary</H2>
            <Tag tone="success">
              {proficient} of {grammarUnits.length} proficient
            </Tag>
          </div>
          <Muted>Short questions, marked right away. Each answer comes with a one-line reason.</Muted>
          <div className="-mx-3 flex flex-col gap-1">
            {grammarUnits.map((unit, i) => (
              <GrammarUnitRow key={unit.key} unit={unit} position={i + 1} />
            ))}
          </div>
        </Card>

        <Card className="gap-3.5 lg:col-start-2 lg:row-start-2">
          <div className="flex items-center justify-between gap-3">
            <H2>Writing</H2>
            <Link href={myEssaysHref} className="text-sm font-semibold text-ns-amber-text underline">
              My essays
            </Link>
          </div>
          <div className="flex flex-col gap-2.5">
            {writingTasks.map((task) => (
              <WritingTaskCard key={task.key} task={task} />
            ))}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Grammar question (choices)                                          */
/* ------------------------------------------------------------------ */

export type GrammarState = "answering" | "wrong" | "right";

/** NEW. One answer choice. */
export interface GrammarChoice {
  id: string;
  label: string;
}

export interface GrammarQuestionProps {
  player: Player;
  state: GrammarState;
  /** NEW. Unit title, e.g. "Subject and verb agreement". Shown on the stem tag. */
  topic: string;
  /** Shorter title for the header when the combo chip needs the room. Defaults to `topic`. */
  headerTopic?: string;
  position: number;
  total: number;
  instruction: string;
  /** The sentence. Build it with <Gap /> where the blank goes. */
  stem: ReactNode;
  choices: GrammarChoice[];
  /** The choice picked and not yet checked (answering state). */
  selectedId: string | null;
  /** Choices already tried and wrong. Struck through and disabled. */
  wrongIds: string[];
  /** Revealed once right. */
  correctId?: string;
  /** Wrong: a nudge. Right: the one-line reason. */
  reason?: ReactNode;
  /** NEW. Gamification. */
  firstTryXp: number;
  retryXp: number;
  earnedXp?: number;
  /** Right answers in a row. Shows the combo chip from 2. */
  combo?: number;
  /** Quest that moved with this answer. */
  questProgress?: Quest;
  closeHref: Href;
  /** Where Check answer goes in the preview. In the app, wire a handler. */
  checkHref?: Href;
  nextHref: Href;
  routes?: KitRoutes;
}

function ChoiceButton({
  choice,
  selected,
  wrong,
  correct,
  locked,
}: {
  choice: GrammarChoice;
  selected: boolean;
  wrong: boolean;
  correct: boolean;
  locked: boolean;
}) {
  return (
    <button
      type="button"
      aria-pressed={selected || correct}
      disabled={wrong || locked}
      className={cn(
        "flex h-14 min-w-0 items-center justify-between gap-2 rounded-xl border-[1.5px] px-[18px] text-left text-lg font-semibold text-ns-ink",
        correct
          ? "border-ns-success bg-ns-success-soft"
          : wrong
            ? "border-ns-danger bg-ns-danger-soft"
            : selected
              ? "border-ns-ink bg-ns-brand-soft"
              : "border-ns-line-strong bg-ns-raised hover:bg-ns-sunken",
        !wrong && !locked && "cursor-pointer",
        focusRing,
      )}
    >
      <span className={cn("truncate", wrong && "line-through")}>
        {choice.label}
        {wrong ? <span className="sr-only"> (not right)</span> : null}
        {correct ? <span className="sr-only"> (right)</span> : null}
      </span>
      {correct ? <Check size={18} className="shrink-0 text-ns-success" aria-hidden /> : null}
      {wrong ? <X size={18} className="shrink-0 text-ns-danger" aria-hidden /> : null}
    </button>
  );
}

/** Canvas: GrammarQuestion.m, GrammarWrong.m, GrammarRight.m */
export function GrammarQuestionScreen({
  player,
  state,
  topic,
  headerTopic,
  position,
  total,
  instruction,
  stem,
  choices,
  selectedId,
  wrongIds,
  correctId,
  reason,
  firstTryXp,
  retryXp,
  earnedXp,
  combo,
  questProgress,
  closeHref,
  checkHref,
  nextHref,
  routes = PREVIEW_ROUTES,
}: GrammarQuestionProps) {
  const right = state === "right";
  const chip = combo && combo >= 2 && right ? <ComboChip label={`${combo} IN A ROW`} /> : <StreakChip small days={player.streakDays} href={routes.streak} />;
  const header = <EnglishQuestionHeader topic={headerTopic ?? topic} position={position} total={total} right={chip} closeHref={closeHref} />;
  const canCheck = state === "answering" && selectedId !== null;

  const footer = (
    <QuestionFooter>
      {state === "answering" ? <XpNote center>Right first try: +{firstTryXp} XP</XpNote> : null}
      {state === "wrong" ? <XpNote center>Pick again. Still +{retryXp} XP</XpNote> : null}
      {right && questProgress ? <QuestToast quest={questProgress} /> : null}
      {right ? (
        <Button variant="primary" full href={nextHref} iconRight={ArrowRight}>
          Next question
        </Button>
      ) : (
        <Button variant="primary" full href={canCheck ? checkHref : undefined} disabled={!canCheck}>
          Check answer
        </Button>
      )}
    </QuestionFooter>
  );

  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={680}
      top={header}
      desktopTop={header}
      footer={footer}
      overlay={right ? <Confetti count={14} seed={8} /> : undefined}
    >
      {state === "wrong" ? (
        <Feedback kind="wrong" note={`Mistakes never cost XP. Get it now for +${retryXp} XP.`}>
          {reason}
        </Feedback>
      ) : null}
      {right ? (
        <Feedback kind="right" title="Spot on!" xp={earnedXp}>
          {reason}
        </Feedback>
      ) : null}
      <QuestionStem topic={topic} instruction={instruction} stem={stem} />
      <div role="group" aria-label="Answer choices" className="grid grid-cols-2 gap-2.5">
        {choices.map((choice) => (
          <ChoiceButton
            key={choice.id}
            choice={choice}
            selected={state === "answering" && choice.id === selectedId}
            wrong={wrongIds.includes(choice.id)}
            correct={right && choice.id === correctId}
            locked={right}
          />
        ))}
      </div>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Vocabulary question (typed answer)                                  */
/* ------------------------------------------------------------------ */

export interface VocabQuestionProps {
  player: Player;
  /** NEW. e.g. "Words in context". */
  topic: string;
  position: number;
  total: number;
  instruction: string;
  stem: ReactNode;
  hint?: ReactNode;
  /** What the student has typed so far. */
  answer: string;
  /** NEW. */
  firstTryXp: number;
  closeHref: Href;
  checkHref?: Href;
  routes?: KitRoutes;
}

/** Canvas: VocabQuestion.m */
export function VocabQuestionScreen({
  player,
  topic,
  position,
  total,
  instruction,
  stem,
  hint,
  answer,
  firstTryXp,
  closeHref,
  checkHref,
  routes = PREVIEW_ROUTES,
}: VocabQuestionProps) {
  const header = (
    <EnglishQuestionHeader
      topic={topic}
      position={position}
      total={total}
      right={<StreakChip small days={player.streakDays} href={routes.streak} />}
      closeHref={closeHref}
    />
  );
  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={680}
      top={header}
      desktopTop={header}
      footer={
        <QuestionFooter>
          <XpNote center>Right first try: +{firstTryXp} XP</XpNote>
          <Button variant="primary" full href={answer.trim() ? checkHref : undefined} disabled={!answer.trim()}>
            Check answer
          </Button>
        </QuestionFooter>
      }
    >
      <QuestionStem topic={topic} instruction={instruction} stem={stem} hint={hint} />
      <Card>
        <Field id="vocab-answer" label="Your answer" value={answer} hint="Spelling counts." />
      </Card>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Essay: the task                                                     */
/* ------------------------------------------------------------------ */

export interface EssayPromptProps {
  player: Player;
  task: WritingTask;
  /** NEW. */
  submitXp: number;
  /** NEW. Name of the badge a first essay unlocks, if not earned yet. */
  firstEssayBadge?: string;
  backHref: Href;
  startHref: Href;
  routes?: KitRoutes;
}

/** Canvas: EssayPrompt.m */
export function EssayPromptScreen({ player, task, submitXp, firstEssayBadge, backHref, startHref, routes = PREVIEW_ROUTES }: EssayPromptProps) {
  const rules = [
    { icon: FileText, text: `${task.words.min} to ${task.words.max} words.` },
    { icon: RefreshCw, text: "Your draft saves as you type, on any device." },
    { icon: Sparkles, text: "No AI help while you write. Feedback comes after you submit." },
    { icon: Lock, text: "After you submit, this version is locked. You can start a new version any time." },
  ];
  return (
    <FocusShell
      player={player}
      routes={routes}
      className="gap-5"
      top={<TopBar title="Writing task" backHref={backHref} />}
      footer={
        <FooterBar>
          <div className="flex flex-col gap-2 lg:flex-row-reverse lg:items-center lg:justify-end lg:gap-4">
            <XpNote>
              Submit for +{submitXp} XP.{firstEssayBadge ? ` Your first essay unlocks the ${firstEssayBadge} badge.` : ""}
            </XpNote>
            <Button variant="primary" full href={startHref} iconRight={ArrowRight} className="lg:w-auto">
              Start writing
            </Button>
          </div>
        </FooterBar>
      }
    >
      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-8">
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-2">
              <Tag tone="brand">{task.kind}</Tag>
              <Tag icon={Clock}>About {task.minutes} min</Tag>
            </div>
            <H1 className="text-2xl leading-8 lg:text-[28px] lg:leading-9">{task.title}</H1>
          </div>
          <Card className="gap-3.5">
            <p className="m-0 text-base leading-6 text-ns-ink">{task.brief}</p>
            <Divider />
            <TaskFrame task={task} />
          </Card>
        </div>
        <div className="flex flex-col gap-5">
          <Card tone="sunken" className="gap-3">
            <H3>How it is marked</H3>
            <dl className="m-0 flex flex-col gap-2.5">
              {task.rubric.map((row) => (
                <div key={row.name} className="flex items-center gap-2">
                  <dt className="grow text-[15px] font-semibold">{row.name}</dt>
                  <dd className="m-0 text-sm text-ns-muted">{row.marks} marks</dd>
                </div>
              ))}
            </dl>
            <Muted className="text-[13px] leading-[18px]">
              The same rubric the feedback uses.{" "}
              <Link href={task.rubricHref} className="font-semibold text-ns-amber-text underline">
                See the full rubric
              </Link>
            </Muted>
          </Card>
          <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
            {rules.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-start gap-2.5">
                <span className="flex pt-0.5 text-ns-muted">
                  <Icon size={18} aria-hidden />
                </span>
                <Muted>{text}</Muted>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Essay: editor and submit sheet                                      */
/* ------------------------------------------------------------------ */

export interface EssayDraft {
  /** NEW. 1 for the first version. */
  version: number;
  text: string;
  wordCount: number;
  /** e.g. "10 s ago". */
  savedLabel: string;
  /** Set when a newer draft from another device was loaded. */
  restoredNotice?: string;
}

export interface EssayEditorProps {
  player: Player;
  task: WritingTask;
  draft: EssayDraft;
  /** NEW. */
  submitXp: number;
  backHref: Href;
  submitHref: Href;
  routes?: KitRoutes;
}

/** A pre-submit check shown in the submit sheet. */
export interface SubmitCheck {
  ok: boolean;
  text: string;
}

export interface EssaySubmitProps extends EssayEditorProps {
  /** NEW. e.g. word range, unfinished sentence, marks left. */
  checks: SubmitCheck[];
  /** NEW. Reward line. */
  rewardNote?: string;
  confirmHref: Href;
  keepWritingHref: Href;
}

function WordGoal({ count, min, max }: { count: number; min: number; max: number }) {
  const reached = count >= min && count <= max;
  return reached ? (
    <span className="inline-flex items-center gap-1 text-sm font-bold text-ns-success">
      <GameIcon name="star" size={14} className="text-ns-gold" />
      Word goal reached
    </span>
  ) : (
    <span className="text-sm font-semibold text-ns-amber-text">
      Aim for {min} to {max}
    </span>
  );
}

function EssayEditorBody({
  player,
  task,
  draft,
  submitXp,
  backHref,
  submitHref,
  routes = PREVIEW_ROUTES,
  dialog,
}: EssayEditorProps & { dialog?: ReactNode }) {
  const pct = Math.min(100, Math.round((draft.wordCount / Math.max(1, task.words.max)) * 100));
  const submitNote = <XpNote>Submitting earns +{submitXp} XP. Keep editing as long as you like.</XpNote>;
  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={1120}
      top={<TopBar title="Draft" sub={task.kind} backHref={backHref} />}
      desktopTop={
        <div className="flex flex-col gap-1.5">
          <Link href={backHref} className={cn("inline-flex items-center gap-1 self-start text-sm font-semibold text-ns-muted no-underline", focusRing)}>
            <ChevronLeft size={18} aria-hidden />
            English
          </Link>
          <H1 className="lg:text-[28px] lg:leading-9">Draft, version {draft.version}</H1>
        </div>
      }
      footer={
        <FooterBar className="lg:hidden">
          <Button variant="primary" full href={submitHref}>
            Submit for feedback
          </Button>
          {submitNote}
        </FooterBar>
      }
    >
      {dialog}
      <div className="grid items-start gap-4 lg:grid-cols-[360px_minmax(0,1fr)] lg:gap-8">
        {/* Phones: collapsible task summary */}
        <details className="group rounded-xl border border-ns-line bg-ns-sunken lg:hidden">
          <summary
            className={cn(
              "flex min-h-11 cursor-pointer list-none items-center gap-2.5 rounded-xl px-4 py-3 text-[15px] leading-5 font-semibold [&::-webkit-details-marker]:hidden",
              focusRing,
            )}
          >
            <FileText size={18} aria-hidden className="shrink-0" />
            <span className="grow">The task: {task.title}</span>
            <ChevronDown size={18} aria-hidden className="shrink-0 transition-transform group-open:rotate-180" />
          </summary>
          <div className="flex flex-col gap-3.5 px-4 pb-4">
            <p className="m-0 text-[15px] leading-[22px] text-ns-ink">{task.brief}</p>
            <TaskFrame task={task} />
          </div>
        </details>

        {/* Desktop: task panel */}
        <Card shadow={false} className="hidden gap-3.5 p-6 lg:flex">
          <div className="flex flex-wrap gap-2">
            <Tag tone="brand">{task.kind}</Tag>
            <Tag>
              {task.words.min} to {task.words.max} words
            </Tag>
          </div>
          <H2>{task.title}</H2>
          <p className="m-0 text-[15px] leading-[22px] text-ns-ink">{task.brief}</p>
          <Divider />
          <TaskFrame task={task} />
          <Divider />
          <div className="flex items-start gap-2 text-ns-muted">
            <Sparkles size={18} aria-hidden className="shrink-0" />
            <Muted className="text-[13px] leading-[18px]">No AI help while you write. Feedback comes after you submit.</Muted>
          </div>
        </Card>

        <div className="flex min-w-0 flex-col gap-4">
          {/* Desktop only, as designed: on phones it would push the word count below the fold. */}
          {draft.restoredNotice ? (
            <div className="hidden lg:block">
              <Callout tone="brand" icon={RefreshCw}>
                <p className="m-0">
                  <b>Draft restored.</b> {draft.restoredNotice}
                </p>
              </Callout>
            </div>
          ) : null}
          <div className="flex flex-col gap-2">
            <label htmlFor="essay-draft" className="text-[15px] font-semibold">
              Your {task.formatNoun}
            </label>
            <textarea
              id="essay-draft"
              aria-describedby="essay-draft-count"
              defaultValue={draft.text}
              spellCheck
              className={cn(
                "h-[420px] w-full resize-y rounded-xl border-[1.5px] border-ns-line-strong bg-ns-raised p-4 text-[17px] leading-7 text-ns-ink lg:h-[520px] lg:p-6 lg:text-lg lg:leading-[30px]",
                focusRing,
              )}
            />
            <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
              <span id="essay-draft-count" className="text-sm font-semibold tabular-nums">
                {draft.wordCount} words
              </span>
              <WordGoal count={draft.wordCount} min={task.words.min} max={task.words.max} />
              <span role="status" className="ml-auto inline-flex items-center gap-1.5 text-[13px] text-ns-muted">
                <Check size={14} aria-hidden />
                Saved {draft.savedLabel}
              </span>
            </div>
            <div
              role="progressbar"
              aria-label={`Words toward ${task.words.max}`}
              aria-valuenow={pct}
              aria-valuemin={0}
              aria-valuemax={100}
              className="h-1.5 overflow-hidden rounded-full bg-ns-line"
            >
              <div className="h-full rounded-full bg-ns-amber" style={{ width: `${pct}%` }} />
            </div>
          </div>
          <div className="hidden items-center gap-4 lg:flex">
            <Button variant="primary" href={submitHref}>
              Submit for feedback
            </Button>
            {submitNote}
          </div>
        </div>
      </div>
    </FocusShell>
  );
}

/** Canvas: EssayEditor.m, EssayEditor.d */
export function EssayEditorScreen(props: EssayEditorProps) {
  return <EssayEditorBody {...props} />;
}

/** Canvas: EssaySubmit.m (the sheet over the dimmed editor) */
export function EssaySubmitScreen({ checks, rewardNote, confirmHref, keepWritingHref, submitXp, ...editor }: EssaySubmitProps) {
  const sheet = (
    <Sheet titleId="essay-submit-title">
      <H2 className="leading-7">
        <span id="essay-submit-title">Submit this version?</span>
      </H2>
      <Muted className="text-[15px] leading-[22px]">
        After you submit, this version is locked and sent for marking. You can start a new version later.
      </Muted>
      <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
        {checks.map((check) => (
          <li key={check.text} className="flex items-center gap-2.5 text-[15px] leading-[22px]">
            {check.ok ? (
              <CheckCircle2 size={20} className="shrink-0 text-ns-success" aria-label="OK" />
            ) : (
              <AlertCircle size={20} className="shrink-0 text-ns-amber-text" aria-label="Check this" />
            )}
            {check.text}
          </li>
        ))}
      </ul>
      <RewardLine
        icon={<GameIcon name="bolt" size={20} className="text-ns-amber" />}
        title={`+${submitXp} XP when you submit`}
        sub={rewardNote}
        right={<XpPill xp={submitXp} />}
      />
      <div className="flex flex-col gap-2">
        <Button variant="primary" full href={confirmHref}>
          Submit for feedback
        </Button>
        <Button full href={keepWritingHref}>
          Keep writing
        </Button>
      </div>
    </Sheet>
  );
  return <EssayEditorBody {...editor} submitXp={submitXp} dialog={sheet} />;
}

/* ------------------------------------------------------------------ */
/* Essay: being marked                                                 */
/* ------------------------------------------------------------------ */

export type MarkingStepState = "done" | "now" | "next";

export interface EssayMarkingProps {
  player: Player;
  formatNoun: string;
  /** NEW. XP added on submit. */
  submitXp: number;
  steps: { label: string; state: MarkingStepState }[];
  version: { number: number; wordCount: number; submittedLabel: string; href: Href };
  /** NEW. */
  practiseXp: number;
  practiseHref: Href;
  backHref: Href;
  routes?: KitRoutes;
}

/** Canvas: EssayMarking.m */
export function EssayMarkingScreen({
  player,
  formatNoun,
  submitXp,
  steps,
  version,
  practiseXp,
  practiseHref,
  backHref,
  routes = PREVIEW_ROUTES,
}: EssayMarkingProps) {
  return (
    <FocusShell player={player} routes={routes} maxWidth={640} className="gap-5" top={<TopBar title="Feedback" backHref={backHref} />}>
      <div className="flex flex-col gap-2.5 pt-1">
        <div className="flex items-center gap-3.5">
          <div className="animate-ns-float">
            <Hornbill size={96} mood="think" branch={false} />
          </div>
          <div className="flex flex-col items-start gap-1.5">
            <XpPill xp={submitXp} />
            <span className="text-[13px] leading-[18px] font-bold text-ns-amber-text">Added for submitting</span>
          </div>
        </div>
        <H1>Marking your {formatNoun}</H1>
        <Muted className="text-base leading-6">
          This usually takes about 2 minutes. You can leave this page. We will show a message on your dashboard when it is ready.
        </Muted>
      </div>
      <Card>
        <ol role="status" className="m-0 flex list-none flex-col gap-3.5 p-0">
          {steps.map((step) => (
            <li key={step.label} className="flex items-center gap-3">
              <span
                className={cn(
                  "inline-flex size-7 shrink-0 items-center justify-center rounded-full",
                  step.state === "done" && "bg-ns-success-soft text-ns-success",
                  step.state === "now" && "bg-ns-amber-soft text-ns-amber-text",
                  step.state === "next" && "bg-ns-sunken",
                )}
              >
                {step.state === "done" ? <Check size={16} aria-label="Done" /> : null}
                {step.state === "now" ? <Clock size={16} aria-label="In progress" /> : null}
              </span>
              <span
                className={cn(
                  "text-[15px] leading-[22px]",
                  step.state === "now" && "font-semibold",
                  step.state === "next" ? "text-ns-muted" : "text-ns-ink",
                )}
              >
                {step.label}
              </span>
            </li>
          ))}
        </ol>
      </Card>
      <Card shadow={false} className="flex-row items-center gap-3 p-4">
        <Lock size={18} className="shrink-0 text-ns-muted" aria-hidden />
        <div className="flex min-w-0 grow flex-col">
          <span className="text-[15px] font-semibold">
            Version {version.number} · {version.wordCount} words
          </span>
          <span className="text-[13px] text-ns-muted">Submitted {version.submittedLabel}</span>
        </div>
        <Button variant="ghost" size="sm" href={version.href}>
          Read it
        </Button>
      </Card>
      <div className="flex flex-col gap-2">
        <Button full href={practiseHref}>
          Practise grammar while you wait · +{practiseXp} XP each
        </Button>
        <Button variant="ghost" full href={backHref}>
          Back to English
        </Button>
      </div>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Essay: feedback                                                     */
/* ------------------------------------------------------------------ */

/** NEW. One "Fix these first" item from the AI feedback. */
export interface EssayFix {
  title: string;
  body: ReactNode;
}

/** NEW. Score and evidence for one rubric criterion. */
export interface CriterionFeedback {
  name: string;
  score: number;
  outOf: number;
  level: string;
  levelTone: Tone;
  summary: string;
  quote: string;
  followUp: ReactNode;
}

export interface EssayFeedbackProps {
  player: Player;
  task: Pick<WritingTask, "kind" | "title" | "formatNoun">;
  version: {
    number: number;
    /** Paragraphs of the submitted text. */
    paragraphs: string[];
    wordCount: number;
    submittedLabel: string;
  };
  /** NEW. Exact phrases in the text to highlight (desktop essay view). */
  highlights: string[];
  score: { total: number; outOf: number; label: string };
  fixes: EssayFix[];
  practise?: { label: string; href: Href };
  criteria: CriterionFeedback[];
  strengths: string[];
  /** NEW. Badge won with this submission. */
  badgeWon?: { name: string; icon: BadgeIcon; tier: Tier; message: string; xp: number };
  /** NEW. XP for raising a score in the next version. */
  improveXp: number;
  /** Usefulness rating already given, 1 to 5. */
  rating: number | null;
  writeNextHref: Href;
  modelAnswerHref: Href;
  essayHref: Href;
  reportHref: Href;
  backHref: Href;
  routes?: KitRoutes;
}

function highlight(text: string, phrases: string[]): ReactNode {
  const hits = phrases.filter((p) => p && text.includes(p));
  if (!hits.length) return text;
  const pattern = new RegExp(`(${hits.map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`);
  return text.split(pattern).map((part, i) =>
    hits.includes(part) ? (
      <mark key={i} className="rounded-[3px] bg-ns-amber-soft px-0.5 text-ns-ink">
        {part}
      </mark>
    ) : (
      part
    ),
  );
}

function CriterionCard({ c }: { c: CriterionFeedback }) {
  return (
    <Card className="gap-3">
      <div className="flex items-center gap-2">
        <H3 className="grow">{c.name}</H3>
        <span className="text-lg font-bold tabular-nums">
          {c.score}
          <span className="text-sm font-medium text-ns-muted"> / {c.outOf}</span>
        </span>
      </div>
      <div
        role="progressbar"
        aria-label={`${c.name}: ${c.score} of ${c.outOf}`}
        aria-valuenow={c.score}
        aria-valuemin={0}
        aria-valuemax={c.outOf}
        className="h-2 overflow-hidden rounded-full bg-ns-brand-soft"
      >
        <div className="h-full rounded-full bg-ns-success" style={{ width: `${Math.round((c.score / Math.max(1, c.outOf)) * 100)}%` }} />
      </div>
      <div className="flex">
        <Tag tone={c.levelTone}>{c.level}</Tag>
      </div>
      <p className="m-0 text-[15px] leading-[22px]">{c.summary}</p>
      <blockquote className="m-0 rounded-[10px] bg-ns-sunken px-3.5 py-2.5 text-[15px] leading-[22px] italic">“{c.quote}”</blockquote>
      <p className="m-0 text-[15px] leading-[22px]">{c.followUp}</p>
    </Card>
  );
}

/** Canvas: EssayFeedback.m, EssayFeedback.d */
export function EssayFeedbackScreen({
  player,
  task,
  version,
  highlights,
  score,
  fixes,
  practise,
  criteria,
  strengths,
  badgeWon,
  improveXp,
  rating,
  writeNextHref,
  modelAnswerHref,
  essayHref,
  reportHref,
  backHref,
  routes = PREVIEW_ROUTES,
}: EssayFeedbackProps) {
  return (
    <FocusShell player={player} routes={routes} maxWidth={1120} top={<TopBar title="Feedback" backHref={backHref} />}>
      <div className="grid items-start gap-5 lg:grid-cols-2 lg:gap-8">
        {/* Left on desktop: heading, badge, score, the essay */}
        <div className="flex min-w-0 flex-col gap-5">
          <div className="flex flex-col gap-2.5">
            <div className="flex flex-wrap gap-2">
              <Tag tone="brand">{task.kind}</Tag>
              <Tag icon={Sparkles}>AI estimate</Tag>
            </div>
            <H1 className="lg:text-[26px] lg:leading-8">Feedback on version {version.number}</H1>
            <Muted className="text-[15px] leading-[22px]">{task.title}</Muted>
          </div>

          {badgeWon ? (
            <Card tone="amber" className="gap-2.5 p-[18px] shadow-ns-sm">
              <div className="flex items-center gap-3">
                <Medal icon={badgeWon.icon} tier={badgeWon.tier} size={52} pop />
                <div className="flex min-w-0 grow flex-col gap-0.5">
                  <Eyebrow>New badge</Eyebrow>
                  <H3>{badgeWon.name}</H3>
                  <Muted className="text-[13px] leading-[18px]">{badgeWon.message}</Muted>
                </div>
                <XpTag xp={badgeWon.xp} />
              </div>
              <div className="flex items-center gap-1.5 text-ns-amber-text">
                <GameIcon name="target" size={16} />
                <span className="text-[13px] leading-[18px] font-semibold">
                  Write version {version.number + 1} and raise any score for another +{improveXp} XP.
                </span>
              </div>
            </Card>
          ) : null}

          <Card className="gap-2.5">
            <div className="flex items-center gap-3">
              <div className="flex grow flex-col gap-0.5">
                <Eyebrow muted>Estimated score</Eyebrow>
                <span className="text-[40px] leading-[44px] font-bold tabular-nums">
                  {score.total}
                  <span className="text-xl font-medium text-ns-muted"> / {score.outOf}</span>
                </span>
              </div>
              <Tag tone="amber">{score.label}</Tag>
            </div>
            <Muted className="text-[13px] leading-[18px]">
              An AI estimate using the NextScholar rubric. A teacher or mentor may mark it a little differently.
            </Muted>
          </Card>

          <Card className="hidden gap-3.5 p-6 lg:flex">
            <div className="flex items-center justify-between gap-3">
              <H3>
                Your {task.formatNoun}, version {version.number}
              </H3>
              <Tag icon={Lock}>Locked</Tag>
            </div>
            <div className="flex flex-col gap-3.5">
              {version.paragraphs.map((para, i) => (
                <p key={i} className="m-0 text-base leading-[26px]">
                  {highlight(para, highlights)}
                </p>
              ))}
            </div>
            <Muted className="text-[13px] leading-[18px]">
              {version.wordCount} words · submitted {version.submittedLabel}
            </Muted>
          </Card>
        </div>

        {/* Right on desktop: what to fix, criteria, rating, actions */}
        <div className="flex min-w-0 flex-col gap-5">
          <Card className="gap-3.5">
            <H3>Fix these first</H3>
            <ol className="m-0 flex list-none flex-col gap-4 p-0">
              {fixes.map((fix, i) => (
                <li key={fix.title} className="flex items-start gap-3">
                  <span className="inline-flex size-[26px] shrink-0 items-center justify-center rounded-full bg-ns-amber-soft text-[13px] font-bold text-ns-amber-text">
                    {i + 1}
                  </span>
                  <div className="flex min-w-0 flex-col gap-1">
                    <span className="text-base font-semibold">{fix.title}</span>
                    <p className="m-0 text-[15px] leading-[22px]">{fix.body}</p>
                  </div>
                </li>
              ))}
            </ol>
            {practise ? (
              <Button size="sm" full href={practise.href} icon={RotateCcw}>
                {practise.label}
              </Button>
            ) : null}
          </Card>

          {criteria.map((c) => (
            <CriterionCard key={c.name} c={c} />
          ))}

          <Card className="gap-3">
            <H3>What went well</H3>
            <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
              {strengths.map((s) => (
                <li key={s} className="flex items-start gap-2.5">
                  <Check size={18} className="mt-0.5 shrink-0 text-ns-success" aria-hidden />
                  <span className="text-[15px] leading-[22px]">{s}</span>
                </li>
              ))}
            </ul>
          </Card>

          <div className="flex flex-col gap-2 lg:order-last">
            <Button variant="primary" full href={writeNextHref} icon={FileText}>
              Write version {version.number + 1} · +{improveXp} XP
            </Button>
            <Button full href={modelAnswerHref} icon={BookOpen}>
              Read a model answer
            </Button>
            <Button variant="ghost" full href={essayHref}>
              See my essay
            </Button>
          </div>

          <Card tone="sunken" className="gap-3">
            <H3>
              <span id="feedback-useful">Was this feedback useful?</span>
            </H3>
            <div role="group" aria-labelledby="feedback-useful" className="flex gap-2">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  aria-label={`${n} of 5`}
                  aria-pressed={rating === n}
                  className={cn(
                    "h-11 min-w-0 flex-1 cursor-pointer rounded-xl border-[1.5px] text-base font-bold",
                    rating === n ? "border-ns-ink bg-ns-ink text-ns-on-brand" : "border-ns-line-strong bg-ns-raised text-ns-ink hover:bg-ns-sunken",
                    focusRing,
                  )}
                >
                  {n}
                </button>
              ))}
            </div>
            <div className="flex justify-between text-xs text-ns-muted">
              <span>Not useful</span>
              <span>Very useful</span>
            </div>
            <Link href={reportHref} className="self-start text-sm font-semibold text-ns-amber-text underline">
              Something looks wrong in this feedback
            </Link>
          </Card>
        </div>
      </div>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Essay history                                                       */
/* ------------------------------------------------------------------ */

export type EssayVersionStatus = "marking" | "marked" | "draft";

/** NEW. One row in My essays. */
export interface EssayVersionSummary {
  key: string;
  title: string;
  status: EssayVersionStatus;
  /** Null for a draft that was never submitted. */
  version: number | null;
  /** "today", "18 Sep", "3 days ago". */
  dateLabel: string;
  score?: { total: number; outOf: number };
  /** Drafts only. */
  wordCount?: number;
  href: Href;
}

export interface EssayHistoryProps {
  player: Player;
  essays: EssayVersionSummary[];
  /** NEW. Latest improvement between two versions of the same task. */
  improvement?: { marks: number; taskLabel: string; from: number; to: number; xp: number };
  backHref: Href;
  routes?: KitRoutes;
}

const HISTORY_TAG: Record<EssayVersionStatus, { label: string; tone: Tone; icon?: typeof Clock }> = {
  marking: { label: "Marking", tone: "amber", icon: Clock },
  marked: { label: "Marked", tone: "success", icon: CheckCircle2 },
  draft: { label: "Draft", tone: "neutral" },
};

function historyDetail(e: EssayVersionSummary) {
  if (e.status === "draft") return `Draft · ${e.wordCount ?? 0} words · edited ${e.dateLabel}`;
  if (e.status === "marking") return `Version ${e.version ?? 1} · submitted ${e.dateLabel}`;
  return `Version ${e.version ?? 1} · ${e.dateLabel}${e.score ? ` · ${e.score.total} of ${e.score.outOf}` : ""}`;
}

/** Canvas: EssayHistory.m */
export function EssayHistoryScreen({ player, essays, improvement, backHref, routes = PREVIEW_ROUTES }: EssayHistoryProps) {
  return (
    <AppShell
      active="course"
      player={player}
      routes={routes}
      maxWidth={720}
      className="gap-5"
      top={<TopBar title="My essays" backHref={backHref} right={<MiniChips player={player} routes={routes} />} />}
    >
      <div className="flex flex-col gap-1.5">
        <Link href={backHref} className={cn("hidden items-center gap-1 self-start text-sm font-semibold text-ns-muted no-underline lg:inline-flex", focusRing)}>
          <ChevronLeft size={18} aria-hidden />
          English
        </Link>
        <H1>My essays</H1>
        <Muted className="text-[15px] leading-[22px]">Every submitted version stays here with its feedback. Drafts are kept until you delete them.</Muted>
      </div>
      <Card className="gap-0 py-1.5">
        <ul className="m-0 flex list-none flex-col p-0">
          {essays.map((e, i) => {
            const tag = HISTORY_TAG[e.status];
            return (
              <li key={e.key} className={cn(i > 0 && "border-t border-ns-line")}>
                <Link
                  href={e.href}
                  className={cn("-mx-2 flex flex-col gap-1.5 rounded-lg px-2 py-3.5 text-inherit no-underline hover:bg-ns-surface", focusRing)}
                >
                  <div className="flex items-start gap-2.5">
                    <span className="grow text-base leading-[22px] font-semibold">{e.title}</span>
                    <Tag tone={tag.tone} icon={tag.icon}>
                      {tag.label}
                    </Tag>
                  </div>
                  <span className="text-[13px] leading-[18px] text-ns-muted">{historyDetail(e)}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </Card>
      {improvement ? (
        <Callout tone="success" icon={BarChart3}>
          <p className="m-0">
            <b>You improved by {improvement.marks} marks</b> on the {improvement.taskLabel} between version {improvement.from} and version{" "}
            {improvement.to}. That earned +{improvement.xp} XP.
          </p>
        </Callout>
      ) : null}
    </AppShell>
  );
}
