/**
 * Mapping from today's learning API responses to kit view models.
 * Use these in server pages; gamification fields the API does not have yet
 * are filled with safe defaults and marked TODO(backend).
 */
import type { components } from "@/lib/api/schema";

import type { ApiLessonState, ContinueCard, LessonSummary, LessonUiState, Stars, UnitSummary } from "./types";

type Schemas = components["schemas"];

export function toLessonUiState(
  state: ApiLessonState,
  availability: Schemas["CourseLessonMap"]["availability"] = "available",
): LessonUiState {
  if (availability === "content_pending") return "in_review";
  switch (state) {
    case "not_started":
      return "ready";
    case "in_progress":
    case "practice_completed":
      return "practising";
    case "proficient":
      return "proficient";
    case "mastered":
      return "mastered";
  }
}

/** 1 star for any right answer, 2 at proficient, 3 at mastered. */
export function starsFor(state: ApiLessonState, correctCount = 0): Stars {
  if (state === "mastered") return 3;
  if (state === "proficient") return 2;
  return correctCount > 0 ? 1 : 0;
}

/**
 * CourseMapResponse (+ optional ProgressResponse) to the unit view model.
 * `lessonHref` lets the page choose its own route (the API sends `href` too).
 */
export function unitFromCourseMap(
  course: Schemas["CourseMapResponse"],
  unitIndex = 0,
  progress?: Schemas["ProgressResponse"],
  lessonHref: (lesson: Schemas["CourseLessonMap"]) => string = (lesson) => lesson.href,
): UnitSummary | null {
  const unit = course.units[unitIndex];
  if (!unit) return null;
  const byKey = new Map(progress?.lessons.map((row) => [row.lesson_key, row]) ?? []);
  const lessons: LessonSummary[] = unit.lessons.map((lesson) => {
    const row = byKey.get(lesson.stable_key);
    const state = row?.state ?? lesson.progress_state;
    return {
      key: lesson.stable_key,
      position: lesson.position,
      title: lesson.title,
      minutes: lesson.estimated_minutes,
      questionCount: lesson.required_practice_count,
      state: toLessonUiState(state, lesson.availability),
      stars: starsFor(state, row?.correct_count),
      xpAvailable: undefined, // TODO(backend): XP still available in the lesson
      href: lessonHref(lesson),
    };
  });
  const proficient = lessons.filter((lesson) => lesson.state === "proficient" || lesson.state === "mastered").length;
  return {
    key: unit.stable_key,
    code: `N${unit.position}`,
    title: unit.title,
    description: course.description,
    lessons,
    lessonsProficient: proficient,
    starsEarned: lessons.reduce((sum, lesson) => sum + lesson.stars, 0),
    starsTotal: lessons.length * 3,
    xpEarned: 0, // TODO(backend)
    xpTotal: 0, // TODO(backend)
    checkpoint: {
      questionCount: unit.checkpoint_question_count,
      minutes: 25, // TODO(backend)
      passMark: Math.ceil(unit.checkpoint_question_count * 0.75),
      open: unit.checkpoint_available,
      href: "#", // TODO: checkpoint route
      rewardXp: 100, // TODO(backend)
      rewardBadge: "Number master", // TODO(backend)
    },
    href: `/courses/${course.stable_key}`,
  };
}

/** LearningHomeResponse.next_action to the "Up next" card. */
export function continueFromNextAction(
  action: Schemas["NextActionResponse"],
  lesson?: Schemas["LessonProgressResponse"],
): ContinueCard {
  const done = lesson?.resolved_count ?? 0;
  const total = lesson?.question_count ?? 0;
  return {
    title: action.title,
    lessonLabel: lesson ? `Lesson ${lesson.position}` : "",
    description: action.description,
    progressLabel: total ? `${done} of ${total} questions` : "",
    progressPct: total ? Math.round((done / total) * 100) : 0,
    primary: { label: action.type === "start_lesson" ? "Start lesson" : "Resume practice", href: action.href },
    xp: 40, // TODO(backend): XP available in this practice set
    stars: lesson ? starsFor(lesson.state, lesson.correct_count) : 0,
  };
}
