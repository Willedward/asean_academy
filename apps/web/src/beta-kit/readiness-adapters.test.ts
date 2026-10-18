import { describe, expect, it } from "vitest";

import type { components } from "@/lib/api/schema";

import { compareOutcomes, readinessCardKind, readinessFromResult } from "./readiness-adapters";

type DiagnosticResult = components["schemas"]["DiagnosticResultResponse"];

const base: DiagnosticResult = {
  band: "on_track",
  band_policy_version: "v1",
  recommendation_policy_version: "topic-readiness-v1",
  form_key: "n1-diagnostic",
  form_revision: 1,
  max_score: 8,
  score: 5,
  percentage: 62.5,
  purpose: "baseline",
  session_id: "5f1d6a0e-0000-4000-8000-000000000001",
  submitted_at: "2026-10-09T03:00:00Z",
  outcome_scores: [
    { outcome_code: "1.1", score: 4, max_score: 4, percentage: 100 },
    { outcome_code: "1.5", score: 1, max_score: 4, percentage: 25 },
  ],
  topic_scores: [],
  recommendations: [],
  strengths: ["1.1"],
  priorities: ["1.5"],
};

const titles = { "1.1": "Primes and prime factorisation" };

describe("readiness adapters", () => {
  it("puts strengths first and names outcomes from the course map", () => {
    const data = readinessFromResult(base, titles, { dateLabel: "9 October", start: { label: "Lesson 1", href: "/lessons/n1-lesson-01" } });
    expect(data.strengths).toEqual([{ code: "1.1", title: "Primes and prime factorisation", score: 4, max: 4 }]);
    expect(data.focus[0]).toMatchObject({ code: "1.5", title: "Outcome 1.5", score: 1 });
    expect(data.summary).not.toMatch(/weak|fail/i);
  });

  it("pairs start and end scores per outcome", () => {
    const end: DiagnosticResult = { ...base, purpose: "endline", outcome_scores: [{ outcome_code: "1.1", score: 4, max_score: 4, percentage: 100 }, { outcome_code: "1.5", score: 3, max_score: 4, percentage: 75 }] };
    expect(compareOutcomes(base, end, titles)[1]).toMatchObject({ code: "1.5", score: 1, after: 3 });
  });

  it("picks the dashboard card from GET /diagnostics/next", () => {
    expect(readinessCardKind({ status: "start", purpose: "baseline", title: "", message: "" })).toBe("baseline");
    expect(readinessCardKind({ status: "start", purpose: "endline", title: "", message: "" })).toBe("endline");
    expect(readinessCardKind({ status: "resume", title: "", message: "" })).toBe("resume");
    expect(readinessCardKind({ status: "baseline_complete", title: "", message: "" })).toBeNull();
  });
});
