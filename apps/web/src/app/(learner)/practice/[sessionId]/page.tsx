import { LearnerHeader } from "@/components/learner-header";
import { PracticePlayer } from "@/components/practice-player";

export default async function PracticePage({
  params,
}: PageProps<"/practice/[sessionId]">) {
  const { sessionId } = await params;
  return (
    <>
      <LearnerHeader />
      <main className="mx-auto w-full max-w-4xl px-5 py-10 sm:px-8">
        <PracticePlayer sessionId={sessionId} />
      </main>
    </>
  );
}
