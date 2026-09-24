import { LearnerHeader } from "@/components/learner-header";
import { ProgressPanel } from "@/components/progress-panel";

export default function ProgressPage() {
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-5xl px-5 py-10 sm:px-8">
        <ProgressPanel />
      </main>
    </>
  );
}
