/**
 * Shared fixtures for the Sec 3-entry scholarship track journeys.
 *
 * The track covers Secondary 1 (g3-sec1-math) and Secondary 2 (g3-sec2-math).
 * Every identity below is created once by services/learning_api/scripts/seed_e2e.py,
 * and each spec file owns exactly one learner, so the files can run serially
 * against the same one-shot database in any order.
 */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { expect, type APIResponse, type Page } from "@playwright/test";

export const e2eSecret = "asean-academy-local-e2e-secret-2026-only";

export const sec3Learners = {
  twoCourse: {
    learner_id: "30000000-0000-4000-8000-000000000001",
    email: "sec3.two-course.e2e@example.test",
    displayName: "Two Course Learner",
    sec1Code: "e2e-sec3-two-course-sec1-invitation-2026",
    sec2Code: "e2e-sec3-two-course-sec2-invitation-2026",
  },
  mastery: {
    learner_id: "30000000-0000-4000-8000-000000000002",
    email: "sec3.mastery.e2e@example.test",
    displayName: "Mastery Learner",
    sec1Code: "e2e-sec3-mastery-invitation-2026",
  },
  support: {
    learner_id: "30000000-0000-4000-8000-000000000003",
    email: "sec3.support.e2e@example.test",
    displayName: "Support Learner",
    sec1Code: "e2e-sec3-support-invitation-2026",
  },
  review: {
    learner_id: "30000000-0000-4000-8000-000000000004",
    email: "sec3.review.e2e@example.test",
    displayName: "Review Learner",
    sec1Code: "e2e-sec3-review-invitation-2026",
  },
  diagnostic: {
    learner_id: "30000000-0000-4000-8000-000000000006",
    email: "sec3.diagnostic.e2e@example.test",
    displayName: "Diagnostic Learner",
    sec1Code: "e2e-sec3-diagnostic-invitation-2026",
  },
  oneInvitation: {
    learner_id: "30000000-0000-4000-8000-000000000005",
    email: "sec3.one-invitation.e2e@example.test",
    displayName: "One Invitation Learner",
    sec1Code: "e2e-sec3-one-invitation-2026",
  },
} as const;

export type Sec3Learner = (typeof sec3Learners)[keyof typeof sec3Learners];

export async function authenticate(page: Page, learner: Sec3Learner) {
  const response = await page.request.post("/auth/e2e-session", {
    data: { learner_id: learner.learner_id, email: learner.email },
    headers: { "x-asean-e2e-secret": e2eSecret },
  });
  expect(response.status()).toBe(200);
}

/** Accepts the learner's Secondary 1 invitation through the real onboarding form. */
export async function onboardToSec1(page: Page, learner: Sec3Learner) {
  await authenticate(page, learner);
  await page.goto("/onboarding");
  await page.getByLabel("Name shown in the academy").fill(learner.displayName);
  await page.getByLabel("Beta invitation code").fill(learner.sec1Code);
  await page.getByRole("button", { name: "Join the beta course" }).click();
  await page.waitForURL("**/diagnostics");
  await page.getByRole("link", { name: "Continue to course" }).click();
  await page.waitForURL("**/learn");
  await expect(
    page.getByRole("heading", {
      name: `Welcome back, ${learner.displayName}`,
    }),
  ).toBeVisible();
}

export async function json<T = Record<string, unknown>>(
  response: APIResponse,
  status = 200,
): Promise<T> {
  expect(response.status(), await response.text()).toBe(status);
  return (await response.json()) as T;
}

/** Reads server state through the same authenticated same-origin gateway as the UI. */
export async function apiGet<T = Record<string, unknown>>(
  page: Page,
  url: string,
): Promise<T> {
  return json<T>(await page.request.get(url));
}

type ProgressLesson = {
  lesson_key: string;
  lesson_title: string;
  state: string;
  unlocked: boolean;
  question_count: number;
  resolved_count: number;
  correct_count: number;
  gave_up_count: number;
  retry_question_count: number;
  checkpoint_passed: boolean;
};

type ProgressCheckpoint = {
  unit_key: string;
  state: string;
  available: boolean;
  question_count: number;
  last_session_id: string | null;
  last_percentage: number | null;
};

export type ProgressSnapshot = {
  course_key: string;
  scheduled_retry_count: number;
  next_retry_due_at: string | null;
  lessons: ProgressLesson[];
  checkpoints: ProgressCheckpoint[];
};

export type LearningHomeSnapshot = {
  course_key: string;
  next_action: {
    type: string;
    title: string;
    description: string;
    href: string;
    lesson_key: string | null;
    unit_key: string | null;
    session_id: string | null;
  };
  unresolved_retry_count: number;
  scheduled_retry_count: number;
  next_retry_due_at: string | null;
};

export function progress(page: Page) {
  return apiGet<ProgressSnapshot>(page, "/api/v1/progress");
}

export function learningHome(page: Page) {
  return apiGet<LearningHomeSnapshot>(page, "/api/v1/learning-home");
}

// ---------------------------------------------------------------------------
// Answer key built from the authored question bank that the E2E database imports.
// ---------------------------------------------------------------------------

type AuthoredResponse = {
  type: string;
  comparison_mode: string;
  canonical_answer?: string;
  canonical_latex?: string;
  canonical_expression?: string;
};

type AuthoredQuestion = {
  stable_key: string;
  title: string;
  parts: { position: number; response: AuthoredResponse }[];
};

const repositoryRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../../..",
);
const questionDirectories = [
  "backend_resources/question_bank/g3_math/secondary_1/n1/v1/questions",
  "backend_resources/question_bank/g3_math/secondary_2/g5/v1/questions",
].map((directory) => path.join(repositoryRoot, directory));

let cachedKey: Map<string, AuthoredQuestion> | null = null;

function authoredQuestions(): Map<string, AuthoredQuestion> {
  if (cachedKey) return cachedKey;
  cachedKey = new Map();
  for (const directory of questionDirectories) {
    for (const file of readdirSync(directory)) {
      if (!file.endsWith(".json")) continue;
      const question = JSON.parse(
        readFileSync(path.join(directory, file), "utf8"),
      ) as AuthoredQuestion;
      cachedKey.set(question.stable_key, question);
    }
  }
  return cachedKey;
}

/** Mirrors question_bank.practice._canonical_submission: what a solution reveals. */
function canonicalSubmission(response: AuthoredResponse): string {
  if (response.type === "numeric") return response.canonical_answer ?? "";
  if (response.comparison_mode === "prime_factorisation")
    return response.canonical_latex ?? "";
  return response.canonical_expression ?? "";
}

export function authoredQuestion(questionKey: string): AuthoredQuestion {
  const question = authoredQuestions().get(questionKey);
  if (!question)
    throw new Error(`No authored answer key for question ${questionKey}.`);
  return question;
}

export function correctAnswers(questionKey: string): Record<string, string> {
  return Object.fromEntries(
    authoredQuestion(questionKey).parts.map((part) => [
      String(part.position),
      canonicalSubmission(part.response),
    ]),
  );
}

/** True when every part takes a number, so WRONG_NUMERIC_ANSWER is well-formed. */
export function isAllNumeric(questionKey: string): boolean {
  return authoredQuestion(questionKey).parts.every(
    (part) => part.response.type === "numeric",
  );
}

export const WRONG_NUMERIC_ANSWER = "987654321";

// ---------------------------------------------------------------------------
// Practice player helpers. They read the current question from the server so the
// answer key is chosen by stable key, never by a title that may repeat.
// ---------------------------------------------------------------------------

export type NextQuestion = {
  status: "active" | "completed";
  position: number | null;
  attempt_count: number | null;
  highest_hint_stage: number | null;
  solution_available: boolean | null;
  session: {
    session_id: string;
    mode: string;
    question_count: number;
    resolved_count: number;
    status: string;
    lesson_key: string | null;
  };
  question: { stable_key: string; revision: number; title: string } | null;
};

export function sessionIdFromUrl(page: Page): string {
  const match = new URL(page.url()).pathname.match(
    /^\/(?:practice|checkpoints)\/([0-9a-f-]{36})$/,
  );
  const sessionId = match?.[1];
  if (!sessionId) throw new Error(`Not on a practice page: ${page.url()}`);
  return sessionId;
}

export async function currentQuestion(
  page: Page,
  sessionId: string,
): Promise<NextQuestion> {
  return apiGet<NextQuestion>(
    page,
    `/api/v1/practice-sessions/${sessionId}/next`,
  );
}

export async function fillAnswers(page: Page, answers: Record<string, string>) {
  for (const [position, value] of Object.entries(answers)) {
    await page.locator(`#answer-${position}`).fill(value);
  }
}

/** Waits for the player to show a question and returns the server's view of it. */
export async function waitForQuestion(page: Page, sessionId: string) {
  await expect(
    page.getByRole("heading", { level: 1, name: /^Question \d+ of \d+$/ }),
  ).toBeVisible();
  const next = await currentQuestion(page, sessionId);
  expect(next.status).toBe("active");
  await expect(
    page.getByRole("heading", { level: 1, name: /^Question \d+ of \d+$/ }),
  ).toHaveText(`Question ${next.position} of ${next.session.question_count}`);
  return next;
}

/**
 * Submits one final answer and returns whether the server marked it correct.
 * Correct answers (and every checkpoint answer) end with the Continue control.
 */
export async function submitAnswer(
  page: Page,
  answers: Record<string, string>,
): Promise<boolean> {
  await fillAnswers(page, answers);
  const attempt = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      new URL(response.url()).pathname === "/api/v1/attempts",
  );
  await page.getByRole("button", { name: "Check final answer" }).click();
  const response = await attempt;
  expect(response.status(), await response.text()).toBe(200);
  const body = (await response.json()) as { correct: boolean };
  return body.correct;
}

export async function continueToNext(page: Page) {
  await page.getByRole("button", { name: "Continue", exact: true }).click();
}

/** Answers every remaining guided-practice question correctly on the first try. */
export async function completeGuidedPracticeCorrectly(page: Page) {
  const sessionId = sessionIdFromUrl(page);
  for (;;) {
    const next = await currentQuestion(page, sessionId);
    if (next.status === "completed" || !next.question) break;
    await waitForQuestion(page, sessionId);
    expect(
      await submitAnswer(page, correctAnswers(next.question.stable_key)),
      `authored canonical answer for ${next.question.stable_key}`,
    ).toBe(true);
    await continueToNext(page);
  }
  await expect(
    page.getByRole("heading", { name: "Practice complete" }),
  ).toBeVisible();
  return sessionId;
}

export async function startLessonPractice(page: Page, lessonKey: string) {
  await page.goto(`/lessons/${lessonKey}`);
  await page.getByRole("button", { name: "Start draft practice" }).click();
  await page.waitForURL(/\/practice\/[0-9a-f-]{36}$/);
  return sessionIdFromUrl(page);
}
