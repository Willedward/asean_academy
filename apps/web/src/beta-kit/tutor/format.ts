import { ApiRequestError } from "@/lib/api/errors";
import type { TutorMessageResponse, TutorQuotaResponse } from "@/lib/api/tutor";

import type { TutorChatMessage, TutorNotice } from "./types";

/** The soft "N left today" note appears at this many messages or fewer. */
export const LOW_QUOTA_AT = 3;

export function toChatMessage(message: TutorMessageResponse): TutorChatMessage {
  return {
    id: message.id,
    role: message.role,
    blocks: message.blocks,
    mode: message.mode ?? null,
    safety: message.safety_outcome,
    delivery: message.role === "student" ? "sent" : undefined,
  };
}

/** Quota is only shown near the limit (decision 2026-10-09: no visible counter). */
export function quotaNotice(quota: TutorQuotaResponse | null | undefined): TutorNotice | null {
  if (!quota) return null;
  if (quota.daily_messages_remaining <= 0) return { kind: "out_for_today", resetsAt: quota.resets_at };
  if (quota.daily_messages_remaining <= LOW_QUOTA_AT)
    return { kind: "quota_low", remaining: quota.daily_messages_remaining, resetsAt: quota.resets_at };
  return null;
}

/** What the dock should do with a failed request. Uses code and status, never the message text. */
export type TutorErrorAction =
  | { type: "sign_in" }
  | { type: "disable" }
  | { type: "plan_required" }
  | { type: "forget_session"; notice: TutorNotice }
  | { type: "notice"; notice: TutorNotice };

function detailString(error: unknown, key: string): string | null {
  const details = (error as { details?: Record<string, unknown> | null }).details;
  const value = details?.[key];
  return typeof value === "string" ? value : null;
}

export function errorAction(error: unknown): TutorErrorAction {
  if (!(error instanceof ApiRequestError)) {
    return { type: "notice", notice: { kind: "offline" } };
  }
  const requestId = error.requestId;
  switch (error.code) {
    case "authentication_required":
      return { type: "sign_in" };
    case "active_enrolment_required":
      return { type: "notice", notice: { kind: "enrolment_required" } };
    case "tutor_plan_required":
      return { type: "plan_required" };
    case "tutor_attempt_required":
      return { type: "notice", notice: { kind: "attempt_required" } };
    case "tutor_session_not_found":
      return { type: "forget_session", notice: { kind: "session_expired" } };
    case "tutor_session_closed":
      return { type: "forget_session", notice: { kind: "closed" } };
    case "tutor_grounding_unavailable":
      return { type: "notice", notice: { kind: "unavailable_question" } };
    case "tutor_quota_exceeded":
      return { type: "notice", notice: { kind: "out_for_today", resetsAt: detailString(error, "resets_at") } };
    case "tutor_disabled":
    case "tutor_requires_live_api":
      return { type: "disable" };
    case "tutor_provider_unavailable":
      return { type: "notice", notice: { kind: "offline", requestId } };
  }
  if (error.status === 401) return { type: "sign_in" };
  if (error.status === 429) return { type: "notice", notice: { kind: "rate_limited", requestId } };
  if (error.status === 0 || error.status >= 500) return { type: "notice", notice: { kind: "offline", requestId } };
  return { type: "notice", notice: { kind: "error", message: error.message, requestId } };
}

/**
 * "7:00 tomorrow", "19:30 today" or "Monday at 7:00", in the learner's own time zone.
 * The server's day resets at 00:00 UTC, which is 7:00 in Jakarta.
 */
export function resetLabel(resetsAt: string | null | undefined, now: Date = new Date(), timeZone?: string): string {
  if (!resetsAt) return "tomorrow";
  const at = new Date(resetsAt);
  if (Number.isNaN(at.getTime())) return "tomorrow";
  const time = new Intl.DateTimeFormat("en-GB", { hour: "numeric", minute: "2-digit", timeZone }).format(at);
  const day = (d: Date) => new Intl.DateTimeFormat("en-CA", { year: "numeric", month: "2-digit", day: "2-digit", timeZone }).format(d);
  const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  if (day(at) === day(now)) return `${time} today`;
  if (day(at) === day(tomorrow)) return `${time} tomorrow`;
  const weekday = new Intl.DateTimeFormat("en-GB", { weekday: "long", timeZone }).format(at);
  return `${weekday} at ${time}`;
}

/** Short label shown over some assistant replies. */
export function modeLabel(mode: TutorChatMessage["mode"]): string | null {
  if (mode === "solution_explanation") return "Explaining the solution";
  if (mode === "lesson_recommendation") return "From the lesson";
  if (mode === "analogous_example") return "A smaller example";
  return null;
}

/** Plain text of a learner message, for retrying a failed send. */
export function plainText(message: TutorChatMessage): string {
  return message.blocks.map((block) => block.content).join("");
}
