import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { lessonFixture } from "@/lib/api/course";
import type { PracticeSessionResponse } from "@/lib/api/practice";
import type {
  LessonProgressResponse,
  LessonSectionProgressResponse,
} from "@/lib/api/progress";

import { LessonPanel } from "./lesson-panel";

const navigation = vi.hoisted(() => ({ push: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => navigation,
}));

afterEach(cleanup);

describe("LessonPanel", () => {
  it("renders the draft lesson note and opens development practice", async () => {
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
    const progress: LessonProgressResponse = {
      lesson_key: "n1-lesson-01",
      lesson_title: "Primes and prime factorisation",
      position: 1,
      state: "in_progress",
      unlocked: true,
      question_count: 0,
      resolved_count: 0,
      correct_count: 0,
      gave_up_count: 0,
      retry_question_count: 0,
      eventual_correct_percentage: 0,
      checkpoint_passed: false,
      last_session_id: null,
      updated_at: "2026-09-24T00:00:00Z",
    };
    const recordStart = vi.fn().mockResolvedValue(progress);
    const sectionProgress: LessonSectionProgressResponse = {
      lesson_key: "n1-lesson-01",
      lesson_revision: 2,
      total_sections: 7,
      completed_count: 0,
      completed_section_keys: [],
    };
    const sectionApi = {
      getProgress: vi.fn().mockResolvedValue(sectionProgress),
      setCompletion: vi.fn().mockResolvedValue(sectionProgress),
      checkRecall: vi.fn(),
    };
    render(
      <LessonPanel
        lessonKey="n1-lesson-01"
        loadLesson={loadLesson}
        startSession={startSession}
        recordStart={recordStart}
        sectionApi={sectionApi}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: lessonFixture.title }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Prime and composite numbers" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Video lesson will be added here" }),
    ).toBeInTheDocument();
    const button = screen.getByRole("button", { name: "Start draft practice" });
    expect(button).toBeEnabled();
    await waitFor(() =>
      expect(recordStart).toHaveBeenCalledWith("n1-lesson-01"),
    );
    await waitFor(() =>
      expect(sectionApi.getProgress).toHaveBeenCalledWith("n1-lesson-01"),
    );

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

  it("renders the B4.2 lesson presentation through the existing controller", async () => {
    const loadLesson = vi.fn().mockResolvedValue(lessonFixture);
    const startSession = vi.fn().mockResolvedValue({
      session_id: "69284c2d-018f-4ddb-8935-51918af14954",
      status: "active",
      question_count: 3,
      lesson_key: "n1-lesson-01",
      mode: "guided_practice",
      development_drafts: true,
    } satisfies PracticeSessionResponse);
    const recordStart = vi.fn().mockResolvedValue({
      lesson_key: "n1-lesson-01",
      lesson_title: lessonFixture.title,
      position: 1,
      state: "in_progress",
      unlocked: true,
      question_count: 0,
      resolved_count: 0,
      correct_count: 0,
      gave_up_count: 0,
      retry_question_count: 0,
      eventual_correct_percentage: 0,
      checkpoint_passed: false,
      last_session_id: null,
      updated_at: "2026-09-24T00:00:00Z",
    } satisfies LessonProgressResponse);
    const sectionProgress: LessonSectionProgressResponse = {
      lesson_key: "n1-lesson-01",
      lesson_revision: 2,
      total_sections: lessonFixture.sections.length,
      completed_count: 0,
      completed_section_keys: [],
    };
    const sectionApi = {
      getProgress: vi.fn().mockResolvedValue(sectionProgress),
      setCompletion: vi.fn().mockResolvedValue(sectionProgress),
      checkRecall: vi.fn(),
    };

    render(
      <LessonPanel
        appearance="nextscholar"
        lessonKey="n1-lesson-01"
        loadLesson={loadLesson}
        startSession={startSession}
        recordStart={recordStart}
        sectionApi={sectionApi}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: lessonFixture.title }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "By the end you can" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Start draft practice" }),
    ).toBeEnabled();
    expect(screen.queryByText(/\bXP\b/i)).not.toBeInTheDocument();
  });
});
