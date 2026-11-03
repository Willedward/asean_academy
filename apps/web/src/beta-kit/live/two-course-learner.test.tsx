import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { courseMapFixture, type CourseMapResponse } from "@/lib/api/course";
import type {
  LearningHomeResponse,
  ProgressResponse,
} from "@/lib/api/progress";
import { EnrolledCourseMaps } from "@/components/enrolled-course-maps";
import {
  activeCourseKeys,
  learnerCourseHref,
} from "@/lib/auth/learner-state";
import type { CurrentLearnerResponse } from "@/lib/api/identity";

import {
  CoreCourseMapScreen,
  CoreLearningDashboard,
} from "./core-learning-screens";
import { LiveProgressView } from "./live-progress-view";

vi.mock("@/components/course-map-panel", () => ({
  CourseMapPanel: ({ courseKey }: { courseKey: string }) => (
    <div data-testid="course-map">{courseKey}</div>
  ),
}));

afterEach(cleanup);

const SEC1_TITLE = "ASEAN Scholarship Mathematics — Level 1";
const SEC2_TITLE = "ASEAN Scholarship Mathematics — Level 2";

const learner = {
  displayName: "William",
  email: "william@example.com",
  targetTrack: "g3-sec1-math",
};

const sec1: CourseMapResponse = {
  ...courseMapFixture,
  stable_key: "g3-sec1-math",
  title: SEC1_TITLE,
};
const sec2: CourseMapResponse = {
  ...courseMapFixture,
  stable_key: "g3-sec2-math",
  title: SEC2_TITLE,
  units: courseMapFixture.units.map((unit) => ({
    ...unit,
    stable_key: `sec2-${unit.stable_key}`,
  })),
};

const courses: ProgressResponse["courses"] = [
  {
    course_key: "g3-sec1-math",
    course_revision: 21,
    title: SEC1_TITLE,
    school_level: "secondary_1",
    proficiency_threshold: 70,
  },
  {
    course_key: "g3-sec2-math",
    course_revision: 11,
    title: SEC2_TITLE,
    school_level: "secondary_2",
    proficiency_threshold: 70,
  },
];

function lesson(
  courseKey: string,
  lessonKey: string,
  state: ProgressResponse["lessons"][number]["state"],
): ProgressResponse["lessons"][number] {
  return {
    course_key: courseKey,
    lesson_key: lessonKey,
    lesson_title: `Lesson ${lessonKey}`,
    position: 1,
    state,
    unlocked: true,
    unlock_reason: null,
    question_count: 0,
    resolved_count: 0,
    correct_count: 0,
    gave_up_count: 0,
    retry_question_count: 0,
    eventual_correct_percentage: 0,
    checkpoint_passed: false,
    last_session_id: null,
    updated_at: null,
  };
}

const progress: ProgressResponse = {
  learner_id: "learner-1",
  course_key: "g3-sec1-math",
  courses,
  proficiency_threshold: 70,
  checkpoint_required_for_mastery: true,
  scheduled_retry_count: 0,
  next_retry_due_at: null,
  lessons: [
    lesson("g3-sec1-math", "n1-lesson-01", "proficient"),
    lesson("g3-sec2-math", "g2-lesson-01", "in_progress"),
  ],
  checkpoints: [],
};

const home: LearningHomeResponse = {
  learner_id: "learner-1",
  course_key: "g3-sec1-math",
  courses,
  lessons: progress.lessons,
  checkpoints: [],
  unresolved_retry_count: 0,
  scheduled_retry_count: 0,
  next_retry_due_at: null,
  next_action: {
    type: "start_lesson",
    title: "Start a lesson",
    description: "Begin.",
    href: "/lessons/g2-lesson-01",
    lesson_key: "g2-lesson-01",
  },
};

function currentLearner(
  enrolments: [string, "active" | "completed" | "withdrawn"][],
): CurrentLearnerResponse {
  return {
    profile: {
      learner_id: "bd9f63f0-87fb-4b2a-a33b-1d58a18a91cf",
      email: "student@example.test",
      display_name: "Student",
      role: "student",
      target_track: "g3-sec2-math",
    },
    enrolments: enrolments.map(([course_key, status]) => ({
      course_key,
      course_revision: 1,
      status,
      enrolled_at: "2026-11-01T00:00:00Z",
    })),
  };
}

describe("two-course learner screens", () => {
  it("links the dashboard to both courses and the shell to the learning home", () => {
    render(
      <CoreLearningDashboard
        learner={learner}
        home={home}
        courses={[sec1, sec2]}
      />,
    );
    expect(
      screen.getByRole("link", { name: new RegExp(SEC1_TITLE) }),
    ).toHaveAttribute("href", "/courses/g3-sec1-math");
    expect(
      screen.getByRole("link", { name: new RegExp(SEC2_TITLE) }),
    ).toHaveAttribute("href", "/courses/g3-sec2-math");
    expect(
      screen.queryByRole("link", { name: "View full course" }),
    ).not.toBeInTheDocument();
    for (const link of screen.getAllByRole("link", { name: "Course map" })) {
      expect(link).toHaveAttribute("href", "/learn");
    }
  });

  it("lets the course map switch only to the learner's other course", () => {
    render(
      <CoreCourseMapScreen learner={learner} course={sec2} progress={progress} />,
    );
    const other = within(
      screen.getByRole("navigation", { name: "Your other courses" }),
    ).getAllByRole("link");
    expect(other).toHaveLength(1);
    expect(other[0]).toHaveAttribute("href", "/courses/g3-sec1-math");
  });

  it("hides the course switch from a single-course learner", () => {
    render(
      <CoreCourseMapScreen
        learner={learner}
        course={sec1}
        progress={{ ...progress, courses: [courses[0]!] }}
      />,
    );
    expect(
      screen.queryByRole("navigation", { name: "Your other courses" }),
    ).not.toBeInTheDocument();
  });

  it("reports lesson progress for each course", () => {
    render(
      <LiveProgressView
        progress={progress}
        startingCheckpoint={null}
        startingRetry={null}
        onOpenCheckpoint={() => undefined}
        onStartRetry={() => undefined}
      />,
    );
    const lessons = within(
      screen.getByRole("region", { name: "Lesson progress" }),
    );
    expect(lessons.getByRole("heading", { name: SEC1_TITLE })).toBeVisible();
    expect(lessons.getByRole("heading", { name: SEC2_TITLE })).toBeVisible();
    expect(screen.getByText("Lesson n1-lesson-01")).toBeVisible();
    expect(screen.getByText("Lesson g2-lesson-01")).toBeVisible();
    expect(screen.getAllByText("1 of 1 lessons")).toHaveLength(1);
    expect(screen.getAllByText("0 of 1 lessons")).toHaveLength(1);
  });

  it("renders the established map of every enrolled course", async () => {
    render(<EnrolledCourseMaps loadProgress={async () => progress} />);
    const maps = await screen.findAllByTestId("course-map");
    expect(maps.map((item) => item.textContent)).toEqual([
      "g3-sec1-math",
      "g3-sec2-math",
    ]);
  });

  it("falls back to the fixture course when progress is unavailable", async () => {
    render(
      <EnrolledCourseMaps
        loadProgress={async () => {
          throw new Error("no API");
        }}
      />,
    );
    expect((await screen.findByTestId("course-map")).textContent).toBe(
      "g3-sec1-math",
    );
  });
});

describe("learner course helpers", () => {
  it("uses only active enrolments, in level order", () => {
    const value = currentLearner([
      ["g3-sec2-math", "active"],
      ["g3-sec1-math", "active"],
      ["g3-other", "withdrawn"],
    ]);
    expect(activeCourseKeys(value)).toEqual(["g3-sec1-math", "g3-sec2-math"]);
    expect(learnerCourseHref(value)).toBe("/learn");
  });

  it("links a single-course learner straight to the course", () => {
    expect(
      learnerCourseHref(currentLearner([["g3-sec2-math", "active"]])),
    ).toBe("/courses/g3-sec2-math");
  });
});
