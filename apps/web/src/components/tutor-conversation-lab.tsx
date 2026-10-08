"use client";

import { useEffect, useMemo, useState } from "react";

import { TutorContent, type TutorBlock } from "@/components/tutor-content";
import { Button } from "@/components/ui/button";
import { adminRequest } from "@/lib/api/admin-dashboard";
import { ApiRequestError } from "@/lib/api/errors";

type AutomatedCheck = { name: string; passed: boolean; detail: string };
type ConversationTurn = {
  id: string;
  turn_index: number;
  learner_message: string;
  mode: string;
  automated_pass: boolean;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  cost_micros_sgd: number;
  response_blocks: TutorBlock[];
  suggested_replies: string[];
  recommended_next_action?: string;
  automated_checks: AutomatedCheck[];
  provider_error?: string;
};
type Conversation = {
  id: string;
  provider: "synthetic" | "gemini";
  model_name: string;
  prompt_version: string;
  turns: ConversationTurn[];
};

function errorMessage(error: unknown) {
  if (error instanceof ApiRequestError)
    return `${error.message}${error.requestId ? ` Request ID: ${error.requestId}` : ""}`;
  return error instanceof Error
    ? error.message
    : "The conversation request could not be completed.";
}

export function TutorConversationLab({
  caseId,
  initialPrompt,
  geminiConfigured,
  groundingApproved,
}: {
  caseId: string;
  initialPrompt: string;
  geminiConfigured: boolean;
  groundingApproved: boolean;
}) {
  const [conversation, setConversation] = useState<Conversation | null>();
  const [draft, setDraft] = useState(initialPrompt);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let current = true;
    void adminRequest<Conversation | null>(
      `tutor-evaluation/cases/${caseId}/conversations/latest`,
    )
      .then((value) => {
        if (current) setConversation(value);
      })
      .catch((cause: unknown) => {
        if (current) {
          setConversation(null);
          setError(errorMessage(cause));
        }
      });
    return () => {
      current = false;
    };
  }, [caseId, initialPrompt]);

  const totals = useMemo(
    () =>
      conversation?.turns.reduce(
        (sum, turn) => ({
          tokens: sum.tokens + turn.input_tokens + turn.output_tokens,
          cost: sum.cost + turn.cost_micros_sgd,
        }),
        { tokens: 0, cost: 0 },
      ) ?? { tokens: 0, cost: 0 },
    [conversation],
  );

  async function start(provider: "synthetic" | "gemini") {
    setBusy(true);
    setError(undefined);
    try {
      const created = await adminRequest<Conversation>(
        `tutor-evaluation/cases/${caseId}/conversations`,
        { provider, confirm_live: provider === "gemini" },
      );
      setConversation(created);
      setDraft(initialPrompt);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  async function send(message = draft) {
    const cleaned = message.trim();
    if (!conversation || !cleaned) return;
    setBusy(true);
    setError(undefined);
    try {
      await adminRequest(
        `tutor-evaluation/conversations/${conversation.id}/turns`,
        { message: cleaned },
      );
      const refreshed = await adminRequest<Conversation>(
        `tutor-evaluation/conversations/${conversation.id}`,
      );
      setConversation(refreshed);
      setDraft("");
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  const latest = conversation?.turns.at(-1);

  return (
    <section className="space-y-4 rounded-xl border-2 border-teal-100 bg-teal-50/30 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-bold">Multi-turn conversation lab</h3>
          <p className="text-sm text-slate-600">
            Test follow-up questions, conversation memory, mode switching, and
            answer locking against this approved case.
          </p>
          {conversation ? (
            <p className="mt-1 text-xs text-slate-600">
              {conversation.model_name} · {conversation.prompt_version} ·{" "}
              {totals.tokens} tokens · SGD{" "}
              {(totals.cost / 1_000_000).toFixed(4)}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            disabled={busy || !groundingApproved}
            onClick={() => void start("synthetic")}
          >
            New synthetic chat
          </Button>
          <Button
            disabled={busy || !geminiConfigured || !groundingApproved}
            onClick={() => void start("gemini")}
          >
            New Gemini chat
          </Button>
        </div>
      </div>

      {error ? (
        <div
          role="alert"
          className="rounded-lg bg-red-50 p-3 text-sm text-red-800"
        >
          {error}
        </div>
      ) : null}

      {conversation === undefined ? (
        <p className="text-sm text-slate-600">
          Loading the latest conversation…
        </p>
      ) : conversation ? (
        <>
          <div
            aria-label="Tutor conversation transcript"
            className="max-h-[32rem] space-y-4 overflow-auto rounded-xl bg-white p-4"
          >
            {conversation.turns.length ? (
              conversation.turns.map((turn) => (
                <div className="space-y-3" key={turn.id}>
                  <div className="ml-auto max-w-[85%] rounded-2xl rounded-br-sm bg-teal-700 px-4 py-3 text-white">
                    <p className="text-xs font-bold uppercase text-teal-100">
                      Learner
                    </p>
                    <p className="whitespace-pre-wrap">
                      {turn.learner_message}
                    </p>
                  </div>
                  <div className="max-w-[92%] rounded-2xl rounded-bl-sm border bg-slate-50 px-4 py-3">
                    <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
                      <strong>Tutor</strong>
                      <span className="rounded-full bg-white px-2 py-1">
                        {turn.mode.replaceAll("_", " ")}
                      </span>
                      <span
                        className={
                          turn.automated_pass
                            ? "text-green-700"
                            : "text-red-700"
                        }
                      >
                        {turn.automated_pass
                          ? "checks passed"
                          : "checks failed"}
                      </span>
                    </div>
                    {turn.response_blocks.length ? (
                      <TutorContent blocks={turn.response_blocks} />
                    ) : null}
                    {turn.recommended_next_action ? (
                      <p className="mt-3 text-sm">
                        <strong>Next:</strong> {turn.recommended_next_action}
                      </p>
                    ) : null}
                    {turn.provider_error ? (
                      <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-800">
                        {turn.provider_error}
                      </p>
                    ) : null}
                    <details className="mt-3 text-xs text-slate-600">
                      <summary className="cursor-pointer">
                        Evidence · {turn.latency_ms} ms ·{" "}
                        {turn.input_tokens + turn.output_tokens} tokens
                      </summary>
                      <ul className="mt-2 space-y-1">
                        {turn.automated_checks.map((check) => (
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
                    </details>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-600">
                This chat is ready. Send the first learner message below.
              </p>
            )}
          </div>

          {latest?.suggested_replies.length ? (
            <div className="flex flex-wrap gap-2">
              {latest.suggested_replies.map((reply) => (
                <button
                  key={reply}
                  type="button"
                  className="rounded-full border bg-white px-3 py-1 text-xs hover:bg-slate-50"
                  onClick={() => setDraft(reply)}
                >
                  {reply}
                </button>
              ))}
            </div>
          ) : null}

          <div className="flex gap-2">
            <textarea
              aria-label="Learner message"
              className="min-h-20 flex-1 rounded-lg border bg-white p-3"
              maxLength={1200}
              placeholder="Ask why an answer is wrong, request another explanation, or ask for an example…"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
            />
            <Button
              className="self-end"
              disabled={busy || !draft.trim()}
              onClick={() => void send()}
            >
              {busy ? "Sending…" : "Send"}
            </Button>
          </div>
        </>
      ) : (
        <p className="rounded-lg border border-dashed bg-white p-4 text-sm text-slate-600">
          Start a Gemini chat to test the real tutor, or a synthetic chat to
          test the conversation flow without using provider quota.
        </p>
      )}
    </section>
  );
}
