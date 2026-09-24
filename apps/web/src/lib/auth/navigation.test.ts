import { afterEach, describe, expect, it } from "vitest";

import { getSiteOrigin, normalizeSiteOrigin, safeNextPath } from "./navigation";

const originalSiteUrl = process.env.NEXT_PUBLIC_SITE_URL;
const originalRailwayDomain = process.env.RAILWAY_PUBLIC_DOMAIN;
const originalVercelUrl = process.env.VERCEL_URL;

afterEach(() => {
  process.env.NEXT_PUBLIC_SITE_URL = originalSiteUrl;
  process.env.RAILWAY_PUBLIC_DOMAIN = originalRailwayDomain;
  process.env.VERCEL_URL = originalVercelUrl;
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
});
