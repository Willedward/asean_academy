import { notFound } from "next/navigation";

import { ENTRIES, findEntry } from "@/beta-kit/preview";

export function generateStaticParams() {
  return ENTRIES.map((entry) => ({ screen: entry.key }));
}

export default async function BetaKitScreen({ params }: { params: Promise<{ screen: string }> }) {
  const { screen } = await params;
  const entry = findEntry(screen);
  if (!entry) notFound();
  return entry.render();
}
