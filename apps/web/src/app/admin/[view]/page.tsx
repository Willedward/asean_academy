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
import { TutorEvaluationPanel } from "@/components/tutor-evaluation-panel";

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
  const pages: Record<
    string,
    { title: string; description: string; content: React.ReactNode }
  > = {
    students: {
      title: "Student progress",
      description:
        "Inspect enrolment, activity, retry, diagnostic and mastery evidence for each invited learner.",
      content: <StudentsPanel />,
    },
    questions: {
      title: "Question performance",
      description:
        "Find questions that need review using attempts, accuracy, hints, give-ups and retry evidence.",
      content: <QuestionsPanel />,
    },
    reports: {
      title: "Question reports",
      description:
        "Review student-raised content concerns and record an auditable learner-visible resolution.",
      content: <ReportsPanel />,
    },
    content: {
      title: "Content review and publication",
      description:
        "Review exact immutable revisions and request publication or retirement without editing Git-authored content.",
      content: (
        <ContentReviewPanel
          academic={administrator.profile.role === "academic_admin"}
        />
      ),
    },
    "tutor-evaluation": {
      title: "AI tutor evaluation lab",
      description:
        "Run approved N2 calibration cases, inspect automated checks and cost evidence, and record mathematics and editorial reviews of each AI response.",
      content: (
        <TutorEvaluationPanel
          academic={administrator.profile.role === "academic_admin"}
        />
      ),
    },
    users: {
      title: "Users, roles and course revisions",
      description:
        "Manage administrator roles and preview learner curriculum migrations before applying them.",
      content: <UsersPanel selfId={administrator.profile.learner_id} />,
    },
    operations: {
      title: "System status",
      description:
        "Check the deployed release, database schema and imported content required to serve the beta.",
      content: <OperationsPanel />,
    },
    audit: {
      title: "Audit history",
      description:
        "Trace append-only administrative events by actor, target, request ID and timestamp.",
      content: <AuditPanel />,
    },
  };
  const page = pages[view];
  if (!page) notFound();
  return (
    <>
      <h1 className="text-3xl font-extrabold">{page.title}</h1>
      <p>{page.description}</p>
      {page.content}
    </>
  );
}
