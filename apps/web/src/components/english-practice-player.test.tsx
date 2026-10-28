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
    exam_profile_key: "asean-english-sec1-id-reported-v1",
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
  correct_parts: 0,
  total_parts: 1,
  score: 0,
  threshold_met: false,
  hint_used: false,
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
            hint_used: true,
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

  it("offers grammar-specific reflection categories for editing questions", async () => {
    const grammar: EnglishNextQuestionResponse = {
      ...current,
      session: {
        ...current.session,
        lesson_key: "e2-lesson-01",
      },
      question: {
        ...current.question!,
        stable_key: "eg-l1-001",
        outcome_code: "EG2.1",
        question_type: "editing",
        title: "Repair a sentence boundary",
      },
    };
    const api = {
      getNextQuestion: vi.fn(async () => grammar),
      submitAttempt: vi.fn(async () => incorrect),
      revealHint: vi.fn(async () => ({
        question_key: "eg-l1-001",
        parts: ["Identify each independent clause first."],
        hint_used: true as const,
      })),
      classifyError: vi.fn(async () => undefined),
    };

    render(
      <EnglishPracticePlayer
        sessionId={grammar.session.session_id}
        api={api}
      />,
    );

    fireEvent.click(await screen.findByRole("radio", { name: /A\. narrow/i }));
    fireEvent.click(screen.getByRole("button", { name: "Check answer" }));

    expect(
      await screen.findByRole("radio", {
        name: /I misidentified the clauses/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /I chose the wrong boundary/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /I missed the agreement/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("radio", { name: /I did not know the word/i }),
    ).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("radio", { name: /I chose the wrong boundary/i }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Save reflection" }));

    await waitFor(() =>
      expect(api.classifyError).toHaveBeenCalledWith(
        incorrect.attempt_id,
        "boundary_choice",
      ),
    );
  });

  it("offers task-analysis reflection categories for composition planning", async () => {
    const composition: EnglishNextQuestionResponse = {
      ...current,
      session: {
        ...current.session,
        lesson_key: "e6-lesson-01",
      },
      question: {
        ...current.question!,
        stable_key: "ex-l1-001",
        outcome_code: "EW6.1",
        question_type: "composition_planning",
        title: "Decode a composition task",
      },
    };
    const api = {
      getNextQuestion: vi.fn(async () => composition),
      submitAttempt: vi.fn(async () => incorrect),
      revealHint: vi.fn(async () => ({
        question_key: "ex-l1-001",
        parts: ["Separate the topic from the command."],
        hint_used: true as const,
      })),
      classifyError: vi.fn(async () => undefined),
    };

    render(
      <EnglishPracticePlayer
        sessionId={composition.session.session_id}
        api={api}
      />,
    );

    fireEvent.click(await screen.findByRole("radio", { name: /A\. narrow/i }));
    fireEvent.click(screen.getByRole("button", { name: "Check answer" }));

    expect(
      await screen.findByRole("radio", { name: /I widened or changed the topic/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /I missed the command/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /I missed the audience or scope/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /I missed the required example/i }),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("radio", { name: /I missed the command/i }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Save reflection" }));

    await waitFor(() =>
      expect(api.classifyError).toHaveBeenCalledWith(
        incorrect.attempt_id,
        "command_word",
      ),
    );
  });

  it("offers exam-strategy reflection categories for readiness questions", async () => {
    const strategy: EnglishNextQuestionResponse = {
      ...current,
      session: { ...current.session, lesson_key: "e0-lesson-01" },
      question: {
        ...current.question!,
        stable_key: "ex-l1-005",
        outcome_code: "EX0.1",
        question_type: "exam_strategy",
        title: "Use the reported English paper profile",
      },
    };
    const api = {
      getNextQuestion: vi.fn(async () => strategy),
      submitAttempt: vi.fn(async () => incorrect),
      revealHint: vi.fn(async () => ({
        question_key: "ex-l1-005",
        parts: ["Keep the two section clocks separate."],
        hint_used: true as const,
      })),
      classifyError: vi.fn(async () => undefined),
    };

    render(
      <EnglishPracticePlayer
        sessionId={strategy.session.session_id}
        api={api}
      />,
    );
    fireEvent.click(await screen.findByRole("radio", { name: /A\. narrow/i }));
    fireEvent.click(screen.getByRole("button", { name: "Check answer" }));

    expect(
      await screen.findByRole("radio", { name: /I mixed up the paper format/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /I missed an instruction/i })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /My timing plan was unsafe/i })).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /I broke the independent conditions/i }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: /My timing plan was unsafe/i }));
    fireEvent.click(screen.getByRole("button", { name: "Save reflection" }));
    await waitFor(() =>
      expect(api.classifyError).toHaveBeenCalledWith(
        incorrect.attempt_id,
        "timing_control",
      ),
    );
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
      correct_parts: 2,
      total_parts: 2,
      score: 1,
      threshold_met: true,
      hint_used: false,
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
        hint_used: true as const,
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

  it("fills open-cloze gaps inside the passage and offers gap-specific reflection", async () => {
    const openCloze: EnglishNextQuestionResponse = {
      status: "active",
      session: {
        ...current.session,
        lesson_key: "e4-lesson-01",
        question_count: 1,
        assigned_count: 1,
      },
      position: 1,
      question: {
        stable_key: "eo-l1-001",
        revision: 1,
        title: "Restore the workshop discovery",
        difficulty: 3,
        outcome_code: "EO4.1",
        question_type: "open_cloze",
        exposure_pool: "exit_ticket",
        instructions: "Enter exactly one word in each gap.",
        passage: {
          stable_key: "english-passage-workshop-box",
          revision: 1,
          title: "The workshop box",
          text_type: "narrative",
          paragraphs: [
            "The guide placed {{1}} unopened box on the table and asked us not to touch {{2}}.",
          ],
          attribution: "Original NextScholar passage.",
        },
        word_bank: null,
        parts: [
          {
            position: 1,
            prompt: "Gap 1",
            response_type: "short_text",
            options: [],
          },
          {
            position: 2,
            prompt: "Gap 2",
            response_type: "short_text",
            options: [],
          },
        ],
      },
    };
    const groupedResult: EnglishAttemptResponse = {
      attempt_id: "a99591e5-1f20-4a45-a453-31995fc99b62",
      attempt_number: 1,
      correct: false,
      correct_parts: 1,
      total_parts: 2,
      score: 0.5,
      threshold_met: false,
      hint_used: false,
      parts: [
        {
          position: 1,
          correct: true,
          error: null,
          feedback: "Use an before the vowel sound.",
        },
        {
          position: 2,
          correct: false,
          error: null,
          feedback: "Use the singular object pronoun it.",
        },
      ],
      question_finished: true,
      retry_queued: true,
      needs_error_classification: true,
      lesson_state: "in_progress",
    };
    const api = {
      getNextQuestion: vi.fn(async () => openCloze),
      submitAttempt: vi.fn(async () => groupedResult),
      revealHint: vi.fn(async () => ({
        question_key: "eo-l1-001",
        parts: ["Article hint", "Pronoun hint"],
        hint_used: true as const,
      })),
      classifyError: vi.fn(async () => undefined),
    };

    render(
      <EnglishPracticePlayer
        sessionId={openCloze.session.session_id}
        api={api}
      />,
    );

    const gap1 = await screen.findByRole("textbox", { name: "Gap 1" });
    const gap2 = screen.getByRole("textbox", { name: "Gap 2" });
    expect(screen.getByText("OPEN CLOZE")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Check answer" })).toBeDisabled();

    fireEvent.change(gap1, { target: { value: "an" } });
    fireEvent.change(gap2, { target: { value: "them" } });
    expect(
      screen.queryByText("Use the singular object pronoun it."),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Check answer" }));

    await waitFor(() =>
      expect(api.submitAttempt).toHaveBeenCalledWith(
        openCloze.session.session_id,
        "eo-l1-001",
        1,
        { "1": "an", "2": "them" },
      ),
    );
    expect(await screen.findByText("Passage feedback")).toBeInTheDocument();
    expect(
      screen.getByText("Use the singular object pronoun it."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /I misidentified the gap role/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /I missed the local grammar/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /I missed a cohesion clue/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("radio", { name: /I chose a tempting option/i }),
    ).not.toBeInTheDocument();
  });

  it("keeps every reading paragraph visible while keyboard navigation highlights one paragraph", async () => {
    const reading: EnglishNextQuestionResponse = {
      status: "active",
      session: {
        ...current.session,
        lesson_key: "e5-lesson-01",
        question_count: 1,
        assigned_count: 1,
      },
      position: 1,
      question: {
        stable_key: "er-l1-001",
        revision: 1,
        title: "Map the courtyard project",
        difficulty: 2,
        outcome_code: "ER5.1",
        question_type: "reading_comprehension",
        exposure_pool: "exit_ticket",
        instructions: "Read the complete passage and answer every question.",
        passage: {
          stable_key: "english-passage-courtyard-rain-garden",
          revision: 1,
          title: "A second life for the school courtyard",
          text_type: "informational",
          paragraphs: [
            "The courtyard was hot after lunch.",
            "Students planned a rain garden.",
            "The garden absorbed pooled water.",
          ],
          attribution: "Original NextScholar passage.",
        },
        word_bank: null,
        parts: [
          {
            position: 1,
            prompt: "Which statement gives the main idea?",
            response_type: "single_choice",
            options: [
              { key: "A", text: "The courtyard stayed empty." },
              { key: "B", text: "Students improved the courtyard." },
            ],
          },
        ],
      },
    };
    const api = {
      getNextQuestion: vi.fn(async () => reading),
      submitAttempt: vi.fn(async () => incorrect),
      revealHint: vi.fn(async () => ({
        question_key: "er-l1-001",
        parts: ["Map each paragraph first."],
        hint_used: true as const,
      })),
      classifyError: vi.fn(async () => undefined),
    };

    render(
      <EnglishPracticePlayer
        sessionId={reading.session.session_id}
        api={api}
      />,
    );

    expect(
      await screen.findByRole("navigation", {
        name: "Passage paragraph navigation",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to paragraph 1" }),
    ).toHaveAttribute("aria-current", "true");
    expect(
      screen.getByRole("button", { name: "Previous paragraph" }),
    ).toBeDisabled();
    expect(screen.getByRole("region", { name: "Paragraph 1" })).toBeVisible();
    expect(screen.getByRole("region", { name: "Paragraph 2" })).toBeVisible();
    expect(screen.getByRole("region", { name: "Paragraph 3" })).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: "Go to paragraph 2" }));

    expect(
      screen.getByRole("button", { name: "Go to paragraph 2" }),
    ).toHaveAttribute("aria-current", "true");
    expect(
      screen.getByText(
        "Paragraph 2 of 3 is highlighted. All paragraphs remain visible.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Previous paragraph" }),
    ).toBeEnabled();
    expect(
      screen.getByRole("button", { name: "Next paragraph" }),
    ).toBeEnabled();
  });
});
