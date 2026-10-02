"use client";

import { AlertCircle, LoaderCircle, LogOut, RotateCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button, Callout } from "@/beta-kit/components/ui";
import { BareShell, Logo } from "@/beta-kit/shell/app-shell";

const MAX_AUTOMATIC_ATTEMPTS = 6;
const RETRY_DELAY_MS = 3_000;

type Props = {
  code: string;
  message: string;
  requestId?: string;
  retryAutomatically: boolean;
};

export function OnboardingLoadState({
  code,
  message,
  requestId,
  retryAutomatically,
}: Props) {
  const router = useRouter();
  const [attempt, setAttempt] = useState(0);
  const sessionRejected = code === "authentication_required";

  useEffect(() => {
    if (!retryAutomatically || attempt >= MAX_AUTOMATIC_ATTEMPTS) return;

    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    async function waitUntilReady() {
      try {
        const response = await fetch("/api/v1/health", { cache: "no-store" });
        if (response.ok && !cancelled) {
          router.refresh();
          return;
        }
      } catch {
        // A sleeping preview API can terminate the first wake-up request.
      }

      if (!cancelled) {
        retryTimer = setTimeout(() => {
          setAttempt((current) => current + 1);
        }, RETRY_DELAY_MS);
      }
    }

    void waitUntilReady();
    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, [attempt, retryAutomatically, router]);

  const warming = retryAutomatically && attempt < MAX_AUTOMATIC_ATTEMPTS;
  const title = sessionRejected
    ? "Your sign-in session could not be verified."
    : warming
      ? "The learning service is waking up."
      : "Your account could not be loaded.";
  const description = sessionRejected
    ? "Sign out, then continue with Google again to refresh the secure session."
    : warming
      ? "Free preview services sleep when idle. This page will continue automatically when the service is ready."
      : message;

  return (
    <BareShell className="flex items-center justify-center px-5 py-12">
      <main className="flex w-full max-w-lg flex-col gap-5 rounded-2xl border border-ns-line bg-ns-raised p-6 shadow-ns-md lg:p-8">
        <Logo height={28} />
        <Callout tone={sessionRejected ? "danger" : "amber"} icon={AlertCircle}>
          <strong>{title}</strong>
          <span>{description}</span>
          {requestId ? (
            <span className="font-mono text-xs">Request ID: {requestId}</span>
          ) : null}
        </Callout>

        {warming ? (
          <div className="flex items-center gap-2 text-sm text-ns-muted" role="status">
            <LoaderCircle className="animate-spin" size={18} aria-hidden />
            Checking the service…
          </div>
        ) : null}

        <div className="flex flex-wrap gap-3">
          {sessionRejected ? (
            <form action="/auth/signout" method="post">
              <Button type="submit" icon={LogOut}>
                Sign out and try again
              </Button>
            </form>
          ) : (
            <Button onClick={() => router.refresh()} icon={RotateCw}>
              Try again now
            </Button>
          )}
          <Button href="/" variant="secondary">
            Return home
          </Button>
        </div>
      </main>
    </BareShell>
  );
}
