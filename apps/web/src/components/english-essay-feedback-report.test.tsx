import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  EnglishEssayFeedbackReportResponse,
  EnglishEssayHistoryResponse,
  EnglishEssaySubmissionResponse,
} from "@/lib/api/english";

import { EnglishEssayFeedbackReport } from "./english-essay-feedback-report";

const getHistory = vi.fn();
const getReport = vi.fn();
const createUsefulness = vi.fn();

vi.mock("@/lib/api/english", () => ({
  getEnglishEssayHistory: (...args: unknown[]) => getHistory(...args),
  getEnglishEssayFeedbackReport: (...args: unknown[]) => getReport(...args),
  createEnglishEssayFeedbackUsefulness: (...args: unknown[]) =>
    createUsefulness(...args),
}));

const submission: EnglishEssaySubmissionResponse = {
  submission_id: "dfdb118f-b09d-4baf-a7e0-64f582729351",
  draft_id: "d209255d-a66c-44a3-b6cd-381f8be70441",
  prompt_key: "english-essay-prompt-school-learning-transfer-v1",
  prompt_revision: 1,
  rubric_key: "english-essay-rubric-instructional-v1",
  rubric_revision: 1,
  draft_edit_revision: 4,
  submission_revision: 2,
  body: "Planning helps me turn a difficult project into smaller, manageable steps.",
  body_sha256: "a".repeat(64),
  word_count: 11,
  paragraph_count: 1,
  deterministic_checks: [],
  draft_created_at: "2026-10-30T01:00:00Z",
  draft_updated_at: "2026-10-30T01:05:00Z",
  draft_age_seconds: 300,
  submitted_at: "2026-10-30T01:06:00Z",
  immutable: true,
  ai_feedback_available: false,
  official_score_available: false,
};

const history: EnglishEssayHistoryResponse = {
  draft_id: submission.draft_id,
  prompt_key: submission.prompt_key,
  prompt_revision: 1,
  prompt_title: "Using school learning beyond the classroom",
  current_draft_edit_revision: 5,
  submissions: [
    {
      submission_id: submission.submission_id,
      submission_revision: 2,
      draft_edit_revision: 4,
      word_count: 11,
      paragraph_count: 1,
      submitted_at: submission.submitted_at,
      feedback_id: "a9577764-b0f0-4ec2-b271-68e7484a26be",
      feedback_source: "validated_ai",
      feedback_created_at: "2026-10-30T01:07:00Z",
      usefulness_rating: null,
    },
  ],
};

const report: EnglishEssayFeedbackReportResponse = {
  submission,
  exact_submission_notice:
    "Feedback is pinned to this immutable essay submission and does not change later drafts.",
  usefulness_response: null,
  feedback: {
    feedback_id: "a9577764-b0f0-4ec2-b271-68e7484a26be",
    submission_id: submission.submission_id,
    rubric_key: submission.rubric_key,
    rubric_revision: 1,
    feedback_source: "validated_ai",
    preparation_estimate: "developing",
    criterion_feedback: [
      {
        criterion_key: "ideas",
        criterion_title: "Ideas and development",
        preparation_level: 3,
        evidence_spans: [
          {
            quote: "turn a difficult project into smaller, manageable steps",
            start: 18,
            end: 73,
          },
        ],
        observed_evidence: null,
        what_works: "The example supports the central idea.",
        next_step: "Explain one concrete result of using the plan.",
      },
    ],
    overall_summary:
      "The response has a clear direction and needs fuller development.",
    strengths: ["A relevant central example"],
    priorities: ["Develop the consequence of the example"],
    revision_task: "Add two sentences showing what changed after planning.",
    transfer_goal: "Use cause-and-effect links in the next timed response.",
    learner_disclaimer:
      "This is formative preparation feedback, not an official ASEAN Scholarship score.",
    created_at: "2026-10-30T01:07:00Z",
    immutable: true,
    official_score_available: false,
  },
};

beforeEach(() => {
  getHistory.mockReset();
  getReport.mockReset();
  createUsefulness.mockReset();
  getHistory.mockResolvedValue(history);
  getReport.mockResolvedValue(report);
});

afterEach(cleanup);

describe("EnglishEssayFeedbackReport", () => {
  it("shows exact revision-pinned evidence without operational metadata", async () => {
    render(
      <EnglishEssayFeedbackReport
        draftId={submission.draft_id}
        currentSubmissionId={submission.submission_id}
      />,
    );

    expect(
      await screen.findByText("Structured revision report"),
    ).toBeInTheDocument();
    expect(screen.getByText(submission.body)).toBeInTheDocument();
    expect(
      screen.getByText(
        "turn a difficult project into smaller, manageable steps",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/pinned to this immutable essay submission/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/not an official ASEAN Scholarship score/),
    ).toBeInTheDocument();
    const rendered = document.body.textContent?.toLowerCase() ?? "";
    expect(rendered).not.toContain("token");
    expect(rendered).not.toContain("provider");
    expect(rendered).not.toContain("model id");
    expect(rendered).not.toContain("cost");
  });

  it("records one immutable usefulness response", async () => {
    createUsefulness.mockResolvedValue({
      usefulness_id: "c9f514f6-89c5-4fdc-b3de-32c8a091fd4d",
      submission_id: submission.submission_id,
      feedback_id: report.feedback!.feedback_id,
      feedback_source: "validated_ai",
      rating: "helpful",
      note: "The evidence quote made the advice clear.",
      created_at: "2026-10-30T01:08:00Z",
      immutable: true,
    });
    render(
      <EnglishEssayFeedbackReport
        draftId={submission.draft_id}
        currentSubmissionId={submission.submission_id}
      />,
    );

    await screen.findByText("Was this report useful?");
    fireEvent.click(screen.getByRole("radio", { name: "Helpful" }));
    fireEvent.change(screen.getByLabelText("Optional note"), {
      target: { value: "The evidence quote made the advice clear." },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Save usefulness response" }),
    );

    await waitFor(() =>
      expect(createUsefulness).toHaveBeenCalledWith(
        submission.submission_id,
        report.feedback!.feedback_id,
        "validated_ai",
        "helpful",
        "The evidence quote made the advice clear.",
      ),
    );
    expect(
      await screen.findByText("Your response is saved permanently."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Save usefulness response" }),
    ).not.toBeInTheDocument();
  });
});
