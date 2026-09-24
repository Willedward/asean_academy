import { describe, expect, it } from "vitest";

import type { CurrentLearnerResponse } from "@/lib/api/identity";

import { hasActiveEnrolment } from "./learner-state";

function learner(status: "active" | "completed" | "withdrawn"): CurrentLearnerResponse {
  return {
    profile: {
      learner_id: "bd9f63f0-87fb-4b2a-a33b-1d58a18a91cf",
      email: "student@example.test",
      display_name: "Student",
      role: "student",
      target_track: "g3-sec1-math",
    },
    enrolments: [{
      course_key: "g3-sec1-math",
      course_revision: 1,
      enrolled_at: "2026-09-24T12:00:00Z",
      status,
    }],
  };
}

describe("hasActiveEnrolment", () => {
  it("accepts only active course enrolments", () => {
    expect(hasActiveEnrolment(learner("active"))).toBe(true);
    expect(hasActiveEnrolment(learner("completed"))).toBe(false);
    expect(hasActiveEnrolment(learner("withdrawn"))).toBe(false);
    expect(hasActiveEnrolment({ ...learner("active"), enrolments: [] })).toBe(false);
  });
});
