import { DiagnosticPlayer } from "@/components/diagnostic-player";
import { LearnerHeader } from "@/components/learner-header";

export default async function DiagnosticSessionPage({ params }: PageProps<"/diagnostics/[sessionId]">) {
  const { sessionId } = await params;
  return <><LearnerHeader /><main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8"><DiagnosticPlayer sessionId={sessionId} /></main></>;
}
