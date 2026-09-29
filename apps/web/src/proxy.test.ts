import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  updateSession: vi.fn(async () => new Response(null, { status: 200 })),
}));

vi.mock("@/lib/supabase/proxy", () => ({
  updateSession: mocks.updateSession,
}));

import { proxy } from "./proxy";

afterEach(() => {
  vi.unstubAllEnvs();
  mocks.updateSession.mockClear();
});

describe("beta kit route gate", () => {
  it("returns a real 404 before session handling in production", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_BETA_KIT", "false");

    const response = await proxy(
      new NextRequest("https://academy.example/beta-kit/dashboard"),
    );

    expect(response.status).toBe(404);
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(mocks.updateSession).not.toHaveBeenCalled();
  });

  it("allows the preview when the production flag is explicit", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_BETA_KIT", "true");

    const request = new NextRequest("https://academy.example/beta-kit");
    const response = await proxy(request);

    expect(response.status).toBe(200);
    expect(mocks.updateSession).toHaveBeenCalledWith(request);
  });

  it("does not affect normal application routes", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_BETA_KIT", "false");

    const request = new NextRequest("https://academy.example/learn");
    const response = await proxy(request);

    expect(response.status).toBe(200);
    expect(mocks.updateSession).toHaveBeenCalledWith(request);
  });
});
