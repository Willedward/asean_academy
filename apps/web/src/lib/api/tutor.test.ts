import createClient from "openapi-fetch";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { paths } from "./schema";

const fetchMock = vi.fn<(request: Request) => Promise<Response>>();

// openapi-fetch needs an absolute URL outside the browser.
vi.mock("./client", () => ({
  createApiClient: () => createClient<paths>({ baseUrl: "http://learning.test", fetch: (request: Request) => fetchMock(request) }),
}));

import {
  TutorApiError,
  closeTutorSession,
  createTutorSession,
  getTutorSession,
  sendTutorMessage,
} from "./tutor";

const SESSION = "6b0f8d0e-1c2b-4d3e-9f40-5a6b7c8d9e0f";
const PRACTICE = "69284c2d-018f-4ddb-8935-51918af14954";

const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...headers } });

const session = {
  session_id: SESSION,
  practice_session_id: PRACTICE,
  question_key: "n1-l1-02",
  question_revision: 1,
  status: "active",
  answer_lock_state: { answer_locked: true, solution_locked: true },
  model_policy_version: "v1",
  messages: [],
  created_at: "2026-10-09T02:00:00Z",
  closed_at: null,
};

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubEnv("NEXT_PUBLIC_USE_API_FIXTURES", "false");
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("tutor API module", () => {
  it("creates a session from the practice identity only", async () => {
    fetchMock.mockResolvedValueOnce(json(session, 201));
    await expect(
      createTutorSession({ practice_session_id: PRACTICE, question_key: "n1-l1-02", question_revision: 1 }),
    ).resolves.toMatchObject({ session_id: SESSION });
    const request = fetchMock.mock.calls[0]![0];
    expect(request.method).toBe("POST");
    expect(new URL(request.url).pathname).toBe("/api/v1/tutor/sessions");
    expect(await request.json()).toEqual({ practice_session_id: PRACTICE, question_key: "n1-l1-02", question_revision: 1 });
  });

  it("sends only the learner's trimmed text", async () => {
    fetchMock.mockResolvedValueOnce(json({ ok: true }));
    await sendTutorMessage(SESSION, "  Why is my answer wrong?  ");
    const request = fetchMock.mock.calls[0]![0];
    expect(new URL(request.url).pathname).toBe(`/api/v1/tutor/sessions/${SESSION}/messages`);
    expect(await request.json()).toEqual({ message: "Why is my answer wrong?" });
  });

  it("rejects empty and over-long messages without calling the API", async () => {
    await expect(sendTutorMessage(SESSION, "   ")).rejects.toMatchObject({ code: "tutor_message_invalid" });
    await expect(sendTutorMessage(SESSION, "x".repeat(1201))).rejects.toMatchObject({ code: "tutor_message_invalid" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("restores and closes a session by id", async () => {
    fetchMock.mockResolvedValueOnce(json(session)).mockResolvedValueOnce(json({ ...session, status: "closed" }));
    await getTutorSession(SESSION);
    await closeTutorSession(SESSION);
    expect(fetchMock.mock.calls.map(([request]) => `${request.method} ${new URL(request.url).pathname}`)).toEqual([
      `GET /api/v1/tutor/sessions/${SESSION}`,
      `POST /api/v1/tutor/sessions/${SESSION}/close`,
    ]);
  });

  it("keeps the code, request id and details of an error envelope", async () => {
    fetchMock.mockResolvedValueOnce(
      json(
        {
          error: {
            code: "tutor_quota_exceeded",
            message: "Daily tutor allowance used.",
            request_id: "req_123",
            details: { resets_at: "2026-10-10T00:00:00Z" },
          },
        },
        429,
      ),
    );
    const error = await sendTutorMessage(SESSION, "hi").catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(TutorApiError);
    expect(error).toMatchObject({
      status: 429,
      code: "tutor_quota_exceeded",
      requestId: "req_123",
      details: { resets_at: "2026-10-10T00:00:00Z" },
    });
  });

  it("turns an HTML gateway page and a network failure into safe errors", async () => {
    fetchMock.mockResolvedValueOnce(new Response("<!DOCTYPE html>Bad Gateway", { status: 502, headers: { "content-type": "text/html" } }));
    await expect(getTutorSession(SESSION)).rejects.toMatchObject({ status: 502 });
    fetchMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await expect(getTutorSession(SESSION)).rejects.toMatchObject({ code: "network_error", status: 0 });
  });

  it("refuses to run against API fixtures", async () => {
    vi.stubEnv("NEXT_PUBLIC_USE_API_FIXTURES", "true");
    await expect(getTutorSession(SESSION)).rejects.toMatchObject({ code: "tutor_requires_live_api" });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
