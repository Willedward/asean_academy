"use client";

import { ArrowRight, CircleAlert, RefreshCw, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  getLearningHome,
  type LearningHomeResponse,
} from "@/lib/api/progress";

export function LearningHomePanel({
  loadLearningHome = getLearningHome,
}: {
  loadLearningHome?: () => Promise<LearningHomeResponse>;
}) {
  const [home, setHome] = useState<LearningHomeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    void loadLearningHome()
      .then((response) => {
        if (active) {
          setHome(response);
          setError(null);
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Your next activity could not be loaded.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [loadLearningHome, reload]);

  if (error) {
    return (
      <div className="status-card border-rose-200 bg-rose-50" role="alert">
        <CircleAlert aria-hidden="true" className="size-5 text-rose-700" />
        <div className="grow">
          <p className="status-title">Recommendation unavailable</p>
          <p className="status-copy">{error}</p>
        </div>
        <Button
          onClick={() => {
            setError(null);
            setReload((value) => value + 1);
          }}
          variant="outline"
        >
          <RefreshCw aria-hidden="true" className="mr-2 size-4" />
          Retry
        </Button>
      </div>
    );
  }

  if (!home) {
    return <div className="status-card animate-pulse" role="status">Loading your next activity…</div>;
  }

  return (
    <section className="rounded-3xl bg-teal-900 p-6 text-white shadow-lg" aria-labelledby="next-action-title">
      <div className="flex flex-wrap items-center justify-between gap-5">
        <div className="max-w-2xl">
          <p className="mb-2 inline-flex items-center gap-2 text-sm font-bold uppercase tracking-wide text-teal-200">
            <Sparkles aria-hidden="true" className="size-4" />
            Recommended next
          </p>
          <h2 className="m-0 text-2xl font-black" id="next-action-title">
            {home.next_action.title}
          </h2>
          <p className="mb-0 mt-2 leading-7 text-teal-50">
            {home.next_action.description}
          </p>
          {home.unresolved_retry_count > 0 ? (
            <p className="mb-0 mt-3 text-sm font-semibold text-amber-200">
              {home.unresolved_retry_count} question{home.unresolved_retry_count === 1 ? "" : "s"} still need a successful retry.
            </p>
          ) : null}
        </div>
        <Button asChild className="bg-white text-teal-900 hover:bg-teal-50">
          <Link href={home.next_action.href}>
            Continue
            <ArrowRight aria-hidden="true" className="ml-2 size-4" />
          </Link>
        </Button>
      </div>
    </section>
  );
}
