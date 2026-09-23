"use client";

import { CircleAlert, CircleCheck, LoaderCircle, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getHealth, type HealthResponse } from "@/lib/api/health";

type HealthPanelProps = {
  loadHealth?: () => Promise<HealthResponse>;
};

export function HealthPanel({ loadHealth = getHealth }: HealthPanelProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setHealth(await loadHealth());
    } catch (caught) {
      setHealth(null);
      setError(caught instanceof Error ? caught.message : "The learning API could not be reached.");
    } finally {
      setLoading(false);
    }
  }, [loadHealth]);

  useEffect(() => {
    let active = true;
    void loadHealth()
      .then((result) => {
        if (active) setHealth(result);
      })
      .catch((caught: unknown) => {
        if (active) {
          setHealth(null);
          setError(caught instanceof Error ? caught.message : "The learning API could not be reached.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [loadHealth]);

  if (loading) {
    return (
      <div className="status-card" role="status">
        <LoaderCircle aria-hidden="true" className="size-5 animate-spin text-teal-700" />
        <div>
          <p className="status-title">Checking the learning API</p>
          <p className="status-copy">This normally takes less than a second.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="status-card border-rose-200 bg-rose-50" role="alert">
        <CircleAlert aria-hidden="true" className="size-5 shrink-0 text-rose-700" />
        <div className="grow">
          <p className="status-title text-rose-950">Learning API unavailable</p>
          <p className="status-copy text-rose-800">{error}</p>
        </div>
        <Button variant="outline" onClick={() => void refresh()}>
          <RefreshCw aria-hidden="true" className="mr-2 size-4" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="status-card border-emerald-200 bg-emerald-50" role="status">
      <CircleCheck aria-hidden="true" className="size-5 shrink-0 text-emerald-700" />
      <div>
        <p className="status-title text-emerald-950">Foundation connected</p>
        <p className="status-copy text-emerald-800">
          {health?.service} {health?.version} · lesson content is held as draft placeholders · AI
          tutor disabled
        </p>
      </div>
    </div>
  );
}
