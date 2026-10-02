import { expect, test, type Page, type TestInfo } from "@playwright/test";

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

async function authenticate(
  page: Page,
  identity: (typeof identities)[keyof typeof identities],
) {
  const response = await page.request.post("/auth/e2e-session", {
    data: identity,
    headers: { "x-asean-e2e-secret": e2eSecret },
  });
  expect(response.status()).toBe(200);
}

async function onboard(
  page: Page,
  identity: (typeof identities)["studentA" | "studentB"],
  code: string,
) {
  await authenticate(page, identity);
  await page.goto("/onboarding");
  await expect(
    page.getByRole("heading", { name: "Activate student access" }),
  ).toBeVisible();
  await page
    .getByLabel("Name shown in the academy")
    .fill(identity === identities.studentA ? "Student A" : "Student B");
  await page.getByLabel("Beta invitation code").fill(code);
  await page.getByRole("button", { name: "Join the beta course" }).click();
  await continueFromReadiness(page);
}

async function continueFromReadiness(page: Page) {
  await page.waitForURL("**/diagnostics");
  await expect(
    page.getByRole("heading", { name: "Readiness check is being prepared" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Continue to course" }).click();
  await page.waitForURL("**/learn");
  await expect(
    page.getByRole("heading", { name: /^Welcome back, / }),
  ).toBeVisible();
  await expect(
    page.getByText("Singapore Secondary 1 G3 Mathematics course", {
      exact: false,
    }),
  ).toBeVisible();
}

async function expectNoPageOverflow(page: Page) {
  await expect
    .poll(() =>
      page.evaluate(
        () =>
          document.documentElement.scrollWidth <=
          document.documentElement.clientWidth + 1,
      ),
    )
    .toBe(true);
}

async function attachScreenshot(page: Page, testInfo: TestInfo, name: string) {
  await testInfo.attach(name, {
    body: await page.screenshot({ fullPage: true }),
    contentType: "image/png",
  });
}

test.describe.serial("authenticated beta journeys", () => {
  test("student onboarding, lesson progress, practice feedback and session persistence", async ({
    page,
  }) => {
    await page.goto("/learn");
    await expect(page).toHaveURL(/\/login\?next=%2Flearn$/);

    await authenticate(page, identities.studentA);
    await page.goto("/onboarding");
    await page.getByLabel("Name shown in the academy").fill("Student A");
    await page
      .getByLabel("Beta invitation code")
      .fill("invalid-invitation-code-2026");
    await page.getByRole("button", { name: "Join the beta course" }).click();
    await expect(
      page.getByRole("alert").filter({ hasText: "The beta invitation" }),
    ).toContainText("invalid or expired");

    await page
      .getByLabel("Beta invitation code")
      .fill("e2e-student-a-invitation-2026");
    await page.getByRole("button", { name: "Join the beta course" }).click();
    await continueFromReadiness(page);

    await page
      .getByRole("link", { name: /Primes and prime factorisation/ })
      .click();
    await expect(
      page.getByRole("heading", { name: "Primes and prime factorisation" }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Mark section complete" })
      .first()
      .click();
    await expect(
      page.getByRole("button", { name: "Mark section incomplete" }),
    ).toBeVisible();
    await page.reload();
    await expect(
      page.getByRole("button", { name: "Mark section incomplete" }),
    ).toBeVisible();

    await page.getByRole("button", { name: "Start draft practice" }).click();
    await page.waitForURL(/\/practice\/[0-9a-f-]+$/);
    await expect(
      page.getByRole("heading", { name: "Prime factorisation of 360" }),
    ).toBeVisible();
    await page.getByRole("textbox", { name: /Your answer/ }).fill("1");
    await page.getByRole("button", { name: "Check final answer" }).click();
    await expect(
      page.getByRole("status").filter({ hasText: "Try again" }),
    ).toContainText("Try again");
    await page.getByRole("button", { name: "Hint 1", exact: true }).click();
    await expect(page.getByRole("region", { name: "Hints" })).toContainText(
      "Hint 1",
    );
    await page.getByRole("button", { name: "Hint 2", exact: true }).click();
    await expect(page.getByRole("region", { name: "Hints" })).toContainText(
      "Hint 2",
    );
    await page.getByRole("button", { name: "Check final answer" }).click();
    await expect(
      page.getByRole("button", { name: "Give up and show solution" }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Give up and show solution" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Worked solution" }),
    ).toBeVisible();

    await page.getByRole("button", { name: "Report a problem" }).click();
    await page
      .getByLabel("What happened?")
      .fill("The E2E learner needs an administrator to review this wording.");
    await page.getByRole("button", { name: "Send report" }).click();
    await expect(
      page.getByRole("status").filter({ hasText: "Report received" }),
    ).toContainText("Report received");

    await page.goto("/progress");
    const lessonProgress = page.getByRole("region", {
      name: "Lesson progress",
    });
    await expect(
      lessonProgress.getByRole("heading", {
        name: "Primes and prime factorisation",
      }),
    ).toBeVisible();
    await expect(lessonProgress).toContainText("In progress");
    await expect(lessonProgress).toContainText("Solutions revealed");

    await page.getByRole("button", { name: "Sign out" }).click();
    await page.waitForURL("**/login");
    await authenticate(page, identities.studentA);
    await page.goto("/progress");
    await expect(
      page.getByRole("region", { name: "Lesson progress" }),
    ).toContainText("Solutions revealed");
  });

  test("a second student cannot see the first student's progress", async ({
    page,
  }) => {
    await onboard(page, identities.studentB, "e2e-student-b-invitation-2026");
    await page.goto("/progress");
    const lessonProgress = page.getByRole("region", {
      name: "Lesson progress",
    });
    await expect(
      lessonProgress.getByRole("heading", {
        name: "Primes and prime factorisation",
      }),
    ).toBeVisible();
    await expect(lessonProgress).toContainText("Not started");
    await expect(lessonProgress).not.toContainText("Solutions revealed");
  });

  test("database roles protect administrator capabilities and content preview", async ({
    page,
  }) => {
    await authenticate(page, identities.content);
    await page.goto("/admin/content");
    await expect(
      page.getByRole("heading", { name: "Content review and publication" }),
    ).toBeVisible();
    await expect(
      page.locator('option[value="mathematics"]').first(),
    ).toHaveAttribute("disabled", "");

    await page.goto("/admin/students/" + identities.studentA.learner_id);
    await expect(
      page.getByRole("heading", { name: "Student detail" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Delete learner account" }),
    ).toHaveCount(0);

    await page.goto("/admin/reports");
    await expect(
      page.getByRole("heading", { name: "Question reports" }),
    ).toBeVisible();
    await expect(
      page.getByText(
        "The E2E learner needs an administrator to review this wording.",
      ),
    ).toBeVisible();
    await page.getByRole("button", { name: "Start review" }).click();
    await page.getByLabel("Status").selectOption("in_review");
    await page.getByRole("button", { name: "Resolve" }).click();
    await page
      .getByLabel("Resolution shown to the learner")
      .fill("Reviewed against the source and forwarded to the content team.");
    await page.getByRole("button", { name: "Confirm resolution" }).click();
    await page.getByLabel("Status").selectOption("resolved");
    await expect(
      page.getByText(
        "Reviewed against the source and forwarded to the content team.",
      ),
    ).toBeVisible();

    await page.goto("/admin/users");
    await expect(page).toHaveURL(/\/admin$/);

    await authenticate(page, identities.academic);
    await page.goto("/admin/content");
    await expect(
      page.getByRole("heading", { name: "Content review and publication" }),
    ).toBeVisible();
    await page.getByLabel("Search").fill("n1-l1-01");
    await page.getByRole("button", { name: "Apply filters" }).click();
    await expect(
      page.getByRole("heading", { name: "Prime factorisation of 360" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Open reviewer preview" }).click();
    await expect(page.getByText("Canonical answer")).toBeVisible();
    await expect(page.getByText("Authored hints")).toBeVisible();
    await expect(page.getByText("Worked solution")).toBeVisible();
    await page.goto("/admin/users");
    await expect(
      page.getByRole("heading", { name: "Users, roles and course revisions" }),
    ).toBeVisible();

    await page.goto("/admin/students/" + identities.studentA.learner_id);
    await expect(
      page.getByRole("heading", { name: "Delete learner account" }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Preview account deletion" })
      .click();
    await expect(page.getByText("Permanent deletion preview")).toBeVisible();
  });

  test("administrator shell is responsive, keyboard operable and role aware", async ({
    page,
  }, testInfo) => {
    await authenticate(page, identities.academic);

    for (const viewport of [
      { name: "phone", width: 390, height: 844 },
      { name: "tablet", width: 768, height: 1024 },
      { name: "desktop", width: 1440, height: 1000 },
    ]) {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      });
      await page.goto("/admin");
      await expect(
        page.getByRole("heading", { name: "Learning overview" }),
      ).toBeVisible();
      await expectNoPageOverflow(page);

      const menu = page.getByRole("button", {
        name: "Open administrator navigation",
      });
      if (viewport.width < 1024) {
        await expect(menu).toBeVisible();
        await menu.focus();
        await page.keyboard.press("Enter");
        await expect(
          page.getByRole("link", { name: "Overview" }),
        ).toBeFocused();
        await expect(
          page.getByRole("link", { name: "Users & roles" }),
        ).toBeVisible();
        await expect(
          page.getByRole("link", { name: "System status" }),
        ).toBeVisible();
        await page.keyboard.press("Escape");
        await expect(menu).toBeFocused();
      } else {
        await expect(menu).toBeHidden();
        await expect(
          page.getByRole("link", { name: "Users & roles" }),
        ).toBeVisible();
      }

      await attachScreenshot(page, testInfo, "admin-" + viewport.name);
    }

    await authenticate(page, identities.content);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/admin");
    const menu = page.getByRole("button", {
      name: "Open administrator navigation",
    });
    await menu.click();
    await expect(
      page.getByRole("link", { name: "Content review" }),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: "Users & roles" })).toHaveCount(
      0,
    );
    await expect(page.getByRole("link", { name: "System status" })).toHaveCount(
      0,
    );
    await expectNoPageOverflow(page);
    await attachScreenshot(page, testInfo, "content-admin-phone-navigation");
  });
});
