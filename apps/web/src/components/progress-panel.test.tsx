import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { PracticeSessionResponse } from "@/lib/api/practice";
import type { ProgressResponse } from "@/lib/api/progress";

import { ProgressPanel } from "./progress-panel";

const { push } = vi.hoisted(() => ({ push: vi.fn() }));

vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

const progressFixture: ProgressResponse = {
  learner_id: "development-learner",
  course_key: "g3-sec1-math",
  proficiency_threshold: 70,
  checkpoint_required_for_mastery: true,
  scheduled_retry_count: 2,
  next_retry_due_at: "2026-09-30T02:00:00Z",
  lessons: [
    {
      lesson_key: "n1-lesson-01",
      lesson_title: "Primes and prime factorisation",
      position: 1,
      state: "practice_completed",
      unlocked: true,
      question_count: 3,
      resolved_count: 2,
      correct_count: 2,
      gave_up_count: 1,
      retry_question_count: 1,
      eventual_correct_percentage: 67,
      checkpoint_passed: false,
      last_session_id: "session-1",
      updated_at: "2026-09-24T00:00:00Z",
    },
  ],
  checkpoints: [
    {
      unit_key: "g3-sec1-n1",
      available: true,
      state: "available",
      question_count: 8,
      passing_percentage: 70,
      last_percentage: 50,
      last_session_id: "completed-checkpoint",
    },
  ],
};

function session(
  overrides: Partial<PracticeSessionResponse>,
): PracticeSessionResponse {
  return {
    session_id: "session-new",
    mode: "guided_practice",
    status: "active",
    question_count: 1,
    development_drafts: false,
    ...overrides,
  };
}

describe("ProgressPanel", () => {
  afterEach(cleanup);

  beforeEach(() => {
    push.mockReset();
  });

  it("shows proficiency without claiming checkpoint mastery", async () => {
    const fixture: ProgressResponse = {
      ...progressFixture,
      lessons: [
        {
          ...progressFixture.lessons[0]!,
          state: "proficient",
          correct_count: 3,
          resolved_count: 3,
          gave_up_count: 0,
          retry_question_count: 0,
          eventual_correct_percentage: 100,
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
      screen.getByText(/Mastery requires passing the unit checkpoint/),
    ).toBeInTheDocument();
    expect(screen.getByText(/2 spaced reviews scheduled/)).toBeInTheDocument();
  });

  it("starts a server-owned retry review from the NextScholar progress view", async () => {
    const startRetry = vi.fn().mockResolvedValue(
      session({
        session_id: "retry-session",
        lesson_key: "n1-lesson-01",
        mode: "retry_review",
      }),
    );

    render(
      <ProgressPanel
        appearance="nextscholar"
        loadProgress={vi.fn().mockResolvedValue(progressFixture)}
        startRetry={startRetry}
      />,
    );

    fireEvent.click(
      await screen.findByRole("button", { name: "Start review" }),
    );

    await waitFor(() =>
      expect(startRetry).toHaveBeenCalledWith("n1-lesson-01"),
    );
    expect(push).toHaveBeenCalledWith("/practice/retry-session");
    expect(screen.queryByText(/XP/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/league/i)).not.toBeInTheDocument();
  });

  it("creates a fresh checkpoint session when retaking a completed attempt", async () => {
    const startCheckpoint = vi.fn().mockResolvedValue(
      session({
        session_id: "checkpoint-retake",
        mode: "checkpoint",
        unit_key: "g3-sec1-n1",
        question_count: 8,
      }),
    );

    render(
      <ProgressPanel
        appearance="nextscholar"
        loadProgress={vi.fn().mockResolvedValue(progressFixture)}
        startCheckpoint={startCheckpoint}
      />,
    );

    fireEvent.click(
      await screen.findByRole("button", { name: "Retake checkpoint" }),
    );

    await waitFor(() =>
      expect(startCheckpoint).toHaveBeenCalledWith("g3-sec1-n1"),
    );
    expect(push).toHaveBeenCalledWith("/checkpoints/checkpoint-retake");
  });

  it("resumes the active checkpoint without creating another session", async () => {
    const startCheckpoint = vi.fn();
    const fixture: ProgressResponse = {
      ...progressFixture,
      checkpoints: [
        {
          ...progressFixture.checkpoints[0]!,
          state: "in_progress",
          last_session_id: "active-checkpoint",
        },
      ],
    };

    render(
      <ProgressPanel
        appearance="nextscholar"
        loadProgress={vi.fn().mockResolvedValue(fixture)}
        startCheckpoint={startCheckpoint}
      />,
    );

    fireEvent.click(
      await screen.findByRole("button", { name: "Resume checkpoint" }),
    );

    expect(startCheckpoint).not.toHaveBeenCalled();
    expect(push).toHaveBeenCalledWith("/checkpoints/active-checkpoint");
  });
});
