import type { ReactNode } from "react";

/**
 * One entry per previewable screen state. `key` becomes the URL
 * /beta-kit/<key>. `canvas` lists the board names on the design canvas this
 * screen implements, so the design and the code can be compared.
 */
export interface PreviewEntry {
  key: string;
  title: string;
  group: string;
  canvas: string[];
  render: () => ReactNode;
}

export const GROUPS = [
  "Entry",
  "Learn",
  "Lesson",
  "Practice",
  "Checkpoint and recheck",
  "English",
  "Progress, league and me",
  "Celebrations",
  "System states",
] as const;
