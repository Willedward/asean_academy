import { CourseMapPanel } from "@/components/course-map-panel";
import { LearnerHeader } from "@/components/learner-header";
import { LearningHomePanel } from "@/components/learning-home-panel";

export default function LearnPage() {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-5xl space-y-8 px-5 py-10 sm:px-8">
        <LearningHomePanel />
        <CourseMapPanel courseKey="g3-sec1-math" />
      </main>
    </>
  );
}
