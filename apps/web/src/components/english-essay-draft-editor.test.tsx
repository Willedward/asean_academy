import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { EnglishEssayDraftResponse } from "@/lib/api/english";

import { countEssayWords, EnglishEssayDraftEditor } from "./english-essay-draft-editor";

const updateDraft = vi.fn();
const getDraft = vi.fn();

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
}));

const initialDraft: EnglishEssayDraftResponse = {
  draft_id: "d209255d-a66c-44a3-b6cd-381f8be70441",
  body: "",
  word_count: 0,
  edit_revision: 1,
  created_at: "2026-10-30T01:00:00Z",
  updated_at: "2026-10-30T01:00:00Z",
  submission_available: false,
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
});

it("uses the same bounded English word-token rule as the API", () => {
  expect(countEssayWords("I can't ignore evidence-based planning—it works."))
    .toBe(7);
});
