import { celebrationEntries } from "./celebrations";
import { checkpointEntries } from "./checkpoint";
import { englishEntries } from "./english";
import { entryEntries } from "./entry";
import { learnEntries } from "./learn";
import { lessonEntries } from "./lesson";
import { meEntries } from "./me";
import { practiceEntries } from "./practice";
import type { PreviewEntry } from "./registry";
import { systemEntries } from "./system";

export const ENTRIES: PreviewEntry[] = [
  ...entryEntries,
  ...learnEntries,
  ...lessonEntries,
  ...practiceEntries,
  ...checkpointEntries,
  ...englishEntries,
  ...meEntries,
  ...celebrationEntries,
  ...systemEntries,
];

export function findEntry(key: string) {
  return ENTRIES.find((entry) => entry.key === key);
}
