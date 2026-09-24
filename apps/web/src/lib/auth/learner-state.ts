import type { CurrentLearnerResponse } from "@/lib/api/identity";

export function hasActiveEnrolment(learner: CurrentLearnerResponse): boolean {
  return learner.enrolments.some((enrolment) => enrolment.status === "active");
}
