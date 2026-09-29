type LearningUiEnvironment = {
  ASEAN_ACADEMY_BETA_LEARNING_UI?: string;
  NODE_ENV?: string;
};

const TRUE_VALUES = new Set(["1", "true", "yes", "on"]);
const FALSE_VALUES = new Set(["0", "false", "no", "off"]);

/**
 * Enables the integrated beta learning screens by default during development.
 * Production requires an explicit opt-in so a deployment can instantly return
 * to the established learner screens without a code rollback.
 */
export function betaLearningUiEnabled(
  environment: LearningUiEnvironment = process.env,
): boolean {
  const configured =
    environment.ASEAN_ACADEMY_BETA_LEARNING_UI?.trim().toLowerCase();
  if (configured && TRUE_VALUES.has(configured)) return true;
  if (configured && FALSE_VALUES.has(configured)) return false;
  return environment.NODE_ENV !== "production";
}
