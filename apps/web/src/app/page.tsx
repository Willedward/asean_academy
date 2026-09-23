import Image from "next/image";
import Link from "next/link";

import { HealthPanel } from "@/components/health-panel";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-5 py-8 sm:px-8 sm:py-12">
      <header className="flex items-center gap-3">
        <Image src="/brand-symbol.svg" width={42} height={42} alt="" priority />
        <div>
          <p className="m-0 text-lg font-extrabold tracking-tight">ASEAN Academy</p>
          <p className="m-0 text-sm text-slate-500">Milestone 1 foundation</p>
        </div>
      </header>

      <section className="my-auto grid gap-8 py-16 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div>
          <p className="mb-3 text-sm font-bold uppercase tracking-[0.16em] text-teal-700">
            Secondary 1 G3 Mathematics
          </p>
          <h1 className="m-0 max-w-2xl text-4xl font-black leading-tight tracking-[-0.04em] sm:text-6xl">
            The learning foundation is ready for your lesson design.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-slate-600">
            Course and question contracts are versioned. The seven N1 lessons remain safe draft
            placeholders while videos and reviewed learning materials are being prepared.
          </p>
          <Button asChild><Link href="/learn">View the N1 course shell</Link></Button>
        </div>

        <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-xl shadow-slate-900/5 sm:p-7">
          <h2 className="mt-0 text-xl font-extrabold">System readiness</h2>
          <p className="text-sm leading-6 text-slate-600">
            This temporary screen proves that the replaceable Next.js client can use the generated
            OpenAPI contract and reach the Python learning API.
          </p>
          <HealthPanel />
        </aside>
      </section>

      <footer className="text-sm text-slate-500">
        Draft content stays unavailable to learners until academic and editorial review is complete.
      </footer>
    </main>
  );
}
