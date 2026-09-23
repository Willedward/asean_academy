import { CourseMapPanel } from "@/components/course-map-panel";
import { LearnerHeader } from "@/components/learner-header";

export default function LearnPage() {
  return <><LearnerHeader /><main className="mx-auto w-full max-w-5xl px-5 py-10 sm:px-8"><CourseMapPanel courseKey="g3-sec1-math" /></main></>;
}
