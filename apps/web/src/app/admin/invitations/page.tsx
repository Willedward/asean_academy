import { ShieldCheck } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { AdminInvitationsPanel } from "@/components/admin-invitations-panel";
import { Button } from "@/components/ui/button";
import { requireAdministrator } from "@/lib/auth/admin";
import { isSupabaseConfigured } from "@/lib/supabase/config";

export default async function AdminInvitationsPage() {
  if (!isSupabaseConfigured()) {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-5 py-12">
        <h1 className="text-3xl font-black">Beta operations require hosted authentication.</h1>
        <p className="leading-7 text-slate-600">
          Configure Supabase and PostgreSQL before using the invitation dashboard. Local lesson and practice development remains available separately.
        </p>
        <Button asChild><Link href="/learn">Return to local course shell</Link></Button>
      </main>
    );
  }

  const administrator = await requireAdministrator();

  return (
    <>
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <Link className="flex items-center gap-3" href="/">
            <Image src="/brand-symbol.svg" width={38} height={38} alt="" priority />
            <span className="font-extrabold tracking-tight">ASEAN Academy</span>
          </Link>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-slate-500 sm:inline">
              {administrator?.profile.email}
            </span>
            <form action="/auth/signout" method="post">
              <Button type="submit" variant="outline">Sign out</Button>
            </form>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl space-y-8 px-5 py-10 sm:px-8">
        <header>
          <p className="mb-2 inline-flex items-center gap-2 text-sm font-bold uppercase tracking-[0.15em] text-teal-700">
            <ShieldCheck aria-hidden="true" className="size-4" />
            Authorized beta operations
          </p>
          <h1 className="m-0 text-4xl font-black tracking-[-0.035em]">Student invitations</h1>
          <p className="mt-3 max-w-3xl leading-7 text-slate-600">
            Issue time-limited invitations, revoke unused access and inspect the immutable operational trail. Raw invitation codes are shown only when created.
          </p>
        </header>
        <AdminInvitationsPanel />
      </main>
    </>
  );
}
