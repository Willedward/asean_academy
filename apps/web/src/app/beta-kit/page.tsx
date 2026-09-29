import Link from "next/link";

import { ENTRIES } from "@/beta-kit/preview";
import { GROUPS } from "@/beta-kit/preview/registry";
import { Hornbill } from "@/beta-kit/components/hornbill";
import { Logo } from "@/beta-kit/shell/app-shell";

export default function BetaKitIndex() {
  return (
    <div className="ns-root min-h-dvh bg-ns-surface px-4 py-10 text-ns-ink lg:px-16">
      <div className="mx-auto flex max-w-[1080px] flex-col gap-8">
        <header className="flex items-center gap-5">
          <Hornbill size={96} mood="happy" pose="cheer" outfit="scarf" branch={false} />
          <div className="flex flex-col gap-2">
            <Logo height={26} />
            <h1 className="m-0 text-3xl font-bold">Beta screens</h1>
            <p className="m-0 max-w-[640px] text-ns-muted">
              Every beta student screen, built from the design canvas, running on sample data. Each screen is one
              responsive component: resize the window, or open &quot;Phone and desktop&quot; to see both at once.
            </p>
          </div>
        </header>
        {GROUPS.map((group) => {
          const items = ENTRIES.filter((entry) => entry.group === group);
          if (!items.length) return null;
          return (
            <section key={group} className="flex flex-col gap-3">
              <h2 className="m-0 text-xl font-semibold">{group}</h2>
              <ul className="m-0 grid list-none gap-2 p-0 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((entry) => (
                  <li key={entry.key} className="flex flex-col gap-1 rounded-xl border border-ns-line bg-ns-raised p-4">
                    <Link href={`/beta-kit/${entry.key}`} className="font-semibold text-ns-ink">
                      {entry.title}
                    </Link>
                    <span className="text-xs text-ns-muted">Canvas: {entry.canvas.join(", ")}</span>
                    <Link href={`/beta-kit/compare/${entry.key}`} className="text-sm font-semibold text-ns-amber-text">
                      Phone and desktop
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
    </div>
  );
}
