import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiErrorMessage } from "./errors";

export type DiagnosticNext = components["schemas"]["DiagnosticNextResponse"];
export type DiagnosticPurpose = components["schemas"]["CreateDiagnosticSessionRequest"]["expected_purpose"];
export type DiagnosticSession = components["schemas"]["DiagnosticSessionResponse"];
export type DiagnosticResult = components["schemas"]["DiagnosticResultResponse"];

function fixtureGuard(): void {
  if (process.env.NEXT_PUBLIC_USE_API_FIXTURES === "true") {
    throw new Error("Interactive diagnostics require the learning API.");
  }
}

function key(): string {
  return crypto.randomUUID();
}

export async function getNextDiagnostic(): Promise<DiagnosticNext> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/diagnostics/next",
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function createDiagnosticSession(
  expectedPurpose?: "baseline" | "endline" | null,
): Promise<DiagnosticSession> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/diagnostics/sessions",
    {
      params: { header: { "Idempotency-Key": key() } },
      body: { expected_purpose: expectedPurpose ?? null },
    },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getDiagnosticSession(
  sessionId: string,
): Promise<DiagnosticSession> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/diagnostics/sessions/{session_id}",
    { params: { path: { session_id: sessionId } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function saveDiagnosticResponse(
  sessionId: string,
  position: number,
  answers: Record<string, string>,
): Promise<void> {
  fixtureGuard();
  const { error, response } = await createApiClient().PUT(
    "/api/v1/diagnostics/sessions/{session_id}/responses/{position}",
    {
      params: {
        path: { session_id: sessionId, position },
        header: { "Idempotency-Key": key() },
      },
      body: { answers },
    },
  );
  if (error) throw new Error(apiErrorMessage(error, response.status));
}

export async function submitDiagnosticSession(
  sessionId: string,
): Promise<DiagnosticResult> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/diagnostics/sessions/{session_id}/submit",
    { params: { path: { session_id: sessionId } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}

export async function getDiagnosticResult(
  sessionId: string,
): Promise<DiagnosticResult> {
  fixtureGuard();
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/diagnostics/sessions/{session_id}/result",
    { params: { path: { session_id: sessionId } } },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}
