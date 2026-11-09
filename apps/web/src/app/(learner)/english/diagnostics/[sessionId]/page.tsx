import type { Metadata } from "next";
import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { EnglishDiagnosticPlayer } from "@/components/english-diagnostic-player";
import { requireEnrolledLearner } from "@/lib/auth/learner";

export const metadata: Metadata = { title: "English check in progress" };

export default async function EnglishDiagnosticPage({
  params,
}: PageProps<"/english/diagnostics/[sessionId]">) {
  const { sessionId } = await params;
  const learner = await requireEnrolledLearner(
    `/english/diagnostics/${encodeURIComponent(sessionId)}`,
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
      <EnglishDiagnosticPlayer sessionId={sessionId} />
    </CoreLearningShell>
  );
}
