import type { Metadata } from "next";
import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { DiagnosticPlayer } from "@/components/diagnostic-player";
import { LearnerHeader } from "@/components/learner-header";
import { hasActiveEnrolment, learnerCourseHref } from "@/lib/auth/learner-state";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";

export const metadata: Metadata = { title: "Readiness check in progress" };

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
  if (!learner || !hasActiveEnrolment(learner)) {
    return <EstablishedDiagnosticSessionPage sessionId={sessionId} />;
  }

  return (
    <CoreLearningShell
      active="readiness"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref={learnerCourseHref(learner)}
      focus
      maxWidth={920}
    >
      <DiagnosticPlayer appearance="nextscholar" sessionId={sessionId} />
    </CoreLearningShell>
  );
}
