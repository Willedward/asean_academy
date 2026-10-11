/**
 * Readiness check: Learning API responses to kit view models.
 * Uses William's existing diagnostic contracts; nothing here invents fields.
 */
import type { components } from "@/lib/api/schema";

import type { ReadinessBand, ReadinessOutcome, ReadinessResultData } from "./screens/readiness";
import type { Href } from "./types";

type DiagnosticResult = components["schemas"]["DiagnosticResultResponse"];
type DiagnosticNext = components["schemas"]["DiagnosticNextResponse"];

const SUMMARY: Record<ReadinessBand, string> = {
  getting_started: "This is where your course begins. Every lesson builds from here, one step at a time.",
  on_track: "You already have a solid base. A few topics need practice before the test.",
  ahead: "You’re ahead of where most students start. The lessons will stretch you further.",
};

/** Outcome titles come from the course map (CourseLessonMap outcomes); unknown codes fall back to "Outcome 1.5". */
export type OutcomeTitles = Record<string, string>;

function outcome(code: string, result: DiagnosticResult, titles: OutcomeTitles): ReadinessOutcome {
  const score = result.outcome_scores.find((row) => row.outcome_code === code);
  return { code, title: titles[code] ?? `Outcome ${code}`, score: score?.score ?? 0, max: score?.max_score ?? 0 };
}

export function readinessFromResult(
  result: DiagnosticResult,
  titles: OutcomeTitles,
  options: { dateLabel: string; start: { label: string; href: Href }; reward?: ReadinessResultData["reward"] },
): ReadinessResultData {
  return {
    purpose: result.purpose,
    band: result.band,
    score: result.score,
    max: result.max_score,
    dateLabel: options.dateLabel,
    strengths: result.strengths.map((code) => outcome(code, result, titles)),
    focus: result.priorities.slice(0, 3).map((code) => outcome(code, result, titles)),
    outcomes: result.outcome_scores.map((row) => outcome(row.outcome_code, result, titles)),
    summary: SUMMARY[result.band],
    reward: options.reward,
    start: options.start,
  };
}

/** Pairs the starting and end-of-beta results outcome by outcome for the comparison screen. */
export function compareOutcomes(start: DiagnosticResult, now: DiagnosticResult, titles: OutcomeTitles): ReadinessOutcome[] {
  return start.outcome_scores.map((row) => {
    const after = now.outcome_scores.find((other) => other.outcome_code === row.outcome_code);
    return {
      code: row.outcome_code,
      title: titles[row.outcome_code] ?? `Outcome ${row.outcome_code}`,
      score: row.score,
      max: row.max_score,
      after: after?.score ?? 0,
    };
  });
}

/** Which dashboard card to show, from GET /diagnostics/next. Null: nothing to prompt. */
export function readinessCardKind(next: DiagnosticNext): "baseline" | "resume" | "endline" | "pending" | null {
  switch (next.status) {
    case "start":
      return next.purpose === "endline" ? "endline" : "baseline";
    case "resume":
      return "resume";
    case "content_pending":
      return "pending";
    case "baseline_complete":
    case "completed":
      return null;
  }
}
