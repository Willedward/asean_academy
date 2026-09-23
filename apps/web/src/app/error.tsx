"use client";

import { Button } from "@/components/ui/button";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-5">
      <h1 className="text-3xl font-black">This page could not be loaded.</h1>
      <p className="text-slate-600">Try the request again. If it still fails, share the request ID shown by the API.</p>
      <div><Button onClick={reset}>Try again</Button></div>
    </main>
  );
}
