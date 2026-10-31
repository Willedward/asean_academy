import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  EnglishEssaySelfReviewResponse,
  EnglishEssaySelfReviewWorkspaceResponse,
  EnglishEssaySubmissionResponse,
} from "@/lib/api/english";

import { EnglishEssaySelfReview } from "./english-essay-self-review";

const getWorkspace = vi.fn();
const createReview = vi.fn();
const getMarking = vi.fn();
const createMarking = vi.fn();
const getAllowance = vi.fn();

vi.mock("@/lib/api/english", () => ({
  getEnglishEssaySelfReviewWorkspace: (...args: unknown[]) =>
    getWorkspace(...args),
  createEnglishEssaySelfReview: (...args: unknown[]) => createReview(...args),
  getEnglishEssayMarkingWorkspace: (...args: unknown[]) => getMarking(...args),
  createEnglishEssayMarkingJob: (...args: unknown[]) => createMarking(...args),
  getEnglishEssayFeedbackAllowance: (...args: unknown[]) =>
    getAllowance(...args),
}));

const submission: EnglishEssaySubmissionResponse = {
  submission_id: "dfdb118f-b09d-4baf-a7e0-64f582729351",
  draft_id: "d209255d-a66c-44a3-b6cd-381f8be70441",
  prompt_key: "english-essay-prompt-school-learning-transfer-v1",
  prompt_revision: 1,
  rubric_key: "english-essay-rubric-instructional-v1",
  rubric_revision: 1,
  draft_edit_revision: 2,
  submission_revision: 1,
  body: "Planning helps me beyond school.",
  body_sha256: "a".repeat(64),
  word_count: 5,
  paragraph_count: 1,
  deterministic_checks: [],
  draft_created_at: "2026-10-30T01:00:00Z",
  draft_updated_at: "2026-10-30T01:01:00Z",
  draft_age_seconds: 60,
  submitted_at: "2026-10-30T01:02:00Z",
  immutable: true,
  ai_feedback_available: false,
  official_score_available: false,
};

const criterionDefinitions = [
  ["task_fulfilment", "Task fulfilment and focus"],
  ["organisation_cohesion", "Organisation and cohesion"],
  ["development_evidence", "Development and evidence"],
  ["language_control", "Language control and precision"],
] as const;

const criteria: EnglishEssaySelfReviewWorkspaceResponse["criteria"] =
  criterionDefinitions.map(([criterion_key, title]) => ({
    criterion_key,
    title,
    description: `Reflect on ${title.toLowerCase()}.`,
    weight_percent: 25,
    bands: [
      {
        level: 3,
        label: "Developing",
        descriptor: `A developing descriptor for ${title.toLowerCase()}.`,
      },
    ],
  }));

const workspace: EnglishEssaySelfReviewWorkspaceResponse = {
  submission,
  rubric_title: "NextScholar instructional composition rubric",
  rubric_purpose: "Formative reflection only.",
  rubric_key: submission.rubric_key,
  rubric_revision: 1,
  learner_disclaimer:
    "This is a NextScholar instructional profile, not an official ASEAN Scholarship score or prediction.",
  criteria,
  self_review: null,
};

beforeEach(() => {
  getWorkspace.mockReset();
  createReview.mockReset();
  getMarking.mockReset();
  createMarking.mockReset();
  getAllowance.mockReset();
  getWorkspace.mockResolvedValue(workspace);
  getMarking.mockResolvedValue({
    submission_id: submission.submission_id,
    job: null,
    feedback: null,
    learner_disclaimer: "Development fixture only.",
  });
  getAllowance.mockResolvedValue({
    live_feedback_available: false,
    availability: "provider_not_released",
    monthly_feedback_limit: 4,
    monthly_feedback_remaining: 0,
    resets_at: "2026-12-01T00:00:00Z",
    fixture_feedback_consumes_allowance: false,
    learner_notice:
      "Development fixture feedback is free and does not use the future live-feedback allowance.",
  });
});

afterEach(cleanup);

describe("EnglishEssaySelfReview", () => {
  it("requires every criterion, evidence, action and disclaimer before immutable completion", async () => {
    const completed: EnglishEssaySelfReviewResponse = {
      self_review_id: "259273f4-a946-44b8-a205-7690e20867a9",
      submission_id: submission.submission_id,
      rubric_key: submission.rubric_key,
      rubric_revision: 1,
      criterion_reflections: criteria.map((criterion) => ({
        criterion_key: criterion.criterion_key,
        criterion_title: criterion.title,
        selected_band_level: 3,
        selected_band_label: "Developing",
        selected_band_descriptor: criterion.bands[0]!.descriptor,
        evidence_note: `Evidence for ${criterion.title}.`,
        improvement_action: `Improve ${criterion.title}.`,
      })),
      overall_reflection:
        "Keep the clear focus and add a more specific example.",
      disclaimer_acknowledged: true,
      completed_at: "2026-10-31T01:00:00Z",
      immutable: true,
      learner_authored: true,
      ai_feedback_available: false,
      official_score_available: false,
    };
    createReview.mockResolvedValue(completed);
    render(<EnglishEssaySelfReview submission={submission} />);

    expect(await screen.findByText("Submitted essay")).toBeInTheDocument();
    const completeButton = screen.getByRole("button", {
      name: "Complete self-review",
    });
    expect(completeButton).toBeDisabled();

    for (const radio of screen.getAllByRole("radio")) fireEvent.click(radio);
    for (const [index, field] of screen
      .getAllByLabelText("Evidence from this essay")
      .entries()) {
      fireEvent.change(field, { target: { value: `Evidence ${index + 1}.` } });
    }
    for (const [index, field] of screen
      .getAllByLabelText("One specific improvement action")
      .entries()) {
      fireEvent.change(field, { target: { value: `Action ${index + 1}.` } });
    }
    fireEvent.change(screen.getByLabelText("Overall reflection"), {
      target: {
        value: "Keep the clear focus and add a more specific example.",
      },
    });
    fireEvent.click(
      screen.getByRole("checkbox", {
        name: /not an official ASEAN Scholarship score or prediction/,
      }),
    );
    expect(completeButton).toBeEnabled();
    fireEvent.click(completeButton);

    expect(
      await screen.findByText("Your self-review is saved permanently."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /learner-authored and contains no AI feedback or official score/,
      ),
    ).toBeInTheDocument();
    expect(createReview).toHaveBeenCalledWith(
      submission.submission_id,
      expect.arrayContaining([
        expect.objectContaining({
          criterion_key: "task_fulfilment",
          selected_band_level: 3,
        }),
      ]),
      "Keep the clear focus and add a more specific example.",
    );
  });

  it("restores a completed immutable self-review from the server", async () => {
    const restored: EnglishEssaySelfReviewResponse = {
      self_review_id: "259273f4-a946-44b8-a205-7690e20867a9",
      submission_id: submission.submission_id,
      rubric_key: submission.rubric_key,
      rubric_revision: 1,
      criterion_reflections: [],
      overall_reflection: "My permanent reflection.",
      disclaimer_acknowledged: true,
      completed_at: "2026-10-31T01:00:00Z",
      immutable: true,
      learner_authored: true,
      ai_feedback_available: false,
      official_score_available: false,
    };
    getWorkspace.mockResolvedValue({ ...workspace, self_review: restored });

    render(<EnglishEssaySelfReview submission={submission} />);

    expect(
      await screen.findByText("Your self-review is saved permanently."),
    ).toBeInTheDocument();
    expect(screen.getByText("Submitted essay")).toBeInTheDocument();
    expect(screen.getByText(submission.body)).toBeInTheDocument();
    expect(screen.getByText("My permanent reflection.")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Complete self-review" }),
    ).not.toBeInTheDocument();
  });
});
