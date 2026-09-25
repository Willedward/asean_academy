import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiErrorMessage } from "./errors";

export type PracticeSessionResponse = components["schemas"]["PracticeSessionResponse"];
export type PracticeSessionSummary = components["schemas"]["PracticeSessionSummary"];
export type NextQuestionResponse = components["schemas"]["NextQuestionResponse"];
export type AttemptResponse = components["schemas"]["AttemptResponse"];
export type HintResponse = components["schemas"]["HintResponse"];
export type GiveUpResponse = components["schemas"]["GiveUpResponse"];
type CreatePracticeSessionRequest = components["schemas"]["CreatePracticeSessionRequest"];

function fixtureGuard(): void {
  if (process.env.NEXT_PUBLIC_USE_API_FIXTURES === "true") {
    throw new Error("Interactive practice requires the local learning API.");
  }
}

function idempotencyKey(): string {
  return crypto.randomUUID();
}

async function startPracticeSession(
  body: CreatePracticeSessionRequest,
  accessToken?: string,
): Promise<PracticeSessionResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).POST(
    "/api/v1/practice-sessions",
    {
      params: { header: { "Idempotency-Key": idempotencyKey() } },
      body,
    },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function createPracticeSession(
  lessonKey: string,
  questionCount?: number,
  accessToken?: string,
): Promise<PracticeSessionResponse> {
  return startPracticeSession(
    {
      lesson_key: lessonKey,
      mode: "guided_practice",
      question_count: questionCount,
    },
    accessToken,
  );
}

export async function createRetryReviewSession(
  lessonKey: string,
  questionCount?: number,
  accessToken?: string,
): Promise<PracticeSessionResponse> {
  return startPracticeSession(
    {
      lesson_key: lessonKey,
      mode: "retry_review",
      question_count: questionCount,
    },
    accessToken,
  );
}

export async function createCheckpointSession(
  unitKey: string,
  accessToken?: string,
): Promise<PracticeSessionResponse> {
  return startPracticeSession(
    {
      unit_key: unitKey,
      mode: "checkpoint",
    },
    accessToken,
  );
}

export async function getPracticeSession(
  sessionId: string,
  accessToken?: string,
): Promise<PracticeSessionSummary> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).GET(
    "/api/v1/practice-sessions/{session_id}",
    { params: { path: { session_id: sessionId } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getNextQuestion(
  sessionId: string,
  accessToken?: string,
): Promise<NextQuestionResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).GET(
    "/api/v1/practice-sessions/{session_id}/next",
    { params: { path: { session_id: sessionId } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function submitAttempt(
  sessionId: string,
  questionKey: string,
  questionRevision: number,
  answers: Record<string, string>,
  accessToken?: string,
): Promise<AttemptResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).POST(
    "/api/v1/attempts",
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

export async function revealHint(
  sessionId: string,
  questionKey: string,
  stage: 1 | 2,
  accessToken?: string,
): Promise<HintResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).POST(
    "/api/v1/practice-sessions/{session_id}/questions/{question_key}/hints/{stage}",
    {
      params: {
        path: {
          session_id: sessionId,
          question_key: questionKey,
          stage,
        },
      },
    },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function giveUp(
  sessionId: string,
  questionKey: string,
  accessToken?: string,
): Promise<GiveUpResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient(accessToken).POST(
    "/api/v1/practice-sessions/{session_id}/questions/{question_key}/give-up",
    { params: { path: { session_id: sessionId, question_key: questionKey } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}
