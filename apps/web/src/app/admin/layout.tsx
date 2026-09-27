import Link from "next/link";
import { requireAdministrator } from "@/lib/auth/admin";
import { Button } from "@/components/ui/button";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const administrator = await requireAdministrator();
  if (!administrator)
    return (
      <main className="mx-auto max-w-2xl p-10">
        <h1 className="text-3xl font-bold">
          Administrator access requires Supabase configuration.
        </h1>
        <Link href="/learn">Return to learning</Link>
      </main>
    );
  const academic = administrator.profile.role === "academic_admin";
  const links: [string, string][] = [
    ["/admin", "Overview"],
    ["/admin/students", "Students"],
    ["/admin/questions", "Question analytics"],
    ["/admin/content", "Content review"],
    ["/admin/invitations", "Invitations"],
    ["/admin/audit", "Audit history"],
    ...(academic
      ? ([
          ["/admin/users", "Users & roles"],
          ["/admin/operations", "System status"],
        ] as [string, string][])
      : []),
  ];
  return (
    <>
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <Link href="/admin" className="text-xl font-extrabold">
            ASEAN Academy · Administration
          </Link>
          <div className="flex flex-wrap items-center gap-4">
            <Link href="/learn" className="underline">
              Learner view
            </Link>
            <span className="text-sm">{administrator.profile.email}</span>
            <form action="/auth/signout" method="post">
              <Button variant="outline">Sign out</Button>
            </form>
          </div>
        </div>
        <nav
          aria-label="Administrator navigation"
          className="mx-auto flex max-w-7xl flex-wrap gap-2 px-6 pb-4"
        >
          {links.map(([href, title]) => (
            <Link
              key={href}
              href={href}
              className="rounded-lg px-3 py-2 font-semibold text-teal-800 hover:bg-teal-50 focus-visible:outline-2"
            >
              {title}
            </Link>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">{children}</main>
    </>
  );
}
