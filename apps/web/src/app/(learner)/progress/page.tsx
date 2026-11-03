import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { LearnerHeader } from "@/components/learner-header";
import { ProgressPanel } from "@/components/progress-panel";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { hasActiveEnrolment, learnerCourseHref } from "@/lib/auth/learner-state";
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
  if (!learner || !hasActiveEnrolment(learner)) return <EstablishedProgressPage />;

  return (
    <CoreLearningShell
      active="progress"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref={learnerCourseHref(learner)}
    >
      <ProgressPanel appearance="nextscholar" />
    </CoreLearningShell>
  );
}
