import Link from "next/link";
import type { ReactNode } from "react";
import {
  BarChart3,
  ClipboardCheck,
  Home,
  LogOut,
  Map as MapIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";

import { Avatar, focusRing } from "../components/ui";
import { Logo } from "../shell/app-shell";

export type CoreNavKey = "learn" | "course" | "readiness" | "progress";

export type CoreLearner = {
  displayName: string;
  email: string;
  targetTrack: string;
};

type NavItem = {
  key: CoreNavKey;
  label: string;
  href: string;
  icon: typeof Home;
};

function initials(name: string): string {
  const letters = name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
  return letters || "ST";
}

function navigation(courseHref: string): NavItem[] {
  return [
    { key: "learn", label: "Learn", href: "/learn", icon: Home },
    { key: "course", label: "Course map", href: courseHref, icon: MapIcon },
    {
      key: "readiness",
      label: "Readiness",
      href: "/diagnostics",
      icon: ClipboardCheck,
    },
    { key: "progress", label: "Progress", href: "/progress", icon: BarChart3 },
  ];
}

function Navigation({
  active,
  courseHref,
  mobile = false,
}: {
  active: CoreNavKey;
  courseHref: string;
  mobile?: boolean;
}) {
  const items = navigation(courseHref);
  if (mobile) {
    return (
      <nav
        aria-label="Main"
        className="fixed inset-x-0 bottom-0 z-30 flex h-[72px] border-t border-ns-line bg-ns-raised px-1 pb-3 lg:hidden"
      >
        {items.map(({ key, label, href, icon: Icon }) => {
          const current = key === active;
          return (
            <Link
              key={key}
              href={href}
              aria-current={current ? "page" : undefined}
              className={cn(
                "flex flex-1 flex-col items-center gap-0.5 pt-1.5 text-xs no-underline",
                current ? "font-bold text-ns-ink" : "font-medium text-ns-muted",
                focusRing,
              )}
            >
              <span
                className={cn(
                  "flex h-[30px] w-14 items-center justify-center rounded-full",
                  current && "bg-ns-brand-soft",
                )}
              >
                <Icon size={22} aria-hidden />
              </span>
              {label === "Course map" ? "Course" : label}
            </Link>
          );
        })}
      </nav>
    );
  }

  return (
    <nav aria-label="Main" className="flex flex-col gap-1">
      {items.map(({ key, label, href, icon: Icon }) => {
        const current = key === active;
        return (
          <Link
            key={key}
            href={href}
            aria-current={current ? "page" : undefined}
            className={cn(
              "flex h-11 items-center gap-3 rounded-full px-3.5 text-[15px] no-underline",
              current
                ? "bg-ns-brand-soft font-bold text-ns-ink"
                : "font-medium text-ns-muted hover:bg-ns-sunken",
              focusRing,
            )}
          >
            <Icon size={20} aria-hidden />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

function AccountCard({ learner }: { learner: CoreLearner }) {
  return (
    <div className="flex flex-col gap-3 rounded-[18px] border border-ns-line bg-ns-raised p-3.5 shadow-ns-sm">
      <div className="flex min-w-0 items-center gap-3">
        <Avatar initials={initials(learner.displayName)} size={44} />
        <div className="min-w-0">
          <div className="truncate text-sm font-extrabold text-ns-ink">
            {learner.displayName}
          </div>
          <div className="truncate text-xs text-ns-muted" title={learner.email}>
            {learner.email}
          </div>
        </div>
      </div>
      <div className="rounded-xl bg-ns-sunken px-3 py-2 text-xs font-semibold text-ns-muted">
        Track: {learner.targetTrack}
      </div>
      <form action="/auth/signout" method="post">
        <button
          type="submit"
          className={cn(
            "flex h-9 w-full items-center justify-center gap-2 rounded-full border border-ns-line-strong bg-ns-raised text-sm font-semibold text-ns-ink hover:bg-ns-sunken",
            focusRing,
          )}
        >
          <LogOut size={16} aria-hidden />
          Sign out
        </button>
      </form>
    </div>
  );
}

export function CoreLearningShell({
  active,
  learner,
  courseHref,
  children,
  maxWidth = 1080,
}: {
  active: CoreNavKey;
  learner: CoreLearner;
  courseHref: string;
  children: ReactNode;
  maxWidth?: number;
}) {
  return (
    <div className="ns-root relative min-h-dvh bg-ns-surface font-ns text-ns-ink lg:flex">
      <aside className="sticky top-0 hidden h-dvh w-[264px] shrink-0 flex-col gap-6 border-r border-ns-line bg-ns-surface px-5 pt-7 pb-6 lg:flex">
        <Link href="/learn" className="block px-3.5">
          <Logo height={26} />
        </Link>
        <Navigation active={active} courseHref={courseHref} />
        <div className="mt-auto">
          <AccountCard learner={learner} />
        </div>
      </aside>
      <div className="flex min-h-dvh min-w-0 grow flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-ns-line bg-ns-surface px-4 lg:hidden">
          <Link href="/learn">
            <Logo height={21} />
          </Link>
          <div className="flex min-w-0 items-center gap-2">
            <span className="max-w-36 truncate text-xs font-semibold text-ns-muted">
              {learner.displayName}
            </span>
            <Avatar initials={initials(learner.displayName)} size={36} />
          </div>
        </header>
        <main className="flex grow justify-center px-4 pt-5 pb-28 lg:px-14 lg:pt-10 lg:pb-16">
          <div
            className="flex w-full flex-col gap-4 lg:gap-6"
            style={{ maxWidth }}
          >
            {children}
          </div>
        </main>
      </div>
      <Navigation active={active} courseHref={courseHref} mobile />
    </div>
  );
}
