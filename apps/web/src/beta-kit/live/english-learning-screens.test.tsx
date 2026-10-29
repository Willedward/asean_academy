import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type {
  EnglishCourseMapResponse,
  EnglishProgressResponse,
} from "@/lib/api/english";

import { EnglishCourseScreen } from "./english-learning-screens";

afterEach(cleanup);

const learner = {
  displayName: "William",
  email: "william@example.com",
  targetTrack: "ASEAN Scholarship",
};

const course: EnglishCourseMapResponse = {
  stable_key: "asean-scholarship-english",
  revision: 1,
  title: "ASEAN Scholarship English",
  description: "Build transferable English exam skills.",
  subject: "English",
  content_status: "draft",
  development_preview: true,
  exam_profile: {
    profile_key: "asean-english-sec1-id-reported-v1",
    status: "reported",
    evidence_boundary: "Candidate-reported format.",
    entry_level: "secondary_1_entry",
    effective_from: "2026-10-01",
    review_due: "2027-10-01",
    sections: [],
    excluded_task_types: [],
  },
  modules: [
    {
      module_code: "E1",
      position: 1,
      stage: "toolkit",
      title: "Vocabulary that transfers",
      purpose: "Reason about unfamiliar words.",
      lessons: [],
    },
  ],
};

const progress: EnglishProgressResponse = {
  learner_id: "learner-1",
  lessons: [],
  checkpoints: [
    {
      module_code: "E1",
      module_title: "Vocabulary that transfers",
      state: "available",
      mastery_lesson_keys: ["e1-lesson-01", "e1-lesson-06"],
      question_count: 1,
      passing_percentage: 75,
      attempt_count: 2,
      last_session_id: "session-1",
      last_form_key: "english-checkpoint-e1-vocabulary-b-v1",
      last_percentage: 60,
    },
  ],
};

describe("English course screen", () => {
  it("shows module checkpoint readiness and latest evidence", () => {
    render(
      <EnglishCourseScreen
        learner={learner}
        course={course}
        progress={progress}
        mathsHref="/courses/g3-sec1-math"
      />,
    );

    expect(screen.getByText("MODULE CHECKPOINT")).toBeInTheDocument();
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText(/2 attempts recorded/)).toBeInTheDocument();
    expect(screen.getByText(/Latest score: 60%/)).toBeInTheDocument();
  });
});
