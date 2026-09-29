import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Clock3,
  RotateCcw,
} from "lucide-react";

import type { CourseMapResponse } from "@/lib/api/course";
import type {
  LearningHomeResponse,
  ProgressResponse,
} from "@/lib/api/progress";

import { unitFromCourseMap } from "../adapters";
import { Hornbill } from "../components/hornbill";
import { LessonRow } from "../components/lesson-row";
import {
  Button,
  Callout,
  Card,
  Divider,
  Eyebrow,
  H1,
  H2,
  H3,
  Muted,
  ProgressBar,
  Tag,
} from "../components/ui";
import type { UnitSummary } from "../types";
import { CoreLearningShell, type CoreLearner } from "./core-learning-shell";

type NextActionType = LearningHomeResponse["next_action"]["type"];

const ACTION_LABEL: Record<NextActionType, string> = {
  start_lesson: "Start lesson",
  resume_practice: "Resume practice",
  retry_practice: "Start review",
  continue_lesson: "Continue lesson",
  content_pending: "View course",
  start_checkpoint: "Start checkpoint",
  resume_checkpoint: "Resume checkpoint",
  course_complete: "View progress",
};

function coreUnit(unit: UnitSummary | null): UnitSummary | null {
  if (!unit) return null;
  return {
    ...unit,
    starsEarned: 0,
    starsTotal: 0,
    xpEarned: 0,
    xpTotal: 0,
    lessons: unit.lessons.map((lesson) => ({
      ...lesson,
      stars: 0,
      xpAvailable: undefined,
    })),
  };
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-SG", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Singapore",
  }).format(new Date(value));
}

function PreviewNotice() {
  return (
    <Callout tone="amber" icon={AlertTriangle}>
      <strong>Development preview</strong>
      <span>
        Lesson material and questions may still be under academic review.
      </span>
    </Callout>
  );
}

export function CoreLearningDashboard({
  learner,
  home,
  course,
}: {
  learner: CoreLearner;
  home: LearningHomeResponse;
  course: CourseMapResponse;
}) {
  const courseHref = `/courses/${course.stable_key}`;
  const firstUnit = coreUnit(unitFromCourseMap(course, 0, home));
  const action = home.next_action;
  const actionLabel = ACTION_LABEL[action.type];
  const actionHref =
    action.type === "course_complete" ? "/progress" : action.href;

  return (
    <CoreLearningShell active="learn" learner={learner} courseHref={courseHref}>
      {course.development_preview ? <PreviewNotice /> : null}
      <section className="grid gap-4 lg:grid-cols-[1fr_250px] lg:items-center">
        <div className="flex flex-col gap-2">
          <Eyebrow>YOUR LEARNING PATH</Eyebrow>
          <H1>Welcome back, {learner.displayName}</H1>
          <Muted className="max-w-2xl">
            Continue your {course.title} course from the next recommended
            activity.
          </Muted>
        </div>
        <div className="hidden justify-end lg:flex">
          <Hornbill
            size={150}
            mood="kind"
            pose="point"
            label="NextScholar hornbill guide"
          />
        </div>
      </section>

      <Card tone="brand" className="gap-4 px-5 py-6 lg:px-7">
        <div className="flex flex-wrap items-center gap-2">
          <Tag tone="amber">Recommended next</Tag>
          {home.unresolved_retry_count > 0 ? (
            <Tag tone="neutral" icon={RotateCcw}>
              {home.unresolved_retry_count} to review
            </Tag>
          ) : null}
        </div>
        <div className="flex flex-col gap-1">
          <H2>{action.title}</H2>
          <p className="m-0 max-w-2xl text-sm leading-6 text-ns-on-dark-muted">
            {action.description}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button href={actionHref} variant="gold" iconRight={ArrowRight}>
            {actionLabel}
          </Button>
          {home.next_retry_due_at ? (
            <span className="inline-flex items-center gap-1.5 text-xs text-ns-on-dark-muted">
              <Clock3 size={15} aria-hidden /> Next scheduled review:{" "}
              {formatDateTime(home.next_retry_due_at)}
            </span>
          ) : null}
        </div>
      </Card>

      {firstUnit ? (
        <Card className="gap-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex flex-col gap-1">
              <Eyebrow>UNIT {course.units[0]?.position}</Eyebrow>
              <H2>{firstUnit.title}</H2>
              <Muted>
                {firstUnit.lessonsProficient} of {firstUnit.lessons.length}{" "}
                lessons proficient
              </Muted>
            </div>
            <Button href={courseHref} size="sm">
              View full course
            </Button>
          </div>
          <Divider />
          <div className="flex flex-col gap-1">
            {firstUnit.lessons.slice(0, 3).map((lesson) => (
              <LessonRow key={lesson.key} lesson={lesson} compact />
            ))}
          </div>
          {firstUnit.lessons.length === 0 ? (
            <Muted>No lessons are available in this unit yet.</Muted>
          ) : null}
        </Card>
      ) : (
        <Card>
          <H3>Course content is being prepared</H3>
          <Muted>No units are available in this course revision yet.</Muted>
        </Card>
      )}
    </CoreLearningShell>
  );
}

export function CoreCourseMapScreen({
  learner,
  course,
  progress,
}: {
  learner: CoreLearner;
  course: CourseMapResponse;
  progress: ProgressResponse;
}) {
  const courseHref = `/courses/${course.stable_key}`;
  const checkpoints = new Map(
    progress.checkpoints.map((checkpoint) => [checkpoint.unit_key, checkpoint]),
  );
  const units = course.units
    .map((_, index) => coreUnit(unitFromCourseMap(course, index, progress)))
    .filter((unit): unit is UnitSummary => unit !== null);

  return (
    <CoreLearningShell
      active="course"
      learner={learner}
      courseHref={courseHref}
    >
      {course.development_preview ? <PreviewNotice /> : null}
      <section className="flex flex-col gap-2">
        <Eyebrow>
          {course.school_level.toUpperCase()} · {course.subject.toUpperCase()}
        </Eyebrow>
        <H1>{course.title}</H1>
        <Muted className="max-w-3xl">{course.description}</Muted>
        <div className="mt-1 flex flex-wrap gap-2">
          <Tag tone="brand">Revision {course.revision}</Tag>
          <Tag
            tone={course.content_status === "published" ? "success" : "amber"}
          >
            {course.content_status}
          </Tag>
        </div>
      </section>

      {units.map((unit, index) => {
        const checkpoint = checkpoints.get(unit.key);
        const pct = unit.lessons.length
          ? Math.round((unit.lessonsProficient / unit.lessons.length) * 100)
          : 0;
        return (
          <Card key={unit.key} className="gap-4 p-4 lg:p-6">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex min-w-0 gap-3">
                <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-full bg-ns-brand-soft font-bold">
                  {index + 1}
                </span>
                <div className="min-w-0">
                  <Eyebrow>UNIT {course.units[index]?.position}</Eyebrow>
                  <H2>{unit.title}</H2>
                </div>
              </div>
              <div className="w-full lg:w-64">
                <ProgressBar
                  label="Lesson proficiency"
                  value={`${unit.lessonsProficient} / ${unit.lessons.length}`}
                  pct={pct}
                  fill="success"
                />
              </div>
            </div>
            <Divider />
            <div className="flex flex-col gap-1">
              {unit.lessons.map((lesson) => (
                <LessonRow key={lesson.key} lesson={lesson} />
              ))}
              {unit.lessons.length === 0 ? (
                <Muted>No lessons have been added to this unit.</Muted>
              ) : null}
            </div>
            <Divider />
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-ns-sunken px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="inline-flex size-9 items-center justify-center rounded-full bg-ns-raised">
                  <BookOpen size={18} aria-hidden />
                </span>
                <div>
                  <div className="text-sm font-semibold">
                    Unit checkpoint · {unit.checkpoint.questionCount} questions
                  </div>
                  <div className="text-xs text-ns-muted">
                    Complete the required lessons to unlock it.
                  </div>
                </div>
              </div>
              <Tag
                tone={
                  checkpoint?.state === "passed"
                    ? "success"
                    : checkpoint?.state === "available" ||
                        checkpoint?.state === "in_progress"
                      ? "brand"
                      : "neutral"
                }
              >
                {checkpoint?.state === "in_progress"
                  ? "In progress"
                  : checkpoint?.state === "passed"
                    ? `Passed${checkpoint.last_percentage == null ? "" : ` · ${checkpoint.last_percentage}%`}`
                    : checkpoint?.state === "available"
                      ? "Available"
                      : "Locked"}
              </Tag>
            </div>
          </Card>
        );
      })}

      {units.length === 0 ? (
        <Card>
          <H3>Course map is being prepared</H3>
          <Muted>No units are available in this course revision yet.</Muted>
        </Card>
      ) : null}
    </CoreLearningShell>
  );
}

export function CoreLearningError({
  learner,
  courseHref,
  requestId,
}: {
  learner: CoreLearner;
  courseHref: string;
  requestId?: string;
}) {
  return (
    <CoreLearningShell
      active="learn"
      learner={learner}
      courseHref={courseHref}
      maxWidth={720}
    >
      <Card className="items-start gap-4 p-6 lg:p-8">
        <Tag tone="danger" icon={AlertTriangle}>
          Unable to load
        </Tag>
        <H1>Your learning page could not be loaded.</H1>
        <Muted>
          Try the request again. Your progress has not been changed.
        </Muted>
        {requestId ? (
          <code className="rounded-lg bg-ns-sunken px-3 py-2 text-xs text-ns-muted">
            Request ID: {requestId}
          </code>
        ) : null}
        <Button href="/learn" variant="primary">
          Try again
        </Button>
      </Card>
    </CoreLearningShell>
  );
}
