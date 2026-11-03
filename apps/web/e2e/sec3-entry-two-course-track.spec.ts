/**
 * Sec 3-entry track: one learner studies Secondary 1 (g3-sec1-math) and
 * Secondary 2 (g3-sec2-math) together.
 *
 * The readiness diagnostic is still marked test.fail, because no diagnostic form
 * is published or attached across both courses. Playwright reports it as an
 * expected failure and flags it when it starts passing.
 */
import { expect, test } from "@playwright/test";

import {
  apiGet,
  authenticate,
  completeGuidedPracticeCorrectly,
  continueToNext,
  currentQuestion,
  correctAnswers,
  learningHome,
  onboardToSec1,
  progress,
  sec3Learners,
  startLessonPractice,
  submitAnswer,
  waitForQuestion,
} from "./support/sec3-entry";

const learner = sec3Learners.twoCourse;
const sec1Title = "ASEAN Scholarship Mathematics — Level 1";
const sec2Title = "ASEAN Scholarship Mathematics — Level 2";

type Me = {
  enrolments: { course_key: string; status: string; course_revision: number }[];
};

type Registry = {
  courses: { stable_key: string; school_level: string; available: boolean }[];
};

async function activeCourseKeys(page: import("@playwright/test").Page) {
  const me = await apiGet<Me>(page, "/api/v1/me");
  return me.enrolments
    .filter((enrolment) => enrolment.status === "active")
    .map((enrolment) => enrolment.course_key)
    .sort();
}

test.describe.serial("Sec 3-entry two-course track", () => {
  test("the learner joins Secondary 1 and both track courses are registered", async ({
    page,
  }) => {
    await onboardToSec1(page, learner);
    await expect(page.getByText(sec1Title, { exact: false })).toBeVisible();
    expect(await activeCourseKeys(page)).toEqual(["g3-sec1-math"]);

    const registry = await apiGet<Registry>(page, "/api/v1/courses");
    expect(
      registry.courses.map((course) => [
        course.stable_key,
        course.school_level,
      ]),
    ).toEqual(
      expect.arrayContaining([
        ["g3-sec1-math", "secondary_1"],
        ["g3-sec2-math", "secondary_2"],
      ]),
    );
  });

  test("the Secondary 1–2 readiness diagnostic can be started", async ({
    page,
  }) => {
    test.fail(
      true,
      "Missing capability: no diagnostic form exists for either course " +
        "revision, and nothing imports one into the E2E database. Forms need " +
        "76 reviewed items across the 19 Secondary 1–2 topic groups, so " +
        "/diagnostics only shows 'Readiness check is being prepared'.",
    );
    await authenticate(page, learner);
    await page.goto("/diagnostics");
    await expect(
      page.getByRole("button", { name: "Start readiness check" }),
    ).toBeVisible({ timeout: 5_000 });
  });

  test("Secondary 1 practice progress persists after a reload", async ({
    page,
  }) => {
    await authenticate(page, learner);
    const sessionId = await startLessonPractice(page, "n1-lesson-01");
    const first = await waitForQuestion(page, sessionId);
    expect(
      await submitAnswer(page, correctAnswers(first.question!.stable_key)),
    ).toBe(true);
    await page.reload();
    const resumed = await waitForQuestion(page, sessionId);
    expect(resumed.position).toBe(2);

    const lesson = (await progress(page)).lessons.find(
      (item) => item.lesson_key === "n1-lesson-01",
    );
    expect(lesson?.state).toBe("in_progress");
    expect(lesson?.resolved_count).toBe(1);
    expect(lesson?.correct_count).toBe(1);
    expect((await learningHome(page)).next_action.session_id).toBe(sessionId);
  });

  test("the learner accepts a Secondary 2 invitation and keeps both enrolments", async ({
    page,
  }) => {
    await authenticate(page, learner);
    await page.goto(`/onboarding?code=${learner.sec2Code}`);
    await expect(page.getByLabel("Beta invitation code")).toHaveValue(
      learner.sec2Code,
      { timeout: 5_000 },
    );
    await page
      .getByLabel("Name shown in the academy")
      .fill(learner.displayName);
    await page.getByRole("button", { name: "Join the beta course" }).click();
    await page.waitForURL(/\/(diagnostics|learn)$/);
    await page.reload();
    expect(await activeCourseKeys(page)).toEqual([
      "g3-sec1-math",
      "g3-sec2-math",
    ]);
  });

  test("the learner moves between the Level 1 and Level 2 courses from the learning shell", async ({
    page,
  }) => {
    await authenticate(page, learner);
    expect(await activeCourseKeys(page)).toContain("g3-sec2-math");
    await page.goto("/learn");
    // This can be the first visit to the course route, which next dev compiles on demand.
    await page.getByRole("link", { name: new RegExp(sec2Title) }).click();
    await expect(
      page.getByRole("heading", { level: 1, name: sec2Title }),
    ).toBeVisible({ timeout: 30_000 });
    await page.getByRole("link", { name: new RegExp(sec1Title) }).click();
    await expect(
      page.getByRole("heading", { level: 1, name: sec1Title }),
    ).toBeVisible({ timeout: 30_000 });
  });

  test("Secondary 2 practice is recorded separately from Secondary 1 progress", async ({
    page,
  }) => {
    await authenticate(page, learner);
    expect(await activeCourseKeys(page)).toContain("g3-sec2-math");

    const sessionId = await startLessonPractice(page, "g2-lesson-01");
    await waitForQuestion(page, sessionId);
    const sec2Map = await apiGet<{
      units: { lessons: { stable_key: string; progress_state: string }[] }[];
    }>(page, "/api/v1/courses/g3-sec2-math/map");
    const sec2Lesson = sec2Map.units
      .flatMap((unit) => unit.lessons)
      .find((lesson) => lesson.stable_key === "g2-lesson-01");
    expect(sec2Lesson?.progress_state).toBe("in_progress");

    // Secondary 1 evidence from the earlier test is unchanged.
    await page.reload();
    const sec1Lesson = (await progress(page)).lessons.find(
      (item) => item.lesson_key === "n1-lesson-01",
    );
    expect(sec1Lesson?.resolved_count).toBe(1);
  });

  test("a Secondary 2 lesson and checkpoint reach mastery and show on the progress page", async ({
    page,
  }) => {
    test.setTimeout(6 * 60_000);
    await authenticate(page, learner);

    await startLessonPractice(page, "g5-lesson-06");
    await completeGuidedPracticeCorrectly(page);

    const ready = await progress(page);
    expect(
      ready.checkpoints.find((item) => item.unit_key === "g3-sec2-g5")?.state,
    ).toBe("available");

    const created = await page.request.post("/api/v1/practice-sessions", {
      data: { unit_key: "g3-sec2-g5", mode: "checkpoint" },
      headers: { "Idempotency-Key": `sec3-sec2-checkpoint-${Date.now()}` },
    });
    expect(created.status()).toBe(201);
    const sessionId = (await created.json()).session_id as string;
    await page.goto(`/checkpoints/${sessionId}`);
    for (;;) {
      const next = await currentQuestion(page, sessionId);
      if (next.status === "completed" || !next.question) break;
      await waitForQuestion(page, sessionId);
      expect(
        await submitAnswer(page, correctAnswers(next.question.stable_key)),
      ).toBe(true);
      await continueToNext(page);
    }

    const after = await progress(page);
    expect(
      after.checkpoints.find((item) => item.unit_key === "g3-sec2-g5")?.state,
    ).toBe("passed");
    expect(
      after.lessons.find((item) => item.lesson_key === "g5-lesson-06")?.state,
    ).toBe("mastered");
    expect(
      after.lessons.find((item) => item.lesson_key === "n1-lesson-01")
        ?.resolved_count,
    ).toBe(1);

    await page.goto("/progress");
    await expect(
      page.getByRole("heading", { name: sec1Title }).first(),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: sec2Title }).first(),
    ).toBeVisible();
  });
});
