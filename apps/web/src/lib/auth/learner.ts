import "server-only";

import { redirect } from "next/navigation";

import { getServerLearner, ServerLearningApiError } from "@/lib/server/learning-api";

import { hasActiveEnrolment } from "./learner-state";
import { requireVerifiedSession } from "./session";

export async function requireEnrolledLearner() {
  const session = await requireVerifiedSession();
  if (!session) return null;

  let learner;
  try {
    learner = await getServerLearner(session);
  } catch (error) {
    if (
      error instanceof ServerLearningApiError &&
      error.status === 403 &&
      ["onboarding_required", "active_enrolment_required"].includes(error.code)
    ) {
      redirect("/onboarding");
    }
    throw error;
  }

  if (!hasActiveEnrolment(learner)) redirect("/onboarding");
  return learner;
}
