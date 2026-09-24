import { LogOut } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { getVerifiedSession } from "@/lib/auth/session";
import { isSupabaseConfigured } from "@/lib/supabase/config";

export async function LearnerHeader() {
  const hostedAuth = isSupabaseConfigured();
  const session = hostedAuth ? await getVerifiedSession() : null;

  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">
        <Link className="flex items-center gap-3" href="/">
          <Image src="/brand-symbol.svg" width={38} height={38} alt="" priority />
          <span className="font-extrabold tracking-tight">ASEAN Academy</span>
        </Link>
        <div className="flex flex-wrap items-center gap-4">
          <nav aria-label="Learning navigation" className="flex items-center gap-4">
            <Link className="text-sm font-semibold text-teal-800 underline-offset-4 hover:underline" href="/learn">
              Course map
            </Link>
            <Link className="text-sm font-semibold text-teal-800 underline-offset-4 hover:underline" href="/progress">
              Progress
            </Link>
          </nav>
          {hostedAuth ? (
            <div className="flex items-center gap-3 border-l border-slate-200 pl-4">
              <span className="hidden max-w-48 truncate text-xs text-slate-500 sm:inline" title={session?.email ?? "Student account"}>
                {session?.email ?? "Student account"}
              </span>
              <form action="/auth/signout" method="post">
                <Button aria-label="Sign out" className="px-3" type="submit" variant="outline">
                  <LogOut aria-hidden="true" className="size-4" />
                  <span className="sr-only">Sign out</span>
                </Button>
              </form>
            </div>
          ) : (
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900">
              Local preview
            </span>
          )}
        </div>
      </div>
    </header>
  );
}
