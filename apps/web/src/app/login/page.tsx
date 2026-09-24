import { ArrowLeft, GraduationCap, ShieldCheck } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";

import { Button } from "@/components/ui/button";
import { getVerifiedSession } from "@/lib/auth/session";
import { safeNextPath } from "@/lib/auth/navigation";
import { isSupabaseConfigured } from "@/lib/supabase/config";

import { signInWithGoogle } from "./actions";

const errorMessages: Record<string, string> = {
  auth_callback_failed: "Google sign-in could not be completed. Please try again.",
  oauth_start_failed: "Google sign-in could not be started. Please try again.",
  site_url_missing: "This hosted application is missing its public site URL configuration.",
};

export default async function LoginPage({
  searchParams,
}: PageProps<"/login">) {
  const params = await searchParams;
  const next = safeNextPath(typeof params.next === "string" ? params.next : undefined);
  const errorCode = typeof params.error === "string" ? params.error : "";
  const configured = isSupabaseConfigured();

  if (configured && await getVerifiedSession()) redirect(next);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-5 py-8 sm:px-8 sm:py-12">
      <Link className="inline-flex items-center gap-2 text-sm font-semibold text-teal-800 hover:underline" href="/">
        <ArrowLeft aria-hidden="true" className="size-4" />
        Back to ASEAN Academy
      </Link>

      <section className="my-auto grid gap-8 py-12 lg:grid-cols-[1fr_0.85fr] lg:items-center">
        <div>
          <Image src="/brand-symbol.svg" width={56} height={56} alt="" priority />
          <p className="mb-3 mt-6 text-sm font-bold uppercase tracking-[0.16em] text-teal-700">
            Invitation-only beta
          </p>
          <h1 className="m-0 text-4xl font-black tracking-[-0.04em] sm:text-5xl">
            Continue your learning with Google.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-slate-600">
            Sign in with the same email address that received your beta invitation. Your progress is kept with your own learner profile.
          </p>
          <div className="mt-6 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
            <p className="m-0 flex gap-2"><ShieldCheck aria-hidden="true" className="size-5 shrink-0 text-teal-700" />No separate password to remember.</p>
            <p className="m-0 flex gap-2"><GraduationCap aria-hidden="true" className="size-5 shrink-0 text-teal-700" />Invitation and course access are checked after sign-in.</p>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-900/5 sm:p-8">
          <h2 className="mt-0 text-2xl font-extrabold">Student sign in</h2>
          {errorMessages[errorCode] ? (
            <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900" role="alert">
              {errorMessages[errorCode]}
            </p>
          ) : null}
          {configured ? (
            <form action={signInWithGoogle}>
              <input name="next" type="hidden" value={next} />
              <Button className="w-full py-3" type="submit">
                Continue with Google
              </Button>
            </form>
          ) : (
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-950" role="status">
              Hosted authentication is not configured yet. Add the Supabase public URL and publishable key to run the Google sign-in flow. Local course development can continue without them.
            </div>
          )}
          <p className="mb-0 mt-4 text-xs leading-5 text-slate-500">
            Access is limited to invited beta students. Signing in does not automatically grant course access.
          </p>
        </div>
      </section>
    </main>
  );
}
