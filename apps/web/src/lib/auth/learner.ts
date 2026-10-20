import "server-only";

import { cache } from "react";
import { redirect } from "next/navigation";

import {
  getServerLearner,
  ServerLearningApiError,
} from "@/lib/server/learning-api";

import { hasActiveEnrolment } from "./learner-state";
import { requireVerifiedSession } from "./session";

export const requireEnrolledLearner = cache(
  async function requireEnrolledLearner(nextPath = "/learn") {
    const session = await requireVerifiedSession(nextPath);
    if (!session) return null;

    let learner;
    try {
      learner = await getServerLearner(session);
    } catch (error) {
      if (
        error instanceof ServerLearningApiError &&
        error.status === 403 &&
        ["onboarding_required", "active_enrolment_required"].includes(
          error.code,
        )
      ) {
        redirect("/onboarding");
      }
      throw error;
    }

    if (!hasActiveEnrolment(learner)) redirect("/onboarding");
    return learner;
  },
);
