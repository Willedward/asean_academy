import { DiagnosticLanding } from "@/components/diagnostic-landing";
import { LearnerHeader } from "@/components/learner-header";

export default function DiagnosticsPage() {
  return <><LearnerHeader /><main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8"><DiagnosticLanding /></main></>;
}
