import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { DiagnosticLanding } from "@/components/diagnostic-landing";
import { LearnerHeader } from "@/components/learner-header";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";

function EstablishedDiagnosticsPage() {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8">
        <DiagnosticLanding />
      </main>
    </>
  );
}

export default async function DiagnosticsPage() {
  if (!betaLearningUiEnabled()) return <EstablishedDiagnosticsPage />;

  const learner = await requireEnrolledLearner();
  const activeEnrolment = learner?.enrolments.find(
    (enrolment) => enrolment.status === "active",
  );
  if (!learner || !activeEnrolment) return <EstablishedDiagnosticsPage />;

  return (
    <CoreLearningShell
      active="readiness"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref={`/courses/${activeEnrolment.course_key}`}
      maxWidth={920}
    >
      <DiagnosticLanding appearance="nextscholar" />
    </CoreLearningShell>
  );
}
