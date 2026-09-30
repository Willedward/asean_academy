import type { CurrentLearnerResponse } from "@/lib/api/identity";

import type { CoreLearner } from "./core-learning-shell";

export function coreLearnerFromProfile(
  profile: CurrentLearnerResponse["profile"],
): CoreLearner {
  return {
    displayName:
      profile.display_name?.trim() || profile.email.split("@")[0] || "Student",
    email: profile.email,
    targetTrack: profile.target_track?.trim() || "G3 Mathematics",
  };
}
