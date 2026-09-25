import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { LearningHomeResponse } from "@/lib/api/progress";

import { LearningHomePanel } from "./learning-home-panel";

describe("LearningHomePanel", () => {
  it("links to the server-recommended active session", async () => {
    const fixture: LearningHomeResponse = {
      learner_id: "development-learner",
      course_key: "g3-sec1-math",
      unresolved_retry_count: 0,
      next_action: {
        type: "resume_practice",
        title: "Resume Primes and prime factorisation",
        description: "Continue question 2 of 3.",
        href: "/practice/session-1",
        lesson_key: "n1-lesson-01",
        session_id: "session-1",
      },
      lessons: [],
      checkpoints: [],
    };
    render(
      <LearningHomePanel loadLearningHome={vi.fn().mockResolvedValue(fixture)} />,
    );

    expect(
      await screen.findByRole("heading", {
        name: "Resume Primes and prime factorisation",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Continue" })).toHaveAttribute(
      "href",
      "/practice/session-1",
    );
  });
});
