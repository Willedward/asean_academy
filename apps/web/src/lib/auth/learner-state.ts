import type { CurrentLearnerResponse } from "@/lib/api/identity";

export function hasActiveEnrolment(learner: CurrentLearnerResponse): boolean {
  return learner.enrolments.some((enrolment) => enrolment.status === "active");
}

/** Active course keys in level order: g3-sec1-math sorts before g3-sec2-math. */
export function activeCourseKeys(learner: CurrentLearnerResponse): string[] {
  return learner.enrolments
    .filter((enrolment) => enrolment.status === "active")
    .map((enrolment) => enrolment.course_key)
    .sort();
}

/** The course link for shared navigation. /learn lists every course of a multi-course learner. */
export function learnerCourseHref(learner: CurrentLearnerResponse): string {
  const courseKeys = activeCourseKeys(learner);
  return courseKeys.length === 1 ? `/courses/${courseKeys[0]}` : "/learn";
}
