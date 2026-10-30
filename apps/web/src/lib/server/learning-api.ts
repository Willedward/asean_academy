import "server-only";

import type { CourseMapResponse } from "@/lib/api/course";
import type { CurrentLearnerResponse } from "@/lib/api/identity";
import type {
  EnglishCourseMapResponse,
  EnglishEssayDraftResponse,
  EnglishEssayPromptResponse,
  EnglishLessonResponse,
  EnglishProgressResponse,
} from "@/lib/api/english";
import type {
  LearningHomeResponse,
  ProgressResponse,
} from "@/lib/api/progress";
import type { VerifiedSession } from "@/lib/auth/session";
import { ensureLearningApiReady } from "@/lib/server/learning-api-readiness";

function baseUrl(): string {
  return (process.env.LEARNING_API_URL ?? "http://127.0.0.1:8000").replace(
    /\/$/,
    "",
  );
}

type ErrorBody = {
  error?: { code?: string; message?: string; request_id?: string };
};

export class ServerLearningApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly requestId?: string,
  ) {
    super(message);
    this.name = "ServerLearningApiError";
  }
}

async function parseError(response: Response): Promise<ServerLearningApiError> {
  let body: ErrorBody = {};
  try {
    body = (await response.json()) as ErrorBody;
  } catch {
    // The fallback below deliberately hides upstream response details.
  }
  return new ServerLearningApiError(
    body.error?.message ?? `Learning API returned ${response.status}.`,
    response.status,
    body.error?.code ?? "learning_api_error",
    body.error?.request_id,
  );
}

async function getServerJson<T>(
  session: VerifiedSession,
  path: string,
): Promise<T> {
  const apiBaseUrl = baseUrl();
  const requestId = crypto.randomUUID();
  let response: Response;
  try {
    await ensureLearningApiReady(apiBaseUrl);
    response = await fetch(`${apiBaseUrl}${path}`, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${session.accessToken}`,
        "X-Request-ID": requestId,
      },
    });
  } catch {
    throw new ServerLearningApiError(
      "The learning service could not be reached.",
      503,
      "learning_api_unavailable",
      requestId,
    );
  }
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as T;
}

export async function getServerLearner(
  session: VerifiedSession,
): Promise<CurrentLearnerResponse> {
  return getServerJson(session, "/api/v1/me");
}

export async function getServerLearningHome(
  session: VerifiedSession,
): Promise<LearningHomeResponse> {
  return getServerJson(session, "/api/v1/learning-home");
}

export async function getServerCourseMap(
  session: VerifiedSession,
  courseKey: string,
): Promise<CourseMapResponse> {
  return getServerJson(
    session,
    `/api/v1/courses/${encodeURIComponent(courseKey)}/map`,
  );
}

export async function getServerProgress(
  session: VerifiedSession,
): Promise<ProgressResponse> {
  return getServerJson(session, "/api/v1/progress");
}

export async function getServerEnglishCourseMap(
  session: VerifiedSession,
): Promise<EnglishCourseMapResponse> {
  return getServerJson(session, "/api/v1/english/course-map");
}

export async function getServerEnglishProgress(
  session: VerifiedSession,
): Promise<EnglishProgressResponse> {
  return getServerJson(session, "/api/v1/english/progress");
}

export async function getServerCurrentEnglishEssayPrompt(
  session: VerifiedSession,
): Promise<EnglishEssayPromptResponse | null> {
  try {
    return await getServerJson(session, "/api/v1/english/essay-prompts/current");
  } catch (error) {
    if (
      error instanceof ServerLearningApiError &&
      error.code === "essay_prompt_not_found"
    )
      return null;
    throw error;
  }
}

export async function getServerEnglishEssayDraft(
  session: VerifiedSession,
  draftId: string,
): Promise<EnglishEssayDraftResponse> {
  return getServerJson(
    session,
    `/api/v1/english/essay-drafts/${encodeURIComponent(draftId)}`,
  );
}

export async function getServerEnglishLesson(
  session: VerifiedSession,
  lessonKey: string,
): Promise<EnglishLessonResponse> {
  return getServerJson(
    session,
    `/api/v1/english/lessons/${encodeURIComponent(lessonKey)}`,
  );
}
