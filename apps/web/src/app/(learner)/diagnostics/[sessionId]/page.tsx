import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { DiagnosticPlayer } from "@/components/diagnostic-player";
import { LearnerHeader } from "@/components/learner-header";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";

function EstablishedDiagnosticSessionPage({
  sessionId,
}: {
  sessionId: string;
}) {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8">
        <DiagnosticPlayer sessionId={sessionId} />
      </main>
    </>
  );
}

export default async function DiagnosticSessionPage({
  params,
}: PageProps<"/diagnostics/[sessionId]">) {
  const { sessionId } = await params;
  if (!betaLearningUiEnabled()) {
    return <EstablishedDiagnosticSessionPage sessionId={sessionId} />;
  }

  const learner = await requireEnrolledLearner();
  const activeEnrolment = learner?.enrolments.find(
    (enrolment) => enrolment.status === "active",
  );
  if (!learner || !activeEnrolment) {
    return <EstablishedDiagnosticSessionPage sessionId={sessionId} />;
  }

  return (
    <CoreLearningShell
      active="readiness"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref={`/courses/${activeEnrolment.course_key}`}
      focus
      maxWidth={920}
    >
      <DiagnosticPlayer appearance="nextscholar" sessionId={sessionId} />
    </CoreLearningShell>
  );
}
