import Link from "next/link";
import { notFound } from "next/navigation";

import { findTutorEntry, tutorEntries } from "@/beta-kit/tutor/preview";

export function generateStaticParams() {
  return tutorEntries.map((entry) => ({ screen: entry.key }));
}

/** Phone (390 x 844) and desktop (1440 x 900, shown at half size) side by side. */
export default async function TutorKitCompare({ params }: { params: Promise<{ screen: string }> }) {
  const { screen } = await params;
  const entry = findTutorEntry(screen);
  if (!entry) notFound();
  const src = `/beta-kit/tutor/${entry.key}`;
  return (
    <div className="ns-root min-h-dvh bg-ns-sunken px-6 py-6 text-ns-ink">
      <div className="mb-4 flex flex-wrap items-baseline gap-4">
        <Link href="/beta-kit/tutor" className="font-semibold text-ns-amber-text">
          All tutor screens
        </Link>
        <h1 className="m-0 text-2xl font-bold">{entry.title}</h1>
        <span className="text-sm text-ns-muted">Canvas: {entry.canvas.join(", ")}</span>
      </div>
      <div className="flex flex-wrap items-start gap-8">
        <figure className="m-0 flex flex-col gap-2">
          <figcaption className="text-sm font-semibold">Phone</figcaption>
          <iframe title={`${entry.title} on a phone`} src={src} width={390} height={844} className="rounded-2xl border border-ns-line bg-white shadow-ns-md" />
        </figure>
        <figure className="m-0 flex flex-col gap-2">
          <figcaption className="text-sm font-semibold">Desktop (half size)</figcaption>
          <div className="h-[450px] w-[720px] overflow-hidden rounded-2xl border border-ns-line bg-white shadow-ns-md">
            <iframe title={`${entry.title} on desktop`} src={src} width={1440} height={900} className="origin-top-left scale-50 border-0" />
          </div>
        </figure>
      </div>
    </div>
  );
}
