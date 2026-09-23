import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { lessonFixture } from "@/lib/api/course";

import { LessonPanel } from "./lesson-panel";

describe("LessonPanel", () => {
  it("renders an honest blank-material state and keeps practice locked", async () => {
    const loadLesson = vi.fn().mockResolvedValue(lessonFixture);
    render(<LessonPanel lessonKey="n1-lesson-01" loadLesson={loadLesson} />);

    expect(await screen.findByRole("heading", { name: lessonFixture.title })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Lesson material is being prepared" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Practice unavailable in draft" })).toBeDisabled();
    for (const objective of lessonFixture.objectives) {
      expect(screen.getByText(objective)).toBeInTheDocument();
    }
  });
});
