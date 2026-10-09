/**
 * Sample conversations for the /beta-kit/tutor previews. Same question as the
 * canvas: 360 = 2³ × 3² × 5, find the smallest k so that 360k is a perfect square.
 * Shapes match TutorMessageResponse / TutorReplyResponse exactly.
 */
import type { ReactNode } from "react";

import type { TutorQuotaResponse } from "@/lib/api/tutor";

import { M, Sup } from "../components/ui";
import type { TutorChatMessage } from "./types";

export const SAMPLE_NOW = new Date("2026-10-09T09:30:00+07:00");
/** Server day resets at 00:00 UTC = 07:00 in Jakarta. */
export const SAMPLE_RESETS_AT = "2026-10-10T00:00:00Z";

export const sampleQuota = (remaining: number): TutorQuotaResponse => ({
  daily_messages_remaining: remaining,
  daily_tokens_remaining: remaining * 2000,
  monthly_cost_remaining_micros_sgd: 6_400_000,
  resets_at: SAMPLE_RESETS_AT,
});

export const sampleSummary: ReactNode = (
  <>
    Smallest <M>
      <i>k</i>
    </M>{" "}
    so that <M>
      360<i>k</i>
    </M>{" "}
    is a perfect square
  </>
);

export const samplePowers: ReactNode = (
  <M>
    <Sup base="2" exp="3" /> × <Sup base="3" exp="2" /> × 5
  </M>
);

const POW = "2^3 \\times 3^2 \\times 5";

export function student(id: string, text: string, delivery: TutorChatMessage["delivery"] = "sent"): TutorChatMessage {
  return { id, role: "student", blocks: [{ type: "text", content: text }], delivery };
}

export const replyWhy: TutorChatMessage = {
  id: "a1",
  role: "assistant",
  mode: "diagnose_misconception",
  safety: "accepted",
  blocks: [
    { type: "text", content: "Nice work on part (a). You found:" },
    { type: "display_math", content: `360 = ${POW}` },
    {
      type: "text",
      content: "For a number to be a perfect square, every power in its prime factors has to be even. Look at yours:",
    },
    { type: "bullets", content: "2 has power 3, odd\n3 has power 2, even\n5 has power 1, odd" },
    { type: "text", content: "Multiplying by 5 fixes the 5. What about the 2?" },
  ],
};

export const replySmaller: TutorChatMessage = {
  id: "a2",
  role: "assistant",
  mode: "analogous_example",
  safety: "accepted",
  blocks: [
    { type: "text", content: "No problem. Let’s try a smaller number first. 36 is a perfect square, because 36 = 6 × 6. In prime factors:" },
    { type: "display_math", content: "36 = 2^2 \\times 3^2" },
    { type: "text", content: "Both powers are even. Now look at 12:" },
    { type: "display_math", content: "12 = 2^2 \\times 3^1" },
    { type: "text", content: "The 3 has an odd power. Multiply 12 by one more 3 and it becomes " },
    { type: "inline_math", content: "2^2 \\times 3^2" },
    { type: "text", content: ", which is 36.\n\nYour turn: in " },
    { type: "inline_math", content: POW },
    { type: "text", content: ", which primes have odd powers?" },
  ],
};

export const replyLocked: TutorChatMessage = {
  id: "a3",
  role: "assistant",
  mode: "socratic_prompt",
  safety: "answer_leakage_blocked",
  blocks: [
    {
      type: "text",
      content:
        "I can’t give you the answer yet. Working it out yourself is what makes it stick, and you are close!\n\nHere’s a nudge instead: you already fixed the 5 by multiplying by 5. Count the 2s in ",
    },
    { type: "inline_math", content: POW },
    { type: "text", content: ". How many more 2s would make that power even?" },
  ],
};

export const replySolution: TutorChatMessage = {
  id: "a4",
  role: "assistant",
  mode: "solution_explanation",
  safety: "accepted",
  blocks: [
    { type: "text", content: "Good question. Two primes have odd powers, not one. Multiplying by 5 only fixes the 5:" },
    { type: "display_math", content: "360 \\times 5 = 2^3 \\times 3^2 \\times 5^2" },
    { type: "text", content: "The 2 still has power 3, so it is not a square yet. One more 2 fixes it. That’s step 4 of the solution:" },
    { type: "display_math", content: "360 \\times 10 = 2^4 \\times 3^2 \\times 5^2 = 60^2" },
    { type: "text", content: "So " },
    { type: "inline_math", content: "k = 2 \\times 5 = 10" },
    { type: "text", content: "." },
  ],
};

export const replyExactly: TutorChatMessage = {
  id: "a5",
  role: "assistant",
  mode: "socratic_prompt",
  safety: "accepted",
  blocks: [
    {
      type: "text",
      content: "Exactly! So which number could you multiply 360 by to make both of those powers even? Try it in part (b).",
    },
  ],
};
