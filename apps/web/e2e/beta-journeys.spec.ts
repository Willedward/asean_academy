import { expect, test, type Page } from "@playwright/test";

const e2eSecret = "asean-academy-local-e2e-secret-2026-only";

const identities = {
  academic: {
    learner_id: "10000000-0000-4000-8000-000000000001",
    email: "academic.e2e@example.test",
  },
  content: {
    learner_id: "10000000-0000-4000-8000-000000000002",
    email: "content.e2e@example.test",
  },
  studentA: {
    learner_id: "20000000-0000-4000-8000-000000000001",
    email: "student.a.e2e@example.test",
  },
  studentB: {
    learner_id: "20000000-0000-4000-8000-000000000002",
    email: "student.b.e2e@example.test",
  },
} as const;

async function authenticate(page: Page, identity: (typeof identities)[keyof typeof identities]) {
  const response = await page.request.post("/auth/e2e-session", {
    data: identity,
    headers: { "x-asean-e2e-secret": e2eSecret },
  });
  expect(response.status()).toBe(200);
}

async function onboard(page: Page, identity: (typeof identities)["studentA" | "studentB"], code: string) {
  await authenticate(page, identity);
  await page.goto("/onboarding");
  await expect(page.getByRole("heading", { name: "Activate student access" })).toBeVisible();
  await page.getByLabel("Name shown in the academy").fill(identity === identities.studentA ? "Student A" : "Student B");
  await page.getByLabel("Beta invitation code").fill(code);
  await page.getByRole("button", { name: "Join the beta course" }).click();
  await page.waitForURL("**/learn");
  await expect(page.getByRole("heading", { name: "Singapore Secondary 1 G3 Mathematics" })).toBeVisible();
}

test.describe.serial("authenticated beta journeys", () => {
  test("student onboarding, lesson progress, practice feedback and session persistence", async ({ page }) => {
    await page.goto("/learn");
    await expect(page).toHaveURL(/\/login\?next=%2Flearn$/);

    await authenticate(page, identities.studentA);
    await page.goto("/onboarding");
    await page.getByLabel("Name shown in the academy").fill("Student A");
    await page.getByLabel("Beta invitation code").fill("invalid-invitation-code-2026");
    await page.getByRole("button", { name: "Join the beta course" }).click();
    await expect(page.getByRole("alert").filter({ hasText: "The beta invitation" })).toContainText("invalid or expired");

    await page.getByLabel("Beta invitation code").fill("e2e-student-a-invitation-2026");
    await page.getByRole("button", { name: "Join the beta course" }).click();
    await page.waitForURL("**/learn");
    await expect(page.getByRole("heading", { name: "Singapore Secondary 1 G3 Mathematics" })).toBeVisible();

    await page.getByRole("link", { name: /Primes and prime factorisation/ }).click();
    await expect(page.getByRole("heading", { name: "Primes and prime factorisation" })).toBeVisible();
    await page.getByRole("button", { name: "Mark section complete" }).first().click();
    await expect(page.getByRole("button", { name: "Mark section incomplete" })).toBeVisible();
    await page.reload();
    await expect(page.getByRole("button", { name: "Mark section incomplete" })).toBeVisible();

    await page.getByRole("button", { name: "Start draft practice" }).click();
    await page.waitForURL(/\/practice\/[0-9a-f-]+$/);
    await expect(page.getByRole("heading", { name: "Prime factorisation of 360" })).toBeVisible();
    await page.getByLabel("Final answer").fill("1");
    await page.getByRole("button", { name: "Check final answer" }).click();
    await expect(page.getByRole("status")).toContainText("Try again");
    await page.getByRole("button", { name: "Hint 1", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Hint 1" })).toBeVisible();
    await page.getByRole("button", { name: "Hint 2", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Hint 2" })).toBeVisible();
    await page.getByRole("button", { name: "Check final answer" }).click();
    await expect(page.getByRole("button", { name: "Give up and show solution" })).toBeVisible();
    await page.getByRole("button", { name: "Give up and show solution" }).click();
    await expect(page.getByRole("heading", { name: "Worked solution" })).toBeVisible();

    await page.goto("/progress");
    const firstLesson = page.getByRole("listitem").filter({ hasText: "Primes and prime factorisation" });
    await expect(firstLesson).toContainText("1");
    await expect(firstLesson).toContainText("Give up results");

    await page.getByRole("button", { name: "Sign out" }).click();
    await page.waitForURL("**/login");
    await authenticate(page, identities.studentA);
    await page.goto("/progress");
    await expect(page.getByRole("listitem").filter({ hasText: "Primes and prime factorisation" })).toContainText("Give up results");
  });

  test("a second student cannot see the first student's progress", async ({ page }) => {
    await onboard(page, identities.studentB, "e2e-student-b-invitation-2026");
    await page.goto("/progress");
    const firstLesson = page.getByRole("listitem").filter({ hasText: "Primes and prime factorisation" });
    await expect(firstLesson).toContainText("Not started");
    await expect(firstLesson).not.toContainText("Give up results");
  });

  test("database roles protect administrator capabilities and content preview", async ({ page }) => {
    await authenticate(page, identities.content);
    await page.goto("/admin/content");
    await expect(page.getByRole("heading", { name: "Content review and publication" })).toBeVisible();
    await expect(page.locator('option[value="mathematics"]').first()).toHaveAttribute("disabled", "");
    await page.goto("/admin/users");
    await expect(page).toHaveURL(/\/admin$/);

    await authenticate(page, identities.academic);
    await page.goto("/admin/content");
    await expect(page.getByRole("heading", { name: "Content review and publication" })).toBeVisible();
    await page.getByLabel("Search").fill("n1-l1-01");
    await page.getByRole("button", { name: "Apply filters" }).click();
    await expect(page.getByRole("heading", { name: "Prime factorisation of 360" })).toBeVisible();
    await page.getByRole("button", { name: "Preview as student" }).click();
    await expect(page.getByLabel("Student answer for part 1")).toBeDisabled();
    await expect(page.getByText("Worked solution")).toHaveCount(0);
    await page.goto("/admin/users");
    await expect(page.getByRole("heading", { name: "Users, roles and course revisions" })).toBeVisible();
  });
});
