import { describe, expect, it } from "vitest";

import { betaLearningUiEnabled } from "./beta-learning-ui";

describe("betaLearningUiEnabled", () => {
  it("defaults on outside production", () => {
    expect(betaLearningUiEnabled({ NODE_ENV: "development" })).toBe(true);
  });

  it("requires an explicit opt-in in production", () => {
    expect(betaLearningUiEnabled({ NODE_ENV: "production" })).toBe(false);
    expect(
      betaLearningUiEnabled({
        NODE_ENV: "production",
        ASEAN_ACADEMY_BETA_LEARNING_UI: "true",
      }),
    ).toBe(true);
  });

  it("allows the integrated UI to be switched off", () => {
    expect(
      betaLearningUiEnabled({
        NODE_ENV: "development",
        ASEAN_ACADEMY_BETA_LEARNING_UI: "false",
      }),
    ).toBe(false);
  });
});
