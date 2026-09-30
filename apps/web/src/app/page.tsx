import Image from "next/image";
import Link from "next/link";

import { LiveLandingScreen } from "@/beta-kit/live/live-landing";
import { HealthPanel } from "@/components/health-panel";
import { Button } from "@/components/ui/button";
import { betaLearningUiEnabled } from "@/lib/features/beta-learning-ui";
import { isSupabaseConfigured } from "@/lib/supabase/config";

function EstablishedHome({
  signInHref,
  hostedAuth,
}: {
  signInHref: string;
  hostedAuth: boolean;
}) {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-5 py-8 sm:px-8 sm:py-12">
      <header className="flex items-center gap-3">
        <Image src="/brand-symbol.svg" width={42} height={42} alt="" priority />
        <div>
          <p className="m-0 text-lg font-extrabold tracking-tight">
            ASEAN Academy
          </p>
          <p className="m-0 text-sm text-slate-500">
            Secondary mathematics beta
          </p>
        </div>
      </header>
      <section className="my-auto grid gap-8 py-16 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div>
          <p className="mb-3 text-sm font-bold uppercase tracking-[0.16em] text-teal-700">
            Secondary 1 G3 Mathematics
          </p>
          <h1 className="m-0 max-w-2xl text-4xl leading-tight font-black tracking-[-0.04em] sm:text-6xl">
            Learn each idea, practise it, and keep moving forward.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-slate-600">
            Follow the N1 course in order, submit typed final answers, and
            revisit questions that need another attempt.
          </p>
          <Button asChild>
            <Link href={signInHref}>
              {hostedAuth ? "Student sign in" : "Open the local course shell"}
            </Link>
          </Button>
        </div>
        <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-xl shadow-slate-900/5 sm:p-7">
          <h2 className="mt-0 text-xl font-extrabold">System readiness</h2>
          <HealthPanel />
        </aside>
      </section>
    </main>
  );
}

export default function Home() {
  const hostedAuth = isSupabaseConfigured();
  const signInHref = hostedAuth ? "/login" : "/learn";
  if (betaLearningUiEnabled())
    return <LiveLandingScreen signInHref={signInHref} />;
  return <EstablishedHome signInHref={signInHref} hostedAuth={hostedAuth} />;
}
