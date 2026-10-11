import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { courseMapFixture } from "@/lib/api/course";
import type {
  LearningHomeResponse,
  ProgressResponse,
} from "@/lib/api/progress";

import {
  CoreCourseMapScreen,
  CoreLearningDashboard,
} from "./core-learning-screens";

const learner = {
  displayName: "William",
  email: "william@example.com",
  targetTrack: "G3 Mathematics",
};

const home: LearningHomeResponse = {
  learner_id: "learner-1",
  course_key: courseMapFixture.stable_key,
  lessons: [],
  checkpoints: [],
  unresolved_retry_count: 2,
  scheduled_retry_count: 1,
  next_retry_due_at: "2026-10-01T02:00:00Z",
  next_action: {
    type: "start_lesson",
    title: "Start Primes and prime factorisation",
    description: "Begin the lesson and its guided practice.",
    href: "/lessons/n1-lesson-01",
    lesson_key: "n1-lesson-01",
  },
};

const progress: ProgressResponse = {
  learner_id: "learner-1",
  course_key: courseMapFixture.stable_key,
  lessons: [],
  checkpoints: [],
  proficiency_threshold: 70,
  checkpoint_required_for_mastery: true,
  scheduled_retry_count: 0,
  next_retry_due_at: null,
};

describe("core learning screens", () => {
  it("renders the API recommendation without placeholder gamification", () => {
    render(
      <CoreLearningDashboard
        learner={learner}
        home={home}
        course={courseMapFixture}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Welcome back, William" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Start lesson" })).toHaveAttribute(
      "href",
      "/lessons/n1-lesson-01",
    );
    expect(screen.getByText("2 to review")).toBeInTheDocument();
    expect(screen.queryByText(/league/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bXP\b/i)).not.toBeInTheDocument();
  });

  it("renders all real course units and no invented reward data", () => {
    const lessonCount = courseMapFixture.units.reduce(
      (total, unit) => total + unit.lessons.length,
      0,
    );
    render(
      <CoreCourseMapScreen
        learner={learner}
        course={courseMapFixture}
        progress={progress}
      />,
    );

    expect(
      screen.getByRole("heading", { name: courseMapFixture.title }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Being reviewed")).toHaveLength(lessonCount);
    expect(screen.getByText("Ratio and proportion")).toBeInTheDocument();
    expect(screen.queryByText(/reward/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bXP\b/i)).not.toBeInTheDocument();
  });
});
