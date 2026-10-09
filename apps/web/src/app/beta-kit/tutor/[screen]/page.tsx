import { notFound } from "next/navigation";

import { findTutorEntry, tutorEntries } from "@/beta-kit/tutor/preview";

export function generateStaticParams() {
  return tutorEntries.map((entry) => ({ screen: entry.key }));
}

export default async function TutorKitScreen({ params }: { params: Promise<{ screen: string }> }) {
  const { screen } = await params;
  const entry = findTutorEntry(screen);
  if (!entry) notFound();
  return entry.render();
}
