"use client";

import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";

const RETRY_SECONDS = 10;

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [seconds, setSeconds] = useState(RETRY_SECONDS);

  useEffect(() => {
    const interval = window.setInterval(
      () => setSeconds((value) => Math.max(0, value - 1)),
      1_000,
    );
    const retry = window.setTimeout(reset, RETRY_SECONDS * 1_000);
    return () => {
      window.clearInterval(interval);
      window.clearTimeout(retry);
    };
  }, [error.digest, reset]);

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-5">
      <p className="font-semibold uppercase tracking-wide text-teal-700">
        Reconnecting
      </p>
      <h1 className="text-3xl font-black">The learning service is starting.</h1>
      <p className="text-slate-600">
        Our free staging API sleeps after inactivity and can take 50 seconds or
        more to wake. This page will retry automatically in {seconds} seconds.
      </p>
      <div>
        <Button
          onClick={() => {
            setSeconds(RETRY_SECONDS);
            reset();
          }}
        >
          Try now
        </Button>
      </div>
      {error.digest ? (
        <p className="mt-6 text-xs text-slate-500">
          Diagnostic reference: {error.digest}
        </p>
      ) : null}
    </main>
  );
}
