import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { EnglishCourseScreen } from "@/beta-kit/live/english-learning-screens";
import { CoreLearningError } from "@/beta-kit/live/core-learning-screens";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { getVerifiedSession } from "@/lib/auth/session";
import {
  getServerEnglishCourseMap,
  ServerLearningApiError,
} from "@/lib/server/learning-api";

export default async function EnglishPage() {
  const learner = await requireEnrolledLearner("/english");
  const session = await getVerifiedSession();
  if (!learner || !session) return null;

  const activeEnrolment = learner.enrolments.find(
    (enrolment) => enrolment.status === "active",
  );
  if (!activeEnrolment) return null;
  const presentationLearner = coreLearnerFromProfile(learner.profile);
  const mathsHref = `/courses/${activeEnrolment.course_key}`;

  const result = await getServerEnglishCourseMap(session)
    .then((course) => ({ course, error: null }))
    .catch((error: unknown) => ({ course: null, error }));
  if (result.error) {
    if (!(result.error instanceof ServerLearningApiError)) throw result.error;
    return (
      <CoreLearningError
        learner={presentationLearner}
        courseHref="/english"
        requestId={result.error.requestId}
      />
    );
  }
  if (!result.course) throw new Error("English course data was not returned.");
  return (
    <EnglishCourseScreen
      learner={presentationLearner}
      course={result.course}
      mathsHref={mathsHref}
    />
  );
}
