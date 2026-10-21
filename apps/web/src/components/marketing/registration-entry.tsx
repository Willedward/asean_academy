import { ArrowLeft, ArrowRight, Check, LockKeyhole, Mail } from "lucide-react";
import Link from "next/link";

import { Hornbill } from "@/beta-kit/components/hornbill";
import { Button, focusRing } from "@/beta-kit/components/ui";
import { Logo } from "@/beta-kit/shell/app-shell";
import { cn } from "@/lib/utils";

export function RegistrationEntry({
  signInHref = "/login?next=%2Flearn",
}: {
  signInHref?: string;
}) {
  return (
    <main className="ns-root min-h-screen bg-ns-surface px-5 py-6 font-ns text-ns-ink sm:px-8 sm:py-10">
      <div className="mx-auto w-full max-w-[1120px]">
        <div className="flex items-center justify-between gap-5">
          <Link
            href="/marketing-preview"
            aria-label="NextScholar marketing home"
          >
            <Logo height={25} />
          </Link>
          <Link
            href="/marketing-preview"
            className={cn(
              "inline-flex items-center gap-2 text-sm font-bold text-ns-muted hover:text-ns-ink",
              focusRing,
            )}
          >
            <ArrowLeft size={16} aria-hidden />
            Back to overview
          </Link>
        </div>

        <section className="grid gap-8 py-12 lg:grid-cols-[1fr_0.8fr] lg:items-center lg:py-20">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-ns-amber-line bg-ns-amber-soft px-3 py-1.5 text-xs font-bold text-ns-amber-text">
              <LockKeyhole size={15} aria-hidden />
              Invitation-only private beta
            </div>
            <h1 className="mt-6 mb-0 text-4xl leading-tight font-bold tracking-[-0.045em] sm:text-6xl">
              Register your interest in NextScholar.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-ns-muted">
              Public account creation is not open yet. Students who already
              received an invitation can continue with the invited Google
              account now.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button
                href={signInHref}
                variant="primary"
                iconRight={ArrowRight}
                className="h-12 px-7 text-base"
              >
                I have an invitation
              </Button>
              <Button
                href="/marketing-preview#features"
                variant="secondary"
                className="h-12 px-7 text-base"
              >
                Explore the features
              </Button>
            </div>
            <ul className="mt-8 grid gap-3 pl-0 text-sm leading-6 text-ns-muted sm:grid-cols-2">
              <li className="flex list-none gap-2">
                <Check
                  className="mt-1 size-4 shrink-0 text-ns-success"
                  aria-hidden
                />
                The invitation is checked after Google sign-in.
              </li>
              <li className="flex list-none gap-2">
                <Check
                  className="mt-1 size-4 shrink-0 text-ns-success"
                  aria-hidden
                />
                One account keeps lessons, practice and progress together.
              </li>
            </ul>
          </div>

          <aside className="overflow-hidden rounded-[2rem] border border-ns-line bg-white shadow-ns-md">
            <div className="flex min-h-60 items-end justify-center bg-[linear-gradient(145deg,#dcebe7,#f8ecd8)] px-6 pt-8">
              <Hornbill
                size={260}
                mood="kind"
                pose="point"
                outfit="scarf"
                label="NextScholar hornbill welcoming an invited student"
                className="size-56"
              />
            </div>
            <div className="p-6 sm:p-8">
              <span className="inline-flex size-11 items-center justify-center rounded-2xl bg-ns-brand-soft text-ns-ink">
                <Mail size={21} aria-hidden />
              </span>
              <h2 className="mt-5 mb-0 text-2xl font-bold">
                Public registration is coming later.
              </h2>
              <p className="mt-3 mb-0 leading-7 text-ns-muted">
                This page is the permanent registration entry point. A verified
                waitlist or public sign-up form can replace this message when
                the beta access policy is ready.
              </p>
              <p className="mt-4 mb-0 rounded-2xl bg-ns-surface p-4 text-sm leading-6 text-ns-muted">
                No email submitted here creates an account or joins a mailing
                list today.
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
