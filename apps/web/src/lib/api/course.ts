import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiErrorMessage } from "./errors";
import courseMapJson from "@/fixtures/course-map.json";
import lessonJson from "@/fixtures/lesson-01.json";

export type CourseMapResponse = components["schemas"]["CourseMapResponse"];
export type LessonResponse = components["schemas"]["LessonResponse"];

export const courseMapFixture = courseMapJson as CourseMapResponse;
export const lessonFixture = lessonJson as LessonResponse;

export async function getCourseMap(courseKey: string): Promise<CourseMapResponse> {
  if (process.env.NEXT_PUBLIC_USE_API_FIXTURES === "true") return courseMapFixture;
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/courses/{course_key}/map",
    { params: { path: { course_key: courseKey } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getLesson(lessonKey: string): Promise<LessonResponse> {
  if (process.env.NEXT_PUBLIC_USE_API_FIXTURES === "true") {
    const lesson = courseMapFixture.units[0]?.lessons.find(
      (candidate) => candidate.stable_key === lessonKey,
    );
    if (!lesson) throw new Error("The requested lesson was not found.");
    return {
      ...lessonFixture,
      stable_key: lesson.stable_key,
      position: lesson.position,
      title: lesson.title,
      summary: lesson.summary,
      outcomes: lesson.outcomes,
      estimated_minutes: lesson.estimated_minutes,
      objectives: lesson.objectives,
      practice: {
        ...lessonFixture.practice,
        lesson_key: lesson.stable_key,
        question_count: lesson.required_practice_count,
      },
    };
  }
  const { data, error, response } = await createApiClient().GET("/api/v1/lessons/{lesson_key}", {
    params: { path: { lesson_key: lessonKey } },
  });
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}
