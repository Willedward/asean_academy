/**
 * Sec 3-entry track: a due spaced review is recommended, completed in the
 * browser and rescheduled by the server.
 *
 * seed_e2e.py gives this learner one N1 Give up that fell due an hour ago. The API
 * uses database time and has no test clock, so the seed is the only way to reach a
 * due review without waiting two days.
 */
import { expect, test } from "@playwright/test";

import {
  authenticate,
  continueToNext,
  correctAnswers,
  learningHome,
  onboardToSec1,
  progress,
  sec3Learners,
  sessionIdFromUrl,
  submitAnswer,
  waitForQuestion,
} from "./support/sec3-entry";

const learner = sec3Learners.review;
const lessonKey = "n1-lesson-01";
const lessonTitle = "Primes and prime factorisation";
const dueQuestionKey = "n1-l1-01";

function lessonCard(page: import("@playwright/test").Page) {
  const region = page.getByRole("region", { name: "Lesson progress" });
  return region
    .locator("div")
    .filter({
      has: page.getByRole("heading", { name: lessonTitle, exact: true }),
    })
    .filter({ hasText: /Open lesson/ })
    .last();
}

test.describe.serial("Sec 3-entry spaced review", () => {
  test("a due review is recommended and completed, then rescheduled after a reload", async ({
    page,
  }) => {
    await onboardToSec1(page, learner);

    const home = await learningHome(page);
    expect(home.next_action.type).toBe("retry_practice");
    expect(home.next_action.lesson_key).toBe(lessonKey);
    expect(home.unresolved_retry_count).toBe(1);
    await expect(
      page.getByRole("heading", { name: `Retry ${lessonTitle}` }),
    ).toBeVisible();
    await expect(page.getByText("1 to review", { exact: true })).toBeVisible();

    await page.goto("/progress");
    await expect(page.getByText(/^1 spaced review scheduled/)).toBeVisible();
    await lessonCard(page)
      .getByRole("button", { name: "Start review" })
      .click();
    await page.waitForURL(/\/practice\/[0-9a-f-]{36}$/);
    const sessionId = sessionIdFromUrl(page);
    const question = await waitForQuestion(page, sessionId);
    expect(question.session.mode).toBe("retry_review");
    expect(question.session.question_count).toBe(1);
    expect(question.question?.stable_key).toBe(dueQuestionKey);
    await expect(page.getByText("RETRY REVIEW", { exact: true })).toBeVisible();

    expect(await submitAnswer(page, correctAnswers(dueQuestionKey))).toBe(true);
    await continueToNext(page);
    await expect(
      page.getByRole("heading", { name: "Practice complete" }),
    ).toBeVisible();

    await page.goto("/progress");
    await page.reload();
    const after = await progress(page);
    const lesson = after.lessons.find((item) => item.lesson_key === lessonKey);
    expect(lesson?.retry_question_count).toBe(0);
    // A clean first review moves the question to the 7-day interval.
    expect(after.scheduled_retry_count).toBe(1);
    const dueInDays =
      (Date.parse(after.next_retry_due_at!) - Date.now()) / 86_400_000;
    expect(dueInDays).toBeGreaterThan(6.9);
    expect(dueInDays).toBeLessThanOrEqual(7);
    await expect(
      lessonCard(page).getByRole("button", { name: "Start review" }),
    ).toHaveCount(0);

    // The review is not offered again before it is due, even by a direct call.
    const early = await page.request.post("/api/v1/practice-sessions", {
      data: { lesson_key: lessonKey, mode: "retry_review" },
      headers: { "Idempotency-Key": `sec3-early-review-${Date.now()}` },
    });
    expect(early.status()).toBe(409);
    expect((await early.json()).error.code).toBe("retry_queue_empty");
  });

  test("the rescheduled review survives signing out and back in", async ({
    page,
  }) => {
    await authenticate(page, learner);
    await page.goto("/learn");
    const home = await learningHome(page);
    expect(home.next_action.type).not.toBe("retry_practice");
    expect(home.unresolved_retry_count).toBe(0);
    expect(home.scheduled_retry_count).toBe(1);
    await expect(page.getByText(/Next scheduled review:/)).toBeVisible();

    await page.getByRole("button", { name: "Sign out" }).click();
    await page.waitForURL("**/login");
    await authenticate(page, learner);
    await page.goto("/progress");
    await expect(page.getByText(/^1 spaced review scheduled/)).toBeVisible();
    await expect(page.getByText(/^Next due /)).toBeVisible();
  });
});
