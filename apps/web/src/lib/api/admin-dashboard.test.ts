import { afterEach, describe, expect, it, vi } from "vitest";

import { adminRequest } from "./admin-dashboard";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("adminRequest", () => {
  it("turns an HTML gateway response into a safe API error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response("<!DOCTYPE html><title>Bad Gateway</title>", {
            status: 502,
            headers: {
              "content-type": "text/html",
              "x-request-id": "gateway-request-id",
            },
          }),
      ),
    );

    await expect(adminRequest("tutor-evaluation")).rejects.toMatchObject({
      message: "The learning service timed out or restarted. Please try again.",
      status: 502,
      code: "learning_api_invalid_response",
      requestId: "gateway-request-id",
    });
  });

  it("still returns a successful JSON response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify({ status: "ready" }), {
            headers: { "content-type": "application/json" },
          }),
      ),
    );

    await expect(adminRequest("system-status")).resolves.toEqual({
      status: "ready",
    });
  });
});
