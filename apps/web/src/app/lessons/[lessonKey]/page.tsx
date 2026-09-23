import { LearnerHeader } from "@/components/learner-header";
import { LessonPanel } from "@/components/lesson-panel";

export default async function LessonPage({ params }: PageProps<"/lessons/[lessonKey]">) {
  const { lessonKey } = await params;
  return <><LearnerHeader /><main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8"><LessonPanel lessonKey={lessonKey} /></main></>;
}
