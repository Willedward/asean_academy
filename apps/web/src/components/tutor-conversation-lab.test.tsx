import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TutorConversationLab } from "./tutor-conversation-lab";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("TutorConversationLab", () => {
  it("starts a durable chat and sends a follow-up learner message", async () => {
    const empty = {
      id: "conversation-1",
      provider: "gemini",
      model_name: "gemini-test",
      prompt_version: "prompt-v3",
      turns: [],
    };
    const withTurn = {
      ...empty,
      turns: [
        {
          id: "turn-1",
          turn_index: 1,
          learner_message: "Why is my answer wrong?",
          mode: "diagnose_misconception",
          automated_pass: true,
          latency_ms: 250,
          input_tokens: 20,
          output_tokens: 10,
          cost_micros_sgd: 0,
          response_blocks: [
            { type: "text", content: "Which step changed the value?" },
          ],
          suggested_replies: ["I divided both terms."],
          automated_checks: [
            {
              name: "answer_lock",
              passed: true,
              detail: "Answer remained locked.",
            },
          ],
        },
      ],
    };
    let started = false;
    let sent = false;
    const fetcher = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith("/conversations/latest"))
        return new Response(JSON.stringify(null));
      if (url.endsWith("/conversations") && init?.method === "POST") {
        started = true;
        return new Response(JSON.stringify(empty), { status: 201 });
      }
      if (url.endsWith("/turns")) {
        sent = true;
        return new Response(JSON.stringify(withTurn.turns[0]), { status: 201 });
      }
      return new Response(JSON.stringify(withTurn));
    });
    vi.stubGlobal("fetch", fetcher);

    render(
      <TutorConversationLab
        caseId="case-1"
        initialPrompt="Why is my answer wrong?"
        geminiConfigured
        groundingApproved
      />,
    );

    await screen.findByText(/Start a Gemini chat/);
    fireEvent.click(screen.getByRole("button", { name: "New Gemini chat" }));
    await waitFor(() => expect(started).toBe(true));
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await screen.findByText("Which step changed the value?");
    expect(sent).toBe(true);
    expect(screen.getByText("diagnose misconception")).toBeInTheDocument();
    expect(screen.getByText("I divided both terms.")).toBeInTheDocument();
  });
});
