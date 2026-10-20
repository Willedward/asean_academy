import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  EnglishAttemptResponse,
  EnglishHintResponse,
  EnglishNextQuestionResponse,
} from "@/lib/api/english";

import { EnglishPracticePlayer } from "./english-practice-player";

const current: EnglishNextQuestionResponse = {
  status: "active",
  session: {
    session_id: "69284c2d-018f-4ddb-8935-51918af14954",
    status: "active",
    lesson_key: "e1-lesson-01",
    lesson_revision: 1,
    mode: "guided_practice",
    question_count: 6,
    assigned_count: 6,
    resolved_count: 0,
    correct_count: 0,
    incorrect_count: 0,
    development_drafts: true,
  },
  position: 1,
  question: {
    stable_key: "ev-l1-001",
    revision: 1,
    title: "Meaning from a direct definition",
    difficulty: 1,
    outcome_code: "EV1.1",
    question_type: "vocabulary_context",
    exposure_pool: "guided_practice",
    instructions: "Use the nearby clue to choose the best meaning.",
    passage: null,
    parts: [
      {
        position: 1,
        prompt: "The path was treacherous—dangerous and unstable after the rain.",
        response_type: "single_choice",
        options: [
          { key: "A", text: "narrow" },
          { key: "B", text: "hazardous" },
          { key: "C", text: "peaceful" },
          { key: "D", text: "familiar" },
        ],
      },
    ],
  },
};

const incorrect: EnglishAttemptResponse = {
  attempt_id: "77a055b2-f447-4f1a-a174-01763a433154",
  attempt_number: 1,
  correct: false,
  parts: [
    {
      position: 1,
      correct: false,
      error: null,
      feedback: "Narrow is possible in general, but the sentence defines the word as dangerous.",
    },
  ],
  question_finished: true,
  retry_queued: false,
  needs_error_classification: true,
  lesson_state: "in_progress",
};

afterEach(cleanup);

describe("EnglishPracticePlayer", () => {
  it("marks an objective answer and records the learner's error classification before continuing", async () => {
    const api = {
      getNextQuestion: vi.fn(async () => current),
      submitAttempt: vi.fn(async () => incorrect),
      revealHint: vi.fn(
        async () =>
          ({
            question_key: "ev-l1-001",
            parts: ["Look for words after the dash."],
          }) as EnglishHintResponse,
      ),
      classifyError: vi.fn(async () => undefined),
    };

    render(
      <EnglishPracticePlayer
        sessionId="69284c2d-018f-4ddb-8935-51918af14954"
        api={api}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Question 1 of 6" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("radio", { name: /A\. narrow/i }));
    fireEvent.click(screen.getByRole("button", { name: "Check answer" }));

    expect(
      await screen.findByText(/sentence defines the word as dangerous/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue" })).toBeDisabled();

    fireEvent.click(screen.getByRole("radio", { name: /I missed the clue/i }));
    fireEvent.click(screen.getByRole("button", { name: "Save reflection" }));

    await waitFor(() =>
      expect(api.classifyError).toHaveBeenCalledWith(
        "77a055b2-f447-4f1a-a174-01763a433154",
        "missed_clue",
      ),
    );
    expect(screen.getByText("Reflection saved")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue" })).toBeEnabled();
    expect(screen.queryByText(/\bXP\b/i)).not.toBeInTheDocument();
  });
});
