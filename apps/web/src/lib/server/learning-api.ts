import "server-only";

import type { CurrentLearnerResponse } from "@/lib/api/identity";
import type { VerifiedSession } from "@/lib/auth/session";

function baseUrl(): string {
  return (process.env.LEARNING_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
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
    body = await response.json() as ErrorBody;
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

export async function getServerLearner(
  session: VerifiedSession,
): Promise<CurrentLearnerResponse> {
  const response = await fetch(`${baseUrl()}/api/v1/me`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${session.accessToken}`,
      "X-Request-ID": crypto.randomUUID(),
    },
  });
  if (!response.ok) throw await parseError(response);
  return await response.json() as CurrentLearnerResponse;
}
