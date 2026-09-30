import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { LearnerHeader } from "@/components/learner-header";
import { PracticePlayer } from "@/components/practice-player";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";

function EstablishedCheckpointPage({ sessionId }: { sessionId: string }) {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8">
        <PracticePlayer sessionId={sessionId} />
      </main>
    </>
  );
}

export default async function CheckpointPage({
  params,
}: PageProps<"/checkpoints/[sessionId]">) {
  const { sessionId } = await params;
  if (!betaLearningUiEnabled()) {
    return <EstablishedCheckpointPage sessionId={sessionId} />;
  }

  const learner = await requireEnrolledLearner();
  const activeEnrolment = learner?.enrolments.find(
    (enrolment) => enrolment.status === "active",
  );
  if (!learner || !activeEnrolment) {
    return <EstablishedCheckpointPage sessionId={sessionId} />;
  }

  return (
    <CoreLearningShell
      active="progress"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref={`/courses/${activeEnrolment.course_key}`}
      focus
      maxWidth={920}
    >
      <PracticePlayer appearance="nextscholar" sessionId={sessionId} />
    </CoreLearningShell>
  );
}
