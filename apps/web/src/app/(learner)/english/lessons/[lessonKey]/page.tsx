import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { EnglishLessonPanel } from "@/components/english-lesson-panel";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { getVerifiedSession } from "@/lib/auth/session";
import { getServerEnglishLesson } from "@/lib/server/learning-api";

export default async function EnglishLessonPage({
  params,
}: PageProps<"/english/lessons/[lessonKey]">) {
  const { lessonKey } = await params;
  const learner = await requireEnrolledLearner();
  const session = await getVerifiedSession();
  if (!learner || !session) return null;
  const lesson = await getServerEnglishLesson(session, lessonKey);

  return (
    <CoreLearningShell
      active="course"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref="/english"
      focus
      maxWidth={920}
    >
      <EnglishLessonPanel lesson={lesson} />
    </CoreLearningShell>
  );
}
