"use client";

import { ArrowLeft, CircleAlert, Clock3, Construction, PlayCircle, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getLesson, type LessonResponse } from "@/lib/api/course";
import { createPracticeSession, type PracticeSessionResponse } from "@/lib/api/practice";
import { startLesson, type LessonProgressResponse } from "@/lib/api/progress";

type Props = {
  lessonKey: string;
  loadLesson?: (lessonKey: string) => Promise<LessonResponse>;
  startSession?: (lessonKey: string, questionCount?: number) => Promise<PracticeSessionResponse>;
  recordStart?: (lessonKey: string) => Promise<LessonProgressResponse>;
};

export function LessonPanel({
  lessonKey,
  loadLesson = getLesson,
  startSession = createPracticeSession,
  recordStart = startLesson,
}: Props) {
  const router = useRouter();
  const [lesson, setLesson] = useState<LessonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const [startingPractice, setStartingPractice] = useState(false);
  const [progressWarning, setProgressWarning] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void loadLesson(lessonKey)
      .then((result) => {
        if (active) {
          setLesson(result);
          setError(null);
          void recordStart(result.stable_key).catch((caught: unknown) => {
            if (active) {
              setProgressWarning(
                caught instanceof Error
                  ? caught.message
                  : "Lesson progress could not be recorded.",
              );
            }
          });
        }
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : "The lesson could not be loaded.");
      });
    return () => {
      active = false;
    };
  }, [lessonKey, loadLesson, recordStart, reload]);

  async function beginPractice() {
    if (!lesson) return;
    setStartingPractice(true);
    try {
      const session = await startSession(
        lesson.stable_key,
        lesson.practice.question_count,
      );
      router.push(`/practice/${session.session_id}`);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The practice session could not be started.",
      );
      setStartingPractice(false);
    }
  }

  if (error) {
    return <div className="status-card border-rose-200 bg-rose-50" role="alert"><CircleAlert aria-hidden="true" className="size-5 text-rose-700" /><div className="grow"><p className="status-title">Lesson unavailable</p><p className="status-copy">{error}</p></div><Button variant="outline" onClick={() => { setError(null); setLesson(null); setReload((value) => value + 1); }}><RefreshCw aria-hidden="true" className="mr-2 size-4" />Retry</Button></div>;
  }
  if (!lesson) return <div className="status-card animate-pulse" role="status">Loading lesson…</div>;

  return (
    <article className="space-y-7">
      <Link className="inline-flex items-center gap-2 text-sm font-semibold text-teal-800 hover:underline" href="/learn"><ArrowLeft aria-hidden="true" className="size-4" />Back to course map</Link>
      {lesson.development_preview && <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950"><strong>Draft lesson shell.</strong> This route is visible only because local draft preview is enabled.</div>}
      {progressWarning ? <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950" role="status">{progressWarning}</div> : null}
      <header>
        <div className="mb-3 flex flex-wrap gap-2 text-sm font-semibold text-teal-700"><span>Lesson {lesson.position}</span><span>·</span><span>Outcome {lesson.outcomes.join(", ")}</span><span>·</span><span className="inline-flex items-center gap-1"><Clock3 aria-hidden="true" className="size-4" />{lesson.estimated_minutes} minutes planned</span></div>
        <h1 className="m-0 text-4xl font-black tracking-[-0.035em] sm:text-5xl">{lesson.title}</h1>
        <p className="max-w-3xl text-lg leading-8 text-slate-600">{lesson.summary}</p>
      </header>
      <section className="rounded-2xl border border-slate-200 bg-white p-6" aria-labelledby="objectives-title">
        <h2 id="objectives-title" className="mt-0 text-xl font-extrabold">Learning objectives</h2>
        <ul className="mb-0 space-y-2 pl-5 text-slate-700">{lesson.objectives.map((objective) => <li key={objective}>{objective}</li>)}</ul>
      </section>
      {lesson.learning_material_state === "pending" ? (
        <section className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center" aria-labelledby="material-title">
          <Construction aria-hidden="true" className="mx-auto size-9 text-amber-700" />
          <h2 id="material-title" className="mb-2 text-2xl font-extrabold">Lesson material is being prepared</h2>
          <p className="mx-auto max-w-xl text-slate-600">Video, explanations, worked examples and recall checks can be added later. This placeholder contains no invented teaching material.</p>
        </section>
      ) : null}
      <section className="rounded-2xl border border-slate-200 bg-white p-6" aria-labelledby="practice-title">
        <h2 id="practice-title" className="mt-0 text-xl font-extrabold">Guided practice</h2>
        <p className="text-slate-600">
          {lesson.practice.question_count} typed-answer questions are allocated to this lesson.
          {lesson.practice.development_available
            ? " You can exercise the complete flow locally while the questions remain drafts."
            : " Practice unlocks for learners after the lesson and question revisions are reviewed."}
        </p>
        {lesson.practice.available || lesson.practice.development_available ? (
          <Button disabled={startingPractice} onClick={() => void beginPractice()}>
            <PlayCircle aria-hidden="true" className="mr-2 size-4" />
            {startingPractice
              ? "Starting practice…"
              : lesson.practice.development_available
                ? "Start draft practice"
                : "Start practice"}
          </Button>
        ) : (
          <Button disabled>
            <PlayCircle aria-hidden="true" className="mr-2 size-4" />
            Practice unavailable
          </Button>
        )}
      </section>
    </article>
  );
}
