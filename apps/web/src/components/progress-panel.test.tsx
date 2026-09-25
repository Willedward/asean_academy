import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ProgressResponse } from "@/lib/api/progress";

import { ProgressPanel } from "./progress-panel";

describe("ProgressPanel", () => {
  it("shows proficiency without claiming checkpoint mastery", async () => {
    const fixture: ProgressResponse = {
      learner_id: "development-learner",
      course_key: "g3-sec1-math",
      proficiency_threshold: 70,
      checkpoint_required_for_mastery: true,
      lessons: [
        {
          lesson_key: "n1-lesson-01",
          lesson_title: "Primes and prime factorisation",
          position: 1,
          state: "proficient",
          unlocked: true,
          question_count: 3,
          resolved_count: 3,
          correct_count: 3,
          gave_up_count: 0,
          retry_question_count: 0,
          eventual_correct_percentage: 100,
          checkpoint_passed: false,
          last_session_id: "session-1",
          updated_at: "2026-09-24T00:00:00Z",
        },
      ],
      checkpoints: [],
    };
    render(<ProgressPanel loadProgress={vi.fn().mockResolvedValue(fixture)} />);

    expect(
      await screen.findByRole("heading", {
        name: "Primes and prime factorisation",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Proficient")).toBeInTheDocument();
    expect(
      screen.getByText(/Mastery remains locked until the reviewed unit checkpoint/),
    ).toBeInTheDocument();
  });
});
