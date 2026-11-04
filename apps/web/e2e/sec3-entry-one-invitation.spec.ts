/**
 * Sec 3-entry track: one invitation link enrols a learner in both Secondary 1
 * (g3-sec1-math) and Secondary 2 (g3-sec2-math) in a single step.
 */
import { expect, test } from "@playwright/test";

import { apiGet, authenticate, sec3Learners } from "./support/sec3-entry";

const learner = sec3Learners.oneInvitation;

type Me = {
  profile: { target_track: string | null };
  enrolments: { course_key: string; status: string }[];
};

test("one Sec 3-entry invitation opens both Mathematics courses", async ({
  page,
}) => {
  await authenticate(page, learner);
  await page.goto(`/onboarding?code=${learner.sec1Code}`);
  await page.getByLabel("Name shown in the academy").fill(learner.displayName);
  await page.getByRole("button", { name: "Join the beta course" }).click();
  await page.waitForURL("**/diagnostics");

  const me = await apiGet<Me>(page, "/api/v1/me");
  expect(me.profile.target_track).toBe("sec3-entry");
  expect(
    me.enrolments
      .filter((enrolment) => enrolment.status === "active")
      .map((enrolment) => enrolment.course_key)
      .sort(),
  ).toEqual(["g3-sec1-math", "g3-sec2-math"]);

  await page.goto("/learn");
  await expect(page.getByText("Track: Sec 3-entry Mathematics")).toBeVisible();
  await expect(
    page.getByText("ASEAN Scholarship Mathematics — Level 1", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByText("ASEAN Scholarship Mathematics — Level 2", { exact: false }),
  ).toBeVisible();
});
