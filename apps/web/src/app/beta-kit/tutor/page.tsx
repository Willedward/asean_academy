import Link from "next/link";

import { Hornbill } from "@/beta-kit/components/hornbill";
import { Logo } from "@/beta-kit/shell/app-shell";
import { TutorPreviewIntro, tutorEntries } from "@/beta-kit/tutor/preview";

export default function TutorKitIndex() {
  return (
    <div className="ns-root min-h-dvh bg-ns-surface px-4 py-10 text-ns-ink lg:px-16">
      <div className="mx-auto flex max-w-[1080px] flex-col gap-8">
        <header className="flex items-center gap-5">
          <Hornbill size={96} mood="happy" pose="point" branch={false} />
          <div className="flex flex-col gap-2">
            <Logo height={26} />
            <h1 className="m-0 text-3xl font-bold">AI tutor: Ask the hornbill</h1>
            <TutorPreviewIntro />
            <Link href="/beta-kit" className="text-sm font-semibold text-ns-amber-text">
              All beta screens
            </Link>
          </div>
        </header>
        <ul className="m-0 grid list-none gap-2 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {tutorEntries.map((entry) => (
            <li key={entry.key} className="flex flex-col gap-1 rounded-xl border border-ns-line bg-ns-raised p-4">
              <Link href={`/beta-kit/tutor/${entry.key}`} className="font-semibold text-ns-ink">
                {entry.title}
              </Link>
              <span className="text-xs text-ns-muted">Canvas: {entry.canvas.join(", ")}</span>
              <Link href={`/beta-kit/tutor/compare/${entry.key}`} className="text-sm font-semibold text-ns-amber-text">
                Phone and desktop
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
