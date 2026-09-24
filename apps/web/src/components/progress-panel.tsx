"use client";

import {
  CheckCircle2,
  Circle,
  CircleAlert,
  Clock3,
  RefreshCw,
  RotateCcw,
  Trophy,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { getProgress, type ProgressResponse } from "@/lib/api/progress";

const statePresentation: Record<
  ProgressResponse["lessons"][number]["state"],
  { label: string; icon: ReactNode; className: string }
> = {
  not_started: {
    label: "Not started",
    icon: <Circle aria-hidden="true" className="size-4" />,
    className: "bg-slate-100 text-slate-700",
  },
  in_progress: {
    label: "In progress",
    icon: <Clock3 aria-hidden="true" className="size-4" />,
    className: "bg-sky-100 text-sky-800",
  },
  practice_completed: {
    label: "Retry recommended",
    icon: <RotateCcw aria-hidden="true" className="size-4" />,
    className: "bg-amber-100 text-amber-900",
  },
  proficient: {
    label: "Proficient",
    icon: <CheckCircle2 aria-hidden="true" className="size-4" />,
    className: "bg-emerald-100 text-emerald-800",
  },
  mastered: {
    label: "Mastered",
    icon: <Trophy aria-hidden="true" className="size-4" />,
    className: "bg-violet-100 text-violet-800",
  },
};

export function ProgressPanel({
  loadProgress = getProgress,
}: {
  loadProgress?: () => Promise<ProgressResponse>;
}) {
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    void loadProgress()
      .then((response) => {
        if (active) {
          setProgress(response);
          setError(null);
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Progress could not be loaded.");
        }
      });
    return () => {
      active = false;
    };
  }, [loadProgress, reload]);

  if (error) {
    return (
      <div className="status-card border-rose-200 bg-rose-50" role="alert">
        <CircleAlert aria-hidden="true" className="size-5 text-rose-700" />
        <div className="grow"><p className="status-title">Progress unavailable</p><p className="status-copy">{error}</p></div>
        <Button onClick={() => setReload((value) => value + 1)} variant="outline"><RefreshCw aria-hidden="true" className="mr-2 size-4" />Retry</Button>
      </div>
    );
  }

  if (!progress) return <div className="status-card animate-pulse" role="status">Loading progress…</div>;

  const proficient = progress.lessons.filter((lesson) =>
    ["proficient", "mastered"].includes(lesson.state),
  ).length;

  return (
    <div className="space-y-7">
      <header>
        <p className="text-sm font-bold uppercase tracking-wide text-teal-700">Local development learner</p>
        <h1 className="mb-2 mt-1 text-4xl font-black tracking-tight">Your progress</h1>
        <p className="max-w-3xl text-slate-600">
          {proficient} of {progress.lessons.length} lessons are proficient. Proficiency requires at least {progress.proficiency_threshold}% eventual correctness with no Give up result.
        </p>
        {progress.checkpoint_required_for_mastery ? (
          <p className="text-sm text-slate-500">Mastery remains locked until the reviewed unit checkpoint is available.</p>
        ) : null}
      </header>

      <ol className="grid list-none gap-4 p-0">
        {progress.lessons.map((lesson) => {
          const presentation = statePresentation[lesson.state];
          return (
            <li className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" key={lesson.lesson_key}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="mb-1 text-sm font-semibold text-teal-700">Lesson {lesson.position}</p>
                  <h2 className="m-0 text-xl font-extrabold">{lesson.lesson_title}</h2>
                </div>
                <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${presentation.className}`}>
                  {presentation.icon}
                  {presentation.label}
                </span>
              </div>
              {lesson.state !== "not_started" ? (
                <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-3">
                  <span><strong className="block text-lg text-slate-950">{lesson.eventual_correct_percentage}%</strong>eventual correctness</span>
                  <span><strong className="block text-lg text-slate-950">{lesson.correct_count}/{lesson.question_count}</strong>resolved correctly</span>
                  <span><strong className="block text-lg text-slate-950">{lesson.gave_up_count}</strong>Give up results</span>
                </div>
              ) : null}
              <Link className="mt-4 inline-block text-sm font-bold text-teal-800 hover:underline" href={`/lessons/${lesson.lesson_key}`}>
                {lesson.state === "practice_completed" ? "Retry lesson practice" : "Open lesson"}
              </Link>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
