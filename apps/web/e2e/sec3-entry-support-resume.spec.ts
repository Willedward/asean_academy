/**
 * Sec 3-entry track: interrupted practice resumes from server state in a second
 * browser, and authored help keeps working when the tutor is unavailable or its
 * daily allowance is spent. Only the deterministic synthetic tutor is used.
 */
import { expect, test, type Page } from "@playwright/test";

import {
  WRONG_NUMERIC_ANSWER,
  authenticate,
  continueToNext,
  correctAnswers,
  currentQuestion,
  isAllNumeric,
  json,
  learningHome,
  onboardToSec1,
  progress,
  sec3Learners,
  startLessonPractice,
  submitAnswer,
  waitForQuestion,
} from "./support/sec3-entry";

const learner = sec3Learners.support;
const lessonKey = "n1-lesson-01";
const lessonTitle = "Primes and prime factorisation";

let practiceSessionId = "";

async function resumeFromLearningHome(page: Page) {
  await page.goto("/learn");
  await expect(
    page.getByRole("heading", { name: `Resume ${lessonTitle}` }),
  ).toBeVisible();
  const home = await learningHome(page);
  expect(home.next_action.type).toBe("resume_practice");
  expect(home.next_action.session_id).toBe(practiceSessionId);
  await expect(page.getByText(home.next_action.description)).toBeVisible();
  await page.getByRole("link", { name: "Resume practice" }).click();
  await page.waitForURL(`**/practice/${practiceSessionId}`);
  return waitForQuestion(page, practiceSessionId);
}

function tutorDialog(page: Page) {
  return page.getByRole("dialog", { name: "Hornbill" });
}

test.describe.serial("Sec 3-entry resume and tutor fallback", () => {
  test("interrupted practice resumes at the same question in a second browser", async ({
    page,
    browser,
  }) => {
    await onboardToSec1(page, learner);
    practiceSessionId = await startLessonPractice(page, lessonKey);

    // Answer until the first numeric question, then stop part-way through it.
    let target = await waitForQuestion(page, practiceSessionId);
    while (!isAllNumeric(target.question!.stable_key)) {
      expect(
        await submitAnswer(page, correctAnswers(target.question!.stable_key)),
      ).toBe(true);
      await continueToNext(page);
      target = await waitForQuestion(page, practiceSessionId);
    }
    const key = target.question!.stable_key;
    const wrong = Object.fromEntries(
      Object.keys(correctAnswers(key)).map((p) => [p, WRONG_NUMERIC_ANSWER]),
    );
    expect(await submitAnswer(page, wrong)).toBe(false);
    await page.getByRole("button", { name: "Hint 1", exact: true }).click();
    await expect(page.getByRole("region", { name: "Hints" })).toContainText(
      "Hint 1",
    );
    expect(await submitAnswer(page, wrong)).toBe(false);
    await expect(
      page.getByRole("button", { name: "Give up and show solution" }),
    ).toBeVisible();
    await page.getByRole("link", { name: "Save and leave" }).click();
    await page.waitForURL(`**/lessons/${lessonKey}`);

    // A second browser has no local state: everything below comes from the API.
    const secondContext = await browser.newContext();
    const second = await secondContext.newPage();
    try {
      await authenticate(second, learner);
      expect((await learningHome(second)).next_action.description).toBe(
        `Continue question ${target.position} of ${target.session.question_count}.`,
      );
      const resumed = await resumeFromLearningHome(second);
      expect(resumed.position).toBe(target.position);
      expect(resumed.question?.stable_key).toBe(key);
      expect(resumed.attempt_count).toBe(2);
      expect(resumed.highest_hint_stage).toBe(1);
      expect(resumed.solution_available).toBe(true);
      await expect(
        second.getByRole("heading", { level: 2, name: target.question!.title }),
      ).toBeVisible();
      // The tutor entry point depends on the server's wrong-try count.
      await expect(
        second.getByRole("button", { name: "Ask the hornbill" }),
      ).toBeVisible();
    } finally {
      await secondContext.close();
    }
  });

  test("a resumed question restores its opened hint and the unlocked Give up control", async ({
    page,
  }) => {
    test.fail(
      true,
      "Product bug: the practice player ignores highest_hint_stage and " +
        "solution_available from GET /practice-sessions/{id}/next. After a " +
        "reload, sign-in or second browser the opened Hint 1 is gone and Give " +
        "up stays hidden until the learner submits a third wrong answer, " +
        "although the server already unlocked it.",
    );
    await authenticate(page, learner);
    const resumed = await resumeFromLearningHome(page);
    expect(resumed.solution_available).toBe(true);
    await expect(page.getByRole("region", { name: "Hints" })).toContainText(
      "Hint 1",
      { timeout: 5_000 },
    );
    await expect(
      page.getByRole("button", { name: "Give up and show solution" }),
    ).toBeVisible({ timeout: 5_000 });
  });

  test("a tutor outage leaves authored hints and solutions working", async ({
    page,
  }) => {
    await authenticate(page, learner);
    await resumeFromLearningHome(page);
    // Simulate the provider failing. The synthetic tutor is never bypassed for a
    // paid provider; this only replaces the message reply in the browser.
    await page.route("**/api/v1/tutor/sessions/*/messages", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "tutor_provider_unavailable",
            message:
              "The AI tutor is temporarily unavailable. Authored hints and worked solutions still work.",
            request_id: "e2e-simulated-tutor-outage",
            details: null,
          },
        }),
      }),
    );
    await page.getByRole("button", { name: "Ask the hornbill" }).click();
    const tutor = tutorDialog(page);
    await expect(tutor).toBeVisible();
    await tutor.getByLabel("Message the hornbill").fill("Can you help me?");
    await tutor.getByRole("button", { name: "Send" }).click();
    await expect(tutor.getByRole("alert")).toContainText(
      "The hornbill can’t answer right now",
    );
    await page.unroute("**/api/v1/tutor/sessions/*/messages");
    await tutor
      .getByRole("button", {
        name: "Close the hornbill and go back to the question",
      })
      .click();

    // The current UI forgets Hint 1 after a reload (see the expected failure
    // above), so open both stages again; the server records the highest.
    await page.getByRole("button", { name: "Hint 1", exact: true }).click();
    await page.getByRole("button", { name: "Hint 2", exact: true }).click();
    await expect(page.getByRole("region", { name: "Hints" })).toContainText(
      "Hint 2",
    );
    await page.reload();
    const after = await waitForQuestion(page, practiceSessionId);
    expect(after.highest_hint_stage).toBe(2);
    expect(after.solution_available).toBe(true);
  });

  test("an exhausted tutor allowance is enforced by the server and authored help remains", async ({
    page,
  }) => {
    test.setTimeout(2 * 60_000);
    await authenticate(page, learner);
    const resumed = await resumeFromLearningHome(page);
    const key = resumed.question!.stable_key;
    await page.getByRole("button", { name: "Ask the hornbill" }).click();
    const tutor = tutorDialog(page);
    await expect(tutor).toBeVisible();
    const outForToday = tutor.getByText("That’s all my help for today");

    // The daily message limit is 10; the token allowance may run out sooner.
    let sent = 0;
    while (!(await outForToday.isVisible()) && sent < 10) {
      const reply = page.waitForResponse(
        (response) =>
          response.request().method() === "POST" &&
          /\/api\/v1\/tutor\/sessions\/[^/]+\/messages$/.test(response.url()),
      );
      await tutor
        .getByLabel("Message the hornbill")
        .fill(`Which step should I check first? (${sent + 1})`);
      await tutor.getByRole("button", { name: "Send" }).click();
      const status = (await reply).status();
      expect([200, 429]).toContain(status);
      sent += 1;
      // After a reply the composer returns, unless that reply used the last message.
      await expect(
        tutor.getByRole("button", { name: "Send" }).or(outForToday),
      ).toBeVisible();
    }
    await expect(outForToday).toBeVisible();
    expect(sent).toBeLessThanOrEqual(10);
    await expect(tutor.getByLabel("Message the hornbill")).toHaveCount(0);
    await expect(tutor).toContainText("Everything else still works:");

    // The allowance is server state: a new tutor session is refused after reload.
    await page.reload();
    await waitForQuestion(page, practiceSessionId);
    const created = await json<{ session_id: string }>(
      await page.request.post("/api/v1/tutor/sessions", {
        data: {
          practice_session_id: practiceSessionId,
          question_key: key,
          question_revision: resumed.question!.revision,
        },
      }),
      201,
    );
    const refused = await page.request.post(
      `/api/v1/tutor/sessions/${created.session_id}/messages`,
      { data: { message: "One more question, please." } },
    );
    const body = await json<{ error: { code: string } }>(refused, 429);
    expect(body.error.code).toBe("tutor_quota_exceeded");

    // Authored help is independent of the tutor allowance.
    await page.getByRole("button", { name: "Hint 1", exact: true }).click();
    await expect(page.getByRole("region", { name: "Hints" })).toContainText(
      "Hint 1",
    );
    expect(
      await submitAnswer(
        page,
        Object.fromEntries(
          Object.keys(correctAnswers(key)).map((p) => [
            p,
            WRONG_NUMERIC_ANSWER,
          ]),
        ),
      ),
    ).toBe(false);
    await page
      .getByRole("button", { name: "Give up and show solution" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Worked solution" }),
    ).toBeVisible();

    await page.goto("/progress");
    await page.reload();
    const lesson = (await progress(page)).lessons.find(
      (item) => item.lesson_key === lessonKey,
    );
    expect(lesson?.gave_up_count).toBe(1);
    expect(lesson?.state).toBe("in_progress");
    const next = await currentQuestion(page, practiceSessionId);
    expect(next.question?.stable_key).not.toBe(key);
  });
});
