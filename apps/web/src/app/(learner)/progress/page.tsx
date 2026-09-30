import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { LearnerHeader } from "@/components/learner-header";
import { ProgressPanel } from "@/components/progress-panel";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";

function EstablishedProgressPage() {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-5xl px-5 py-10 sm:px-8">
        <ProgressPanel />
      </main>
    </>
  );
}

export default async function ProgressPage() {
  if (!betaLearningUiEnabled()) return <EstablishedProgressPage />;

  const learner = await requireEnrolledLearner();
  const activeEnrolment = learner?.enrolments.find(
    (enrolment) => enrolment.status === "active",
  );
  if (!learner || !activeEnrolment) return <EstablishedProgressPage />;

  return (
    <CoreLearningShell
      active="progress"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref={`/courses/${activeEnrolment.course_key}`}
    >
      <ProgressPanel appearance="nextscholar" />
    </CoreLearningShell>
  );
}
