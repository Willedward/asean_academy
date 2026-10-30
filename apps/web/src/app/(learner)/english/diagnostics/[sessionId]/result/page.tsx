import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { EnglishDiagnosticResult } from "@/components/english-diagnostic-result";
import { requireEnrolledLearner } from "@/lib/auth/learner";

export default async function EnglishDiagnosticResultPage({
  params,
}: PageProps<"/english/diagnostics/[sessionId]/result">) {
  const { sessionId } = await params;
  const learner = await requireEnrolledLearner(
    `/english/diagnostics/${encodeURIComponent(sessionId)}/result`,
  );
  if (!learner) return null;
  return (
    <CoreLearningShell
      active="readiness"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref="/english"
      focus
      maxWidth={960}
    >
      <EnglishDiagnosticResult sessionId={sessionId} />
    </CoreLearningShell>
  );
}
