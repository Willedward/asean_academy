import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiErrorMessage } from "./errors";

export type PracticeSessionResponse = components["schemas"]["PracticeSessionResponse"];
export type NextQuestionResponse = components["schemas"]["NextQuestionResponse"];
export type AttemptResponse = components["schemas"]["AttemptResponse"];
export type HintResponse = components["schemas"]["HintResponse"];
export type GiveUpResponse = components["schemas"]["GiveUpResponse"];

function fixtureGuard(): void {
  if (process.env.NEXT_PUBLIC_USE_API_FIXTURES === "true") {
    throw new Error("Interactive practice requires the local learning API.");
  }
}

function idempotencyKey(): string {
  return crypto.randomUUID();
}

export async function createPracticeSession(
  lessonKey: string,
  questionCount?: number,
): Promise<PracticeSessionResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST("/api/v1/practice-sessions", {
    params: { header: { "Idempotency-Key": idempotencyKey() } },
    body: {
      lesson_key: lessonKey,
      mode: "guided_practice",
      question_count: questionCount,
    },
  });
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getNextQuestion(sessionId: string): Promise<NextQuestionResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().GET(
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
): Promise<AttemptResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST("/api/v1/attempts", {
    params: { header: { "Idempotency-Key": idempotencyKey() } },
    body: {
      session_id: sessionId,
      question_key: questionKey,
      question_revision: questionRevision,
      answers,
    },
  });
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function revealHint(
  sessionId: string,
  questionKey: string,
  stage: 1 | 2,
): Promise<HintResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
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
): Promise<GiveUpResponse> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/practice-sessions/{session_id}/questions/{question_key}/give-up",
    { params: { path: { session_id: sessionId, question_key: questionKey } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}
