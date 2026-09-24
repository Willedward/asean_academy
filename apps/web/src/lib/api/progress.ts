import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiErrorMessage } from "./errors";

export type LessonProgressResponse = components["schemas"]["LessonProgressResponse"];
export type ProgressResponse = components["schemas"]["ProgressResponse"];
export type LearningHomeResponse = components["schemas"]["LearningHomeResponse"];

function fixtureGuard(): void {
  if (process.env.NEXT_PUBLIC_USE_API_FIXTURES === "true") {
    throw new Error("Learner progress requires the local learning API.");
  }
}

export async function startLesson(
  lessonKey: string,
): Promise<LessonProgressResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/lessons/{lesson_key}/start",
    { params: { path: { lesson_key: lessonKey } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getProgress(accessToken?: string): Promise<ProgressResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).GET("/api/v1/progress");
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getLearningHome(
  accessToken?: string,
): Promise<LearningHomeResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).GET(
    "/api/v1/learning-home",
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}
