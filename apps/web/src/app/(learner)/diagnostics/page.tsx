import type { Metadata } from "next";
import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { DiagnosticLanding } from "@/components/diagnostic-landing";
import { LearnerHeader } from "@/components/learner-header";
import { hasActiveEnrolment, learnerCourseHref } from "@/lib/auth/learner-state";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";

export const metadata: Metadata = { title: "Readiness check" };

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
  if (!learner || !hasActiveEnrolment(learner)) return <EstablishedDiagnosticsPage />;

  return (
    <CoreLearningShell
      active="readiness"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref={learnerCourseHref(learner)}
      maxWidth={920}
    >
      <DiagnosticLanding appearance="nextscholar" />
    </CoreLearningShell>
  );
}
