import Image from "next/image";
import Link from "next/link";

export function LearnerHeader() {
  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-5 py-4 sm:px-8">
        <Link className="flex items-center gap-3" href="/">
          <Image src="/brand-symbol.svg" width={38} height={38} alt="" priority />
          <span className="font-extrabold tracking-tight">ASEAN Academy</span>
        </Link>
        <nav aria-label="Learning navigation" className="flex items-center gap-5">
          <Link className="text-sm font-semibold text-teal-800 underline-offset-4 hover:underline" href="/learn">
            Course map
          </Link>
          <Link className="text-sm font-semibold text-teal-800 underline-offset-4 hover:underline" href="/progress">
            Progress
          </Link>
        </nav>
      </div>
    </header>
  );
}
