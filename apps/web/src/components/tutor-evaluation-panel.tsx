"use client";

import { useEffect, useMemo, useState } from "react";

import { MathContent, type ContentBlock } from "@/components/math-content";
import { Button } from "@/components/ui/button";
import { adminRequest } from "@/lib/api/admin-dashboard";
import { ApiRequestError } from "@/lib/api/errors";

type Review = {
  id: string;
  dimension: string;
  decision: string;
  notes: string;
  reviewer_email: string;
  created_at: string;
};
type Run = {
  id: string;
  provider: string;
  model_name?: string;
  automated_pass: boolean;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  cost_micros_sgd: number;
  response_blocks: ContentBlock[];
  automated_checks: { name: string; passed: boolean; detail: string }[];
  reviews: Review[];
  created_at: string;
};
type Case = {
  case_id: string;
  title: string;
  question_key?: string;
  difficulty?: number;
  outcome_code?: string;
  mode: string;
  learner_message: string;
  question_title: string;
  question_blocks: { blocks?: ContentBlock[] }[];
  answer_locked: boolean;
  solution_locked: boolean;
  latest_run?: Run;
};
type Lab = {
  suite_id: string;
  suite_version: string;
  description: string;
  case_count: number;
  gemini_configured: boolean;
  gemini_model: string;
  prompt_version: string;
  grounding_gate: {
    review_state: string;
    mathematics_review?: Review;
    editorial_review?: Review;
    blockers: string[];
  };
  cases: Case[];
};

function message(error: unknown) {
  if (error instanceof ApiRequestError)
    return `${error.message}${error.requestId ? ` Request ID: ${error.requestId}` : ""}`;
  return error instanceof Error
    ? error.message
    : "The operation could not be completed.";
}

function latestByDimension(reviews: Review[], dimension: string) {
  return reviews.find((review) => review.dimension === dimension);
}

export function TutorEvaluationPanel({ academic }: { academic: boolean }) {
  const [lab, setLab] = useState<Lab>();
  const [selected, setSelected] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [dimension, setDimension] = useState<"mathematics" | "editorial">(
    academic ? "mathematics" : "editorial",
  );
  const [decision, setDecision] = useState<"approved" | "changes_requested">(
    "approved",
  );
  const [notes, setNotes] = useState("");
  const [scores, setScores] = useState({
    mathematics_correctness: 5,
    pedagogical_quality: 5,
    curriculum_fit: 5,
    safety_and_leakage: 5,
  });

  async function load() {
    try {
      const value = await adminRequest<Lab>("tutor-evaluation");
      setLab(value);
      setSelected((current) => current ?? value.cases[0]?.case_id);
      setError(undefined);
    } catch (cause) {
      setError(message(cause));
    }
  }
  useEffect(() => {
    let current = true;
    void adminRequest<Lab>("tutor-evaluation")
      .then((value) => {
        if (!current) return;
        setLab(value);
        setSelected(value.cases[0]?.case_id);
      })
      .catch((cause: unknown) => {
        if (current) setError(message(cause));
      });
    return () => {
      current = false;
    };
  }, []);
  const active = useMemo(
    () => lab?.cases.find((value) => value.case_id === selected),
    [lab, selected],
  );

  async function run(provider: "synthetic" | "gemini") {
    if (!active) return;
    setBusy(true);
    setError(undefined);
    try {
      await adminRequest(`tutor-evaluation/cases/${active.case_id}/runs`, {
        provider,
        confirm_live: provider === "gemini",
      });
      await load();
    } catch (cause) {
      setError(message(cause));
    } finally {
      setBusy(false);
    }
  }

  async function review() {
    if (!active?.latest_run) return;
    setBusy(true);
    setError(undefined);
    try {
      await adminRequest(
        `tutor-evaluation/runs/${active.latest_run.id}/reviews`,
        { dimension, decision, notes, ...scores },
      );
      setNotes("");
      await load();
    } catch (cause) {
      setError(message(cause));
    } finally {
      setBusy(false);
    }
  }

  if (!lab && !error) return <p>Loading the tutor evaluation lab…</p>;
  return (
    <div className="space-y-6">
      {error ? (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-800"
        >
          {error}
        </div>
      ) : null}
      {lab ? (
        <>
          <section className="grid gap-4 rounded-2xl border bg-white p-5 md:grid-cols-3">
            <div>
              <p className="text-xs font-bold uppercase text-slate-500">
                Suite
              </p>
              <p className="font-bold">{lab.suite_id}</p>
              <p>
                {lab.case_count} cases · version {lab.suite_version}
              </p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-500">
                Grounding gate
              </p>
              <p className="font-bold">
                {lab.grounding_gate.review_state.replaceAll("_", " ")}
              </p>
              <p>
                Math:{" "}
                {lab.grounding_gate.mathematics_review?.decision ?? "pending"} ·
                Editorial:{" "}
                {lab.grounding_gate.editorial_review?.decision ?? "pending"}
              </p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-500">
                Live provider
              </p>
              <p className="font-bold">
                {lab.gemini_configured
                  ? `${lab.gemini_model} ready`
                  : "Gemini key not configured"}
              </p>
              <p>{lab.prompt_version}</p>
            </div>
          </section>
          <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
            <aside className="max-h-[70vh] space-y-2 overflow-auto rounded-2xl border bg-white p-3">
              {lab.cases.map((item) => (
                <button
                  key={item.case_id}
                  type="button"
                  onClick={() => setSelected(item.case_id)}
                  className={`w-full rounded-xl border p-3 text-left ${selected === item.case_id ? "border-teal-700 bg-teal-50" : "bg-white"}`}
                >
                  <span className="block text-xs font-bold uppercase text-teal-700">
                    L{item.difficulty ?? "–"} · {item.outcome_code ?? "–"} ·{" "}
                    {item.mode.replaceAll("_", " ")}
                  </span>
                  <span className="font-bold">{item.title}</span>
                  <span className="block text-xs text-slate-600">
                    {item.latest_run
                      ? `${item.latest_run.provider} · ${item.latest_run.automated_pass ? "checks passed" : "checks failed"}`
                      : "Not run"}
                  </span>
                </button>
              ))}
            </aside>
            {active ? (
              <main className="space-y-5 rounded-2xl border bg-white p-5">
                <div>
                  <p className="text-xs font-bold uppercase text-teal-700">
                    {active.case_id} · {active.question_key}
                  </p>
                  <h2 className="text-2xl font-bold">{active.title}</h2>
                  <p>
                    <strong>Learner prompt:</strong> {active.learner_message}
                  </p>
                  <p className="text-sm">
                    Answer {active.answer_locked ? "locked" : "unlocked"} ·
                    solution {active.solution_locked ? "locked" : "unlocked"}
                  </p>
                </div>
                <section className="rounded-xl bg-slate-50 p-4">
                  <h3 className="font-bold">Question</h3>
                  {active.question_blocks.map((part, index) => (
                    <MathContent key={index} blocks={part.blocks ?? []} />
                  ))}
                </section>
                <div className="flex flex-wrap gap-3">
                  <Button
                    disabled={
                      busy || lab.grounding_gate.review_state !== "approved"
                    }
                    onClick={() => void run("synthetic")}
                  >
                    Run synthetic check
                  </Button>
                  <Button
                    disabled={
                      busy ||
                      !lab.gemini_configured ||
                      lab.grounding_gate.review_state !== "approved"
                    }
                    onClick={() => void run("gemini")}
                  >
                    Run Gemini (uses quota)
                  </Button>
                </div>
                {active.latest_run ? (
                  <>
                    <section className="rounded-xl border p-4">
                      <h3 className="font-bold">Latest AI response</h3>
                      <MathContent blocks={active.latest_run.response_blocks} />
                      <p className="text-sm">
                        {active.latest_run.model_name} ·{" "}
                        {active.latest_run.latency_ms} ms ·{" "}
                        {active.latest_run.input_tokens +
                          active.latest_run.output_tokens}{" "}
                        tokens · SGD{" "}
                        {(
                          active.latest_run.cost_micros_sgd / 1_000_000
                        ).toFixed(4)}
                      </p>
                      <ul className="mt-3 space-y-1">
                        {active.latest_run.automated_checks.map((check) => (
                          <li
                            key={check.name}
                            className={
                              check.passed ? "text-green-700" : "text-red-700"
                            }
                          >
                            {check.passed ? "✓" : "✗"} {check.name}:{" "}
                            {check.detail}
                          </li>
                        ))}
                      </ul>
                    </section>
                    <section className="space-y-3 rounded-xl border p-4">
                      <h3 className="font-bold">Human response review</h3>
                      <p className="text-sm">
                        Mathematics:{" "}
                        {latestByDimension(
                          active.latest_run.reviews,
                          "mathematics",
                        )?.decision ?? "pending"}{" "}
                        · Editorial:{" "}
                        {latestByDimension(
                          active.latest_run.reviews,
                          "editorial",
                        )?.decision ?? "pending"}
                      </p>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <select
                          value={dimension}
                          onChange={(e) =>
                            setDimension(e.target.value as typeof dimension)
                          }
                          disabled={!academic}
                          className="rounded-lg border p-2"
                        >
                          <option value="mathematics">Mathematics</option>
                          <option value="editorial">Editorial</option>
                        </select>
                        <select
                          value={decision}
                          onChange={(e) =>
                            setDecision(e.target.value as typeof decision)
                          }
                          className="rounded-lg border p-2"
                        >
                          <option value="approved">Approve</option>
                          <option value="changes_requested">
                            Request changes
                          </option>
                        </select>
                      </div>
                      <div className="grid gap-2 sm:grid-cols-4">
                        {Object.entries(scores).map(([key, value]) => (
                          <label className="text-xs" key={key}>
                            {key.replaceAll("_", " ")}
                            <select
                              className="mt-1 block w-full rounded border p-2"
                              value={value}
                              onChange={(e) =>
                                setScores((old) => ({
                                  ...old,
                                  [key]: Number(e.target.value),
                                }))
                              }
                            >
                              {[1, 2, 3, 4, 5].map((score) => (
                                <option key={score}>{score}</option>
                              ))}
                            </select>
                          </label>
                        ))}
                      </div>
                      <textarea
                        className="min-h-24 w-full rounded-lg border p-3"
                        placeholder="Record what you checked (minimum 10 characters)"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                      />
                      <Button
                        disabled={busy || notes.trim().length < 10}
                        onClick={() => void review()}
                      >
                        Record response review
                      </Button>
                    </section>
                  </>
                ) : (
                  <p className="rounded-xl border border-dashed p-5">
                    Run this case to create a response for review.
                  </p>
                )}
              </main>
            ) : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
