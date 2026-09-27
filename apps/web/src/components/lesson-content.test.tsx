import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { lessonFixture } from "@/lib/api/course";
import type {
  ActiveRecallAttemptResponse,
  LessonSectionProgressResponse,
} from "@/lib/api/progress";

import {
  LessonContent,
  type LessonContentApi,
} from "./lesson-content";

const initialProgress: LessonSectionProgressResponse = {
  lesson_key: "n1-lesson-01",
  lesson_revision: 2,
  total_sections: 7,
  completed_count: 0,
  completed_section_keys: [],
};

describe("LessonContent", () => {
  it("records explicit reading completion and checks active recall through the API", async () => {
    const firstCompleted: LessonSectionProgressResponse = {
      ...initialProgress,
      completed_count: 1,
      completed_section_keys: ["prime-numbers"],
    };
    const recallCompleted: LessonSectionProgressResponse = {
      ...initialProgress,
      completed_count: 2,
      completed_section_keys: ["prime-numbers", "factorise-84-check"],
    };
    const recallResult: ActiveRecallAttemptResponse = {
      correct: true,
      error: null,
      feedback: [
        { type: "text", text: "Correct. " },
        { type: "inline_math", latex: "84=2^2\\times3\\times7" },
      ],
      progress: recallCompleted,
    };
    const api = {
      getProgress: vi.fn().mockResolvedValue(initialProgress),
      setCompletion: vi.fn().mockResolvedValue(firstCompleted),
      checkRecall: vi.fn().mockResolvedValue(recallResult),
    } satisfies LessonContentApi;

    render(
      <LessonContent
        api={api}
        lessonKey="n1-lesson-01"
        sections={lessonFixture.sections}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Learn the ideas, then practise them" }),
    ).toBeInTheDocument();
    await waitFor(() => expect(api.getProgress).toHaveBeenCalledWith("n1-lesson-01"));

    const firstCompletionButton = screen
      .getAllByRole("button", { name: "Mark section complete" })
      .at(0);
    expect(firstCompletionButton).toBeDefined();
    fireEvent.click(firstCompletionButton!);
    await waitFor(() =>
      expect(api.setCompletion).toHaveBeenCalledWith(
        "n1-lesson-01",
        "prime-numbers",
        true,
      ),
    );

    fireEvent.change(screen.getByLabelText("Your answer"), {
      target: { value: "2^2 * 3 * 7" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Check answer" }));

    await waitFor(() =>
      expect(api.checkRecall).toHaveBeenCalledWith(
        "n1-lesson-01",
        "factorise-84-check",
        "2^2 * 3 * 7",
      ),
    );
    expect(await screen.findByText("Correct", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByText("2 of 7 sections complete")).toBeInTheDocument();
  });
});
