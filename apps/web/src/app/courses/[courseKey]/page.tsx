import { CourseMapPanel } from "@/components/course-map-panel";
import { LearnerHeader } from "@/components/learner-header";

export default async function CoursePage({ params }: PageProps<"/courses/[courseKey]">) {
  const { courseKey } = await params;
  return <><LearnerHeader /><main className="mx-auto w-full max-w-5xl px-5 py-10 sm:px-8"><CourseMapPanel courseKey={courseKey} /></main></>;
}
