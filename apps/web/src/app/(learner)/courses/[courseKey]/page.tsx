import {
  CoreCourseMapScreen,
  CoreLearningError,
} from "@/beta-kit/live/core-learning-screens";
import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CourseMapPanel } from "@/components/course-map-panel";
import { LearnerHeader } from "@/components/learner-header";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { getVerifiedSession } from "@/lib/auth/session";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";
import {
  getServerCourseMap,
  getServerProgress,
  ServerLearningApiError,
} from "@/lib/server/learning-api";

function EstablishedCoursePage({ courseKey }: { courseKey: string }) {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-5xl px-5 py-10 sm:px-8">
        <CourseMapPanel courseKey={courseKey} />
      </main>
    </>
  );
}

export default async function CoursePage({
  params,
}: PageProps<"/courses/[courseKey]">) {
  const { courseKey } = await params;
  if (!betaLearningUiEnabled())
    return <EstablishedCoursePage courseKey={courseKey} />;

  const learner = await requireEnrolledLearner();
  const session = await getVerifiedSession();
  if (!learner || !session)
    return <EstablishedCoursePage courseKey={courseKey} />;

  const presentationLearner = coreLearnerFromProfile(learner.profile);
  const courseHref = `/courses/${courseKey}`;
  const result = await Promise.all([
    getServerCourseMap(session, courseKey),
    getServerProgress(session),
  ])
    .then(([course, progress]) => ({ course, progress, error: null }))
    .catch((error: unknown) => ({ course: null, progress: null, error }));

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
  if (!result.course || !result.progress)
    throw new Error("Course data was not returned.");
  return (
    <CoreCourseMapScreen
      learner={presentationLearner}
      course={result.course}
      progress={result.progress}
    />
  );
}
