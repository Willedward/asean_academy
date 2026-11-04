/**
 * Sec 3-entry track: one readiness check covers Secondary 1 and 2, whichever course a learner
 * joined last. The seed approves the diagnostic drafts in this disposable database only.
 */
import { expect, test } from "@playwright/test";

import {
  apiGet,
  authenticate,
  correctAnswers,
  sec3Learners,
} from "./support/sec3-entry";

const learner = sec3Learners.diagnostic;

type Session = {
  session_id: string;
  items: { position: number; question: { stable_key: string } }[];
};

test("a two-course learner completes one cross-year readiness check", async ({
  page,
}) => {
  await authenticate(page, learner);
  await page.goto(`/onboarding?code=${learner.sec1Code}`);
  await page.getByLabel("Name shown in the academy").fill(learner.displayName);
  await page.getByRole("button", { name: "Join the beta course" }).click();
  await page.waitForURL("**/diagnostics");
  await expect(page.getByRole("link", { name: "Continue to course" })).toBeVisible();
  await page.getByRole("button", { name: "Start readiness check" }).click();
  await page.waitForURL(/\/diagnostics\/[0-9a-f-]+$/);
  await expect(page.getByRole("heading", { name: "Question 1", level: 2 })).toBeVisible();

  const next = await apiGet<{ status: string; session_id: string }>(
    page,
    "/api/v1/diagnostics/next",
  );
  expect(next.status).toBe("resume");
  const session = await apiGet<Session>(
    page,
    `/api/v1/diagnostics/sessions/${next.session_id}`,
  );
  expect(session.items).toHaveLength(38);

  const unreadable = await page.request.put(
    `/api/v1/diagnostics/sessions/${session.session_id}/responses/1`,
    {
      headers: { "Idempotency-Key": "e2e-diagnostic-unreadable" },
      data: { answers: { "1": "not an answer!" } },
    },
  );
  expect(unreadable.status()).toBe(422);

  for (const item of session.items) {
    const saved = await page.request.put(
      `/api/v1/diagnostics/sessions/${session.session_id}/responses/${item.position}`,
      {
        headers: { "Idempotency-Key": `e2e-diagnostic-${item.position}` },
        data: {
          answers: correctAnswers(item.question.stable_key),
        },
      },
    );
    expect(saved.status()).toBe(200);
  }
  const submitted = await page.request.post(
    `/api/v1/diagnostics/sessions/${session.session_id}/submit`,
    { headers: { "Idempotency-Key": "e2e-diagnostic-submit" } },
  );
  expect(submitted.status()).toBe(200);

  const result = await apiGet<{
    topic_scores: { school_level: string }[];
  }>(page, `/api/v1/diagnostics/sessions/${session.session_id}/result`);
  expect(result.topic_scores).toHaveLength(19);
  expect(new Set(result.topic_scores.map((topic) => topic.school_level))).toEqual(
    new Set(["secondary_1", "secondary_2"]),
  );

  const after = await apiGet<{ status: string }>(page, "/api/v1/diagnostics/next");
  expect(after.status).toBe("baseline_complete");
  await page.goto(`/diagnostics/${session.session_id}/result`);
  await expect(page.getByText(/^Level 2 · /).first()).toBeVisible();
});
