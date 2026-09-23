"use client";

import { BookOpen, CircleAlert, Clock3, FileClock, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getCourseMap, type CourseMapResponse } from "@/lib/api/course";

type Props = {
  courseKey: string;
  loadCourseMap?: (courseKey: string) => Promise<CourseMapResponse>;
};

export function CourseMapPanel({ courseKey, loadCourseMap = getCourseMap }: Props) {
  const [course, setCourse] = useState<CourseMapResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    void loadCourseMap(courseKey)
      .then((result) => {
        if (active) {
          setCourse(result);
          setError(null);
        }
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : "The course could not be loaded.");
      });
    return () => {
      active = false;
    };
  }, [courseKey, loadCourseMap, reload]);

  if (error) {
    return (
      <div className="status-card border-rose-200 bg-rose-50" role="alert">
        <CircleAlert aria-hidden="true" className="size-5 text-rose-700" />
        <div className="grow"><p className="status-title">Course unavailable</p><p className="status-copy">{error}</p></div>
        <Button variant="outline" onClick={() => { setError(null); setCourse(null); setReload((value) => value + 1); }}>
          <RefreshCw aria-hidden="true" className="mr-2 size-4" />Retry
        </Button>
      </div>
    );
  }

  if (!course) {
    return <div className="status-card animate-pulse" role="status">Loading course map…</div>;
  }

  return (
    <div className="space-y-8">
      {course.development_preview && (
        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">
          <strong>Development preview.</strong> Lesson material and questions remain drafts and are unavailable to students.
        </div>
      )}
      <div>
        <p className="text-sm font-bold uppercase tracking-[0.15em] text-teal-700">{course.school_level.replaceAll("_", " ")} · {course.subject}</p>
        <h1 className="mt-2 text-4xl font-black tracking-[-0.035em] sm:text-5xl">{course.title}</h1>
        <p className="max-w-3xl text-lg leading-8 text-slate-600">{course.description}</p>
      </div>
      {course.units.map((unit) => (
        <section key={unit.stable_key} aria-labelledby={`${unit.stable_key}-title`}>
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div><p className="mb-1 text-sm font-semibold text-teal-700">Unit {unit.position}</p><h2 id={`${unit.stable_key}-title`} className="m-0 text-2xl font-extrabold">{unit.title}</h2></div>
            <p className="m-0 text-sm text-slate-500">{unit.checkpoint_question_count}-question checkpoint · pending</p>
          </div>
          <ol className="grid list-none gap-3 p-0">
            {unit.lessons.map((lesson) => (
              <li key={lesson.stable_key}>
                <Link className="group flex gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-300 hover:shadow-md" href={lesson.href}>
                  <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-slate-100 font-black text-slate-700">{lesson.position}</span>
                  <span className="grow">
                    <span className="flex flex-wrap items-start justify-between gap-2">
                      <span className="font-extrabold text-slate-950 group-hover:text-teal-800">{lesson.title}</span>
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-bold text-amber-900"><FileClock aria-hidden="true" className="size-3.5" />Material pending</span>
                    </span>
                    <span className="mt-2 flex flex-wrap gap-4 text-sm text-slate-500">
                      <span className="inline-flex items-center gap-1"><BookOpen aria-hidden="true" className="size-4" />Outcome {lesson.outcomes.join(", ")}</span>
                      <span className="inline-flex items-center gap-1"><Clock3 aria-hidden="true" className="size-4" />{lesson.estimated_minutes} min planned</span>
                      <span>{lesson.required_practice_count} practice question{lesson.required_practice_count === 1 ? "" : "s"}</span>
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}
