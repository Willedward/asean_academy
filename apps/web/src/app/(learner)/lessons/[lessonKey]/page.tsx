import type { Metadata } from "next";
import { coreLearnerFromProfile } from "@/beta-kit/live/core-learner";
import { CoreLearningShell } from "@/beta-kit/live/core-learning-shell";
import { LearnerHeader } from "@/components/learner-header";
import { LessonPanel } from "@/components/lesson-panel";
import { requireEnrolledLearner } from "@/lib/auth/learner";
import { hasActiveEnrolment, learnerCourseHref } from "@/lib/auth/learner-state";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";

export const metadata: Metadata = { title: "Lesson" };

function EstablishedLessonPage({ lessonKey }: { lessonKey: string }) {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8">
        <LessonPanel lessonKey={lessonKey} />
      </main>
    </>
  );
}

export default async function LessonPage({
  params,
}: PageProps<"/lessons/[lessonKey]">) {
  const { lessonKey } = await params;
  if (!betaLearningUiEnabled()) {
    return <EstablishedLessonPage lessonKey={lessonKey} />;
  }

  const learner = await requireEnrolledLearner();
  if (!learner || !hasActiveEnrolment(learner)) {
    return <EstablishedLessonPage lessonKey={lessonKey} />;
  }

  return (
    <CoreLearningShell
      active="course"
      learner={coreLearnerFromProfile(learner.profile)}
      courseHref={learnerCourseHref(learner)}
      focus
    >
      <LessonPanel appearance="nextscholar" lessonKey={lessonKey} />
    </CoreLearningShell>
  );
}
