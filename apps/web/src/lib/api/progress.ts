import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiErrorMessage } from "./errors";

export type LessonProgressResponse = components["schemas"]["LessonProgressResponse"];
export type ProgressResponse = components["schemas"]["ProgressResponse"];
export type CheckpointProgressResponse = components["schemas"]["CheckpointProgressResponse"];
export type LearningHomeResponse = components["schemas"]["LearningHomeResponse"];
export type LessonSectionProgressResponse = components["schemas"]["LessonSectionProgressResponse"];
export type ActiveRecallAttemptResponse = components["schemas"]["ActiveRecallAttemptResponse"];

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


export async function getLessonSectionProgress(
  lessonKey: string,
): Promise<LessonSectionProgressResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/lessons/{lesson_key}/section-progress",
    { params: { path: { lesson_key: lessonKey } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function setLessonSectionCompletion(
  lessonKey: string,
  sectionKey: string,
  completed: boolean,
): Promise<LessonSectionProgressResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().PUT(
    "/api/v1/lessons/{lesson_key}/sections/{section_key}/completion",
    {
      params: { path: { lesson_key: lessonKey, section_key: sectionKey } },
      body: { completed },
    },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function checkLessonActiveRecall(
  lessonKey: string,
  sectionKey: string,
  answer: string,
): Promise<ActiveRecallAttemptResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/lessons/{lesson_key}/sections/{section_key}/active-recall",
    {
      params: { path: { lesson_key: lessonKey, section_key: sectionKey } },
      body: { answer },
    },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}
