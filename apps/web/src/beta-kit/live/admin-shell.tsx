"use client";

import {
  Activity,
  BarChart3,
  BookOpenCheck,
  ClipboardList,
  FileQuestion,
  GraduationCap,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  Send,
  ShieldCheck,
  UserCog,
  Users,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  useEffect,
  useRef,
  useState,
  type ComponentType,
  type ReactNode,
} from "react";

import { cn } from "@/lib/utils";

import { Avatar, focusRing, Tag } from "../components/ui";
import { Logo } from "../shell/app-shell";

type AdminRole = "content_admin" | "academic_admin";

type AdminIdentity = {
  displayName: string;
  email: string;
  role: AdminRole;
};

type AdminLink = {
  href: string;
  label: string;
  icon: ComponentType<{ size?: number; "aria-hidden"?: boolean }>;
  academicOnly?: boolean;
};

const links: AdminLink[] = [
  { href: "/admin", label: "Overview", icon: LayoutDashboard },
  { href: "/admin/students", label: "Students", icon: GraduationCap },
  { href: "/admin/questions", label: "Question analytics", icon: BarChart3 },
  { href: "/admin/reports", label: "Reports inbox", icon: FileQuestion },
  { href: "/admin/content", label: "Content review", icon: BookOpenCheck },
  { href: "/admin/invitations", label: "Invitations", icon: Send },
  { href: "/admin/audit", label: "Audit history", icon: History },
  {
    href: "/admin/users",
    label: "Users & roles",
    icon: UserCog,
    academicOnly: true,
  },
  {
    href: "/admin/operations",
    label: "System status",
    icon: Activity,
    academicOnly: true,
  },
];

function initials(name: string): string {
  return (
    name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "AD"
  );
}

function isActive(pathname: string, href: string): boolean {
  if (href === "/admin") return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

function Navigation({
  identity,
  onNavigate,
}: {
  identity: AdminIdentity;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  return (
    <nav aria-label="Administrator navigation" className="flex flex-col gap-1">
      {links
        .filter(
          (item) => !item.academicOnly || identity.role === "academic_admin",
        )
        .map(({ href, label, icon: Icon }) => {
          const active = isActive(pathname, href);
          return (
            <Link
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex min-h-11 items-center gap-3 rounded-xl px-3.5 py-2 text-[15px] no-underline",
                active
                  ? "bg-ns-brand-soft font-bold text-ns-ink"
                  : "font-medium text-ns-muted hover:bg-ns-sunken",
                focusRing,
              )}
              href={href}
              key={href}
              onClick={onNavigate}
            >
              <Icon size={20} aria-hidden />
              {label}
            </Link>
          );
        })}
    </nav>
  );
}

function Account({ identity }: { identity: AdminIdentity }) {
  const roleLabel =
    identity.role === "academic_admin"
      ? "Academic administrator"
      : "Content administrator";
  return (
    <div className="rounded-2xl border border-ns-line bg-ns-raised p-4 shadow-ns-sm">
      <div className="flex min-w-0 items-center gap-3">
        <Avatar initials={initials(identity.displayName)} size={42} />
        <div className="min-w-0 grow">
          <p className="m-0 truncate text-sm font-extrabold">
            {identity.displayName}
          </p>
          <p
            className="m-0 truncate text-xs text-ns-muted"
            title={identity.email}
          >
            {identity.email}
          </p>
        </div>
      </div>
      <div className="mt-3 flex flex-col gap-2">
        <Tag tone="brand" icon={ShieldCheck}>
          {roleLabel}
        </Tag>
        <Link
          className={cn(
            "flex h-9 items-center justify-center gap-2 rounded-full border border-ns-line-strong text-sm font-semibold no-underline hover:bg-ns-sunken",
            focusRing,
          )}
          href="/learn"
        >
          <Users size={16} aria-hidden />
          Learner view
        </Link>
        <form action="/auth/signout" method="post">
          <button
            className={cn(
              "flex h-9 w-full items-center justify-center gap-2 rounded-full border border-ns-line-strong bg-ns-raised text-sm font-semibold hover:bg-ns-sunken",
              focusRing,
            )}
            type="submit"
          >
            <LogOut size={16} aria-hidden />
            Sign out
          </button>
        </form>
      </div>
    </div>
  );
}

export function AdminShell({
  identity,
  children,
}: {
  identity: AdminIdentity;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const mobilePanelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    mobilePanelRef.current
      ?.querySelector<HTMLElement>("a[href], button:not([disabled])")
      ?.focus();

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      setOpen(false);
      menuButtonRef.current?.focus();
    }

    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [open]);

  return (
    <div className="ns-root ns-admin-root min-h-dvh bg-ns-surface font-ns text-ns-ink lg:flex">
      <aside className="sticky top-0 hidden h-dvh w-[280px] shrink-0 flex-col border-r border-ns-line bg-ns-surface px-5 py-6 lg:flex">
        <Link className="mb-2 block px-3" href="/admin">
          <Logo height={25} />
        </Link>
        <div className="mb-5 flex items-center gap-2 px-3">
          <ClipboardList size={17} className="text-ns-amber-text" aria-hidden />
          <span className="text-xs font-bold tracking-[0.08em] text-ns-muted uppercase">
            Administration
          </span>
        </div>
        <Navigation identity={identity} />
        <div className="mt-auto">
          <Account identity={identity} />
        </div>
      </aside>

      <div className="min-w-0 grow">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-ns-line bg-ns-surface px-4 lg:hidden">
          <Link href="/admin">
            <Logo height={21} />
          </Link>
          <div className="flex min-w-0 items-center gap-2">
            <span className="max-w-24 truncate text-xs font-semibold text-ns-muted sm:max-w-40">
              {identity.displayName}
            </span>
            <Avatar initials={initials(identity.displayName)} size={34} />
            <button
              aria-controls="admin-mobile-navigation"
              aria-expanded={open}
              aria-label={
                open
                  ? "Close administrator navigation"
                  : "Open administrator navigation"
              }
              className={cn(
                "inline-flex size-11 items-center justify-center rounded-full hover:bg-ns-sunken",
                focusRing,
              )}
              onClick={() => setOpen((value) => !value)}
              ref={menuButtonRef}
              type="button"
            >
              {open ? (
                <X size={22} aria-hidden />
              ) : (
                <Menu size={22} aria-hidden />
              )}
            </button>
          </div>
        </header>

        {open ? (
          <div
            className="fixed inset-0 top-16 z-20 bg-ns-dark/30 lg:hidden"
            onClick={(event) => {
              if (event.target !== event.currentTarget) return;
              setOpen(false);
              menuButtonRef.current?.focus();
            }}
          >
            <div
              className="max-h-[calc(100dvh-4rem)] overflow-y-auto border-b border-ns-line bg-ns-raised p-4 shadow-ns-lg"
              id="admin-mobile-navigation"
              ref={mobilePanelRef}
            >
              <Navigation
                identity={identity}
                onNavigate={() => setOpen(false)}
              />
              <div className="mt-4 grid grid-cols-2 gap-3">
                <Link
                  className={cn(
                    "flex h-10 items-center justify-center gap-2 rounded-full border border-ns-line-strong text-sm font-semibold no-underline",
                    focusRing,
                  )}
                  href="/learn"
                  onClick={() => setOpen(false)}
                >
                  Learner view
                </Link>
                <form action="/auth/signout" method="post">
                  <button
                    className={cn(
                      "h-10 w-full rounded-full border border-ns-line-strong bg-ns-raised text-sm font-semibold",
                      focusRing,
                    )}
                    type="submit"
                  >
                    Sign out
                  </button>
                </form>
              </div>
            </div>
          </div>
        ) : null}

        <main className="ns-admin-content mx-auto w-full max-w-[1320px] px-4 py-6 sm:px-6 lg:px-10 lg:py-10">
          {children}
        </main>
      </div>
    </div>
  );
}
