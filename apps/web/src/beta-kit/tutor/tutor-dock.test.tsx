/**
 * Contract tests from docs/plan/AI_TUTOR_FRONTEND_BACKEND_HANDOFF.md
 * ("Minimum integration tests"), against a mocked Learning API.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { TutorReplyResponse, TutorSessionResponse } from "@/lib/api/tutor";

vi.mock("@/lib/api/tutor", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/tutor")>();
  return {
    ...actual,
    createTutorSession: vi.fn(),
    getTutorSession: vi.fn(),
    sendTutorMessage: vi.fn(),
    closeTutorSession: vi.fn(),
  };
});

import * as api from "@/lib/api/tutor";

import { TutorDock, type TutorDockProps } from "./tutor-dock";

const createTutorSession = vi.mocked(api.createTutorSession);
const getTutorSession = vi.mocked(api.getTutorSession);
const sendTutorMessage = vi.mocked(api.sendTutorMessage);
const closeTutorSession = vi.mocked(api.closeTutorSession);

const PRACTICE = "69284c2d-018f-4ddb-8935-51918af14954";
const SESSION = "6b0f8d0e-1c2b-4d3e-9f40-5a6b7c8d9e0f";

function sessionResponse(overrides: Partial<TutorSessionResponse> = {}): TutorSessionResponse {
  return {
    session_id: SESSION,
    practice_session_id: PRACTICE,
    question_key: "n1-l1-02",
    question_revision: 1,
    status: "active",
    answer_lock_state: { answer_locked: true, solution_locked: true },
    model_policy_version: "v1",
    messages: [],
    created_at: "2026-10-09T02:00:00Z",
    closed_at: null,
    ...overrides,
  };
}

function reply(overrides: Partial<TutorReplyResponse> = {}): TutorReplyResponse {
  return {
    session_id: SESSION,
    response_type: "tutor_reply",
    message: {
      id: "c8a7d3b2-0000-4000-8000-000000000001",
      role: "assistant",
      mode: "diagnose_misconception",
      safety_outcome: "accepted",
      created_at: "2026-10-09T02:01:00Z",
      blocks: [
        { type: "text", content: "For a perfect square every power is even." },
        { type: "inline_math", content: "2^3" },
        { type: "display_math", content: "360 = 2^3 \\times 3^2 \\times 5" },
        { type: "bullets", content: "2 has power 3\n5 has power 1" },
      ],
    },
    suggested_replies: ["I still don't get it", "Show me in the lesson"],
    recommended_next_action: "Try part (b) again",
    answer_lock_state: { answer_locked: true, solution_locked: true },
    quota: { daily_messages_remaining: 9, daily_tokens_remaining: 18000, monthly_cost_remaining_micros_sgd: 6_000_000, resets_at: "2026-10-10T00:00:00Z" },
    ...overrides,
  };
}

const props: TutorDockProps = {
  practiceSessionId: PRACTICE,
  questionKey: "n1-l1-02",
  questionRevision: 1,
  wrongTries: 1,
  questionLabel: "Question 2 · part (b)",
  studentName: "Dimas",
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

async function openTutor() {
  fireEvent.click(screen.getByRole("button", { name: /ask the hornbill/i }));
  await screen.findByRole("dialog", { name: "Hornbill" });
}

async function typeAndSend(text: string) {
  fireEvent.change(screen.getByLabelText("Message the hornbill"), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: "Send" }));
}

beforeEach(() => {
  window.sessionStorage.clear();
  createTutorSession.mockResolvedValue(sessionResponse());
  closeTutorSession.mockResolvedValue(sessionResponse({ status: "closed" }));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("TutorDock", () => {
  it("stays hidden before the first try and in checkpoints", () => {
    const { rerender } = render(<TutorDock {...props} wrongTries={0} />);
    expect(screen.queryByRole("button", { name: /ask the hornbill/i })).toBeNull();
    rerender(<TutorDock {...props} practiceMode="checkpoint" />);
    expect(screen.queryByRole("button", { name: /ask the hornbill/i })).toBeNull();
  });

  it("1. creates a session from the practice-session and question identity", async () => {
    render(<TutorDock {...props} />);
    await openTutor();
    await waitFor(() => expect(createTutorSession).toHaveBeenCalledTimes(1));
    expect(createTutorSession).toHaveBeenCalledWith(
      { practice_session_id: PRACTICE, question_key: "n1-l1-02", question_revision: 1 },
      undefined,
    );
    expect(window.sessionStorage.getItem(`ns-tutor:${PRACTICE}:n1-l1-02:1`)).toBe(SESSION);
  });

  it("2 and 3. sends one message and renders every block type safely", async () => {
    sendTutorMessage.mockResolvedValue(
      reply({
        message: {
          ...reply().message,
          blocks: [
            { type: "text", content: '<img src=x onerror="alert(1)"> is just text' },
            { type: "inline_math", content: "2^3" },
            { type: "display_math", content: "360 = 2^3 \\times 3^2 \\times 5" },
            { type: "bullets", content: "- 2 has power 3\n- 5 has power 1" },
          ],
        },
      }),
    );
    const { container } = render(<TutorDock {...props} />);
    await openTutor();
    await typeAndSend("Why is my answer wrong?");
    await screen.findByText(/is just text/);
    expect(sendTutorMessage).toHaveBeenCalledWith(SESSION, "Why is my answer wrong?", undefined);
    expect(screen.getByText("Why is my answer wrong?")).toBeInTheDocument();
    expect(container.ownerDocument.querySelector("img[src=x]")).toBeNull();
    expect(container.ownerDocument.querySelectorAll(".katex").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("2 has power 3").tagName).toBe("LI");
    expect(screen.getByRole("button", { name: "Show me in the lesson" })).toBeInTheDocument();
    expect(screen.getByText("Try part (b) again")).toBeInTheDocument();
  });

  it("4. never sends twice while a reply is pending", async () => {
    const pending = deferred<TutorReplyResponse>();
    sendTutorMessage.mockReturnValue(pending.promise);
    render(<TutorDock {...props} />);
    await openTutor();
    await waitFor(() => expect(createTutorSession).toHaveBeenCalled());
    await typeAndSend("first");
    await waitFor(() => expect(sendTutorMessage).toHaveBeenCalledTimes(1));
    fireEvent.change(screen.getByLabelText("Message the hornbill"), { target: { value: "second" } });
    fireEvent.keyDown(screen.getByLabelText("Message the hornbill"), { key: "Enter" });
    expect(screen.getByRole("button", { name: "The hornbill is replying" })).toBeDisabled();
    expect(sendTutorMessage).toHaveBeenCalledTimes(1);
    await act(async () => pending.resolve(reply()));
  });

  it("5. restores the server conversation after a refresh", async () => {
    window.sessionStorage.setItem(`ns-tutor:${PRACTICE}:n1-l1-02:1`, SESSION);
    getTutorSession.mockResolvedValue(
      sessionResponse({
        messages: [
          { id: "m1", role: "student", blocks: [{ type: "text", content: "What is the question asking?" }], safety_outcome: "accepted", created_at: "2026-10-09T02:00:00Z" },
          { id: "m2", role: "assistant", mode: "clarify_question", blocks: [{ type: "text", content: "It asks for the smallest k." }], safety_outcome: "accepted", created_at: "2026-10-09T02:00:05Z" },
        ],
      }),
    );
    render(<TutorDock {...props} />);
    await openTutor();
    await screen.findByText("It asks for the smallest k.");
    expect(getTutorSession).toHaveBeenCalledWith(SESSION, undefined);
    expect(createTutorSession).not.toHaveBeenCalled();
  });

  it("6. starts fresh and closes the old session when the question changes", async () => {
    sendTutorMessage.mockResolvedValue(reply());
    const { rerender } = render(<TutorDock {...props} />);
    await openTutor();
    await typeAndSend("Why is my answer wrong?");
    await screen.findByText("For a perfect square every power is even.");
    rerender(<TutorDock {...props} questionKey="n1-l1-03" />);
    await waitFor(() => expect(closeTutorSession).toHaveBeenCalledWith(SESSION, undefined));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByText("For a perfect square every power is even.")).toBeNull();
    expect(window.sessionStorage.getItem(`ns-tutor:${PRACTICE}:n1-l1-02:1`)).toBeNull();
  });

  it("7. hides itself when the tutor is disabled, without breaking the page", async () => {
    createTutorSession.mockRejectedValue(new api.TutorApiError("off", 503, "tutor_disabled"));
    render(
      <div>
        <button type="button">Check answer</button>
        <TutorDock {...props} />
      </div>,
    );
    fireEvent.click(screen.getByRole("button", { name: /ask the hornbill/i }));
    await waitFor(() => expect(screen.queryByRole("button", { name: /ask the hornbill/i })).toBeNull());
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByRole("button", { name: "Check answer" })).toBeEnabled();
  });

  it("8. shows the reset time when the daily allowance is used up", async () => {
    sendTutorMessage.mockRejectedValue(
      new api.TutorApiError("used", 429, "tutor_quota_exceeded", "req_9", { resets_at: "2026-10-10T00:00:00Z" }),
    );
    render(<TutorDock {...props} />);
    await openTutor();
    await waitFor(() => expect(createTutorSession).toHaveBeenCalled());
    await typeAndSend("hello");
    await screen.findByText("That’s all my help for today");
    expect(screen.getByText(/back at/).textContent).toMatch(/(today|tomorrow|on \w+)\.$/);
    expect(screen.queryByLabelText("Message the hornbill")).toBeNull();
  });

  it("shows a soft note when 3 or fewer messages are left", async () => {
    sendTutorMessage.mockResolvedValue(reply({ quota: { ...reply().quota, daily_messages_remaining: 2 } }));
    render(<TutorDock {...props} />);
    await openTutor();
    await typeAndSend("hello");
    await screen.findByText(/2 questions left for the hornbill today/);
  });

  it("9. renders an answer_leakage_blocked reply as a normal, safe reply", async () => {
    sendTutorMessage.mockResolvedValue(
      reply({
        message: {
          ...reply().message,
          safety_outcome: "answer_leakage_blocked",
          blocks: [{ type: "text", content: "I can't give you the answer yet." }],
        },
      }),
    );
    render(<TutorDock {...props} />);
    await openTutor();
    await typeAndSend("just tell me k");
    await screen.findByText("I can't give you the answer yet.");
    expect(screen.getByText("The full answer stays hidden until the solution opens.")).toBeInTheDocument();
  });

  it("only retries a failed send when the learner taps Try again", async () => {
    sendTutorMessage
      .mockRejectedValueOnce(new api.TutorApiError("down", 503, "tutor_provider_unavailable", "req_5"))
      .mockResolvedValueOnce(reply());
    render(<TutorDock {...props} />);
    await openTutor();
    await typeAndSend("What is the question asking?");
    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("req_5")).toBeInTheDocument();
    await new Promise((done) => setTimeout(done, 50));
    expect(sendTutorMessage).toHaveBeenCalledTimes(1);
    fireEvent.click(within(alert).getByRole("button", { name: "Try again" }));
    await screen.findByText("For a perfect square every power is even.");
    expect(sendTutorMessage).toHaveBeenCalledTimes(2);
    expect(screen.getAllByText("What is the question asking?")).toHaveLength(1);
  });

  it("opens the Season pass sheet on the free plan instead of calling the API", () => {
    render(<TutorDock {...props} plan="locked" />);
    fireEvent.click(screen.getByRole("button", { name: /ask the hornbill/i }));
    expect(screen.getByRole("dialog", { name: /get help from the hornbill/i })).toBeInTheDocument();
    expect(createTutorSession).not.toHaveBeenCalled();
  });

  it("10. contains no model provider key or URL", () => {
    const files = [
      ...readdirSync(__dirname).filter((name) => /\.tsx?$/.test(name) && !name.includes(".test.")).map((name) => join(__dirname, name)),
      join(__dirname, "../../lib/api/tutor.ts"),
    ];
    for (const file of files) {
      const source = readFileSync(file, "utf8");
      expect(source, file).not.toMatch(/GEMINI_API_KEY|OPENAI_API_KEY|generativelanguage\.googleapis|api\.openai\.com|anthropic\.com\/v1/i);
    }
  });
});
