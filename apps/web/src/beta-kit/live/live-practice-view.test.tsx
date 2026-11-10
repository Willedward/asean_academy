import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  GiveUpResponse,
  HintResponse,
  NextQuestionResponse,
} from "@/lib/api/practice";

import { LivePracticeView } from "./live-practice-view";

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
    lesson_key: "n7-lesson-05",
    mode: "guided_practice",
    development_drafts: false,
  },
  position: 1,
  selection_reason: "configured_lesson_pool",
  stage: "guided",
  attempt_count: 1,
  highest_hint_stage: 1,
  solution_available: false,
  question: {
    stable_key: "n7-l1-502",
    revision: 1,
    title: "Left side of an equation",
    difficulty: 1,
    primary_outcome: "7.5",
    calculator_allowed: false,
    total_marks: 1,
    source_status: "draft",
    stem: [],
    parts: [
      {
        position: 1,
        label: null,
        prompt: [{ type: "text", text: "Find the value." }],
        marks: 1,
        response_type: "numeric",
        input_placeholder: "Enter a number",
      },
    ],
    assets: [],
  },
};

const hint: HintResponse = {
  stage: 1,
  parts: [
    {
      position: 1,
      content: [
        { type: "text", text: "Substitute " },
        { type: "inline_math", latex: "x=3" },
        { type: "text", text: " into the equation." },
      ],
    },
  ],
} as HintResponse;

describe("LivePracticeView hints", () => {
  afterEach(cleanup);

  it("keeps a hint's text and inline maths in one line of flow", () => {
    render(
      <LivePracticeView
        sessionId={current.session.session_id}
        current={current}
        answers={{}}
        attempt={null}
        hints={[hint]}
        solution={null}
        error={null}
        busy={false}
        allAnswersPresent={false}
        onAnswerChange={vi.fn()}
        onCheckAnswers={vi.fn()}
        onOpenHint={vi.fn()}
        onRevealSolution={vi.fn()}
        onContinue={vi.fn()}
      />,
    );

    const region = screen.getByRole("region", { name: "Hints" });
    const text = Array.from(region.querySelectorAll("div"))
      .flatMap((element) => Array.from(element.childNodes))
      .find((node) => node.textContent === "Substitute ");
    const flow = text?.parentElement;
    expect(flow).toBeDefined();
    // Children of a flex column are stacked, which split the sentence around its maths.
    expect(flow?.className ?? "").not.toMatch(/\bflex\b/);
    expect(flow?.querySelector(".katex")).not.toBeNull();
    expect(flow?.textContent).toContain("into the equation.");
  });
});

const solution = {
  parts: [
    {
      position: 1,
      label: null,
      canonical_latex: "270",
      steps: [
        { content: [{ type: "display_math", latex: "1.8\\times150=270" }] },
      ],
    },
  ],
} as unknown as GiveUpResponse["solution"];

function renderView(overrides: {
  solution?: GiveUpResponse["solution"] | null;
}) {
  return render(
    <LivePracticeView
      sessionId={current.session.session_id}
      current={current}
      answers={{}}
      attempt={null}
      hints={[]}
      solution={overrides.solution ?? null}
      error={null}
      busy={false}
      allAnswersPresent={false}
      onAnswerChange={vi.fn()}
      onCheckAnswers={vi.fn()}
      onOpenHint={vi.fn()}
      onRevealSolution={vi.fn()}
      onContinue={vi.fn()}
    />,
  );
}

describe("LivePracticeView readability", () => {
  afterEach(cleanup);

  it("shows the question prompt at body size, not as muted helper text", () => {
    renderView({});
    const prompt = screen.getByText("Find the value.");
    expect(prompt.className).not.toMatch(/text-ns-muted|text-sm/);
    expect(prompt.className).toMatch(/text-ns-ink/);
  });

  it("starts a display-maths step level with its step number", () => {
    const { container } = renderView({ solution });
    const step = container
      .querySelector("ol li .katex-display")
      ?.closest("li > div");
    expect(step).not.toBeNull();
    expect(step?.className).toContain("[&_.katex-display]:my-0!");
    expect(step?.className).toContain("[&_.katex-display>.katex]:text-left!");
  });
});
