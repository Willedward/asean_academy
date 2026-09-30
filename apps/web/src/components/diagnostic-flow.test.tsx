import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  DiagnosticNext,
  DiagnosticResult,
  DiagnosticSession,
} from "@/lib/api/diagnostics";

import { DiagnosticLanding } from "./diagnostic-landing";
import { DiagnosticPlayer } from "./diagnostic-player";
import { DiagnosticResultPanel } from "./diagnostic-result";

const push = vi.fn();
const replace = vi.fn();
const router = { push, replace };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

const session: DiagnosticSession = {
  session_id: "69284c2d-018f-4ddb-8935-51918af14954",
  state: "in_progress",
  purpose: "baseline",
  form_key: "n1-baseline-a",
  form_revision: 1,
  title: "N1 baseline readiness check",
  instructions: "Answer every question.",
  estimated_minutes: 20,
  started_at: "2026-09-29T00:00:00Z",
  submitted_at: null,
  items: [
    {
      position: 1,
      outcome_code: "1.1",
      weight: 1,
      saved_answers: null,
      saved_at: null,
      question: {
        stable_key: "n1-diagnostic-a-01",
        revision: 1,
        title: "Prime recognition",
        difficulty: 1,
        calculator_allowed: true,
        stem: [],
        total_marks: 1,
        parts: [
          {
            position: 1,
            label: null,
            prompt: [{ type: "text", text: "Enter the requested number." }],
            marks: 1,
            response_type: "numeric",
            input_placeholder: "Enter your final answer",
          },
        ],
      },
    },
  ],
};

const result: DiagnosticResult = {
  session_id: session.session_id,
  purpose: "baseline",
  form_key: "n1-baseline-a",
  form_revision: 1,
  score: 1,
  max_score: 2,
  percentage: 50,
  band: "on_track",
  band_policy_version: "n1-readiness-v1",
  outcome_scores: [
    { outcome_code: "1.1", score: 1, max_score: 2, percentage: 50 },
  ],
  strengths: [],
  priorities: ["1.1"],
  submitted_at: "2026-09-29T00:20:00Z",
};

afterEach(cleanup);

beforeEach(() => {
  push.mockReset();
  replace.mockReset();
});

describe("diagnostic learner flow", () => {
  it("shows a safe course fallback while reviewed diagnostic content is pending", async () => {
    const pending: DiagnosticNext = {
      status: "content_pending",
      purpose: null,
      session_id: null,
      result_session_id: null,
      title: "Readiness check is being prepared",
      message: "Reviewed diagnostic questions have not been published yet.",
      estimated_minutes: null,
      question_count: null,
    };
    render(
      <DiagnosticLanding
        appearance="nextscholar"
        loadNext={vi.fn().mockResolvedValue(pending)}
      />,
    );
    expect(
      await screen.findByRole("heading", { name: pending.title }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Continue to course" }),
    ).toHaveAttribute("href", "/learn");
  });

  it("starts the API-selected readiness purpose and follows its session id", async () => {
    const available: DiagnosticNext = {
      status: "start",
      purpose: "baseline",
      session_id: null,
      result_session_id: null,
      title: "Start your readiness check",
      message: "Answer the reviewed readiness questions.",
      estimated_minutes: 20,
      question_count: 38,
    };
    const start = vi.fn().mockResolvedValue(session);
    render(
      <DiagnosticLanding
        appearance="nextscholar"
        loadNext={vi.fn().mockResolvedValue(available)}
        start={start}
      />,
    );

    fireEvent.click(
      await screen.findByRole("button", { name: "Start readiness check" }),
    );

    await waitFor(() => expect(start).toHaveBeenCalledWith("baseline"));
    expect(push).toHaveBeenCalledWith(`/diagnostics/${session.session_id}`);
    expect(screen.queryByText(/xp|streak|league/i)).not.toBeInTheDocument();
  });

  it("waits for every multipart answer before autosaving", async () => {
    const baseItem = session.items[0]!;
    const basePart = baseItem.question.parts[0]!;
    const multipart: DiagnosticSession = {
      ...session,
      items: [
        {
          ...baseItem,
          question: {
            ...baseItem.question,
            total_marks: 2,
            parts: [
              {
                ...basePart,
                label: "a",
              },
              {
                ...basePart,
                position: 2,
                label: "b",
                prompt: [{ type: "text", text: "Enter the second number." }],
              },
            ],
          },
        },
      ],
    };
    const api = {
      get: vi.fn().mockResolvedValue(multipart),
      save: vi.fn().mockResolvedValue(undefined),
      submit: vi.fn().mockResolvedValue(result),
    };
    render(
      <DiagnosticPlayer
        api={api}
        appearance="nextscholar"
        sessionId={session.session_id}
      />,
    );

    await screen.findByRole("heading", { name: "Prime recognition" });
    fireEvent.change(screen.getByLabelText(/Part \(a\)/), {
      target: { value: "2" },
    });
    await new Promise((resolve) => window.setTimeout(resolve, 800));
    expect(api.save).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: /Submit readiness check/ }),
    ).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/Part \(b\)/), {
      target: { value: "3" },
    });
    await waitFor(
      () =>
        expect(api.save).toHaveBeenCalledWith(session.session_id, 1, {
          "1": "2",
          "2": "3",
        }),
      { timeout: 2000 },
    );
  });

  it("autosaves without revealing correctness and submits the complete form", async () => {
    const api = {
      get: vi.fn().mockResolvedValue(session),
      save: vi.fn().mockResolvedValue(undefined),
      submit: vi.fn().mockResolvedValue(result),
    };
    render(
      <DiagnosticPlayer
        api={api}
        appearance="nextscholar"
        sessionId={session.session_id}
      />,
    );
    expect(
      await screen.findByRole("heading", { name: "Prime recognition" }),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Your final answer/), {
      target: { value: "17" },
    });
    await waitFor(
      () =>
        expect(api.save).toHaveBeenCalledWith(session.session_id, 1, {
          "1": "17",
        }),
      { timeout: 2000 },
    );
    expect(screen.queryByText(/correct/i)).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /Submit readiness check/ }),
    );
    await waitFor(() =>
      expect(api.submit).toHaveBeenCalledWith(session.session_id),
    );
    expect(push).toHaveBeenCalledWith(
      `/diagnostics/${session.session_id}/result`,
    );
  });

  it("presents supportive outcome evidence after submission", async () => {
    render(
      <DiagnosticResultPanel
        appearance="nextscholar"
        sessionId={session.session_id}
        load={vi.fn().mockResolvedValue(result)}
      />,
    );
    expect(
      await screen.findByRole("heading", { name: "On track" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Outcome 1.1").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/learning evidence to guide your next steps/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/xp|streak/i)).not.toBeInTheDocument();
  });
});
