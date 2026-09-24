import { CircleCheck, LogOut } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";

import { OnboardingForm } from "@/components/onboarding-form";
import { Button } from "@/components/ui/button";
import { hasActiveEnrolment } from "@/lib/auth/learner-state";
import { requireVerifiedSession } from "@/lib/auth/session";
import { getServerLearner, ServerLearningApiError } from "@/lib/server/learning-api";
import { isSupabaseConfigured } from "@/lib/supabase/config";

export default async function OnboardingPage({
  searchParams,
}: PageProps<"/onboarding">) {
  const params = await searchParams;
  const initialCode = typeof params.code === "string" ? params.code.slice(0, 300) : "";

  if (!isSupabaseConfigured()) {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-5 py-12">
        <h1 className="text-3xl font-black">Hosted onboarding is not configured.</h1>
        <p className="leading-7 text-slate-600">
          Add the Supabase public configuration to test Google sign-in and invitation acceptance. The local course shell remains available for technical development.
        </p>
        <Button asChild><Link href="/learn">Open local course shell</Link></Button>
      </main>
    );
  }

  const session = await requireVerifiedSession();
  if (!session) redirect("/login");

  let currentLearner = null;
  try {
    currentLearner = await getServerLearner(session);
  } catch (error) {
    if (!(error instanceof ServerLearningApiError && error.status === 403 && error.code === "onboarding_required")) {
      throw error;
    }
  }
  if (
    currentLearner &&
    ["content_admin", "academic_admin"].includes(currentLearner.profile.role)
  ) {
    redirect("/admin/invitations");
  }
  if (currentLearner && hasActiveEnrolment(currentLearner)) redirect("/learn");

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-5 py-8 sm:px-8 sm:py-12">
      <header className="flex items-center justify-between gap-4">
        <Link className="flex items-center gap-3" href="/">
          <Image src="/brand-symbol.svg" width={42} height={42} alt="" priority />
          <span className="font-extrabold tracking-tight">ASEAN Academy</span>
        </Link>
        <form action="/auth/signout" method="post">
          <Button type="submit" variant="outline"><LogOut aria-hidden="true" className="mr-2 size-4" />Sign out</Button>
        </form>
      </header>

      <section className="my-auto grid gap-8 py-12 lg:grid-cols-[1fr_0.9fr] lg:items-center">
        <div>
          <p className="mb-3 text-sm font-bold uppercase tracking-[0.16em] text-teal-700">One final step</p>
          <h1 className="m-0 text-4xl font-black tracking-[-0.04em] sm:text-5xl">Connect your invitation to your learner profile.</h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-slate-600">
            The invitation chooses the correct course revision and prevents uninvited accounts from entering the beta.
          </p>
          <ul className="mt-6 grid list-none gap-3 p-0 text-sm text-slate-700">
            <li className="flex gap-2"><CircleCheck aria-hidden="true" className="size-5 shrink-0 text-teal-700" />Your attempt history and progress remain attached to this Google identity.</li>
            <li className="flex gap-2"><CircleCheck aria-hidden="true" className="size-5 shrink-0 text-teal-700" />Each invitation has an expiry and usage limit.</li>
            <li className="flex gap-2"><CircleCheck aria-hidden="true" className="size-5 shrink-0 text-teal-700" />The invitation email must match the signed-in email.</li>
          </ul>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-900/5 sm:p-8">
          <h2 className="mt-0 text-2xl font-extrabold">Activate student access</h2>
          <OnboardingForm email={session.email} initialCode={initialCode} />
        </div>
      </section>
    </main>
  );
}
