import { describe, expect, it } from "vitest";

import { TutorApiError } from "@/lib/api/tutor";

import { errorAction, quotaNotice, resetLabel } from "./format";

const quota = (remaining: number) => ({
  daily_messages_remaining: remaining,
  daily_tokens_remaining: 1000,
  monthly_cost_remaining_micros_sgd: 1000,
  resets_at: "2026-10-10T00:00:00Z",
});

const err = (status: number, code: string, details: Record<string, unknown> | null = null) =>
  new TutorApiError("message text is never parsed", status, code, "req_1", details);

describe("tutor quota", () => {
  it("stays hidden until 3 or fewer messages are left", () => {
    expect(quotaNotice(quota(10))).toBeNull();
    expect(quotaNotice(quota(4))).toBeNull();
    expect(quotaNotice(quota(3))).toMatchObject({ kind: "quota_low", remaining: 3 });
    expect(quotaNotice(quota(0))).toMatchObject({ kind: "out_for_today", resetsAt: "2026-10-10T00:00:00Z" });
  });

  it("names the reset time in the learner's time zone", () => {
    const now = new Date("2026-10-09T09:30:00+07:00");
    expect(resetLabel("2026-10-10T00:00:00Z", now, "Asia/Jakarta")).toBe("7:00 tomorrow");
    expect(resetLabel("2026-10-09T12:30:00Z", now, "Asia/Jakarta")).toBe("19:30 today");
    expect(resetLabel("2026-10-12T00:00:00Z", now, "Asia/Jakarta")).toBe("7:00 on Monday");
    expect(resetLabel(null, now, "Asia/Jakarta")).toBe("tomorrow");
  });
});

describe("tutor error handling", () => {
  it.each([
    [401, "authentication_required", { type: "sign_in" }],
    [403, "active_enrolment_required", { type: "notice", notice: { kind: "enrolment_required" } }],
    [404, "tutor_session_not_found", { type: "forget_session", notice: { kind: "session_expired" } }],
    [409, "tutor_session_closed", { type: "forget_session", notice: { kind: "closed" } }],
    [409, "tutor_grounding_unavailable", { type: "notice", notice: { kind: "unavailable_question" } }],
    [429, "rate_limited", { type: "notice", notice: { kind: "rate_limited", requestId: "req_1" } }],
    [503, "tutor_disabled", { type: "disable" }],
    [503, "tutor_provider_unavailable", { type: "notice", notice: { kind: "offline", requestId: "req_1" } }],
  ])("%i %s", (status, code, expected) => {
    expect(errorAction(err(status, code))).toEqual(expected);
  });

  it("shows the reset time from a quota error", () => {
    expect(errorAction(err(429, "tutor_quota_exceeded", { resets_at: "2026-10-10T00:00:00Z" }))).toEqual({
      type: "notice",
      notice: { kind: "out_for_today", resetsAt: "2026-10-10T00:00:00Z" },
    });
  });
});
