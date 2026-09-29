import localFont from "next/font/local";

import { requireEnrolledLearner } from "@/lib/auth/learner";

const figtree = localFont({
  src: "../../beta-kit/fonts/Figtree-latin-wght.woff2",
  display: "swap",
  variable: "--font-figtree",
  weight: "300 900",
});

export default async function LearnerLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  await requireEnrolledLearner();
  return <div className={figtree.variable}>{children}</div>;
}
