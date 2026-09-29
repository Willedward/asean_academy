import { DiagnosticResultPanel } from "@/components/diagnostic-result";
import { LearnerHeader } from "@/components/learner-header";

export default async function DiagnosticResultPage({ params }: PageProps<"/diagnostics/[sessionId]/result">) {
  const { sessionId } = await params;
  return <><LearnerHeader /><main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8"><DiagnosticResultPanel sessionId={sessionId} /></main></>;
}
