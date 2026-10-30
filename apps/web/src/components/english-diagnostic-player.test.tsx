import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  EnglishDiagnosticAttemptResponse,
  EnglishDiagnosticNextQuestionResponse,
} from "@/lib/api/english";

import { EnglishDiagnosticPlayer } from "./english-diagnostic-player";

const replace = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));

const session = {
  session_id: "69284c2d-018f-4ddb-8935-51918af14954",
  status: "active" as const,
  purpose: "baseline" as const,
  exam_profile_key: "asean-english-sec1-id-reported-v1",
  form_key: "english-baseline-sec1-id-v1",
  form_revision: 1,
  title: "English Core baseline form A",
  question_count: 1,
  expected_part_count: 1,
  resolved_count: 0,
  correct_parts: 0,
  total_parts: 0,
  score: null,
  percentage: null,
  band: null,
  task_scores: [],
  development_drafts: true,
  started_at: "2026-10-30T00:00:00Z",
  completed_at: null,
};

const current: EnglishDiagnosticNextQuestionResponse = {
  status: "active",
  session,
  position: 1,
  question: {
    stable_key: "ev-l5-003",
    revision: 1,
    title: "Vocabulary in context",
    difficulty: 3,
    outcome_code: "EV1.1",
    question_type: "vocabulary_in_context",
    exposure_pool: "diagnostic",
    instructions: "Choose the best meaning.",
    passage: null,
    word_bank: null,
    parts: [
      {
        position: 1,
        prompt: "The instructions were lucid.",
        response_type: "single_choice",
        options: [
          { key: "A", text: "unclear" },
          { key: "B", text: "clear" },
        ],
      },
    ],
  },
};

afterEach(() => {
  cleanup();
  replace.mockReset();
});

describe("EnglishDiagnosticPlayer", () => {
  it("submits a complete protected group without exposing early correctness", async () => {
    const completed: EnglishDiagnosticAttemptResponse = {
      attempt_id: "77a055b2-f447-4f1a-a174-01763a433154",
      accepted: true,
      diagnostic_completed: true,
      session: {
        ...session,
        status: "completed",
        resolved_count: 1,
        correct_parts: 1,
        total_parts: 1,
        score: 1,
        percentage: 100,
        band: "secure",
        completed_at: "2026-10-30T00:05:00Z",
      },
    };
    const api = {
      getNextQuestion: vi.fn(async () => current),
      submitAttempt: vi.fn(async () => completed),
    };

    render(
      <EnglishDiagnosticPlayer sessionId={session.session_id} api={api} />,
    );

    expect(
      await screen.findByRole("heading", { name: "Question group 1 of 1" }),
    ).toBeInTheDocument();
    expect(screen.getByText("No feedback during the form")).toBeInTheDocument();
    expect(screen.queryByText(/correct/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: /B\. clear/i }));
    fireEvent.click(screen.getByRole("button", { name: "Submit final group" }));

    await waitFor(() =>
      expect(api.submitAttempt).toHaveBeenCalledWith(
        session.session_id,
        "ev-l5-003",
        1,
        { "1": "B" },
      ),
    );
    expect(replace).toHaveBeenCalledWith(
      `/english/diagnostics/${session.session_id}/result`,
    );
  });
});
