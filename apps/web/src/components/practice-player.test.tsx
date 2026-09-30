import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  AttemptResponse,
  GiveUpResponse,
  HintResponse,
  NextQuestionResponse,
} from "@/lib/api/practice";

import { PracticePlayer } from "./practice-player";

const current: NextQuestionResponse = {
  status: "active",
  session: {
    session_id: "69284c2d-018f-4ddb-8935-51918af14954",
    status: "active",
    question_count: 3,
    assigned_count: 1,
    resolved_count: 0,
    correct_count: 0,
    gave_up_count: 0,
    incorrect_count: 0,
    lesson_key: "n1-lesson-01",
    mode: "guided_practice",
    development_drafts: true,
  },
  position: 1,
  selection_reason: "configured_lesson_pool",
  stage: "guided",
  attempt_count: 0,
  highest_hint_stage: 0,
  solution_available: false,
  question: {
    stable_key: "n1-l1-01",
    revision: 1,
    title: "Prime factorisation of 360",
    difficulty: 1,
    primary_outcome: "1.1",
    calculator_allowed: true,
    total_marks: 2,
    source_status: "draft",
    stem: [],
    parts: [
      {
        position: 1,
        label: null,
        prompt: [
          { type: "text", text: "Express " },
          { type: "inline_math", latex: "360" },
          { type: "text", text: " as a product of prime factors." },
        ],
        marks: 2,
        response_type: "algebraic_expression",
        input_placeholder: "Enter a product of prime factors",
      },
    ],
    assets: [],
  },
};

const correct: AttemptResponse = {
  attempt_number: 1,
  correct: true,
  parts: [
    {
      position: 1,
      correct: true,
      error: null,
      marks_awarded: 2,
      marks_available: 2,
    },
  ],
  marks_awarded: 2,
  marks_available: 2,
  question_finished: true,
  solution_available: false,
};

afterEach(cleanup);

describe("PracticePlayer", () => {
  it("collects a typed final answer and sends it for backend marking", async () => {
    const api = {
      getNextQuestion: vi.fn(async () => current),
      submitAttempt: vi.fn(async () => correct),
      revealHint: vi.fn(async () => ({ stage: 1, parts: [] }) as HintResponse),
      giveUp: vi.fn(
        async () => ({ status: "gave_up", solution: {} }) as GiveUpResponse,
      ),
    };

    render(
      <PracticePlayer
        api={api}
        sessionId="69284c2d-018f-4ddb-8935-51918af14954"
      />,
    );

    expect(
      await screen.findByRole("heading", {
        name: "Prime factorisation of 360",
      }),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Final answer"), {
      target: { value: "2^3 * 3^2 * 5" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Check final answer" }));

    await waitFor(() =>
      expect(api.submitAttempt).toHaveBeenCalledWith(
        "69284c2d-018f-4ddb-8935-51918af14954",
        "n1-l1-01",
        1,
        { "1": "2^3 * 3^2 * 5" },
      ),
    );
    expect(
      await screen.findByRole("heading", { name: "Correct" }),
    ).toBeInTheDocument();
    expect(screen.getByText("You earned 2 of 2 marks.")).toBeInTheDocument();
  });

  it("uses the live B4.2 view without inventing rewards", async () => {
    const api = {
      getNextQuestion: vi.fn(async () => current),
      submitAttempt: vi.fn(async () => correct),
      revealHint: vi.fn(async () => ({ stage: 1, parts: [] }) as HintResponse),
      giveUp: vi.fn(
        async () => ({ status: "gave_up", solution: {} }) as GiveUpResponse,
      ),
    };

    render(
      <PracticePlayer
        appearance="nextscholar"
        api={api}
        sessionId="69284c2d-018f-4ddb-8935-51918af14954"
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Question 1 of 3" }),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Your answer/), {
      target: { value: "2^3 * 3^2 * 5" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Check final answer" }));

    expect(
      await screen.findByText("You earned 2 of 2 marks."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/\bXP\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/league/i)).not.toBeInTheDocument();
  });

  it("preserves authored hint sequencing and the give-up solution flow", async () => {
    const incorrect: AttemptResponse = {
      attempt_number: 1,
      correct: false,
      parts: [
        {
          position: 1,
          correct: false,
          error: null,
          marks_awarded: 0,
          marks_available: 2,
        },
      ],
      marks_awarded: 0,
      marks_available: 2,
      question_finished: false,
      solution_available: true,
    };
    const api = {
      getNextQuestion: vi.fn(async () => current),
      submitAttempt: vi.fn(async () => incorrect),
      revealHint: vi.fn(
        async (_sessionId: string, _questionKey: string, stage: 1 | 2) =>
          ({
            stage,
            parts: [
              {
                position: 1,
                content: [
                  {
                    type: "text",
                    text:
                      stage === 1
                        ? "Start with the smallest prime."
                        : "Divide repeatedly by 2.",
                  },
                ],
              },
            ],
          }) as HintResponse,
      ),
      giveUp: vi.fn(
        async () =>
          ({
            status: "gave_up",
            solution: {
              stable_key: "n1-l1-01",
              revision: 1,
              parts: [
                {
                  position: 1,
                  label: null,
                  canonical_answer: "2^3 * 3^2 * 5",
                  canonical_latex: "2^3 \\times 3^2 \\times 5",
                  steps: [
                    {
                      position: 1,
                      content: [
                        {
                          type: "text",
                          text: "Divide 360 by successive prime numbers.",
                        },
                      ],
                    },
                  ],
                },
              ],
            },
          }) as GiveUpResponse,
      ),
    };

    render(
      <PracticePlayer
        appearance="nextscholar"
        api={api}
        sessionId="69284c2d-018f-4ddb-8935-51918af14954"
      />,
    );

    await screen.findByRole("heading", { name: "Question 1 of 3" });
    fireEvent.click(screen.getByRole("button", { name: "Hint 1" }));
    expect(
      await screen.findByText("Start with the smallest prime."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hint 2" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Hint 2" }));
    expect(
      await screen.findByText("Divide repeatedly by 2."),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Your answer/), {
      target: { value: "12" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Check final answer" }));
    expect(
      await screen.findByText(
        "That final answer is not correct yet. Retry it or open an authored hint.",
      ),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Give up and show solution" }),
    );
    expect(
      await screen.findByRole("heading", { name: "Worked solution" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Divide 360 by successive prime numbers."),
    ).toBeInTheDocument();
    expect(api.giveUp).toHaveBeenCalledWith(
      "69284c2d-018f-4ddb-8935-51918af14954",
      "n1-l1-01",
    );
  });
});
