import { afterEach, describe, expect, it } from "vitest";

import { getE2EAuthSecret, isE2EAuthenticationEnabled } from "./e2e-config";

const originalEnvironment = process.env.ASEAN_ACADEMY_ENV;
const originalSecret = process.env.ASEAN_ACADEMY_E2E_AUTH_SECRET;

afterEach(() => {
  process.env.ASEAN_ACADEMY_ENV = originalEnvironment;
  process.env.ASEAN_ACADEMY_E2E_AUTH_SECRET = originalSecret;
});

describe("test-only authentication configuration", () => {
  it("enables signed E2E sessions only in test with a strong secret", () => {
    process.env.ASEAN_ACADEMY_ENV = "test";
    process.env.ASEAN_ACADEMY_E2E_AUTH_SECRET = "asean-academy-local-e2e-secret-2026-only";

    expect(isE2EAuthenticationEnabled()).toBe(true);
    expect(getE2EAuthSecret()).toBe("asean-academy-local-e2e-secret-2026-only");
  });

  it("fails closed outside test and for short secrets", () => {
    process.env.ASEAN_ACADEMY_ENV = "production";
    process.env.ASEAN_ACADEMY_E2E_AUTH_SECRET = "asean-academy-local-e2e-secret-2026-only";
    expect(isE2EAuthenticationEnabled()).toBe(false);

    process.env.ASEAN_ACADEMY_ENV = "test";
    process.env.ASEAN_ACADEMY_E2E_AUTH_SECRET = "too-short";
    expect(isE2EAuthenticationEnabled()).toBe(false);
  });
});
