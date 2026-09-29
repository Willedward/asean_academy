import Link from "next/link";
import type { ReactNode } from "react";
import {
  ArrowRight,
  Captions,
  Check,
  ChevronDown,
  ChevronLeft,
  Clock,
  Download,
  FileText,
  List,
  Lock,
  Maximize,
  Pause,
  Play,
  RotateCcw,
} from "lucide-react";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { GameIcon } from "../components/icons";
import { LessonStateTag } from "../components/lesson-row";
import {
  DoubleXpPill,
  MiniChips,
  Stars,
  XpBar,
  XpPill,
  XpTag,
} from "../components/rewards";
import {
  Button,
  Card,
  Divider,
  H1,
  H2,
  H3,
  Muted,
  Steps,
  Tag,
  focusRing,
} from "../components/ui";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import { FocusShell, FooterBar, Logo, TopBar } from "../shell/app-shell";
import type { Href, LessonUiState, Player, Stars as StarCount } from "../types";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

/** Lesson heading data. Most of it comes from LessonResponse. */
export interface LessonMeta {
  /** API: LessonResponse.position */
  position: number;
  /** Lessons in the unit. API: CourseMap unit lessons length. */
  lessonCount: number;
  /** API: LessonResponse.title */
  title: string;
  /** API: LessonResponse.estimated_minutes */
  minutes: number;
  /** API: LessonProgressResponse.state, mapped with toLessonUiState(). */
  state: LessonUiState;
  /** NEW */
  stars: StarCount;
  /** Unit code, e.g. "N1". API: LessonResponse.unit_key via the course map. */
  unitCode: string;
  /** Unit title, e.g. "Numbers and their operations". */
  unitTitle: string;
  unitHref: Href;
}

/** The lesson video, shown as a poster that opens the video screen. */
export interface LessonVideoSummary {
  /** Text over the poster, bottom left. */
  title: string;
  /** e.g. "6:12" */
  duration: string;
  /** Whole minutes, for the play button label. */
  minutes: number;
  /** NEW. XP for watching to the end. */
  xp: number;
  /** NEW. Watched to the end. */
  done: boolean;
  href: Href;
  transcriptHref: Href;
  /** Optional poster image, e.g. a next/image with fill. */
  poster?: ReactNode;
}

/**
 * One teaching section. API: LessonResponse.sections[] (content rendered with
 * the app's MathContent, passed in as `content`).
 */
export interface LessonSection {
  /** Anchor id, used by the contents list. */
  id: string;
  title: string;
  /** NEW. XP for finishing the section. */
  xp: number;
  /** NEW. Section finished. */
  done: boolean;
  content: ReactNode;
}

/** Guided practice call to action at the end of a lesson. */
export interface LessonPracticeCta {
  /** API: LessonResponse.practice.question_count */
  questionCount: number;
  /** API: LessonResponse.practice.available */
  available: boolean;
  /** NEW. Stars won so far in this lesson. */
  stars: StarCount;
  /** NEW. Rough XP on offer. */
  xp: number;
  /** NEW. The daily quest this practice counts toward. */
  quest?: { title: string; progress: number; target: number };
  /** Starts a session (createPracticeSession) and opens the player. */
  href: Href;
}

/* ------------------------------------------------------------------ */
/* Small shared pieces (also used by practice.tsx)                     */
/* ------------------------------------------------------------------ */

/** Desktop "< Parent" link above a page title. */
export function BackLink({
  href,
  children,
}: {
  href: Href;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "-my-2.5 inline-flex min-h-11 items-center gap-1 self-start rounded-full text-sm font-semibold text-ns-muted no-underline hover:text-ns-ink",
        focusRing,
      )}
    >
      <ChevronLeft size={18} aria-hidden />
      {children}
    </Link>
  );
}

export interface NumberedStep {
  text: ReactNode;
  math?: ReactNode;
  /** Long maths line: scrolls sideways in its own labelled box. */
  wide?: boolean;
}

/** A long maths line that scrolls sideways instead of widening the page. */
export function ScrollMath({
  children,
  label = "Working, scrolls sideways",
}: {
  children: ReactNode;
  label?: string;
}) {
  return (
    <div className="relative">
      <div
        tabIndex={0}
        role="region"
        aria-label={label}
        className={cn(
          "overflow-x-auto rounded-[10px] border border-ns-line bg-ns-sunken py-3.5 pr-11 pl-3.5 font-ns-math text-[19px] leading-7 whitespace-nowrap text-ns-ink",
          focusRing,
        )}
      >
        {children}
      </div>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute inset-y-px right-px flex w-12 items-center justify-end rounded-r-[10px] bg-[linear-gradient(90deg,transparent,var(--color-ns-sunken)_70%)] pr-2 text-ns-muted"
      >
        <ArrowRight size={18} />
      </span>
    </div>
  );
}

/** Numbered working: worked examples and solutions. */
export function NumberedSteps({
  steps,
  mathSize = 20,
}: {
  steps: NumberedStep[];
  mathSize?: number;
}) {
  const firstWide = steps.findIndex((step) => step.wide);
  return (
    <ol className="m-0 flex list-none flex-col gap-3.5 p-0">
      {steps.map((step, i) => (
        <li key={i} className="flex items-start gap-3">
          <span
            aria-hidden="true"
            className="inline-flex size-[26px] shrink-0 items-center justify-center rounded-full bg-ns-brand-soft text-[13px] font-bold text-ns-ink"
          >
            {i + 1}
          </span>
          <div className="flex min-w-0 grow flex-col gap-1">
            <span className="text-[15px] leading-[22px] text-ns-muted">
              {step.text}
            </span>
            {step.math && step.wide ? (
              <>
                <ScrollMath>{step.math}</ScrollMath>
                {i === firstWide ? (
                  <span className="flex items-center gap-1.5 text-[13px] leading-[18px] text-ns-muted">
                    <ArrowRight size={16} aria-hidden />
                    Swipe the grey box to see the whole line.
                  </span>
                ) : null}
              </>
            ) : step.math ? (
              <span
                className="font-ns-math text-ns-ink"
                style={{ fontSize: mathSize, lineHeight: "28px" }}
              >
                {step.math}
              </span>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  );
}

/* ------------------------------------------------------------------ */
/* Lesson content building blocks                                      */
/* ------------------------------------------------------------------ */

/** Display maths in a white box, e.g. 2 × 2 × 2 = 2³. */
export function LessonMath({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-ns-line bg-ns-raised p-5 text-center font-ns-math text-2xl text-ns-ink">
      {children}
    </div>
  );
}

export function WorkedExample({
  title,
  steps,
}: {
  title: ReactNode;
  steps: NumberedStep[];
}) {
  return (
    <Card className="gap-4">
      <H3>{title}</H3>
      <NumberedSteps steps={steps} />
    </Card>
  );
}

export interface CheckYourselfProps {
  question: ReactNode;
  options: string[];
  /** Index of the option the learner picked, if any. */
  chosen?: number | null;
  /** Shown after a pick. */
  feedback?: { correct: boolean; body: ReactNode } | null;
  /** NEW */
  xp: number;
}

/** Unmarked recall check inside a lesson. Options are real buttons. */
export function CheckYourself({
  question,
  options,
  chosen = null,
  feedback = null,
  xp,
}: CheckYourselfProps) {
  return (
    <Card className="gap-3.5">
      <div className="flex items-center gap-2">
        <Muted className="grow text-[13px] leading-[18px]">
          Not marked. Just checking the idea landed.
        </Muted>
        <XpTag xp={xp} />
      </div>
      <H3>{question}</H3>
      <div className="flex gap-2">
        {options.map((option, i) => {
          const picked = chosen === i;
          return (
            <button
              key={option}
              type="button"
              aria-pressed={picked}
              className={cn(
                "h-[52px] min-w-0 flex-1 rounded-[14px] border-2 text-[17px] font-extrabold text-ns-ink",
                picked
                  ? feedback && !feedback.correct
                    ? "border-ns-amber-text bg-ns-amber-soft"
                    : "border-ns-success bg-ns-success-soft"
                  : "border-ns-line bg-ns-raised hover:bg-ns-sunken",
                focusRing,
              )}
            >
              {option}
            </button>
          );
        })}
      </div>
      {feedback ? (
        <div
          role="status"
          className={cn(
            "flex animate-ns-pop items-center gap-2.5 rounded-[14px] py-2.5 pr-3 pl-1",
            feedback.correct ? "bg-ns-success-soft" : "bg-ns-amber-soft",
          )}
        >
          <Hornbill
            size={56}
            mood={feedback.correct ? "happy" : "kind"}
            pose={feedback.correct ? "cheer" : "point"}
            branch={false}
          />
          <div className="flex min-w-0 grow flex-col gap-0.5">
            <div className="flex items-center gap-2">
              <b
                className={cn(
                  "text-base",
                  feedback.correct ? "text-ns-success" : "text-ns-amber-text",
                )}
              >
                {feedback.correct ? "Nice one!" : "Not yet."}
              </b>
              {feedback.correct ? <XpTag xp={xp} /> : null}
            </div>
            <p className="m-0 text-sm leading-5 text-ns-ink">{feedback.body}</p>
          </div>
        </div>
      ) : null}
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* Lesson page pieces                                                  */
/* ------------------------------------------------------------------ */

function LessonTags({
  lesson,
  withStars,
}: {
  lesson: LessonMeta;
  withStars?: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Tag tone="brand">
        Lesson {lesson.position} of {lesson.lessonCount}
      </Tag>
      {lesson.state === "in_review" ? null : (
        <Tag icon={Clock}>{lesson.minutes} min</Tag>
      )}
      <LessonStateTag state={lesson.state} />
      {withStars && lesson.stars > 0 ? (
        <span className="hidden lg:inline-flex">
          <Stars count={lesson.stars} size={18} />
        </span>
      ) : null}
    </div>
  );
}

function LessonHead({ lesson }: { lesson: LessonMeta }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="hidden lg:flex">
        <BackLink href={lesson.unitHref}>
          {lesson.unitCode} · {lesson.unitTitle}
        </BackLink>
      </div>
      <LessonTags lesson={lesson} withStars />
      <H1 className="lg:text-4xl lg:leading-[44px]">{lesson.title}</H1>
    </div>
  );
}

function Objectives({ items }: { items: string[] }) {
  return (
    <Card tone="sunken" className="gap-3">
      <H3>By the end you can</H3>
      <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
        {items.map((item) => (
          <li
            key={item}
            className="flex items-start gap-2.5 text-[15px] leading-[22px]"
          >
            <Check
              size={18}
              aria-hidden
              className="mt-0.5 shrink-0 text-ns-success"
            />
            {item}
          </li>
        ))}
      </ul>
    </Card>
  );
}

function VideoPoster({ video }: { video: LessonVideoSummary }) {
  return (
    <figure id="video" className="m-0 flex scroll-mt-20 flex-col gap-2">
      <div className="relative flex h-[196px] items-center justify-center overflow-hidden rounded-2xl bg-ns-ink lg:h-[360px]">
        {video.poster}
        <span className="absolute top-[18px] left-5 opacity-80">
          <Logo height={18} reversed />
        </span>
        <Link
          href={video.href}
          aria-label={`Play lesson video, ${video.minutes} minutes`}
          className={cn(
            "relative inline-flex size-[72px] items-center justify-center rounded-full bg-ns-surface pl-1 text-ns-ink shadow-ns-md",
            focusRing,
          )}
        >
          <Play size={30} aria-hidden />
        </Link>
        <span className="absolute bottom-3.5 left-5 text-[15px] font-bold text-ns-on-brand lg:text-lg">
          {video.title}
        </span>
        <span className="absolute right-4 bottom-3.5 rounded-full bg-ns-dark/70 px-2.5 py-1 text-[13px] font-semibold text-ns-on-brand tabular-nums">
          {video.duration}
        </span>
      </div>
      <figcaption className="flex flex-col gap-2">
        <div className="flex flex-wrap gap-x-5">
          <Link
            href={video.href}
            className={cn(
              "inline-flex min-h-9 items-center gap-1.5 text-sm font-semibold text-ns-amber-text underline",
              focusRing,
            )}
          >
            <Captions size={18} aria-hidden />
            Captions on
          </Link>
          <Link
            href={video.transcriptHref}
            className={cn(
              "inline-flex min-h-9 items-center gap-1.5 text-sm font-semibold text-ns-amber-text underline",
              focusRing,
            )}
          >
            <FileText size={18} aria-hidden />
            Read the transcript
          </Link>
        </div>
        <div className="flex items-center gap-2">
          <XpPill xp={video.xp} />
          <Muted className="text-[13px] leading-[18px]">
            Watch to the end to earn it.
          </Muted>
        </div>
      </figcaption>
    </figure>
  );
}

function SectionXp({ xp, done }: { xp: number; done: boolean }) {
  if (done) {
    return (
      <span className="ml-auto inline-flex h-[26px] shrink-0 items-center gap-1 rounded-full bg-ns-success-soft px-2.5 text-xs font-extrabold whitespace-nowrap text-ns-success">
        <Check size={14} aria-hidden />
        <span className="sr-only">Done, earned </span>+{xp} XP
      </span>
    );
  }
  return <XpTag xp={xp} size={12} className="ml-auto" />;
}

function Section({
  section,
  index,
}: {
  section: LessonSection;
  index: number;
}) {
  const titleId = `${section.id}-title`;
  return (
    <section
      id={section.id}
      aria-labelledby={titleId}
      className="flex scroll-mt-20 flex-col gap-4"
    >
      <div className="flex items-center gap-3">
        <span
          aria-hidden="true"
          className="text-[13px] font-bold text-ns-amber-text tabular-nums"
        >
          {String(index + 1).padStart(2, "0")}
        </span>
        <h2
          id={titleId}
          className="m-0 text-xl leading-7 font-semibold lg:text-[22px] lg:leading-[30px]"
        >
          {section.title}
        </h2>
        <SectionXp xp={section.xp} done={section.done} />
      </div>
      <div className="flex flex-col gap-4 text-[17px] leading-7 text-ns-ink [&_p]:m-0">
        {section.content}
      </div>
    </section>
  );
}

function Summary({ points }: { points: ReactNode[] }) {
  return (
    <section
      id="summary"
      aria-labelledby="summary-title"
      className="scroll-mt-20"
    >
      <Card tone="sunken" className="gap-3">
        <h3
          id="summary-title"
          className="m-0 text-[17px] leading-6 font-semibold"
        >
          Summary
        </h3>
        <ul className="m-0 flex list-disc flex-col gap-1.5 pl-5 text-base leading-6">
          {points.map((point, i) => (
            <li key={i}>{point}</li>
          ))}
        </ul>
      </Card>
    </section>
  );
}

export function PracticeCtaCard({ practice }: { practice: LessonPracticeCta }) {
  return (
    <Card className="gap-3.5 shadow-ns-md">
      <div className="flex items-start gap-3">
        <div className="flex min-w-0 grow flex-col gap-1">
          <H3>Guided practice</H3>
          <Muted>
            {practice.questionCount} questions. Win up to 3 stars and about +
            {practice.xp} XP. Wrong answers get hints and never cost XP.
          </Muted>
        </div>
        <Stars count={practice.stars} size={20} />
      </div>
      {practice.quest ? (
        <div className="flex items-start gap-1.5 text-[13px] leading-[18px] font-semibold text-ns-amber-text">
          <GameIcon name="target" size={16} className="mt-px" />
          <span>
            Counts toward today’s quest: {practice.quest.title} (
            {practice.quest.progress} of {practice.quest.target})
          </span>
        </div>
      ) : null}
      <Button
        variant="primary"
        full
        href={practice.href}
        iconRight={ArrowRight}
        disabled={!practice.available}
      >
        Start practice
      </Button>
    </Card>
  );
}

interface TocItem {
  id: string;
  title: string;
  xp?: number;
  done: boolean;
}

function tocItems(
  video: LessonVideoSummary | null,
  sections: LessonSection[],
): TocItem[] {
  const started = Boolean(video?.done) || sections.some((s) => s.done);
  return [
    { id: "before-you-start", title: "Before you start", done: started },
    ...(video
      ? [{ id: "video", title: "Video", xp: video.xp, done: video.done }]
      : []),
    ...sections.map((s) => ({
      id: s.id,
      title: s.title,
      xp: s.xp,
      done: s.done,
    })),
    {
      id: "summary",
      title: "Summary",
      done: sections.length > 0 && sections.every((s) => s.done),
    },
  ];
}

function TocList({
  items,
  currentId,
}: {
  items: TocItem[];
  currentId?: string;
}) {
  return (
    <ul className="m-0 flex list-none flex-col p-0">
      {items.map((item) => {
        const current = item.id === currentId;
        return (
          <li key={item.id}>
            <a
              href={`#${item.id}`}
              aria-current={current ? "location" : undefined}
              className={cn(
                "flex min-h-8 items-center gap-2.5 rounded-md text-sm leading-5 no-underline",
                current
                  ? "font-bold text-ns-ink"
                  : item.done
                    ? "font-medium text-ns-ink"
                    : "font-medium text-ns-muted",
                focusRing,
              )}
            >
              <span
                aria-hidden="true"
                className={cn(
                  "size-2 shrink-0 rounded-full",
                  current
                    ? "bg-ns-amber"
                    : item.done
                      ? "bg-ns-success"
                      : "bg-ns-line",
                )}
              />
              <span className="grow">{item.title}</span>
              {item.xp ? (
                <span
                  className={cn(
                    "text-xs font-extrabold",
                    item.done ? "text-ns-success" : "text-ns-amber-text",
                  )}
                >
                  {item.done ? (
                    <>
                      <span aria-hidden="true">✓ </span>
                      <span className="sr-only">done, </span>
                    </>
                  ) : null}
                  +{item.xp}
                  <span className="sr-only"> XP</span>
                </span>
              ) : null}
            </a>
          </li>
        );
      })}
    </ul>
  );
}

/** Tablet top bar dropdown with the same contents list. No JS needed. */
function TocMenu({
  items,
  currentId,
}: {
  items: TocItem[];
  currentId?: string;
}) {
  return (
    <details className="group relative hidden md:block">
      <summary
        className={cn(
          "inline-flex h-11 cursor-pointer list-none items-center gap-2 rounded-full border-[1.5px] border-ns-line-strong bg-ns-raised px-4 text-sm font-semibold [&::-webkit-details-marker]:hidden",
          focusRing,
        )}
      >
        <List size={18} aria-hidden />
        In this lesson
        <ChevronDown
          size={18}
          aria-hidden
          className="transition-transform group-open:rotate-180"
        />
      </summary>
      <div className="absolute top-12 right-0 z-30 w-72 rounded-2xl border border-ns-line bg-ns-raised p-4 shadow-ns-lg">
        <TocList items={items} currentId={currentId} />
      </div>
    </details>
  );
}

/* ------------------------------------------------------------------ */
/* Lesson                                                              */
/* ------------------------------------------------------------------ */

export interface LessonScreenProps {
  player: Player;
  lesson: LessonMeta;
  /** API: LessonResponse.objectives */
  objectives: string[];
  video: LessonVideoSummary | null;
  /** "Quick recall" callout before the first section. */
  recall?: ReactNode;
  /** API: LessonResponse.sections */
  sections: LessonSection[];
  summary: ReactNode[];
  practice: LessonPracticeCta;
  /** Section the learner is reading. Highlighted in the contents list. */
  currentSectionId?: string;
  routes?: KitRoutes;
}

/** Canvas: Lesson.m, Lesson.d, Lesson.t */
export function LessonScreen({
  player,
  lesson,
  objectives,
  video,
  recall,
  sections,
  summary,
  practice,
  currentSectionId,
  routes = PREVIEW_ROUTES,
}: LessonScreenProps) {
  const items = tocItems(video, sections);
  const xpTotal = items.reduce((sum, item) => sum + (item.xp ?? 0), 0);
  const xpEarned = items.reduce(
    (sum, item) => sum + (item.done ? (item.xp ?? 0) : 0),
    0,
  );

  return (
    <FocusShell
      player={player}
      routes={routes}
      top={
        <TopBar
          title={`Lesson ${lesson.position}`}
          sub={`Unit ${lesson.unitCode}`}
          backHref={lesson.unitHref}
          right={
            <>
              <MiniChips player={player} routes={routes} />
              <TocMenu items={items} currentId={currentSectionId} />
            </>
          }
        />
      }
    >
      <div className="grid items-start gap-7 lg:grid-cols-[minmax(0,680px)_300px] lg:gap-14">
        <article className="flex min-w-0 flex-col gap-7 lg:gap-8">
          <div
            id="before-you-start"
            className="flex scroll-mt-20 flex-col gap-7 lg:gap-8"
          >
            <LessonHead lesson={lesson} />
            <Objectives items={objectives} />
          </div>
          {video ? <VideoPoster video={video} /> : null}
          {recall ? (
            <div className="flex items-start gap-3 rounded-xl bg-ns-brand-soft p-4 text-[15px] leading-[22px]">
              <RotateCcw size={20} aria-hidden className="mt-0.5 shrink-0" />
              <p className="m-0">{recall}</p>
            </div>
          ) : null}
          {sections.map((section, i) => (
            <Section key={section.id} section={section} index={i} />
          ))}
          <Summary points={summary} />
          <div className="lg:hidden">
            <PracticeCtaCard practice={practice} />
          </div>
        </article>

        <aside
          aria-label="In this lesson"
          className="sticky top-10 hidden lg:block"
        >
          <Card shadow={false} className="gap-4">
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs font-semibold text-ns-muted">
                In this lesson
              </span>
              <span className="text-xs font-extrabold text-ns-amber-text tabular-nums">
                {xpEarned} of {xpTotal} XP
              </span>
            </div>
            <TocList items={items} currentId={currentSectionId} />
            <XpBar
              level={player.level}
              current={player.xpIntoLevel}
              needed={player.xpForLevel}
              showLabel={false}
              height={8}
            />
            <Divider />
            <PracticeCtaCard practice={practice} />
          </Card>
        </aside>
      </div>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Lesson still in review                                              */
/* ------------------------------------------------------------------ */

export interface LessonInReviewScreenProps {
  player: Player;
  /** state should be "in_review" (LessonResponse.content_status is not "published"). */
  lesson: LessonMeta;
  /** API: LessonResponse.objectives */
  objectives: string[];
  /** NEW. Try again questions the learner can clear while waiting. */
  reviewDue: { count: number; xp: number; href: Href } | null;
  /** NEW. XP on offer once practice opens. */
  practiceXp: number;
  previous: { label: string; href: Href };
  routes?: KitRoutes;
}

/** Canvas: LessonPending.m */
export function LessonInReviewScreen({
  player,
  lesson,
  objectives,
  reviewDue,
  practiceXp,
  previous,
  routes = PREVIEW_ROUTES,
}: LessonInReviewScreenProps) {
  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={680}
      top={
        <TopBar
          title={`Lesson ${lesson.position}`}
          sub={`Unit ${lesson.unitCode}`}
          backHref={lesson.unitHref}
          right={<MiniChips player={player} routes={routes} />}
        />
      }
    >
      <LessonHead lesson={lesson} />
      <Objectives items={objectives} />

      <Card className="gap-3 p-6">
        <div className="animate-ns-float self-start">
          <Hornbill size={88} mood="sleepy" branch={false} />
        </div>
        <H2>This lesson is being checked</H2>
        <Muted className="text-[15px] leading-[22px]">
          A former scholar is reviewing the explanations and questions so
          nothing wrong reaches you. It opens here as soon as it passes.
        </Muted>
      </Card>

      {reviewDue ? (
        <Card tone="amber" className="gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <DoubleXpPill />
            <span className="text-[13px] font-bold text-ns-amber-text">
              While you wait
            </span>
          </div>
          <H3>
            {reviewDue.count} review question
            {reviewDue.count === 1 ? " is" : "s are"} ready
          </H3>
          <Muted>
            Keep your {player.streakDays}-day streak going and earn up to +
            {reviewDue.xp} XP.
          </Muted>
          <Button variant="primary" full icon={RotateCcw} href={reviewDue.href}>
            Review for double XP
          </Button>
        </Card>
      ) : null}

      <Card className="gap-3.5">
        <div className="flex items-start gap-3">
          <div className="flex min-w-0 grow flex-col gap-1">
            <H3>Guided practice</H3>
            <Muted>
              Opens with the lesson. Worth about +{practiceXp} XP and 3 stars.
            </Muted>
          </div>
          <Tag icon={Lock}>Not open yet</Tag>
        </div>
        <Button variant="primary" full disabled>
          Start practice
        </Button>
      </Card>

      <Button full icon={ChevronLeft} href={previous.href}>
        {previous.label}
      </Button>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Lesson video                                                        */
/* ------------------------------------------------------------------ */

export interface TranscriptLine {
  /** e.g. "2:14" */
  time: string;
  text: string;
}

/** NEW. Video player state. Lesson video assets are not in the API yet. */
export interface LessonVideoPlayer {
  /** Page heading on desktop, e.g. "Video: breaking a number into primes". */
  title: string;
  minutes: number;
  /** NEW */
  xp: number;
  /**
   * The picture. The app passes its real <video> element (with a <track> for
   * captions); the preview passes a still frame.
   */
  media: ReactNode;
  /** Caption line on screen right now. */
  caption?: string;
  captionsOn: boolean;
  playing: boolean;
  /** Playback speed, e.g. 1 or 1.5. */
  speed: number;
  positionSeconds: number;
  durationSeconds: number;
}

export interface LessonVideoScreenProps {
  player: Player;
  lesson: { position: number; title: string; href: Href };
  video: LessonVideoPlayer;
  /** Titles of every lesson step, e.g. ["Before you start", "Video", ...]. */
  steps: string[];
  /** Index into `steps` of this video. */
  stepIndex: number;
  transcript: {
    lines: TranscriptLine[];
    /** Line being spoken now. */
    currentIndex: number;
    followVideo: boolean;
    downloadHref: Href;
    /** e.g. "English captions" */
    language: string;
  };
  doneHref: Href;
  routes?: KitRoutes;
}

function clock(seconds: number) {
  const s = Math.max(0, Math.round(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function StepProgress({
  steps,
  index,
  xp,
}: {
  steps: string[];
  index: number;
  xp: number;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-3">
        <span className="text-[13px] font-semibold text-ns-muted">
          Section {index + 1} of {steps.length} · {steps[index]}
        </span>
        <XpTag xp={xp} />
      </div>
      <Steps done={index} current={index} total={steps.length} />
    </div>
  );
}

function PlayerButton({
  label,
  children,
  pressed,
}: {
  label: string;
  children: ReactNode;
  pressed?: boolean;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={pressed}
      className={cn(
        "inline-flex size-11 shrink-0 items-center justify-center rounded-full text-ns-on-brand hover:bg-ns-on-brand/10",
        pressed && "bg-ns-on-brand/15",
        focusRing,
      )}
    >
      {children}
    </button>
  );
}

function VideoPlayer({ video }: { video: LessonVideoPlayer }) {
  const now = clock(video.positionSeconds);
  const total = clock(video.durationSeconds);
  const speedLabel = `${video.speed}×`;
  return (
    <figure className="m-0 overflow-hidden rounded-2xl shadow-ns-md">
      <div className="relative h-[201px] overflow-hidden bg-ns-dark lg:h-[380px]">
        <div className="absolute inset-0">{video.media}</div>
        {video.captionsOn && video.caption ? (
          <p className="absolute bottom-3.5 left-1/2 m-0 w-[86%] -translate-x-1/2 text-center text-[15px] leading-[1.35] font-semibold text-white lg:text-xl">
            <span className="rounded-md bg-black/80 box-decoration-clone px-2 py-0.5">
              {video.caption}
            </span>
          </p>
        ) : null}
      </div>
      <div className="flex flex-col gap-0.5 bg-ns-ink px-2 pt-1.5 pb-2">
        <div className="flex items-center gap-2.5 px-2">
          <label htmlFor="lesson-video-seek" className="sr-only">
            Seek
          </label>
          <input
            id="lesson-video-seek"
            type="range"
            min={0}
            max={video.durationSeconds}
            defaultValue={video.positionSeconds}
            aria-valuetext={`${now} of ${total}`}
            className={cn("h-6 min-w-0 grow accent-ns-amber", focusRing)}
          />
          <span className="pr-1.5 text-xs whitespace-nowrap text-ns-on-brand tabular-nums">
            {now} / {total}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <PlayerButton label={video.playing ? "Pause" : "Play"}>
            {video.playing ? (
              <Pause size={22} aria-hidden />
            ) : (
              <Play size={22} aria-hidden />
            )}
          </PlayerButton>
          <PlayerButton label="Back 10 seconds">
            <RotateCcw size={22} aria-hidden />
          </PlayerButton>
          <span className="grow" />
          <PlayerButton label="Captions" pressed={video.captionsOn}>
            <Captions size={22} aria-hidden />
          </PlayerButton>
          <button
            type="button"
            aria-label={`Playback speed, ${video.speed} times`}
            className={cn(
              "inline-flex h-11 min-w-11 items-center justify-center rounded-full text-[13px] font-bold text-ns-on-brand",
              focusRing,
            )}
          >
            <span className="inline-flex h-8 min-w-9 items-center justify-center rounded-full border-[1.5px] border-ns-on-brand/40 px-2.5">
              {speedLabel}
            </span>
          </button>
          <PlayerButton label="Full screen">
            <Maximize size={22} aria-hidden />
          </PlayerButton>
        </div>
      </div>
    </figure>
  );
}

function Transcript({
  transcript,
  duration,
}: {
  transcript: LessonVideoScreenProps["transcript"];
  duration: string;
}) {
  return (
    <Card className="gap-3">
      <div className="flex items-center justify-between gap-3">
        <H3>Transcript</H3>
        <label className="flex min-h-11 cursor-pointer items-center gap-2.5 text-[15px]">
          <input
            type="checkbox"
            defaultChecked={transcript.followVideo}
            className={cn("size-5 shrink-0 accent-ns-ink", focusRing)}
          />
          Follow the video
        </label>
      </div>
      <ol
        aria-label="Transcript"
        className="-mx-2.5 my-0 flex list-none flex-col gap-0.5 p-0 lg:max-h-[420px] lg:overflow-y-auto"
      >
        {transcript.lines.map((line, i) => {
          const on = i === transcript.currentIndex;
          return (
            <li key={line.time}>
              <button
                type="button"
                aria-current={on ? "true" : undefined}
                className={cn(
                  "flex w-full items-start gap-3 rounded-lg px-2.5 py-2 text-left",
                  on ? "bg-ns-amber-soft" : "hover:bg-ns-sunken",
                  focusRing,
                )}
              >
                <span
                  className={cn(
                    "w-[34px] shrink-0 pt-px text-[13px] font-bold tabular-nums",
                    on ? "text-ns-amber-text" : "text-ns-muted",
                  )}
                >
                  {line.time}
                </span>
                <span
                  className={cn(
                    "text-[15px] leading-[22px] text-ns-ink",
                    on && "font-semibold",
                  )}
                >
                  {line.text}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Button
          variant="ghost"
          size="sm"
          icon={Download}
          href={transcript.downloadHref}
          className="-ml-4"
        >
          Download transcript
        </Button>
        <Muted className="text-[13px] leading-[18px]">
          {transcript.language} · {duration}
        </Muted>
      </div>
    </Card>
  );
}

/** Canvas: LessonVideo.m, LessonVideo.d */
export function LessonVideoScreen({
  player,
  lesson,
  video,
  steps,
  stepIndex,
  transcript,
  doneHref,
  routes = PREVIEW_ROUTES,
}: LessonVideoScreenProps) {
  const doneLabel = `Done with the video · +${video.xp} XP`;
  return (
    <FocusShell
      player={player}
      routes={routes}
      maxWidth={1120}
      top={
        <TopBar
          title={`Lesson ${lesson.position}`}
          sub={lesson.title}
          backHref={lesson.href}
          right={<MiniChips player={player} routes={routes} />}
        />
      }
      desktopTop={
        <div className="flex flex-col gap-2">
          <BackLink href={lesson.href}>
            Lesson {lesson.position} · {lesson.title}
          </BackLink>
          <div className="flex flex-wrap items-center gap-3">
            <H1 className="lg:text-[30px] lg:leading-[38px]">{video.title}</H1>
            <Tag icon={Clock}>{video.minutes} min</Tag>
          </div>
        </div>
      }
      footer={
        <FooterBar className="lg:hidden">
          <Button variant="primary" full href={doneHref} iconRight={ArrowRight}>
            {doneLabel}
          </Button>
          <Muted className="text-center text-[13px] leading-[18px]">
            You can come back to it any time.
          </Muted>
        </FooterBar>
      }
    >
      <h1 className="sr-only lg:hidden">{video.title}</h1>
      <div className="lg:hidden">
        <StepProgress steps={steps} index={stepIndex} xp={video.xp} />
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_360px] lg:gap-6">
        <div className="flex min-w-0 flex-col gap-5">
          <VideoPlayer video={video} />
          <Card className="hidden gap-3.5 lg:flex">
            <StepProgress steps={steps} index={stepIndex} xp={video.xp} />
            <div className="flex flex-wrap items-center gap-4">
              <Button variant="primary" href={doneHref} iconRight={ArrowRight}>
                {doneLabel}
              </Button>
              <Muted>You can come back to it any time.</Muted>
            </div>
          </Card>
        </div>
        <Transcript
          transcript={transcript}
          duration={clock(video.durationSeconds)}
        />
      </div>
    </FocusShell>
  );
}
