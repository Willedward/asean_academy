/**
 * Learner AI tutor ("Ask the hornbill") API.
 *
 * Contract: docs/plan/AI_TUTOR_FRONTEND_BACKEND_HANDOFF.md. Types come from the
 * generated OpenAPI schema; nothing here invents a response shape. The browser
 * only talks to the same-origin /api/v1 gateway, never to a model provider.
 */
import type { components } from "./schema";
import { createApiClient } from "./client";
import { ApiRequestError } from "./errors";

type Schemas = components["schemas"];

export type TutorSessionResponse = Schemas["TutorSessionResponse"];
export type TutorReplyResponse = Schemas["TutorReplyResponse"];
export type TutorMessageResponse = Schemas["TutorMessageResponse"];
export type TutorQuotaResponse = Schemas["TutorQuotaResponse"];
export type TutorBlock = Schemas["TutorBlock"];
export type TutorAnswerLockState = Schemas["AnswerLockState"];
export type TutorMode = NonNullable<TutorMessageResponse["mode"]>;
export type CreateTutorSessionInput = Schemas["CreateTutorSessionRequest"];

/** Messages must hold 1 to 1,200 visible characters (SendTutorMessageRequest). */
export const TUTOR_MESSAGE_MAX_LENGTH = 1200;

/** ApiRequestError plus the envelope's `details` (for example `resets_at` on quota errors). */
export class TutorApiError extends ApiRequestError {
  constructor(
    message: string,
    status: number,
    code: string,
    requestId?: string,
    readonly details: Record<string, unknown> | null = null,
  ) {
    super(message, status, code, requestId);
    this.name = "TutorApiError";
  }
}

type Envelope = {
  error?: {
    code?: string;
    message?: string;
    request_id?: string;
    details?: Record<string, unknown> | null;
  };
};

function toError(error: unknown, response: Response | undefined): TutorApiError {
  const status = response?.status ?? 0;
  const detail = typeof error === "object" && error !== null ? (error as Envelope).error : undefined;
  return new TutorApiError(
    detail?.message ?? `Learning API returned ${status}.`,
    status,
    detail?.code ?? "learning_api_error",
    detail?.request_id ?? response?.headers.get("x-request-id") ?? undefined,
    detail?.details ?? null,
  );
}

function liveApiGuard(): void {
  // The tutor must never show fake conversations in a hosted build.
  if (process.env.NEXT_PUBLIC_USE_API_FIXTURES === "true") {
    throw new TutorApiError(
      "The AI tutor needs the live Learning API.",
      503,
      "tutor_requires_live_api",
    );
  }
}

type Result<T> = { data?: T; error?: unknown; response: Response };

/** Runs one request and turns every failure (HTTP, network, non-JSON gateway page) into a TutorApiError. */
async function run<T>(request: () => Promise<Result<T>>): Promise<T> {
  liveApiGuard();
  let result: Result<T>;
  try {
    result = await request();
  } catch (cause) {
    if (cause instanceof TutorApiError) throw cause;
    const invalid = cause instanceof SyntaxError;
    throw new TutorApiError(
      invalid
        ? "The learning service returned an unexpected response."
        : "Could not reach the learning service.",
      invalid ? 502 : 0,
      invalid ? "learning_api_invalid_response" : "network_error",
    );
  }
  const { data, error, response } = result;
  if (error !== undefined || data === undefined) throw toError(error, response);
  return data;
}

/** Starts a session pinned to one practice question. The server checks ownership and revisions. */
export function createTutorSession(
  input: CreateTutorSessionInput,
  accessToken?: string,
): Promise<TutorSessionResponse> {
  return run(() =>
    createApiClient(accessToken).POST("/api/v1/tutor/sessions", { body: input }),
  );
}

/** Restores the server-owned history, for example after a page refresh. */
export function getTutorSession(
  sessionId: string,
  accessToken?: string,
): Promise<TutorSessionResponse> {
  return run(() =>
    createApiClient(accessToken).GET("/api/v1/tutor/sessions/{session_id}", {
      params: { path: { session_id: sessionId } },
    }),
  );
}

/**
 * Sends one learner message. Send only what the learner typed: the server reads
 * the latest attempt and marking itself. There is no idempotency key, so never
 * replay this automatically after a timeout.
 */
export function sendTutorMessage(
  sessionId: string,
  message: string,
  accessToken?: string,
): Promise<TutorReplyResponse> {
  const text = message.trim();
  if (!text || text.length > TUTOR_MESSAGE_MAX_LENGTH) {
    return Promise.reject(
      new TutorApiError(
        `Messages must be 1 to ${TUTOR_MESSAGE_MAX_LENGTH} characters.`,
        400,
        "tutor_message_invalid",
      ),
    );
  }
  return run(() =>
    createApiClient(accessToken).POST("/api/v1/tutor/sessions/{session_id}/messages", {
      params: { path: { session_id: sessionId } },
      body: { message: text },
    }),
  );
}

/** Ends the session when the learner ends it or leaves the question. */
export function closeTutorSession(
  sessionId: string,
  accessToken?: string,
): Promise<TutorSessionResponse> {
  return run(() =>
    createApiClient(accessToken).POST("/api/v1/tutor/sessions/{session_id}/close", {
      params: { path: { session_id: sessionId } },
    }),
  );
}
