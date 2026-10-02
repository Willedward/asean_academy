import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
  vi.resetModules();
});

describe("ensureLearningApiReady", () => {
  it("retries a sleeping service and caches the ready result", async () => {
    vi.useFakeTimers();
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 502 }))
      .mockResolvedValueOnce(new Response(null, { status: 200 }));
    vi.stubGlobal("fetch", fetcher);
    const { ensureLearningApiReady } = await import("./learning-api-readiness");

    const readiness = ensureLearningApiReady("https://api.example/");
    await vi.advanceTimersByTimeAsync(1_000);
    await readiness;
    await ensureLearningApiReady("https://api.example");

    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(fetcher).toHaveBeenLastCalledWith(
      new URL("https://api.example/api/v1/ready"),
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("shares one readiness probe across concurrent requests", async () => {
    let finishProbe: ((response: Response) => void) | undefined;
    const fetcher = vi.fn(
      () => new Promise<Response>((resolve) => {
        finishProbe = resolve;
      }),
    );
    vi.stubGlobal("fetch", fetcher);
    const { ensureLearningApiReady } = await import("./learning-api-readiness");

    const first = ensureLearningApiReady("https://api.example");
    const second = ensureLearningApiReady("https://api.example");
    expect(fetcher).toHaveBeenCalledTimes(1);

    finishProbe?.(new Response(null, { status: 200 }));
    await Promise.all([first, second]);
  });
});
