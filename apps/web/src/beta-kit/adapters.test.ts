import { describe, expect, it } from "vitest";

import { courseMapFixture } from "@/lib/api/course";

import { continueFromNextAction, starsFor, toLessonUiState, unitFromCourseMap } from "./adapters";

describe("beta kit adapters", () => {
  it("maps API lesson states to what the lesson row shows", () => {
    expect(toLessonUiState("not_started")).toBe("ready");
    expect(toLessonUiState("in_progress")).toBe("practising");
    expect(toLessonUiState("practice_completed")).toBe("practising");
    expect(toLessonUiState("proficient")).toBe("proficient");
    expect(toLessonUiState("mastered")).toBe("mastered");
    expect(toLessonUiState("proficient", "content_pending")).toBe("in_review");
  });

  it("gives stars for progress, never for nothing", () => {
    expect(starsFor("not_started")).toBe(0);
    expect(starsFor("in_progress", 0)).toBe(0);
    expect(starsFor("in_progress", 1)).toBe(1);
    expect(starsFor("proficient")).toBe(2);
    expect(starsFor("mastered")).toBe(3);
  });

  it("builds the unit view model from the course map fixture", () => {
    const unit = unitFromCourseMap(courseMapFixture);
    expect(unit).not.toBeNull();
    expect(unit?.lessons).toHaveLength(7);
    expect(unit?.lessons[0]).toMatchObject({ key: "n1-lesson-01", position: 1, state: "in_review", href: "/lessons/n1-lesson-01" });
    expect(unit?.starsTotal).toBe(21);
    expect(unit?.checkpoint.questionCount).toBe(8);
  });

  it("builds the up next card from a next action", () => {
    const card = continueFromNextAction(
      { type: "resume_practice", title: "HCF and LCM", description: "Pick up where you left off.", href: "/practice/abc" },
      {
        lesson_key: "n1-lesson-02",
        lesson_title: "HCF and LCM",
        position: 2,
        state: "in_progress",
        question_count: 4,
        resolved_count: 2,
        correct_count: 1,
        gave_up_count: 0,
        eventual_correct_percentage: 50,
        checkpoint_passed: false,
      },
    );
    expect(card).toMatchObject({ progressPct: 50, progressLabel: "2 of 4 questions", stars: 1, primary: { href: "/practice/abc" } });
  });
});
