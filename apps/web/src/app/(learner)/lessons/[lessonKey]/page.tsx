import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { LearnerHeader } from "@/components/learner-header";
import { LessonPanel } from "@/components/lesson-panel";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";

function EstablishedLessonPage({ lessonKey }: { lessonKey: string }) {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8">
        <LessonPanel lessonKey={lessonKey} />
      </main>
    </>
  );
}

export default async function LessonPage({
  params,
}: PageProps<"/lessons/[lessonKey]">) {
  const { lessonKey } = await params;
  if (!betaLearningUiEnabled()) {
    return <EstablishedLessonPage lessonKey={lessonKey} />;
  }

  const learner = await requireEnrolledLearner();
  const activeEnrolment = learner?.enrolments.find(
    (enrolment) => enrolment.status === "active",
  );
  if (!learner || !activeEnrolment) {
    return <EstablishedLessonPage lessonKey={lessonKey} />;
  }

  return (
    <CoreLearningShell
      active="course"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref={`/courses/${activeEnrolment.course_key}`}
      focus
    >
      <LessonPanel appearance="nextscholar" lessonKey={lessonKey} />
    </CoreLearningShell>
  );
}
