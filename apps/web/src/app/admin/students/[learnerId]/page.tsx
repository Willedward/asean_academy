import { notFound } from "next/navigation";

import { StudentPanel } from "@/components/admin-dashboard";
import { requireAdministrator } from "@/lib/auth/admin";

export default async function StudentPage({
  params,
}: {
  params: Promise<{ learnerId: string }>;
}) {
  const { learnerId } = await params;
  if (!/^[0-9a-f-]{36}$/i.test(learnerId)) notFound();

  const administrator = await requireAdministrator();
  if (!administrator) return null;

  return (
    <>
      <h1 className="text-3xl font-extrabold">Student detail</h1>
      <StudentPanel
        academic={administrator.profile.role === "academic_admin"}
        learnerId={learnerId}
      />
    </>
  );
}
