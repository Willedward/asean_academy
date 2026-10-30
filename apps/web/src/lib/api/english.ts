import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiErrorMessage } from "./errors";

export type EnglishCourseMapResponse =
  components["schemas"]["EnglishCourseMapResponse"];
export type EnglishLessonResponse =
  components["schemas"]["EnglishLessonResponse"];
export type EnglishPracticeSessionResponse =
  components["schemas"]["EnglishPracticeSessionResponse"];
export type EnglishNextQuestionResponse =
  components["schemas"]["EnglishNextQuestionResponse"];
export type EnglishAttemptResponse =
  components["schemas"]["EnglishAttemptResponse"];
export type EnglishHintResponse = components["schemas"]["EnglishHintResponse"];
export type EnglishProgressResponse =
  components["schemas"]["EnglishProgressResponse"];
export type EnglishDiagnosticNextResponse =
  components["schemas"]["EnglishDiagnosticNextResponse"];
export type EnglishDiagnosticSessionResponse =
  components["schemas"]["EnglishDiagnosticSessionResponse"];
export type EnglishDiagnosticNextQuestionResponse =
  components["schemas"]["EnglishDiagnosticNextQuestionResponse"];
export type EnglishDiagnosticAttemptResponse =
  components["schemas"]["EnglishDiagnosticAttemptResponse"];
export type EnglishEssayPromptResponse =
  components["schemas"]["EnglishEssayPromptResponse"];
export type EnglishEssayDraftResponse =
  components["schemas"]["EnglishEssayDraftResponse"];
export type EnglishEssayPreSubmitResponse =
  components["schemas"]["EnglishEssayPreSubmitResponse"];
export type EnglishEssaySubmissionResponse =
  components["schemas"]["EnglishEssaySubmissionResponse"];
export type EnglishErrorCategory =
  components["schemas"]["ClassifyEnglishErrorRequest"]["category"];
export type EnglishAnswers = Record<string, string | string[]>;

function idempotencyKey(): string {
  return crypto.randomUUID();
}

function fixtureGuard(): void {
  if (process.env.NEXT_PUBLIC_USE_API_FIXTURES === "true") {
    throw new Error("English learning requires the local learning API.");
  }
}

export class EnglishEssayDraftApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "EnglishEssayDraftApiError";
  }
}

export async function createEnglishEssayDraft(
  promptKey: string,
  promptRevision: number,
): Promise<EnglishEssayDraftResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/english/essay-drafts",
    {
      params: {
        header: {
          "Idempotency-Key": `english-essay-draft:${promptKey}:r${promptRevision}`,
        },
      },
      body: { prompt_key: promptKey, prompt_revision: promptRevision },
    },
  );
  if (error || !data)
    throw new EnglishEssayDraftApiError(
      apiErrorMessage(error, response.status),
      response.status,
    );
  return data;
}

export async function getEnglishEssayDraft(
  draftId: string,
): Promise<EnglishEssayDraftResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/english/essay-drafts/{draft_id}",
    { params: { path: { draft_id: draftId } } },
  );
  if (error || !data)
    throw new EnglishEssayDraftApiError(
      apiErrorMessage(error, response.status),
      response.status,
    );
  return data;
}

export async function updateEnglishEssayDraft(
  draftId: string,
  body: string,
  expectedEditRevision: number,
): Promise<EnglishEssayDraftResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().PATCH(
    "/api/v1/english/essay-drafts/{draft_id}",
    {
      params: { path: { draft_id: draftId } },
      body: { body, expected_edit_revision: expectedEditRevision },
    },
  );
  if (error || !data)
    throw new EnglishEssayDraftApiError(
      apiErrorMessage(error, response.status),
      response.status,
    );
  return data;
}

export async function preSubmitEnglishEssayDraft(
  draftId: string,
  expectedEditRevision: number,
): Promise<EnglishEssayPreSubmitResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/english/essay-drafts/{draft_id}/pre-submit",
    {
      params: { path: { draft_id: draftId } },
      body: { expected_edit_revision: expectedEditRevision },
    },
  );
  if (error || !data)
    throw new EnglishEssayDraftApiError(
      apiErrorMessage(error, response.status),
      response.status,
    );
  return data;
}

export async function createEnglishEssaySubmission(
  draftId: string,
  expectedEditRevision: number,
): Promise<EnglishEssaySubmissionResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/english/essay-submissions",
    {
      params: {
        header: {
          "Idempotency-Key": `english-essay-submission:${draftId}:r${expectedEditRevision}`,
        },
      },
      body: {
        draft_id: draftId,
        expected_edit_revision: expectedEditRevision,
        confirmed: true,
      },
    },
  );
  if (error || !data)
    throw new EnglishEssayDraftApiError(
      apiErrorMessage(error, response.status),
      response.status,
    );
  return data;
}

export async function getEnglishCourseMap(
  accessToken?: string,
): Promise<EnglishCourseMapResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).GET(
    "/api/v1/english/course-map",
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getEnglishLesson(
  lessonKey: string,
  accessToken?: string,
): Promise<EnglishLessonResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).GET(
    "/api/v1/english/lessons/{lesson_key}",
    { params: { path: { lesson_key: lessonKey } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function createEnglishPracticeSession(
  lessonKey: string,
  mode: "guided_practice" | "retry_review" = "guided_practice",
  accessToken?: string,
): Promise<EnglishPracticeSessionResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).POST(
    "/api/v1/english/practice-sessions",
    {
      params: { header: { "Idempotency-Key": idempotencyKey() } },
      body: { lesson_key: lessonKey, mode },
    },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getNextEnglishQuestion(
  sessionId: string,
  accessToken?: string,
): Promise<EnglishNextQuestionResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).GET(
    "/api/v1/english/practice-sessions/{session_id}/next",
    { params: { path: { session_id: sessionId } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function submitEnglishAttempt(
  sessionId: string,
  questionKey: string,
  questionRevision: number,
  answers: EnglishAnswers,
  accessToken?: string,
): Promise<EnglishAttemptResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).POST(
    "/api/v1/english/attempts",
    {
      params: { header: { "Idempotency-Key": idempotencyKey() } },
      body: {
        session_id: sessionId,
        question_key: questionKey,
        question_revision: questionRevision,
        answers,
      },
    },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function classifyEnglishError(
  attemptId: string,
  category: EnglishErrorCategory,
  accessToken?: string,
): Promise<void> {
  fixtureGuard();
  const { error, response } = await createApiClient(accessToken).POST(
    "/api/v1/english/attempts/{attempt_id}/error-classification",
    {
      params: { path: { attempt_id: attemptId } },
      body: { category },
    },
  );
  if (error) throw new Error(apiErrorMessage(error, response.status));
}

export async function revealEnglishHint(
  sessionId: string,
  questionKey: string,
  accessToken?: string,
): Promise<EnglishHintResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).POST(
    "/api/v1/english/practice-sessions/{session_id}/questions/{question_key}/hint",
    { params: { path: { session_id: sessionId, question_key: questionKey } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getEnglishProgress(
  accessToken?: string,
): Promise<EnglishProgressResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).GET(
    "/api/v1/english/progress",
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getNextEnglishDiagnostic(): Promise<EnglishDiagnosticNextResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/english/diagnostics/next",
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function createEnglishDiagnosticSession(
  expectedPurpose: "baseline" | "endline",
): Promise<EnglishDiagnosticSessionResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/english/diagnostic-sessions",
    {
      params: { header: { "Idempotency-Key": idempotencyKey() } },
      body: { expected_purpose: expectedPurpose },
    },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getNextEnglishDiagnosticQuestion(
  sessionId: string,
): Promise<EnglishDiagnosticNextQuestionResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/english/diagnostic-sessions/{session_id}/next",
    { params: { path: { session_id: sessionId } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function submitEnglishDiagnosticAttempt(
  sessionId: string,
  questionKey: string,
  questionRevision: number,
  answers: EnglishAnswers,
): Promise<EnglishDiagnosticAttemptResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/english/diagnostic-attempts",
    {
      params: { header: { "Idempotency-Key": idempotencyKey() } },
      body: {
        session_id: sessionId,
        question_key: questionKey,
        question_revision: questionRevision,
        answers,
      },
    },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getEnglishDiagnosticResult(
  sessionId: string,
): Promise<EnglishDiagnosticSessionResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/english/diagnostic-sessions/{session_id}/result",
    { params: { path: { session_id: sessionId } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}
