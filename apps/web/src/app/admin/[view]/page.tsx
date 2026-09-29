import { notFound, redirect } from "next/navigation";
import {
  StudentsPanel,
  QuestionsPanel,
  UsersPanel,
  OperationsPanel,
  AuditPanel,
  ReportsPanel,
} from "@/components/admin-dashboard";
import { requireAdministrator } from "@/lib/auth/admin";
import { ContentReviewPanel } from "@/components/content-review-panel";

export default async function AdminView({
  params,
}: {
  params: Promise<{ view: string }>;
}) {
  const { view } = await params;
  const administrator = await requireAdministrator();
  if (!administrator) return null;
  if (
    ["users", "operations"].includes(view) &&
    administrator.profile.role !== "academic_admin"
  )
    redirect("/admin");
  const pages: Record<string, { title: string; content: React.ReactNode }> = {
    students: { title: "Student progress", content: <StudentsPanel /> },
    questions: { title: "Question performance", content: <QuestionsPanel /> },
    reports: { title: "Question reports", content: <ReportsPanel /> },
    content: { title: "Content review and publication", content: <ContentReviewPanel academic={administrator.profile.role === "academic_admin"} /> },
    users: {
      title: "Users, roles and course revisions",
      content: <UsersPanel selfId={administrator.profile.learner_id} />,
    },
    operations: { title: "System status", content: <OperationsPanel /> },
    audit: { title: "Audit history", content: <AuditPanel /> },
  };
  const page = pages[view];
  if (!page) notFound();
  return (
    <>
      <h1 className="text-3xl font-extrabold">{page.title}</h1>
      {page.content}
    </>
  );
}
