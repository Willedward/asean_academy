import type { Metadata } from "next";

import { OverviewPanel } from "@/components/admin-dashboard";

export const metadata: Metadata = { title: "Admin · Overview" };

export default function AdminPage() {
  return (
    <>
      <h1 className="text-3xl font-extrabold">Learning overview</h1>
      <OverviewPanel />
    </>
  );
}
