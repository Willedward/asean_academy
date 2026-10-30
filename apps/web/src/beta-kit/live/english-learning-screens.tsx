import {
  AlertTriangle,
  ArrowRight,
  BookOpenText,
  CheckCircle2,
  CircleDashed,
  Clock3,
  LockKeyhole,
  RotateCcw,
} from "lucide-react";
import Link from "next/link";

import type {
  EnglishCourseMapResponse,
  EnglishEssayPromptResponse,
  EnglishProgressResponse,
} from "@/lib/api/english";
import { EnglishDiagnosticCard } from "@/components/english-diagnostic-card";
import { EnglishEssayDraftCard } from "@/components/english-essay-draft-card";

import { SubjectSwitch } from "../screens/english";
import {
  Callout,
  Card,
  Divider,
  Eyebrow,
  H1,
  H2,
  Muted,
  ProgressBar,
  Tag,
} from "../components/ui";
import { CoreLearningShell, type CoreLearner } from "./core-learning-shell";

const STATE_LABEL = {
  not_started: "Not started",
  in_progress: "In progress",
  practice_completed: "Review due",
  proficient: "Proficient",
  mastered: "Mastered",
} as const;

const CHECKPOINT_LABEL = {
  locked: "Locked",
  available: "Ready",
  in_progress: "In progress",
  passed: "Passed",
} as const;

export function EnglishCourseScreen({
  learner,
  course,
  progress,
  essayPrompt = null,
  mathsHref,
}: {
  learner: CoreLearner;
  course: EnglishCourseMapResponse;
  progress: EnglishProgressResponse;
  essayPrompt?: EnglishEssayPromptResponse | null;
  mathsHref: string;
}) {
  const lessons = course.modules.flatMap((module) => module.lessons);
  const available = lessons.filter((lesson) => lesson.available).length;
  const proficient = lessons.filter(
    (lesson) =>
      lesson.progress_state === "proficient" ||
      lesson.progress_state === "mastered",
  ).length;

  return (
    <CoreLearningShell active="course" learner={learner} courseHref="/english">
      {course.development_preview ? (
        <Callout tone="amber" icon={AlertTriangle}>
          <strong>Development preview</strong>
          <span>
            English content remains hidden from production learners until its
            academic and editorial approvals are complete.
          </span>
        </Callout>
      ) : null}

      <SubjectSwitch
        active="english"
        links={{ maths: mathsHref, english: "/english" }}
      />

      <section className="flex flex-col gap-2">
        <Eyebrow>LAYER 1 · ENGLISH</Eyebrow>
        <H1>{course.title}</H1>
        <Muted className="max-w-3xl">{course.description}</Muted>
        <div className="mt-1 flex flex-wrap gap-2">
          <Tag tone="brand">Revision {course.revision}</Tag>
          <Tag
            tone={course.content_status === "published" ? "success" : "amber"}
          >
            {course.content_status}
          </Tag>
          <Tag>{available} lessons available</Tag>
        </div>
      </section>

      <Card className="gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <Eyebrow>YOUR ENGLISH PATH</Eyebrow>
            <H2>Build transferable exam skills</H2>
          </div>
          <div className="w-full sm:w-64">
            <ProgressBar
              label="Lesson proficiency"
              value={`${proficient} / ${lessons.length}`}
              pct={
                lessons.length
                  ? Math.round((100 * proficient) / lessons.length)
                  : 0
              }
              fill="success"
            />
          </div>
        </div>
        <Muted>
          Start with context clues, then progress through grammar, cloze,
          comprehension and timed composition.
        </Muted>
      </Card>

      <EnglishDiagnosticCard />

      {essayPrompt ? <EnglishEssayDraftCard prompt={essayPrompt} /> : null}

      {course.modules.map((module) => {
        const moduleAvailable = module.lessons.filter(
          (lesson) => lesson.available,
        ).length;
        const checkpoint = progress.checkpoints.find(
          (item) => item.module_code === module.module_code,
        );
        return (
          <Card key={module.module_code} className="gap-4 p-4 lg:p-6">
            <div className="flex items-start gap-3">
              <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-full bg-ns-brand-soft font-bold">
                {module.position}
              </span>
              <div className="min-w-0 grow">
                <Eyebrow>
                  {module.module_code} · {module.stage.replaceAll("_", " ")}
                </Eyebrow>
                <H2>{module.title}</H2>
                <Muted className="mt-1">{module.purpose}</Muted>
              </div>
              <Tag tone={moduleAvailable ? "brand" : "neutral"}>
                {moduleAvailable ? `${moduleAvailable} ready` : "Planned"}
              </Tag>
            </div>
            <Divider />
            <div className="flex flex-col gap-2">
              {module.lessons.map((lesson) => {
                const Icon = lesson.available
                  ? lesson.progress_state === "proficient" ||
                    lesson.progress_state === "mastered"
                    ? CheckCircle2
                    : BookOpenText
                  : lesson.authored
                    ? CircleDashed
                    : LockKeyhole;
                const content = (
                  <>
                    <span
                      className={`inline-flex size-9 shrink-0 items-center justify-center rounded-full ${lesson.available ? "bg-ns-brand-soft" : "bg-ns-sunken text-ns-muted"}`}
                    >
                      <Icon size={17} aria-hidden />
                    </span>
                    <span className="min-w-0 grow">
                      <span className="block text-xs font-semibold text-ns-muted">
                        {lesson.lesson_code} · Outcome {lesson.outcome_code}
                      </span>
                      <span className="block font-semibold text-ns-ink">
                        {lesson.title}
                      </span>
                      <span className="block text-sm leading-5 text-ns-muted">
                        {lesson.outcome}
                      </span>
                    </span>
                    {lesson.retry_question_count ? (
                      <Tag tone="amber" icon={RotateCcw}>
                        {lesson.retry_question_count} to retry
                      </Tag>
                    ) : (
                      <Tag
                        tone={
                          lesson.progress_state === "proficient" ||
                          lesson.progress_state === "mastered"
                            ? "success"
                            : lesson.available
                              ? "brand"
                              : "neutral"
                        }
                      >
                        {lesson.available
                          ? STATE_LABEL[lesson.progress_state]
                          : "Coming later"}
                      </Tag>
                    )}
                    {lesson.available ? (
                      <ArrowRight size={18} aria-hidden />
                    ) : null}
                  </>
                );
                return lesson.href ? (
                  <Link
                    key={lesson.stable_key}
                    href={lesson.href}
                    className="flex items-center gap-3 rounded-xl px-3 py-3 no-underline hover:bg-ns-sunken"
                  >
                    {content}
                  </Link>
                ) : (
                  <div
                    key={lesson.stable_key}
                    className="flex items-center gap-3 rounded-xl px-3 py-3 opacity-70"
                  >
                    {content}
                  </div>
                );
              })}
            </div>
            {checkpoint ? (
              <>
                <Divider />
                <div className="flex flex-col gap-3 rounded-xl bg-ns-sunken p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <Eyebrow>MODULE CHECKPOINT</Eyebrow>
                    <p className="font-semibold text-ns-ink">
                      {checkpoint.question_count}-question protected checkpoint
                    </p>
                    <Muted className="mt-1">
                      Pass at {checkpoint.passing_percentage}%.
                      {checkpoint.attempt_count
                        ? ` ${checkpoint.attempt_count} ${checkpoint.attempt_count === 1 ? "attempt" : "attempts"} recorded.`
                        : " No attempts yet."}
                      {checkpoint.last_percentage == null
                        ? ""
                        : ` Latest score: ${checkpoint.last_percentage}%.`}
                    </Muted>
                  </div>
                  <Tag
                    tone={
                      checkpoint.state === "passed"
                        ? "success"
                        : checkpoint.state === "available" ||
                            checkpoint.state === "in_progress"
                          ? "brand"
                          : "neutral"
                    }
                  >
                    {CHECKPOINT_LABEL[checkpoint.state]}
                  </Tag>
                </div>
              </>
            ) : null}
          </Card>
        );
      })}
    </CoreLearningShell>
  );
}

export function EnglishLessonHeader({
  code,
  outcome,
  title,
  summary,
  minutes,
}: {
  code: string;
  outcome: string;
  title: string;
  summary: string;
  minutes: number;
}) {
  return (
    <section className="flex flex-col gap-2">
      <Eyebrow>
        {code} · OUTCOME {outcome}
      </Eyebrow>
      <H1>{title}</H1>
      <Muted className="max-w-3xl text-base leading-7">{summary}</Muted>
      <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-ns-muted">
        <Clock3 size={16} aria-hidden /> {minutes} minutes
      </span>
    </section>
  );
}
