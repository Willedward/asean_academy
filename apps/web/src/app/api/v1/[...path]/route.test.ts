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
});
