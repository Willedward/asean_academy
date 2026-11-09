import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TutorEvaluationPanel } from "./tutor-evaluation-panel";

const { adminRequestMock } = vi.hoisted(() => ({
  adminRequestMock: vi.fn(),
}));

vi.mock("@/lib/api/admin-dashboard", () => ({
  adminRequest: adminRequestMock,
}));

vi.mock("@/components/tutor-conversation-lab", () => ({
  TutorConversationLab: () => null,
}));

const lab = {
  suite_id: "n2-calibration",
  suite_version: "1",
  description: "Calibration cases",
  case_count: 1,
  gemini_configured: false,
  gemini_model: "gemini-3.5-flash-lite",
  prompt_version: "tutor-v1",
  grounding_gate: { review_state: "approved", blockers: [] },
  cases: [
    {
      case_id: "case-1",
      title: "Prime factors",
      mode: "hint",
      learner_message: "Can you help?",
      question_title: "Prime factors",
      question_blocks: [],
      answer_locked: true,
      solution_locked: true,
      latest_run: {
        id: "run-1",
        provider: "synthetic",
        model_name: "synthetic",
        automated_pass: true,
        latency_ms: 10,
        input_tokens: 1,
        output_tokens: 1,
        cost_micros_sgd: 0,
        response_blocks: [],
        suggested_replies: [],
        automated_checks: [],
        reviews: [],
        created_at: "2026-10-09T01:02:03Z",
      },
    },
  ],
};

afterEach(() => {
  cleanup();
  adminRequestMock.mockReset();
});

describe("TutorEvaluationPanel", () => {
  it("labels the response review controls", async () => {
    adminRequestMock.mockResolvedValue(lab);

    render(<TutorEvaluationPanel academic={false} />);

    expect(await screen.findByLabelText("Review dimension")).toHaveValue(
      "editorial",
    );
    expect(screen.getByLabelText("Decision")).toHaveValue("approved");
    expect(screen.getByLabelText("Review notes")).toHaveAttribute(
      "placeholder",
      "Record what you checked (minimum 10 characters)",
    );
  });
});
