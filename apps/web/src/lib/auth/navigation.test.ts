import { afterEach, describe, expect, it } from "vitest";

import {
  getSiteOrigin,
  loginErrorPath,
  normalizeSiteOrigin,
  onboardingPath,
  safeNextPath,
} from "./navigation";

const originalSiteUrl = process.env.NEXT_PUBLIC_SITE_URL;
const originalRailwayDomain = process.env.RAILWAY_PUBLIC_DOMAIN;
const originalVercelUrl = process.env.VERCEL_URL;
const originalRenderUrl = process.env.RENDER_EXTERNAL_URL;

afterEach(() => {
  process.env.NEXT_PUBLIC_SITE_URL = originalSiteUrl;
  process.env.RAILWAY_PUBLIC_DOMAIN = originalRailwayDomain;
  process.env.VERCEL_URL = originalVercelUrl;
  process.env.RENDER_EXTERNAL_URL = originalRenderUrl;
});

describe("hosted auth navigation", () => {
  it("allows only application-relative post-login paths", () => {
    expect(safeNextPath("/lessons/n1-lesson-01?from=login")).toBe(
      "/lessons/n1-lesson-01?from=login",
    );
    expect(safeNextPath("https://attacker.example/steal")).toBe("/onboarding");
    expect(safeNextPath("//attacker.example/steal")).toBe("/onboarding");
    expect(safeNextPath("/\\attacker.example/steal")).toBe("/onboarding");
  });

  it("preserves invitation links across sign-in and safe error retries", () => {
    const invitation = onboardingPath("invite / + token");
    expect(invitation).toBe("/onboarding?code=invite%20%2F%20%2B%20token");
    expect(loginErrorPath("oauth_start_failed", invitation)).toBe(
      "/login?error=oauth_start_failed&next=%2Fonboarding%3Fcode%3Dinvite%2520%252F%2520%252B%2520token",
    );
    expect(
      loginErrorPath("auth_callback_failed", "https://attacker.example"),
    ).toBe("/login?error=auth_callback_failed&next=%2Fonboarding");
  });

  it("normalizes deployed hostnames to HTTPS origins", () => {
    expect(normalizeSiteOrigin("academy.example.com/path")).toBe(
      "https://academy.example.com",
    );
    expect(normalizeSiteOrigin("http://localhost:3000/callback")).toBe(
      "http://localhost:3000",
    );
  });

  it("uses the explicit public site URL before platform fallbacks", () => {
    process.env.NEXT_PUBLIC_SITE_URL = "https://beta.academy.example/path";
    process.env.RAILWAY_PUBLIC_DOMAIN = "railway.example";
    expect(getSiteOrigin()).toBe("https://beta.academy.example");
  });

  it("uses the Render public URL when no explicit site URL is configured", () => {
    delete process.env.NEXT_PUBLIC_SITE_URL;
    delete process.env.RAILWAY_PUBLIC_DOMAIN;
    delete process.env.VERCEL_URL;
    process.env.RENDER_EXTERNAL_URL = "https://nextscholar-review.onrender.com";

    expect(getSiteOrigin()).toBe("https://nextscholar-review.onrender.com");
  });
});
