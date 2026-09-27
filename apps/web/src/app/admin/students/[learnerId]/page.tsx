import { notFound } from "next/navigation";
import { StudentPanel } from "@/components/admin-dashboard";
export default async function StudentPage({
  params,
}: {
  params: Promise<{ learnerId: string }>;
}) {
  const { learnerId } = await params;
  if (!/^[0-9a-f-]{36}$/i.test(learnerId)) notFound();
  return (
    <>
      <h1 className="text-3xl font-extrabold">Student detail</h1>
      <StudentPanel learnerId={learnerId} />
    </>
  );
}
