import type { CurrentLearnerResponse } from "@/lib/api/identity";

import type { CoreLearner } from "./core-learning-shell";

const trackLabels: Record<string, string> = {
  "sec3-entry": "Sec 3-entry Mathematics",
  "g3-sec1-math": "Mathematics Level 1",
  "g3-sec2-math": "Mathematics Level 2",
};

export function coreLearnerFromProfile(
  profile: CurrentLearnerResponse["profile"],
): CoreLearner {
  return {
    displayName:
      profile.display_name?.trim() || profile.email.split("@")[0] || "Student",
    email: profile.email,
    targetTrack: trackLabels[profile.target_track?.trim() ?? ""] ?? "Mathematics",
  };
}
