/**
 * Sec 3-entry track: Secondary 1 N1 lesson proficiency, a failed checkpoint, a
 * retake and unit mastery. Every outcome is read back after a reload from the
 * Learning API and PostgreSQL, never from local answer state.
 */
import { expect, test } from "@playwright/test";

import {
  WRONG_NUMERIC_ANSWER,
  authenticate,
  completeGuidedPracticeCorrectly,
  continueToNext,
  correctAnswers,
  currentQuestion,
  isAllNumeric,
  json,
  learningHome,
  onboardToSec1,
  progress,
  sec3Learners,
  sessionIdFromUrl,
  startLessonPractice,
  submitAnswer,
  waitForQuestion,
} from "./support/sec3-entry";

const learner = sec3Learners.mastery;
const unitKey = "g3-sec1-n1";
// Prerequisite order from the authored N1 course snapshot.
const n1Lessons = [
  "n1-lesson-01",
  "n1-lesson-02",
  "n1-lesson-03",
  "n1-lesson-04",
  "n1-lesson-05",
  "n1-lesson-06",
  "n1-lesson-07",
];

/** The innermost card that holds both the heading and the card's own marker text. */
function card(
  scope: import("@playwright/test").Locator,
  heading: string,
  marker: RegExp,
) {
  return scope
    .locator("div")
    .filter({
      has: scope.page().getByRole("heading", { name: heading, exact: true }),
    })
    .filter({ hasText: marker })
    .last();
}

function wrongAnswers(questionKey: string) {
  return Object.fromEntries(
    Object.keys(correctAnswers(questionKey)).map((position) => [
      position,
      WRONG_NUMERIC_ANSWER,
    ]),
  );
}

function n1Checkpoint(page: import("@playwright/test").Page) {
  // N1 is the only Secondary 1 unit with an eight-question checkpoint.
  return card(
    page.getByRole("region", { name: "Unit checkpoints" }),
    "8-question checkpoint",
    /(Start|Retake|Resume) checkpoint|Passed/,
  );
}

function lessonCard(page: import("@playwright/test").Page, title: string) {
  return card(
    page.getByRole("region", { name: "Lesson progress" }),
    title,
    /Open lesson/,
  );
}

async function openCheckpointFromProgress(
  page: import("@playwright/test").Page,
  action: "Start checkpoint" | "Resume checkpoint" | "Retake checkpoint",
) {
  await page.goto("/progress");
  await n1Checkpoint(page).getByRole("button", { name: action }).click();
  await page.waitForURL(/\/checkpoints\/[0-9a-f-]{36}$/);
  return sessionIdFromUrl(page);
}

test.describe.serial("Sec 3-entry checkpoint, retry and mastery", () => {
  test("every N1 lesson becomes proficient and unlocks the checkpoint", async ({
    page,
  }) => {
    test.setTimeout(6 * 60_000);
    await onboardToSec1(page, learner);

    const before = await progress(page);
    expect(before.course_key).toBe("g3-sec1-math");
    expect(
      before.checkpoints.find((item) => item.unit_key === unitKey)?.state,
    ).toBe("locked");
    // A locked lesson cannot be opened by calling the API directly.
    const bypass = await page.request.post("/api/v1/practice-sessions", {
      data: { lesson_key: "n1-lesson-02", mode: "guided_practice" },
      headers: { "Idempotency-Key": `sec3-mastery-bypass-${Date.now()}` },
    });
    expect(bypass.status()).toBe(409);
    expect((await bypass.json()).error.code).toBe("lesson_locked");
    const checkpointBypass = await page.request.post(
      "/api/v1/practice-sessions",
      {
        data: { unit_key: unitKey, mode: "checkpoint" },
        headers: { "Idempotency-Key": `sec3-checkpoint-bypass-${Date.now()}` },
      },
    );
    expect(checkpointBypass.status()).toBe(409);
    expect((await checkpointBypass.json()).error.code).toBe(
      "checkpoint_locked",
    );

    for (const lessonKey of n1Lessons) {
      await startLessonPractice(page, lessonKey);
      await completeGuidedPracticeCorrectly(page);
    }

    await page.reload();
    await page.goto("/progress");
    const after = await progress(page);
    for (const lessonKey of n1Lessons) {
      const lesson = after.lessons.find(
        (item) => item.lesson_key === lessonKey,
      );
      expect(lesson?.state, lessonKey).toBe("proficient");
      expect(lesson?.gave_up_count, lessonKey).toBe(0);
      await expect(lessonCard(page, lesson!.lesson_title)).toContainText(
        "Proficient",
      );
    }
    expect(
      after.checkpoints.find((item) => item.unit_key === unitKey)?.state,
    ).toBe("available");
    await expect(
      n1Checkpoint(page).getByRole("button", { name: "Start checkpoint" }),
    ).toBeVisible();
    expect((await learningHome(page)).next_action.type).toBe(
      "start_checkpoint",
    );
  });

  test("a wrong checkpoint answer is final and the player moves on to the next question", async ({
    page,
  }) => {
    test.fail(
      true,
      "Product bug: after a wrong checkpoint answer the player keeps showing " +
        "'Try again' and an enabled 'Check final answer' button with no " +
        "Continue control, although the API has already resolved the question " +
        "as incorrect (finished is attempt.correct || solution in " +
        "live-practice-view.tsx). The learner can only advance by reloading.",
    );
    await authenticate(page, learner);
    const sessionId = await openCheckpointFromProgress(
      page,
      "Start checkpoint",
    );
    const next = await waitForQuestion(page, sessionId);
    expect(next.session.mode).toBe("checkpoint");
    expect(next.session.question_count).toBe(8);
    expect(next.position).toBe(1);
    const key = next.question!.stable_key;
    // The next test counts on this first answer being wrong.
    expect(isAllNumeric(key), `${key} must take numeric answers`).toBe(true);

    await expect(
      page.getByRole("button", { name: "Hint 1", exact: true }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Ask the hornbill" }),
    ).toHaveCount(0);
    // Support stays locked even when the browser calls the API directly.
    for (const action of ["hints/1", "give-up"]) {
      const locked = await page.request.post(
        `/api/v1/practice-sessions/${sessionId}/questions/${key}/${action}`,
      );
      const body = await json<{ error: { code: string } }>(locked, 403);
      expect(body.error.code).toBe("checkpoint_support_locked");
    }

    expect(await submitAnswer(page, wrongAnswers(key))).toBe(false);
    // The server treats the answer as final: a second attempt is refused and
    // the session has moved on to question 2.
    const retry = await page.request.post("/api/v1/attempts", {
      data: {
        session_id: sessionId,
        question_key: key,
        question_revision: next.question!.revision,
        answers: correctAnswers(key),
      },
      headers: {
        "Idempotency-Key": `sec3-checkpoint-second-try-${Date.now()}`,
      },
    });
    const refused = await json<{ error: { code: string } }>(retry, 409);
    expect(refused.error.code).toBe("question_not_current");
    expect((await currentQuestion(page, sessionId)).position).toBe(2);

    await expect(
      page.getByRole("button", { name: "Continue", exact: true }),
    ).toBeVisible({ timeout: 5_000 });
  });

  test("a failed checkpoint keeps proficiency and queues missed questions for spaced retry", async ({
    page,
  }) => {
    test.setTimeout(3 * 60_000);
    await authenticate(page, learner);
    const before = await progress(page);
    const active = before.checkpoints.find((item) => item.unit_key === unitKey);
    expect(active?.state).toBe("in_progress");
    const sessionId = await openCheckpointFromProgress(
      page,
      "Resume checkpoint",
    );
    expect(sessionId).toBe(active?.last_session_id);
    // Resuming continues after the answer already submitted in the previous test.
    let wrong = 1;
    for (;;) {
      const next = await currentQuestion(page, sessionId);
      if (next.status === "completed" || !next.question) break;
      await waitForQuestion(page, sessionId);
      const key = next.question.stable_key;
      // Four wrong answers out of eight is 50%, below the 70% pass mark.
      const answerWrong = wrong < 4 && isAllNumeric(key);
      expect(
        await submitAnswer(
          page,
          answerWrong ? wrongAnswers(key) : correctAnswers(key),
        ),
      ).toBe(!answerWrong);
      if (answerWrong) {
        wrong += 1;
        // Workaround for the missing Continue control reported above: the
        // server already resolved the question, so a reload shows the next one.
        await page.reload();
      } else {
        await continueToNext(page);
      }
    }
    expect(wrong).toBe(4);
    await expect(
      page.getByRole("heading", { name: "Checkpoint submitted" }),
    ).toBeVisible();

    await page.goto("/progress");
    await page.reload();
    const state = await progress(page);
    const checkpoint = state.checkpoints.find(
      (item) => item.unit_key === unitKey,
    );
    expect(checkpoint?.state).toBe("available");
    expect(checkpoint?.last_percentage).toBe(50);
    expect(checkpoint?.last_session_id).toBe(sessionId);
    for (const lessonKey of n1Lessons)
      expect(
        state.lessons.find((item) => item.lesson_key === lessonKey)?.state,
      ).toBe("proficient");
    // Missed checkpoint questions enter spaced retry two days from now.
    expect(state.scheduled_retry_count).toBe(4);
    const dueInDays =
      (Date.parse(state.next_retry_due_at!) - Date.now()) / 86_400_000;
    expect(dueInDays).toBeGreaterThan(1.9);
    expect(dueInDays).toBeLessThanOrEqual(2);

    // Only the N1 checkpoint has been attempted, so its score is unique on the page.
    await expect(
      page
        .getByRole("region", { name: "Unit checkpoints" })
        .getByText("Latest score: 50%.", { exact: true }),
    ).toBeVisible();
    await expect(
      n1Checkpoint(page).getByRole("button", { name: "Retake checkpoint" }),
    ).toBeVisible();
    await expect(page.getByText(/^4 spaced reviews scheduled/)).toBeVisible();
  });

  test("a passed retake masters every N1 lesson and cannot be repeated", async ({
    page,
  }) => {
    test.setTimeout(3 * 60_000);
    await authenticate(page, learner);
    const sessionId = await openCheckpointFromProgress(
      page,
      "Retake checkpoint",
    );
    for (;;) {
      const next = await currentQuestion(page, sessionId);
      if (next.status === "completed" || !next.question) break;
      await waitForQuestion(page, sessionId);
      expect(
        await submitAnswer(page, correctAnswers(next.question.stable_key)),
      ).toBe(true);
      await continueToNext(page);
    }
    await expect(
      page.getByRole("heading", { name: "Checkpoint submitted" }),
    ).toBeVisible();

    await page.goto("/progress");
    await page.reload();
    const state = await progress(page);
    const checkpoint = state.checkpoints.find(
      (item) => item.unit_key === unitKey,
    );
    expect(checkpoint?.state).toBe("passed");
    expect(checkpoint?.last_percentage).toBe(100);
    for (const lessonKey of n1Lessons) {
      const lesson = state.lessons.find(
        (item) => item.lesson_key === lessonKey,
      );
      expect(lesson?.state, lessonKey).toBe("mastered");
      expect(lesson?.checkpoint_passed, lessonKey).toBe(true);
    }
    await expect(n1Checkpoint(page)).toContainText("Passed · 100%");
    for (const lessonKey of n1Lessons) {
      const title = state.lessons.find(
        (item) => item.lesson_key === lessonKey,
      )!.lesson_title;
      await expect(lessonCard(page, title)).toContainText("Mastered");
    }

    const repeat = await page.request.post("/api/v1/practice-sessions", {
      data: { unit_key: unitKey, mode: "checkpoint" },
      headers: { "Idempotency-Key": `sec3-checkpoint-repeat-${Date.now()}` },
    });
    const body = await json<{ error: { code: string } }>(repeat, 409);
    expect(body.error.code).toBe("checkpoint_already_passed");

    const home = await learningHome(page);
    expect(home.next_action.type).not.toBe("start_checkpoint");
    expect(home.next_action.unit_key).not.toBe(unitKey);
  });
});
