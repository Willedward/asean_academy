import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { EnglishEssayDraftEditor } from "@/components/english-essay-draft-editor";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { getVerifiedSession } from "@/lib/auth/session";
import { getServerEnglishEssayDraft } from "@/lib/server/learning-api";

export default async function EnglishEssayDraftPage({
  params,
}: PageProps<"/english/essays/[draftId]">) {
  const { draftId } = await params;
  const learner = await requireEnrolledLearner(
    `/english/essays/${encodeURIComponent(draftId)}`,
  );
  const session = await getVerifiedSession();
  if (!learner || !session) return null;
  const draft = await getServerEnglishEssayDraft(session, draftId);

  return (
    <CoreLearningShell
      active="course"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref="/english"
      focus
      maxWidth={1120}
    >
      <EnglishEssayDraftEditor initialDraft={draft} />
    </CoreLearningShell>
  );
}
