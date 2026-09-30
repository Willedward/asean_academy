import { CourseMapPanel } from "@/components/course-map-panel";
import { LearnerHeader } from "@/components/learner-header";
import { LearningHomePanel } from "@/components/learning-home-panel";
import {
  CoreLearningDashboard,
  CoreLearningError,
} from "@/beta-kit/live/core-learning-screens";
import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { getVerifiedSession } from "@/lib/auth/session";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";
import {
  getServerCourseMap,
  getServerLearningHome,
  ServerLearningApiError,
} from "@/lib/server/learning-api";

function EstablishedLearningPage() {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-5xl space-y-8 px-5 py-10 sm:px-8">
        <LearningHomePanel />
        <CourseMapPanel courseKey="g3-sec1-math" />
      </main>
    </>
  );
}

export default async function LearnPage() {
  if (!betaLearningUiEnabled()) return <EstablishedLearningPage />;

  const learner = await requireEnrolledLearner();
  const session = await getVerifiedSession();
  if (!learner || !session) return <EstablishedLearningPage />;

  const activeEnrolment = learner.enrolments.find(
    (enrolment) => enrolment.status === "active",
  );
  if (!activeEnrolment) return <EstablishedLearningPage />;

  const presentationLearner = coreLearnerFromProfile(learner.profile);
  const courseHref = `/courses/${activeEnrolment.course_key}`;
  const result = await Promise.all([
    getServerLearningHome(session),
    getServerCourseMap(session, activeEnrolment.course_key),
  ])
    .then(([home, course]) => ({ home, course, error: null }))
    .catch((error: unknown) => ({ home: null, course: null, error }));

  if (result.error) {
    if (result.error instanceof ServerLearningApiError) {
      return (
        <CoreLearningError
          learner={presentationLearner}
          courseHref={courseHref}
          requestId={result.error.requestId}
        />
      );
    }
    throw result.error;
  }
  if (!result.home || !result.course)
    throw new Error("Learning data was not returned.");
  return (
    <CoreLearningDashboard
      learner={presentationLearner}
      home={result.home}
      course={result.course}
    />
  );
}
