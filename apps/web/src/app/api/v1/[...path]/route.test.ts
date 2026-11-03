import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  getVerifiedSession: vi.fn(),
  isAuthenticationConfigured: () => false,
}));

vi.mock("@/lib/server/learning-api-readiness", () => ({
  ensureLearningApiReady: vi.fn().mockResolvedValue(undefined),
}));

import { GET } from "./route";

describe("learning API proxy", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("does not forward an upstream content-length after fetch decompression", async () => {
    const payload = { items: [{ stable_key: "g3-sec1-math" }] };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(payload), {
          headers: {
            "content-type": "application/json",
            "content-length": "5",
          },
        }),
      ),
    );

    const response = await GET(
      new NextRequest("http://localhost/api/v1/admin/content?limit=25"),
      { params: Promise.resolve({ path: ["admin", "content"] }) },
    );

    expect(response.headers.get("content-length")).toBeNull();
    await expect(response.json()).resolves.toEqual(payload);
  });

  it("sends a signed client address only when a secret is configured", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response("{}", { headers: { "content-type": "application/json" } }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const send = async () => {
      await GET(
        new NextRequest("http://localhost/api/v1/admin/content", {
          headers: { "x-forwarded-for": "203.0.113.7, 10.0.0.1" },
        }),
        { params: Promise.resolve({ path: ["admin", "content"] }) },
      );
      const init = fetchMock.mock.lastCall?.at(1) as unknown as RequestInit;
      return init.headers as Headers;
    };

    vi.stubEnv("ASEAN_ACADEMY_ABUSE_HASH_SECRET", "");
    expect((await send()).get("x-academy-client-address")).toBeNull();

    vi.stubEnv("ASEAN_ACADEMY_ABUSE_HASH_SECRET", "test-secret");
    const headers = await send();
    expect(headers.get("x-academy-client-address")).toBe("203.0.113.7");
    expect(headers.get("x-academy-client-address-signature")).toBe(
      "2122bc91ce2ddbe6a40a41de2babfb9bb875f51ac727e452281448662dca27f5",
    );
  });
});
