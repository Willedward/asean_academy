const READY_CACHE_MS = 10 * 60 * 1000;
const PROBE_TIMEOUT_MS = 40_000;
const RETRY_DELAYS_MS = [0, 1_000, 2_000, 4_000, 8_000, 16_000] as const;
const RETRYABLE_STATUSES = new Set([502, 503, 504]);

type ReadinessProbe = {
  baseUrl: string;
  promise: Promise<void>;
};

let readyBaseUrl = "";
let readyUntil = 0;
let readinessProbe: ReadinessProbe | null = null;

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function probeUntilReady(baseUrl: string): Promise<void> {
  let lastFailure = "The learning service did not become ready.";

  for (const retryDelay of RETRY_DELAYS_MS) {
    if (retryDelay > 0) await delay(retryDelay);

    let response: Response;
    try {
      response = await fetch(new URL("/api/v1/ready", baseUrl), {
        cache: "no-store",
        signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
      });
    } catch (error) {
      lastFailure = error instanceof Error ? error.message : lastFailure;
      continue;
    }

    if (response.ok) {
      readyBaseUrl = baseUrl;
      readyUntil = Date.now() + READY_CACHE_MS;
      return;
    }
    if (!RETRYABLE_STATUSES.has(response.status)) {
      throw new Error(`Learning API readiness check returned ${response.status}.`);
    }
    lastFailure = `Learning API readiness check returned ${response.status}.`;
  }

  throw new Error(lastFailure);
}

export async function ensureLearningApiReady(baseUrl: string): Promise<void> {
  const normalizedBaseUrl = baseUrl.replace(/\/$/, "");
  if (readyBaseUrl === normalizedBaseUrl && Date.now() < readyUntil) return;

  if (!readinessProbe || readinessProbe.baseUrl !== normalizedBaseUrl) {
    const promise = probeUntilReady(normalizedBaseUrl).finally(() => {
      if (readinessProbe?.promise === promise) readinessProbe = null;
    });
    readinessProbe = { baseUrl: normalizedBaseUrl, promise };
  }
  await readinessProbe.promise;
}
