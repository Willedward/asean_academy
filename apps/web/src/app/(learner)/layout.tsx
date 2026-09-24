import { requireEnrolledLearner } from "@/lib/auth/learner";

export default async function LearnerLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  await requireEnrolledLearner();
  return children;
}
