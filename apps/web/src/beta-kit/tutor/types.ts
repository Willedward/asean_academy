import type {
  TutorBlock,
  TutorMessageResponse,
  TutorMode,
} from "@/lib/api/tutor";

export type { TutorBlock, TutorMode };

/** One bubble in the chat. Built from TutorMessageResponse, or locally for the learner's own message while it sends. */
export interface TutorChatMessage {
  id: string;
  role: TutorMessageResponse["role"];
  blocks: TutorBlock[];
  /** API: TutorMessageResponse.mode (assistant only). */
  mode?: TutorMode | null;
  /** API: TutorMessageResponse.safety_outcome (assistant only). Never inferred from the text. */
  safety?: TutorMessageResponse["safety_outcome"];
  /** Learner messages only: still sending, or sent but no reply came back. */
  delivery?: "sending" | "sent" | "failed";
}

/**
 * Something the tutor needs to tell the learner instead of (or as well as) a reply.
 * Built from the server's quota and error codes in `format.ts`.
 */
export type TutorNotice =
  | { kind: "quota_low"; remaining: number; resetsAt: string }
  | { kind: "out_for_today"; resetsAt: string | null }
  | { kind: "offline"; requestId?: string }
  | { kind: "rate_limited"; requestId?: string }
  | { kind: "session_expired" }
  | { kind: "closed" }
  | { kind: "unavailable_question" }
  | { kind: "enrolment_required" }
  | { kind: "attempt_required" }
  | { kind: "error"; message: string; requestId?: string };

/**
 * How the "Ask the hornbill" entry point shows.
 * hidden: before the first try, in checkpoints, or when the tutor is switched off.
 * locked: free plan, opens the Season pass sheet.
 */
export type TutorLaunchState = "hidden" | "available" | "locked";

/** Reasons offered in "Report this reply". */
export type TutorReportReason = "maths_wrong" | "gave_away_answer" | "confusing" | "other";

export const REPORT_REASONS: { value: TutorReportReason; label: string }[] = [
  { value: "maths_wrong", label: "The maths is wrong" },
  { value: "gave_away_answer", label: "It gave away the answer" },
  { value: "confusing", label: "It was confusing" },
  { value: "other", label: "Something else" },
];

/** Starter questions shown before the first message. Sent as ordinary learner text. */
export const STARTER_QUESTIONS = [
  { text: "Why is my answer wrong?", icon: "alert" },
  { text: "What is the question asking?", icon: "search" },
  { text: "Show me a smaller example", icon: "layers" },
] as const;
