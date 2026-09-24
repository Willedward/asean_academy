import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { lessonFixture } from "@/lib/api/course";
import type { PracticeSessionResponse } from "@/lib/api/practice";

import { LessonPanel } from "./lesson-panel";

const navigation = vi.hoisted(() => ({ push: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => navigation,
}));

describe("LessonPanel", () => {
  it("keeps lesson material blank but opens development practice", async () => {
    const loadLesson = vi.fn().mockResolvedValue(lessonFixture);
    const session: PracticeSessionResponse = {
      session_id: "69284c2d-018f-4ddb-8935-51918af14954",
      status: "active",
      question_count: 3,
      lesson_key: "n1-lesson-01",
      mode: "guided_practice",
      development_drafts: true,
    };
    const startSession = vi.fn().mockResolvedValue(session);
    render(
      <LessonPanel
        lessonKey="n1-lesson-01"
        loadLesson={loadLesson}
        startSession={startSession}
      />,
    );

    expect(await screen.findByRole("heading", { name: lessonFixture.title })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Lesson material is being prepared" }),
    ).toBeInTheDocument();
    const button = screen.getByRole("button", { name: "Start draft practice" });
    expect(button).toBeEnabled();

    fireEvent.click(button);

    await waitFor(() =>
      expect(startSession).toHaveBeenCalledWith("n1-lesson-01", 3),
    );
    expect(navigation.push).toHaveBeenCalledWith(
      "/practice/69284c2d-018f-4ddb-8935-51918af14954",
    );
    for (const objective of lessonFixture.objectives) {
      expect(screen.getByText(objective)).toBeInTheDocument();
    }
  });
});
