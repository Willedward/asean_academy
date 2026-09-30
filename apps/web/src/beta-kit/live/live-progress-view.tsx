import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Circle,
  Clock3,
  LockKeyhole,
  RotateCcw,
  Trophy,
} from "lucide-react";

import type { ProgressResponse } from "@/lib/api/progress";

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
  Stat,
  Tag,
} from "../components/ui";

type Lesson = ProgressResponse["lessons"][number];
type Checkpoint = ProgressResponse["checkpoints"][number];

const lessonState: Record<
  Lesson["state"],
  {
    label: string;
    tone: "neutral" | "brand" | "amber" | "success";
    icon: typeof Circle;
  }
> = {
  not_started: { label: "Not started", tone: "neutral", icon: Circle },
  in_progress: { label: "In progress", tone: "brand", icon: Clock3 },
  practice_completed: {
    label: "Review needed",
    tone: "amber",
    icon: RotateCcw,
  },
  proficient: {
    label: "Proficient",
    tone: "success",
    icon: CheckCircle2,
  },
  mastered: { label: "Mastered", tone: "success", icon: Trophy },
};

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-SG", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Singapore",
  }).format(new Date(value));
}

function LessonCard({
  lesson,
  startingRetry,
  onStartRetry,
}: {
  lesson: Lesson;
  startingRetry: boolean;
  onStartRetry: (lessonKey: string) => void;
}) {
  const presentation = lessonState[lesson.state];
  const hasEvidence = lesson.state !== "not_started";

  return (
    <Card className="gap-4 p-4 lg:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 gap-3">
          <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-ns-brand-soft text-sm font-bold">
            {lesson.position}
          </span>
          <div className="min-w-0">
            <Eyebrow>LESSON {lesson.position}</Eyebrow>
            <H3>{lesson.lesson_title}</H3>
          </div>
        </div>
        <Tag tone={presentation.tone} icon={presentation.icon}>
          {presentation.label}
        </Tag>
      </div>

      {hasEvidence ? (
        <div className="grid grid-cols-2 gap-4 rounded-xl bg-ns-sunken p-4 sm:grid-cols-4">
          <Stat
            value={`${lesson.eventual_correct_percentage}%`}
            label="Eventual correctness"
          />
          <Stat
            value={`${lesson.correct_count}/${lesson.question_count}`}
            label="Correct"
          />
          <Stat value={lesson.gave_up_count} label="Solutions revealed" />
          <Stat
            value={lesson.retry_question_count}
            label="Questions to review"
          />
        </div>
      ) : (
        <Muted>
          Complete this lesson and its guided practice to record progress.
        </Muted>
      )}

      <div className="flex flex-wrap gap-2">
        {lesson.retry_question_count > 0 ? (
          <Button
            icon={RotateCcw}
            disabled={startingRetry}
            onClick={() => onStartRetry(lesson.lesson_key)}
          >
            {startingRetry ? "Starting review…" : "Start review"}
          </Button>
        ) : null}
        <Button
          href={`/lessons/${lesson.lesson_key}`}
          variant="ghost"
          icon={BookOpen}
        >
          Open lesson
        </Button>
      </div>
    </Card>
  );
}

function CheckpointCard({
  checkpoint,
  starting,
  onOpen,
}: {
  checkpoint: Checkpoint;
  starting: boolean;
  onOpen: (unitKey: string, sessionId?: string | null) => void;
}) {
  const action =
    checkpoint.state === "in_progress"
      ? "Resume checkpoint"
      : checkpoint.last_session_id
        ? "Retake checkpoint"
        : "Start checkpoint";

  return (
    <Card className="gap-4 p-4 lg:p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 gap-3">
          <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-full bg-ns-brand-soft">
            {checkpoint.state === "locked" ? (
              <LockKeyhole size={18} aria-hidden />
            ) : checkpoint.state === "passed" ? (
              <Trophy size={18} aria-hidden />
            ) : (
              <CheckCircle2 size={18} aria-hidden />
            )}
          </span>
          <div>
            <Eyebrow>
              {checkpoint.unit_key.replaceAll("-", " ").toUpperCase()}
            </Eyebrow>
            <H3>{checkpoint.question_count}-question checkpoint</H3>
            <Muted>
              Pass at {checkpoint.passing_percentage}% or above. Hints and
              worked solutions remain locked during the attempt.
            </Muted>
          </div>
        </div>
        {checkpoint.state === "passed" ? (
          <Tag tone="success" icon={Trophy}>
            Passed
            {checkpoint.last_percentage == null
              ? ""
              : ` · ${checkpoint.last_percentage}%`}
          </Tag>
        ) : checkpoint.state === "locked" ? (
          <Tag tone="neutral" icon={LockKeyhole}>
            Complete every lesson to unlock
          </Tag>
        ) : (
          <Button
            disabled={starting}
            iconRight={ArrowRight}
            onClick={() =>
              onOpen(
                checkpoint.unit_key,
                checkpoint.state === "in_progress"
                  ? checkpoint.last_session_id
                  : null,
              )
            }
          >
            {starting ? "Starting…" : action}
          </Button>
        )}
      </div>
      {checkpoint.state !== "passed" && checkpoint.last_percentage !== null ? (
        <Muted>Latest score: {checkpoint.last_percentage}%.</Muted>
      ) : null}
    </Card>
  );
}

export function LiveProgressView({
  progress,
  startingCheckpoint,
  startingRetry,
  onOpenCheckpoint,
  onStartRetry,
}: {
  progress: ProgressResponse;
  startingCheckpoint: string | null;
  startingRetry: string | null;
  onOpenCheckpoint: (unitKey: string, sessionId?: string | null) => void;
  onStartRetry: (lessonKey: string) => void;
}) {
  const proficient = progress.lessons.filter((lesson) =>
    ["proficient", "mastered"].includes(lesson.state),
  ).length;
  const completion = progress.lessons.length
    ? Math.round((proficient / progress.lessons.length) * 100)
    : 0;

  return (
    <>
      <section className="flex flex-col gap-2">
        <Eyebrow>LEARNING EVIDENCE</Eyebrow>
        <H1>Your progress</H1>
        <Muted className="max-w-3xl">
          Proficiency requires at least {progress.proficiency_threshold}%
          eventual correctness with every question resolved.
          {progress.checkpoint_required_for_mastery
            ? " Unit mastery also requires a passing checkpoint."
            : ""}
        </Muted>
      </section>

      <Card className="gap-5">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <Stat value={proficient} label="Lessons proficient" />
          <Stat value={progress.lessons.length} label="Lessons in course" />
          <Stat
            value={progress.scheduled_retry_count}
            label="Scheduled reviews"
          />
        </div>
        <ProgressBar
          label="Course proficiency"
          value={`${proficient} of ${progress.lessons.length} lessons`}
          pct={completion}
          fill="success"
        />
      </Card>

      {progress.scheduled_retry_count > 0 ? (
        <Callout tone="amber" icon={RotateCcw}>
          <strong>
            {progress.scheduled_retry_count} spaced{" "}
            {progress.scheduled_retry_count === 1 ? "review" : "reviews"}{" "}
            scheduled
          </strong>
          <span>
            {progress.next_retry_due_at
              ? `Next due ${formatDateTime(progress.next_retry_due_at)}.`
              : "Open a lesson with unresolved questions to begin reviewing."}
          </span>
        </Callout>
      ) : null}

      <section className="flex flex-col gap-3" aria-label="Lesson progress">
        <div>
          <Eyebrow>LESSONS</Eyebrow>
          <H2>Lesson progress</H2>
        </div>
        {progress.lessons.map((lesson) => (
          <LessonCard
            key={lesson.lesson_key}
            lesson={lesson}
            startingRetry={startingRetry === lesson.lesson_key}
            onStartRetry={onStartRetry}
          />
        ))}
        {progress.lessons.length === 0 ? (
          <Card>
            <Muted>No lessons are available in this course revision.</Muted>
          </Card>
        ) : null}
      </section>

      <Divider />

      <section className="flex flex-col gap-3" aria-label="Unit checkpoints">
        <div>
          <Eyebrow>MASTERY</Eyebrow>
          <H2>Unit checkpoints</H2>
        </div>
        {progress.checkpoints.map((checkpoint) => (
          <CheckpointCard
            key={checkpoint.unit_key}
            checkpoint={checkpoint}
            starting={startingCheckpoint === checkpoint.unit_key}
            onOpen={onOpenCheckpoint}
          />
        ))}
        {progress.checkpoints.length === 0 ? (
          <Card>
            <Muted>No unit checkpoints are available yet.</Muted>
          </Card>
        ) : null}
      </section>
    </>
  );
}
