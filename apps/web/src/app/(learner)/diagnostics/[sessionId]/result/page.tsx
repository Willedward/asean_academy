import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { DiagnosticResultPanel } from "@/components/diagnostic-result";
import { LearnerHeader } from "@/components/learner-header";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";

function EstablishedDiagnosticResultPage({ sessionId }: { sessionId: string }) {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8">
        <DiagnosticResultPanel sessionId={sessionId} />
      </main>
    </>
  );
}

export default async function DiagnosticResultPage({
  params,
}: PageProps<"/diagnostics/[sessionId]/result">) {
  const { sessionId } = await params;
  if (!betaLearningUiEnabled()) {
    return <EstablishedDiagnosticResultPage sessionId={sessionId} />;
  }

  const learner = await requireEnrolledLearner();
  const activeEnrolment = learner?.enrolments.find(
    (enrolment) => enrolment.status === "active",
  );
  if (!learner || !activeEnrolment) {
    return <EstablishedDiagnosticResultPage sessionId={sessionId} />;
  }

  return (
    <CoreLearningShell
      active="readiness"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref={`/courses/${activeEnrolment.course_key}`}
      maxWidth={920}
    >
      <DiagnosticResultPanel appearance="nextscholar" sessionId={sessionId} />
    </CoreLearningShell>
  );
}
