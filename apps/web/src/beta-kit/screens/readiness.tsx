/**
 * Readiness check (the diagnostic, roadmap B-04 and B-05).
 *
 * Built on the Learning API William already has: GET /diagnostics/next,
 * sessions, autosaved responses, submit and result (bands getting_started /
 * on_track / ahead, purposes baseline / endline). Fields marked NEW still need
 * backend work: see the "Readiness check" section of READINESS.md.
 *
 * Canvas page: "Readiness check (diagnostic)".
 */
import Link from "next/link";
import type { ReactNode } from "react";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronLeft,
  Clock,
  Copy,
  Download,
  Eye,
  Flag,
  List,
  Lock,
  Map as MapIcon,
  Send,
  ShieldCheck,
  Target,
  Users,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";

import { Hornbill } from "../components/hornbill";
import { Confetti, MascotCard, MascotSays, Medal, RewardLine, XpPill } from "../components/rewards";
import { Bar, Button, Callout, Card, Eyebrow, H1, H2, H3, Muted, Sheet, Tag, focusRing } from "../components/ui";
import { PREVIEW_ROUTES, type KitRoutes } from "../routes";
import { AppShell, BareShell, FocusShell, FooterBar, Logo, StatBar, TopBar } from "../shell/app-shell";
import type { Href, Player } from "../types";
import { AnswerInput, type PracticePart } from "./practice";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

/** API: DiagnosticResultResponse.band */
export type ReadinessBand = "getting_started" | "on_track" | "ahead";
/** API: DiagnosticResultResponse.purpose. baseline = start of beta, endline = end. */
export type ReadinessPurpose = "baseline" | "endline";

export const BAND_LABEL: Record<ReadinessBand, string> = {
  getting_started: "Getting started",
  on_track: "On track",
  ahead: "Ahead",
};

/** One syllabus outcome. API: DiagnosticOutcomeScore, title from the course map outcomes. */
export interface ReadinessOutcome {
  code: string;
  title: string;
  score: number;
  max: number;
  /** End-of-beta score, on the comparison screen. */
  after?: number;
}

export interface ReadinessResultData {
  purpose: ReadinessPurpose;
  band: ReadinessBand;
  /** API: score / max_score */
  score: number;
  max: number;
  /** e.g. "9 October" from submitted_at */
  dateLabel: string;
  /** API: strengths (outcome codes) mapped to outcomes. */
  strengths: ReadinessOutcome[];
  /** API: priorities, first 3. */
  focus: ReadinessOutcome[];
  /** API: outcome_scores */
  outcomes: ReadinessOutcome[];
  /** One friendly line under the band. Never says weak or failing. */
  summary: string;
  /** NEW: XP for finishing (not for the score) and the badge. */
  reward?: { xp: number; badge: string; badgeNote: string };
  /** NEW: the recommended first lesson. */
  start: { label: string; href: Href };
}

/* ------------------------------------------------------------------ */
/* Small pieces                                                        */
/* ------------------------------------------------------------------ */

/** The three bands as a scale, with the student's band filled in. */
export function BandScale({ band, dark }: { band: ReadinessBand; dark?: boolean }) {
  return (
    <div role="img" aria-label={`Band: ${BAND_LABEL[band]}, of Getting started, On track and Ahead`} className="flex gap-1.5">
      {(Object.keys(BAND_LABEL) as ReadinessBand[]).map((key) => (
        <span
          key={key}
          className={cn(
            "flex h-9 flex-1 items-center justify-center rounded-full text-[13px]",
            key === band
              ? "bg-ns-gold font-black text-ns-ink"
              : dark
                ? "bg-ns-on-brand/10 font-semibold text-ns-on-dark-muted"
                : "bg-ns-sunken font-semibold text-ns-muted",
          )}
        >
          {BAND_LABEL[key]}
        </span>
      ))}
    </div>
  );
}

/** Score bar for one outcome. With `after`, shows start (grey) under now (green). */
export function OutcomeBar({ outcome }: { outcome: ReadinessOutcome }) {
  const pct = (outcome.score / Math.max(1, outcome.max)) * 100;
  const compare = outcome.after !== undefined;
  const afterPct = ((outcome.after ?? 0) / Math.max(1, outcome.max)) * 100;
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline gap-2">
        <span className="w-[30px] shrink-0 text-xs font-bold text-ns-muted">{outcome.code}</span>
        <span className="grow text-sm font-semibold">{outcome.title}</span>
        <span className="text-[13px] font-bold tabular-nums">
          {compare ? (
            <>
              <span className="text-ns-muted">{outcome.score} →</span> {outcome.after} of {outcome.max}
            </>
          ) : (
            `${outcome.score} of ${outcome.max}`
          )}
        </span>
      </div>
      {compare ? (
        <div className="relative h-2.5 overflow-hidden rounded-full bg-ns-brand-soft" aria-hidden="true">
          <div className="absolute inset-y-0 left-0 rounded-full bg-ns-success" style={{ width: `${afterPct}%` }} />
          <div className="absolute inset-y-0 left-0 rounded-full bg-ns-line-strong" style={{ width: `${pct}%` }} />
        </div>
      ) : (
        <Bar pct={pct} fill={pct >= 75 ? "success" : "amber"} />
      )}
    </div>
  );
}

function FactRow({ icon: Icon, title, sub }: { icon: typeof Clock; title: string; sub: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-ns-brand-soft">
        <Icon size={20} aria-hidden />
      </span>
      <div className="flex min-w-0 flex-col gap-0.5">
        <b className="text-[15px] leading-5">{title}</b>
        <span className="text-[13px] leading-[18px] text-ns-muted">{sub}</span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Dashboard card                                                      */
/* ------------------------------------------------------------------ */

export interface ReadinessCardProps {
  /** API: DiagnosticNextResponse.status start / resume, purpose baseline / endline */
  kind: "baseline" | "resume" | "endline";
  /** API: DiagnosticNextResponse.question_count, estimated_minutes */
  questionCount: number;
  minutes: number;
  /** resume only: answered so far */
  answered?: number;
  /** NEW */
  xp: number;
  href: Href;
}

/** Canvas: DashboardReadiness.m, DashboardReadinessEnd.m */
export function ReadinessCard({ kind, questionCount, minutes, answered = 0, xp, href }: ReadinessCardProps) {
  if (kind === "resume") {
    return (
      <Card className="gap-3">
        <div className="flex items-center gap-2">
          <Tag tone="amber" icon={Target}>
            Readiness check
          </Tag>
          <span className="ml-auto text-[13px] text-ns-muted">Saved</span>
        </div>
        <H3>
          {answered} of {questionCount} answered
        </H3>
        <Bar pct={(answered / Math.max(1, questionCount)) * 100} />
        <Button variant="primary" full href={href} iconRight={ArrowRight}>
          Continue where you stopped
        </Button>
      </Card>
    );
  }
  const end = kind === "endline";
  return (
    <Card className={cn("gap-3.5 shadow-ns-md", !end && "border-ns-amber-line")}>
      <div className="flex items-center gap-2">
        <Tag tone={end ? "brand" : "amber"} icon={end ? Flag : Target}>
          {end ? "End of beta" : "Readiness check"}
        </Tag>
        <span className="ml-auto">
          <XpPill xp={xp} />
        </span>
      </div>
      <div className="flex items-center gap-3">
        {!end ? <Hornbill size={56} crop="head" mood="happy" outfit="glasses" /> : null}
        <div className="flex min-w-0 grow flex-col gap-1">
          <H3>{end ? "See how far you’ve come" : "Find your starting point"}</H3>
          <Muted>
            {end
              ? "Take the readiness check again. We’ll show your new score next to your starting point."
              : `${questionCount} questions, about ${minutes} minutes. We use it to pick your first lesson.`}
          </Muted>
        </div>
      </div>
      <Button variant="primary" full href={href} iconRight={ArrowRight}>
        {end ? "Take it again" : "Start the readiness check"}
      </Button>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/* Intro                                                               */
/* ------------------------------------------------------------------ */

export interface ReadinessIntroProps {
  questionCount: number;
  minutes: number;
  /** NEW */
  reward: { xp: number; badge: string };
  startHref: Href;
  laterHref: Href;
}

/** Right after onboarding, before Lesson 1. Canvas: ReadinessIntro.m */
export function ReadinessIntroScreen({ questionCount, minutes, reward, startHref, laterHref }: ReadinessIntroProps) {
  return (
    <BareShell>
      <div className="mx-auto flex min-h-dvh w-full max-w-[560px] flex-col">
        <header className="flex h-[60px] items-center px-4">
          <Logo />
        </header>
        <main className="flex grow flex-col gap-[18px] px-4 pt-4 pb-8">
          <div className="flex flex-col items-center gap-2 text-center">
            <div className="motion-safe:animate-ns-float">
              <Hornbill size={120} mood="happy" pose="point" outfit="glasses" branch={false} label="Hornbill with glasses" />
            </div>
            <Eyebrow>BEFORE LESSON 1</Eyebrow>
            <H1>Let’s find your starting point</H1>
            <Muted className="text-[15px] leading-[22px]">
              A short readiness check shows what you already know, so your first lesson is the right one.
            </Muted>
          </div>
          <Card className="gap-3.5">
            <FactRow icon={List} title={`${questionCount} maths questions, about ${minutes} minutes`} sub="From the N1 topics in your course." />
            <FactRow icon={Clock} title="No timer, no hints" sub="Take your time. It’s not a test you can fail." />
            <FactRow icon={Check} title="Saved as you go" sub="Leave any time and pick up where you stopped." />
            <FactRow icon={Eye} title="Results at the end" sub="Your strengths first, then what to work on next." />
          </Card>
          <Card tone="amber" shadow={false}>
            <RewardLine
              icon={<Target size={20} aria-hidden />}
              title={`Finish it for +${reward.xp} XP`}
              sub={`Whatever your score. You also get the ${reward.badge} badge.`}
              right={<XpPill xp={reward.xp} />}
            />
          </Card>
        </main>
        <FooterBar className="sticky bottom-0">
          <Button variant="primary" full href={startHref} iconRight={ArrowRight}>
            Start the readiness check
          </Button>
          <Button variant="ghost" full href={laterHref}>
            Do it later
          </Button>
          <p className="m-0 text-center text-xs text-ns-muted">You can come back to it from your dashboard.</p>
        </FooterBar>
      </div>
    </BareShell>
  );
}

/* ------------------------------------------------------------------ */
/* Taking the check                                                    */
/* ------------------------------------------------------------------ */

export interface ReadinessQuestionProps {
  player: Player;
  purpose: ReadinessPurpose;
  /** API: DiagnosticItemResponse.position */
  position: number;
  total: number;
  /** positions with saved answers (DiagnosticItemResponse.saved_answers) */
  answered: number[];
  /** API: DiagnosticItemResponse.outcome_code */
  outcome: string;
  calculatorAllowed: boolean;
  marks: number;
  /** API: DiagnosticQuestionResponse.stem through MathContent */
  stem: ReactNode;
  /** API: DiagnosticPartResponse[]; inputs are named answer-<position> */
  parts: PracticePart[];
  /** API: DiagnosticItemResponse.saved_at */
  savedLabel: string;
  minutesLeft: number;
  /** Autosave target (PUT responses/{position}); a server action or URL. */
  saveAction?: string | ((formData: FormData) => void | Promise<void>);
  questionHref: (position: number) => Href;
  previousHref?: Href;
  nextHref: Href;
  skipHref: Href;
  leaveHref: Href;
  routes?: KitRoutes;
}

/** Numbered map of all questions. */
export function QuestionMap({
  total,
  current,
  answered,
  href,
}: {
  total: number;
  current?: number;
  answered: number[];
  href: (position: number) => Href;
}) {
  return (
    <nav aria-label="Questions" className="flex flex-wrap gap-1.5">
      {Array.from({ length: total }, (_, i) => i + 1).map((n) => {
        const on = n === current;
        const done = answered.includes(n);
        return (
          <Link
            key={n}
            href={href(n)}
            aria-current={on ? "step" : undefined}
            aria-label={`Question ${n}${done ? ", answered" : ""}`}
            className={cn(
              "inline-flex size-8 items-center justify-center rounded-full text-[13px] font-bold no-underline",
              on ? "bg-ns-ink text-ns-on-brand" : done ? "bg-ns-brand-soft text-ns-ink" : "bg-ns-raised text-ns-muted shadow-[inset_0_0_0_1px_var(--color-ns-line)]",
              focusRing,
            )}
          >
            {n}
          </Link>
        );
      })}
    </nav>
  );
}

/** Canvas: ReadinessQuestion.m, ReadinessQuestion.d */
export function ReadinessQuestionScreen({
  player,
  purpose,
  position,
  total,
  answered,
  outcome,
  calculatorAllowed,
  marks,
  stem,
  parts,
  savedLabel,
  minutesLeft,
  saveAction,
  questionHref,
  previousHref,
  nextHref,
  skipHref,
  leaveHref,
  routes = PREVIEW_ROUTES,
}: ReadinessQuestionProps) {
  const label = `Readiness check · ${purpose === "endline" ? "end of beta" : "starting point"}`;
  const saved = (
    <span role="status" className="inline-flex items-center gap-1 text-xs font-bold text-ns-success lg:text-[13px]">
      <Check size={14} aria-hidden />
      {savedLabel}
    </span>
  );
  const nav = (
    <>
      <Button icon={ChevronLeft} href={previousHref} disabled={!previousHref}>
        Previous
      </Button>
      <div className="grow lg:grow-0">
        <Button variant="primary" full href={nextHref} iconRight={ArrowRight}>
          {position === total ? "Review and finish" : "Next question"}
        </Button>
      </div>
    </>
  );
  return (
    <FocusShell
      player={player}
      routes={routes}
      active="learn"
      maxWidth={1120}
      top={
        <header className="flex flex-col gap-2 border-b border-ns-line bg-ns-surface px-4 pt-2 pb-3">
          <div className="flex items-center gap-1.5">
            <div className="flex grow flex-col">
              <span className="text-xs font-semibold text-ns-muted">{label}</span>
              <span className="text-base font-bold">
                Question {position} of {total}
              </span>
            </div>
            {saved}
            <Link href={leaveHref} aria-label="Save and leave. You can finish later" className={cn("inline-flex size-11 items-center justify-center rounded-full", focusRing)}>
              <X size={22} aria-hidden />
            </Link>
          </div>
          <Bar pct={((position - 1) / total) * 100} height={6} />
        </header>
      }
      desktopTop={
        <div className="flex flex-col gap-4">
          <div className="flex items-end gap-3">
            <div className="flex grow flex-col gap-1.5">
              <Link href={leaveHref} className="inline-flex items-center gap-1 text-sm font-semibold text-ns-muted no-underline">
                <ChevronLeft size={18} aria-hidden />
                Save and leave
              </Link>
              <h1 className="m-0 text-[28px] leading-9 font-bold">
                Readiness check · Question {position} of {total}
              </h1>
            </div>
            {saved}
          </div>
          <Bar pct={((position - 1) / total) * 100} />
        </div>
      }
      footer={
        <FooterBar className="lg:hidden">
          <div className="flex gap-2">{nav}</div>
          <Button variant="ghost" full href={skipHref}>
            Skip for now
          </Button>
        </FooterBar>
      }
    >
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-8">
        <form className="flex min-w-0 flex-col gap-4" action={saveAction}>
          <Card className="gap-3.5">
            <div className="flex flex-wrap items-center gap-2">
              <Tag>Outcome {outcome}</Tag>
              <Tag>{calculatorAllowed ? "Calculator allowed" : "No calculator"}</Tag>
              <span className="ml-auto text-[13px] text-ns-muted">
                {marks} mark{marks === 1 ? "" : "s"}
              </span>
            </div>
            <div className="text-[17px] leading-7 lg:text-lg">{stem}</div>
          </Card>
          <Card className="gap-5">
            {parts.map((part) => (
              <AnswerInput key={part.position} part={part} single={parts.length === 1} />
            ))}
          </Card>
          <p className="m-0 flex items-start gap-1.5 text-xs leading-4 text-ns-muted lg:hidden">
            <Lock size={14} className="shrink-0" aria-hidden />
            No hints or marking during the check. You’ll see everything at the end.
          </p>
          <div className="hidden items-center gap-2 lg:flex">
            {nav}
            <Button variant="ghost" href={skipHref}>
              Skip for now
            </Button>
          </div>
          <Card tone="sunken" shadow={false} className="gap-2.5 lg:hidden">
            <H3 className="text-[15px] leading-5">Jump to a question</H3>
            <QuestionMap total={total} current={position} answered={answered} href={questionHref} />
          </Card>
        </form>
        <div className="hidden min-w-0 flex-col gap-4 lg:flex">
          <Card className="gap-3.5">
            <H3>Your progress</H3>
            <Muted>
              {answered.length} of {total} answered · about {minutesLeft} minutes left
            </Muted>
            <QuestionMap total={total} current={position} answered={answered} href={questionHref} />
            <p className="m-0 flex items-start gap-2 border-t border-ns-line pt-3 text-[13px] leading-[18px] text-ns-muted">
              <Lock size={16} className="shrink-0" aria-hidden />
              No hints or marking during the check. Your results come at the end, strengths first.
            </p>
          </Card>
          <MascotCard mood="kind">Not sure? Give it your best try or skip it. Skipped questions just help us find your starting point.</MascotCard>
        </div>
      </div>
    </FocusShell>
  );
}

export interface ReadinessReviewProps {
  player: Player;
  total: number;
  answered: number[];
  reward: { xp: number; badge: string };
  questionHref: (position: number) => Href;
  /** POST submit, then the result page. A server action or URL. */
  submitAction?: string | ((formData: FormData) => void | Promise<void>);
  backHref: Href;
  routes?: KitRoutes;
}

/** Canvas: ReadinessReview.m */
export function ReadinessReviewScreen({ player, total, answered, reward, questionHref, submitAction, backHref, routes = PREVIEW_ROUTES }: ReadinessReviewProps) {
  const missing = Array.from({ length: total }, (_, i) => i + 1).filter((n) => !answered.includes(n));
  return (
    <FocusShell
      player={player}
      routes={routes}
      active="learn"
      maxWidth={640}
      top={<TopBar title="Readiness check" backHref={backHref} />}
      footer={
        <FooterBar>
          <form action={submitAction} className="flex flex-col gap-2 lg:mx-auto lg:w-full lg:max-w-[640px]">
            <Button variant="primary" full type="submit">
              Finish and see my results
            </Button>
            {missing[0] ? (
              <Button full href={questionHref(missing[0])}>
                Go to question {missing[0]}
              </Button>
            ) : null}
          </form>
        </FooterBar>
      }
    >
      <div className="flex flex-col gap-1.5">
        <H1>Ready to finish?</H1>
        <Muted className="text-[15px] leading-[22px]">
          You answered {answered.length} of {total}. Once you finish, the answers are locked and your results appear.
        </Muted>
      </div>
      <Card className="gap-3.5">
        <H3>Questions</H3>
        <QuestionMap total={total} answered={answered} href={questionHref} />
        {missing.length ? (
          <Callout tone="amber">
            <span>
              <b>
                {missing.length === 1 ? `Question ${missing[0]} is` : `${missing.length} questions are`} unanswered.
              </b>{" "}
              That’s okay. You can still finish.
            </span>
          </Callout>
        ) : null}
      </Card>
      <MascotCard mood="happy" outfit="glasses">
        Nice work getting this far! Finishing gets you <b>+{reward.xp} XP</b> and the <b>{reward.badge}</b> badge.
      </MascotCard>
    </FocusShell>
  );
}

/* ------------------------------------------------------------------ */
/* Results                                                             */
/* ------------------------------------------------------------------ */

function ResultHero({ data }: { data: ReadinessResultData }) {
  return (
    <div className="flex flex-col gap-3.5 rounded-[20px] bg-ns-ink p-5 text-ns-on-brand">
      <div className="flex items-center gap-3">
        <Hornbill size={84} mood="happy" pose="cheer" outfit="glasses" branch={false} />
        <div className="flex min-w-0 grow flex-col gap-0.5">
          <span className="text-xs font-extrabold tracking-[0.1em] text-ns-gold">YOUR STARTING POINT</span>
          <h1 className="m-0 text-[30px] leading-9 font-black">{BAND_LABEL[data.band]}</h1>
          <span className="text-sm leading-5 text-ns-on-brand/80">
            {data.score} of {data.max} marks · {data.dateLabel}
          </span>
        </div>
      </div>
      <BandScale band={data.band} dark />
      <p className="m-0 text-sm leading-5 text-ns-on-brand/80">{data.summary}</p>
    </div>
  );
}

function StrengthsCard({ data }: { data: ReadinessResultData }) {
  return (
    <Card className="gap-3.5">
      <div className="flex flex-col gap-0.5">
        <span className="text-xs font-semibold tracking-[0.02em] text-ns-success">STRENGTHS FIRST</span>
        <H2>What you already know</H2>
      </div>
      {data.strengths.length ? (
        data.strengths.map((o) => (
          <div key={o.code} className="flex items-center gap-2.5">
            <CheckCircle2 size={20} className="shrink-0 text-ns-success" aria-hidden />
            <div className="flex flex-col">
              <b className="text-[15px]">{o.title}</b>
              <span className="text-[13px] text-ns-muted">
                {o.score} of {o.max} marks
              </span>
            </div>
          </div>
        ))
      ) : (
        <Muted>Your lessons will build these from the very start.</Muted>
      )}
    </Card>
  );
}

function FocusCard({ data }: { data: ReadinessResultData }) {
  return (
    <Card className="gap-3.5">
      <div className="flex flex-col gap-0.5">
        <Eyebrow>WHAT TO WORK ON NEXT</Eyebrow>
        <H2>Your next {data.focus.length} topics</H2>
      </div>
      {data.focus.map((o, i) => (
        <div key={o.code} className="flex items-center gap-2.5">
          <span className="inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-ns-amber-soft text-[13px] font-extrabold text-ns-amber-text">{i + 1}</span>
          <div className="flex flex-col">
            <b className="text-[15px]">{o.title}</b>
            <span className="text-[13px] text-ns-muted">
              Outcome {o.code} · {o.score} of {o.max} marks
            </span>
          </div>
        </div>
      ))}
      <Callout tone="brand" icon={MapIcon}>
        <span>
          <b>We start you at {data.start.label}</b> and mark these topics in your course, so you know where to slow down.
        </span>
      </Callout>
    </Card>
  );
}

function AllTopicsCard({ outcomes, legend }: { outcomes: ReadinessOutcome[]; legend?: boolean }) {
  return (
    <Card className="gap-3.5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <H3>{legend ? "Topic by topic" : "All topics"}</H3>
        {legend ? (
          <span className="flex items-center gap-1.5 text-xs text-ns-muted">
            <span className="h-2 w-3 rounded-full bg-ns-line-strong" /> Start
            <span className="ml-1.5 h-2 w-3 rounded-full bg-ns-success" /> Now
          </span>
        ) : (
          <span className="text-xs text-ns-muted">Scores only, never your answers</span>
        )}
      </div>
      {outcomes.map((o) => (
        <OutcomeBar key={o.code} outcome={o} />
      ))}
    </Card>
  );
}

export interface ShareLink {
  /** NEW: POST /diagnostics/sessions/{id}/share returns a private URL valid 30 days. */
  url: string;
  expiresLabel: string;
  whatsappHref: Href;
  /** NEW: PDF of the same report. */
  pdfHref: Href;
}

/** Canvas: ReadinessShare.m */
export function ReadinessShareSheet({ link, onCopy, closeHref, onClose }: { link: ShareLink; onCopy?: () => void; closeHref?: Href; onClose?: () => void }) {
  const titleId = "readiness-share-title";
  return (
    <Sheet titleId={titleId}>
      <h2 id={titleId} className="m-0 text-xl leading-7 font-semibold">
        Share your results with a parent
      </h2>
      <Muted>They’ll see your band, strengths and next topics. Never your answers.</Muted>
      <div className="flex items-center gap-2 rounded-xl border border-ns-line bg-ns-sunken py-2.5 pr-2.5 pl-3">
        <span className="grow truncate font-mono text-[13px]">{link.url}</span>
        <Button size="sm" icon={Copy} onClick={onCopy}>
          Copy
        </Button>
      </div>
      <div className="flex flex-col gap-2">
        <Button variant="primary" full icon={Send} href={link.whatsappHref}>
          Send on WhatsApp
        </Button>
        <Button full icon={Download} href={link.pdfHref}>
          Download PDF
        </Button>
      </div>
      <p className="m-0 flex items-start gap-2 text-xs leading-4 text-ns-muted">
        <ShieldCheck size={16} className="shrink-0" aria-hidden />
        Private link. Anyone with it can view the report. It stops working on {link.expiresLabel}, or when you turn it off in Settings.
      </p>
      <Button variant="ghost" full href={closeHref} onClick={onClose}>
        Done
      </Button>
    </Sheet>
  );
}

export interface ReadinessResultProps {
  player: Player;
  data: ReadinessResultData;
  shareHref: Href;
  /** Shows the share sheet over the result. */
  share?: ShareLink;
  shareCloseHref?: Href;
  backHref: Href;
  routes?: KitRoutes;
}

/** Canvas: ReadinessResult.m, ReadinessResult.d, ReadinessShare.m */
export function ReadinessResultScreen({ player, data, shareHref, share, shareCloseHref, backHref, routes = PREVIEW_ROUTES }: ReadinessResultProps) {
  const actions = (
    <div className="flex flex-col gap-2">
      <Button variant="primary" full href={data.start.href} iconRight={ArrowRight}>
        Start {data.start.label}
      </Button>
      <Button full icon={Users} href={shareHref}>
        Share with a parent
      </Button>
    </div>
  );
  const reward = data.reward ? (
    <Card tone="amber" shadow={false} className="py-4">
      <RewardLine
        icon={<Medal icon="star" tier="bronze" size={40} pop />}
        title={`${data.reward.badge} badge unlocked`}
        sub={data.reward.badgeNote}
        right={<XpPill xp={data.reward.xp} />}
      />
    </Card>
  ) : null;
  return (
    <AppShell
      active="progress"
      player={player}
      routes={routes}
      maxWidth={1120}
      top={<TopBar title="Your results" backHref={backHref} />}
      overlay={
        <>
          {data.reward ? <Confetti count={22} seed={4} /> : null}
          {share ? <ReadinessShareSheet link={share} closeHref={shareCloseHref} /> : null}
        </>
      }
    >
      <div className="hidden flex-col gap-1.5 lg:flex">
        <Link href={backHref} className="inline-flex items-center gap-1 text-sm font-semibold text-ns-muted no-underline">
          <ChevronLeft size={18} aria-hidden />
          Dashboard
        </Link>
        <H1 className="lg:text-[30px] lg:leading-[38px]">Your readiness check results</H1>
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-2 lg:gap-6">
        <div className="flex min-w-0 flex-col gap-4 lg:gap-5">
          <ResultHero data={data} />
          <div className="lg:hidden">{reward}</div>
          <StrengthsCard data={data} />
          <FocusCard data={data} />
        </div>
        <div className="flex min-w-0 flex-col gap-4 lg:gap-5">
          <div className="hidden lg:block">{reward}</div>
          <AllTopicsCard outcomes={data.outcomes} />
          {actions}
        </div>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Parent view (shared link, no sign-in)                               */
/* ------------------------------------------------------------------ */

export interface ParentReportProps {
  studentFirstName: string;
  courseLabel: string;
  data: ReadinessResultData;
  expiresLabel: string;
}

/** Canvas: ReadinessParent.m */
export function ParentReportScreen({ studentFirstName, courseLabel, data, expiresLabel }: ParentReportProps) {
  return (
    <BareShell>
      <div className="mx-auto flex min-h-dvh w-full max-w-[640px] flex-col">
        <header className="flex h-[60px] items-center gap-2 border-b border-ns-line px-4">
          <Logo />
          <span className="ml-auto">
            <Tag icon={Lock}>Shared report</Tag>
          </span>
        </header>
        <main className="flex flex-col gap-4 p-4">
          <Card className="gap-3.5">
            <Eyebrow muted>READINESS CHECK · {courseLabel.toUpperCase()}</Eyebrow>
            <H1>
              {studentFirstName} is {BAND_LABEL[data.band].toLowerCase()}
            </H1>
            <Muted>
              {data.score} of {data.max} marks on {data.dateLabel}, at the {data.purpose === "endline" ? "end" : "start"} of the NextScholar beta.
            </Muted>
            <BandScale band={data.band} />
          </Card>
          <Card className="gap-3">
            <H3>Strengths</H3>
            {data.strengths.map((o) => (
              <span key={o.code} className="flex items-center gap-2 text-sm">
                <CheckCircle2 size={18} className="text-ns-success" aria-hidden />
                {o.title}
              </span>
            ))}
          </Card>
          <Card className="gap-3">
            <H3>Working on next</H3>
            {data.focus.map((o, i) => (
              <span key={o.code} className="flex items-center gap-2 text-sm">
                <b className="w-4 text-[13px] text-ns-amber-text">{i + 1}</b>
                {o.title}
              </span>
            ))}
            <Muted className="text-[13px]">These topics are marked in {studentFirstName}’s course. Practice adapts as they improve.</Muted>
          </Card>
          <Card tone="sunken" shadow={false} className="gap-2.5">
            <H3>How to read this</H3>
            <Muted>
              The band compares the score with what the entry test expects at this point. <b>Getting started</b>, <b>On track</b> and{" "}
              <b>Ahead</b> describe where to begin, not ability. A second check at the end of the beta shows progress.
            </Muted>
            <Muted className="text-[13px]">This page shows scores only. Answers stay private to {studentFirstName}.</Muted>
          </Card>
        </main>
        <p className="m-0 mt-auto border-t border-ns-line p-4 text-center text-xs text-ns-muted">
          Shared by {studentFirstName} · link expires {expiresLabel}
        </p>
      </div>
    </BareShell>
  );
}

/* ------------------------------------------------------------------ */
/* End of beta: start and now                                          */
/* ------------------------------------------------------------------ */

export interface ReadinessCompareProps {
  player: Player;
  start: { score: number; band: ReadinessBand; dateLabel: string };
  now: { score: number; band: ReadinessBand; dateLabel: string };
  max: number;
  /** Outcomes with score (start) and after (now). NEW: the API returns one result per session; pair baseline and endline. */
  outcomes: ReadinessOutcome[];
  /** NEW: biggest improvement badge. */
  biggest?: { title: string; from: number; to: number; xp: number; badge: string };
  shareHref: Href;
  backHref: Href;
  routes?: KitRoutes;
}

/** Canvas: ReadinessCompare.m, ReadinessCompare.d */
export function ReadinessCompareScreen({ player, start, now, max, outcomes, biggest, shareHref, backHref, routes = PREVIEW_ROUTES }: ReadinessCompareProps) {
  const gain = now.score - start.score;
  const movedUp = now.band !== start.band;
  return (
    <AppShell
      active="progress"
      player={player}
      routes={routes}
      maxWidth={1120}
      top={<TopBar title="Your progress" backHref={backHref} />}
      overlay={gain > 0 ? <Confetti count={30} seed={9} /> : undefined}
    >
      <div className="hidden flex-col gap-1.5 lg:flex">
        <Link href={backHref} className="inline-flex items-center gap-1 text-sm font-semibold text-ns-muted no-underline">
          <ChevronLeft size={18} aria-hidden />
          Progress
        </Link>
        <H1 className="lg:text-[30px] lg:leading-[38px]">Readiness check: start and now</H1>
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-2 lg:gap-6">
        <div className="flex min-w-0 flex-col gap-4 lg:gap-5">
          <div className="flex flex-col gap-3.5 rounded-[20px] bg-ns-ink p-5 text-ns-on-brand">
            <span className="text-xs font-extrabold tracking-[0.1em] text-ns-gold">HOW FAR YOU’VE COME</span>
            <div className="flex items-end gap-4">
              <div className="flex flex-col text-ns-on-dark-muted">
                <span className="text-[13px]">Start · {start.dateLabel}</span>
                <span className="text-[32px] leading-10 font-black">{start.score}</span>
                <span className="text-[13px]">{BAND_LABEL[start.band]}</span>
              </div>
              <ArrowRight size={28} className="mb-6 text-ns-gold" aria-hidden />
              <div className="flex flex-col">
                <span className="text-[13px] text-ns-on-brand/80">Now · {now.dateLabel}</span>
                <span className="text-[32px] leading-10 font-black">{now.score}</span>
                <span className="text-[13px] font-extrabold text-ns-gold">{BAND_LABEL[now.band]}</span>
              </div>
              <span className="ml-auto self-center rounded-[14px] bg-ns-gold px-3 py-2 text-xl font-black text-ns-ink">
                {gain >= 0 ? `+${gain}` : gain}
              </span>
            </div>
            <p className="m-0 text-sm leading-5 text-ns-on-brand/80">
              out of {max} marks.{" "}
              {movedUp ? "You moved up a band. That’s your practice showing." : "Every topic you practised is in the bars below."}
            </p>
          </div>
          {biggest ? (
            <Card tone="amber" shadow={false} className="py-4">
              <RewardLine
                icon={<Medal icon="star" tier="gold" size={40} pop />}
                title={`Biggest jump: ${biggest.title}`}
                sub={`From ${biggest.from} to ${biggest.to} marks. +${biggest.xp} XP and the ${biggest.badge} badge.`}
              />
            </Card>
          ) : null}
          <div className="flex flex-col gap-2 lg:flex-row">
            <Button variant="primary" full icon={Users} href={shareHref}>
              Share the progress with a parent
            </Button>
            <Button full href={backHref}>
              Back
            </Button>
          </div>
        </div>
        <AllTopicsCard outcomes={outcomes} legend />
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* Not ready yet / dashboard prompt                                    */
/* ------------------------------------------------------------------ */

/** API: DiagnosticNextResponse.status "content_pending". Canvas: ReadinessPending.m */
export function ReadinessPendingScreen({ player, lessonHref, backHref, routes = PREVIEW_ROUTES }: { player: Player; lessonHref: Href; backHref: Href; routes?: KitRoutes }) {
  return (
    <AppShell active="learn" player={player} routes={routes} maxWidth={560} top={<TopBar title="Readiness check" backHref={backHref} />}>
      <div className="flex flex-col items-center gap-2.5 pt-6 text-center">
        <Hornbill size={120} mood="think" branch={false} label="Thinking hornbill" />
        <H1>The readiness check is nearly ready</H1>
        <Muted className="text-[15px] leading-[22px]">
          Our teachers are still checking the questions. You can start Lesson 1 now and take the check when it opens.
        </Muted>
      </div>
      <Button variant="primary" full href={lessonHref} iconRight={ArrowRight}>
        Start Lesson 1
      </Button>
    </AppShell>
  );
}

/** Dashboard for a new student who skipped the check. Canvas: DashboardReadiness.m */
export function DashboardReadinessScreen({
  player,
  card,
  firstLesson,
  routes = PREVIEW_ROUTES,
}: {
  player: Player;
  card: ReadinessCardProps;
  firstLesson: { title: string; label: string; href: Href };
  routes?: KitRoutes;
}) {
  return (
    <AppShell active="learn" player={player} routes={routes} maxWidth={720} top={<StatBar player={player} routes={routes} />}>
      <MascotSays mood="happy" pose="cheer">
        Welcome, {player.displayName.split(" ")[0]}! Start with a quick readiness check so your first lesson fits you.
      </MascotSays>
      <ReadinessCard {...card} />
      <Card className="gap-3">
        <div className="flex items-center gap-2">
          <Tag>After the check</Tag>
          <span className="text-[13px] text-ns-muted">{firstLesson.label}</span>
        </div>
        <H3>{firstLesson.title}</H3>
        <Muted>Or skip ahead: you can start lessons now and do the check later.</Muted>
        <Button full href={firstLesson.href}>
          Start Lesson 1 anyway
        </Button>
      </Card>
    </AppShell>
  );
}
