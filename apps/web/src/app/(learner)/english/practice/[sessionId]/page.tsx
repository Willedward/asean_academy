import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { EnglishPracticePlayer } from "@/components/english-practice-player";
import { requireEnrolledLearner } from "@/lib/auth/learner";

export default async function EnglishPracticePage({
  params,
}: PageProps<"/english/practice/[sessionId]">) {
  const { sessionId } = await params;
  const learner = await requireEnrolledLearner(
    `/english/practice/${encodeURIComponent(sessionId)}`,
  );
  if (!learner) return null;

  return (
    <CoreLearningShell
      active="course"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref="/english"
      focus
      maxWidth={920}
    >
      <EnglishPracticePlayer sessionId={sessionId} />
    </CoreLearningShell>
  );
}
