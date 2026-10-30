import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  EnglishEssayDraftResponse,
  EnglishEssayPreSubmitResponse,
  EnglishEssaySubmissionResponse,
} from "@/lib/api/english";

import { countEssayWords, EnglishEssayDraftEditor } from "./english-essay-draft-editor";

const updateDraft = vi.fn();
const getDraft = vi.fn();
const preSubmitDraft = vi.fn();
const createSubmission = vi.fn();

vi.mock("@/lib/api/english", () => ({
  EnglishEssayDraftApiError: class EnglishEssayDraftApiError extends Error {
    constructor(
      message: string,
      readonly status: number,
    ) {
      super(message);
    }
  },
  updateEnglishEssayDraft: (...args: unknown[]) => updateDraft(...args),
  getEnglishEssayDraft: (...args: unknown[]) => getDraft(...args),
  preSubmitEnglishEssayDraft: (...args: unknown[]) => preSubmitDraft(...args),
  createEnglishEssaySubmission: (...args: unknown[]) =>
    createSubmission(...args),
}));

const initialDraft: EnglishEssayDraftResponse = {
  draft_id: "d209255d-a66c-44a3-b6cd-381f8be70441",
  body: "",
  word_count: 0,
  edit_revision: 1,
  created_at: "2026-10-30T01:00:00Z",
  updated_at: "2026-10-30T01:00:00Z",
  submission_available: true,
  ai_feedback_available: false,
  prompt: {
    stable_key: "english-essay-prompt-school-learning-transfer-v1",
    revision: 1,
    title: "Using school learning beyond the classroom",
    prompt_family: "reflective_personal_expository",
    prompt_text:
      "Describe something useful you learned at school and explain how you could use it elsewhere.",
    instructions: ["Develop one clear central response."],
    time_limit_minutes: 30,
    time_limit_evidence: "candidate_reported",
    word_count_guidance: 300,
    word_count_status: "guidance",
    content_status: "draft",
    development_preview: true,
  },
};

beforeEach(() => {
  window.localStorage.clear();
  updateDraft.mockReset();
  getDraft.mockReset();
  preSubmitDraft.mockReset();
  createSubmission.mockReset();
});

afterEach(cleanup);

describe("EnglishEssayDraftEditor", () => {
  it("backs up every change locally and autosaves it using the current edit revision", async () => {
    updateDraft.mockResolvedValue({
      ...initialDraft,
      body: "Planning helps me outside school.",
      word_count: 5,
      edit_revision: 2,
      updated_at: "2026-10-30T01:01:00Z",
    });
    render(<EnglishEssayDraftEditor initialDraft={initialDraft} />);

    fireEvent.change(screen.getByLabelText("Your essay"), {
      target: { value: "Planning helps me outside school." },
    });

    await waitFor(() =>
      expect(window.localStorage.getItem(`nextscholar:english-essay-draft:${initialDraft.draft_id}`)).toContain(
        "Planning helps me outside school.",
      ),
    );
    expect(screen.getByText("5 words")).toBeInTheDocument();
    await waitFor(
      () =>
        expect(updateDraft).toHaveBeenCalledWith(
          initialDraft.draft_id,
          "Planning helps me outside school.",
          1,
        ),
      { timeout: 2000 },
    );
    expect(await screen.findByText("Saved remotely")).toBeInTheDocument();
    expect(window.localStorage.getItem(`nextscholar:english-essay-draft:${initialDraft.draft_id}`)).toBeNull();
  });

  it("restores an unsent device backup after refresh without claiming it was remotely saved", async () => {
    window.localStorage.setItem(
      `nextscholar:english-essay-draft:${initialDraft.draft_id}`,
      JSON.stringify({
        text: "My recovered local paragraph.",
        baseEditRevision: 1,
        savedAt: "2026-10-30T01:02:00Z",
      }),
    );
    updateDraft.mockImplementation(() => new Promise(() => undefined));

    render(<EnglishEssayDraftEditor initialDraft={initialDraft} />);

    expect(await screen.findByDisplayValue("My recovered local paragraph.")).toBeInTheDocument();
    expect(screen.getByText(/Backed up on this device|Saving/)).toBeInTheDocument();
  });

  it("requires deterministic review and explicit confirmation before creating a permanent snapshot", async () => {
    const body = "Planning helps me beyond school.\n\nI use it before every team project.";
    const readyDraft = {
      ...initialDraft,
      body,
      word_count: 12,
      edit_revision: 2,
    };
    const preSubmit: EnglishEssayPreSubmitResponse = {
      draft_id: readyDraft.draft_id,
      edit_revision: 2,
      prompt_key: readyDraft.prompt.stable_key,
      prompt_revision: 1,
      rubric_key: "english-essay-rubric-instructional-v1",
      rubric_revision: 1,
      word_count: 12,
      paragraph_count: 2,
      body_sha256: "a".repeat(64),
      prompt_time_limit_minutes: 30,
      time_limit_evidence: "candidate_reported",
      continuous_timing_observed: false,
      can_submit: true,
      checks: [
        {
          check_key: "revision_snapshot",
          status: "pass",
          message: "The saved draft revision is ready to snapshot.",
        },
      ],
    };
    const submitted: EnglishEssaySubmissionResponse = {
      submission_id: "dfdb118f-b09d-4baf-a7e0-64f582729351",
      draft_id: readyDraft.draft_id,
      prompt_key: readyDraft.prompt.stable_key,
      prompt_revision: 1,
      rubric_key: preSubmit.rubric_key,
      rubric_revision: 1,
      draft_edit_revision: 2,
      submission_revision: 1,
      body,
      body_sha256: preSubmit.body_sha256,
      word_count: 12,
      paragraph_count: 2,
      deterministic_checks: preSubmit.checks,
      draft_created_at: readyDraft.created_at,
      draft_updated_at: readyDraft.updated_at,
      draft_age_seconds: 120,
      submitted_at: "2026-10-30T01:02:00Z",
      immutable: true,
      ai_feedback_available: false,
      official_score_available: false,
    };
    preSubmitDraft.mockResolvedValue(preSubmit);
    createSubmission.mockResolvedValue(submitted);

    render(<EnglishEssayDraftEditor initialDraft={readyDraft} />);
    fireEvent.click(screen.getByRole("button", { name: "Review before submitting" }));

    expect(
      await screen.findByText("The saved draft revision is ready to snapshot."),
    ).toBeInTheDocument();
    const submitButton = screen.getByRole("button", {
      name: "Submit saved revision",
    });
    expect(submitButton).toBeDisabled();
    fireEvent.click(
      screen.getByRole("checkbox", {
        name: /I understand that this creates a permanent snapshot/,
      }),
    );
    expect(submitButton).toBeEnabled();
    fireEvent.click(submitButton);

    expect(
      await screen.findByText("Submission revision 1 is saved permanently."),
    ).toBeInTheDocument();
    expect(screen.getByText(/No AI feedback or official score was generated/)).toBeInTheDocument();
    expect(preSubmitDraft).toHaveBeenCalledWith(readyDraft.draft_id, 2);
    expect(createSubmission).toHaveBeenCalledWith(readyDraft.draft_id, 2);
  });
});

it("uses the same bounded English word-token rule as the API", () => {
  expect(countEssayWords("I can't ignore evidence-based planning—it works."))
    .toBe(7);
});
