import "server-only";

import { redirect } from "next/navigation";

import { getServerLearner, ServerLearningApiError } from "@/lib/server/learning-api";
import { requireVerifiedSession } from "./session";

export async function requireAdministrator() {
  const session = await requireVerifiedSession("/admin");
  if (!session) return null;

  let learner;
  try {
    learner = await getServerLearner(session);
  } catch (error) {
    if (
      error instanceof ServerLearningApiError &&
      error.status === 403 &&
      error.code === "onboarding_required"
    ) {
      redirect("/onboarding");
    }
    throw error;
  }

  if (!["content_admin", "academic_admin"].includes(learner.profile.role)) {
    redirect("/learn");
  }
  return learner;
}
