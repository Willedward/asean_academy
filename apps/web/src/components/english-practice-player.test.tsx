import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
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
        prompt:
          "The path was treacherous—dangerous and unstable after the rain.",
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
      feedback:
        "Narrow is possible in general, but the sentence defines the word as dangerous.",
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

  it("fills a shared word bank with keyboard-native controls and reveals feedback as one group", async () => {
    const banked: EnglishNextQuestionResponse = {
      status: "active",
      session: {
        ...current.session,
        lesson_key: "e3-lesson-01",
        question_count: 1,
        assigned_count: 1,
      },
      position: 1,
      question: {
        stable_key: "eb-l1-001",
        revision: 1,
        title: "Restore the afternoon broadcast",
        difficulty: 2,
        outcome_code: "EB3.1",
        question_type: "banked_cloze",
        exposure_pool: "exit_ticket",
        instructions:
          "Choose one word for each gap. Each word can be used once.",
        passage: {
          stable_key: "english-passage-afternoon-broadcast",
          revision: 1,
          title: "The afternoon broadcast",
          text_type: "narrative",
          paragraphs: [
            "The studio was {{1}} while rain {{2}} against the windows.",
          ],
          attribution: "Original NextScholar passage.",
        },
        word_bank: [
          { key: "A", text: "anxious" },
          { key: "C", text: "deserted" },
          { key: "E", text: "hammered" },
          { key: "F", text: "relieved" },
        ],
        parts: [
          {
            position: 1,
            prompt: "Gap 1",
            response_type: "single_choice",
            options: [
              { key: "A", text: "anxious" },
              { key: "C", text: "deserted" },
              { key: "E", text: "hammered" },
              { key: "F", text: "relieved" },
            ],
          },
          {
            position: 2,
            prompt: "Gap 2",
            response_type: "single_choice",
            options: [
              { key: "A", text: "anxious" },
              { key: "C", text: "deserted" },
              { key: "E", text: "hammered" },
              { key: "F", text: "relieved" },
            ],
          },
        ],
      },
    };
    const groupedResult: EnglishAttemptResponse = {
      attempt_id: "a99591e5-1f20-4a45-a453-31995fc99b61",
      attempt_number: 1,
      correct: true,
      parts: [
        {
          position: 1,
          correct: true,
          error: null,
          feedback: "Deserted describes the empty studio.",
        },
        {
          position: 2,
          correct: true,
          error: null,
          feedback: "Hammered describes the forceful rain.",
        },
      ],
      question_finished: true,
      retry_queued: false,
      needs_error_classification: false,
      lesson_state: "proficient",
    };
    const api = {
      getNextQuestion: vi.fn(async () => banked),
      submitAttempt: vi.fn(async () => groupedResult),
      revealHint: vi.fn(async () => ({
        question_key: "eb-l1-001",
        parts: ["Hint 1", "Hint 2"],
      })),
      classifyError: vi.fn(async () => undefined),
    };

    render(
      <EnglishPracticePlayer sessionId={banked.session.session_id} api={api} />,
    );

    const gap1 = await screen.findByRole("combobox", { name: "Gap 1" });
    const gap2 = screen.getByRole("combobox", { name: "Gap 2" });
    expect(screen.getByRole("button", { name: "Check answer" })).toBeDisabled();

    fireEvent.change(gap1, { target: { value: "C" } });
    expect(screen.getByText("deserted · gap 1")).toBeInTheDocument();
    fireEvent.change(gap2, { target: { value: "C" } });
    expect(gap1).toHaveValue("");
    expect(screen.getByText("deserted · gap 2")).toBeInTheDocument();

    fireEvent.change(gap1, { target: { value: "C" } });
    fireEvent.change(gap2, { target: { value: "E" } });
    expect(
      screen.queryByText("Deserted describes the empty studio."),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Check answer" }));

    await waitFor(() =>
      expect(api.submitAttempt).toHaveBeenCalledWith(
        banked.session.session_id,
        "eb-l1-001",
        1,
        { "1": "C", "2": "E" },
      ),
    );
    expect(await screen.findByText("Passage feedback")).toBeInTheDocument();
    expect(
      screen.getByText("Deserted describes the empty studio."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Hammered describes the forceful rain."),
    ).toBeInTheDocument();
  });
});
