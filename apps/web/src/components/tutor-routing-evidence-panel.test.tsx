import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError } from "@/lib/api/errors";

import { TutorRoutingEvidencePanel } from "./tutor-routing-evidence-panel";

const { adminRequestMock } = vi.hoisted(() => ({
  adminRequestMock: vi.fn(),
}));

vi.mock("@/lib/api/admin-dashboard", () => ({
  adminRequest: adminRequestMock,
}));

const status = {
  configured_mode: "shadow",
  resolved_mode: "shadow",
  cohort: "admins",
  policy_version: "math-tutor-routing-v1",
  schema_revision: "202610100024",
  economy_provider: "gemini",
  economy_model: "gemini-3.5-flash-lite",
  premium_provider: "openai",
  premium_model: "gpt-4o",
};

const usage = {
  usage_month: "2026-10",
  learners: 3,
  actual_requests: 12,
  failed_requests: 1,
  input_tokens: 10_000,
  output_tokens: 2_000,
  actual_cost_micros_sgd: 15_000,
  reserved_cost_micros_sgd: 2_000,
  active_reservations: 1,
  route_decisions: 10,
  shadow_route_decisions: 10,
  shadow_premium_executions: 0,
  recommended_premium_routes: 2,
  executed_premium_routes: 0,
  projected_recommended_cost_micros_sgd: 25_000,
};

const decision = {
  decision_id: "11111111-1111-4111-8111-111111111111",
  created_at: "2026-10-09T01:02:03Z",
  policy_version: "math-tutor-routing-v1",
  routing_mode: "shadow",
  tutor_mode: "alternative_explanation",
  question_difficulty: 4,
  route_score: 7,
  reason_codes: ["high_difficulty", "repeated_confusion"],
  recommended_tier: "premium",
  recommended_provider: "openai",
  recommended_model: "gpt-4o",
  executed_tier: "economy",
  executed_provider: "gemini",
  executed_model: "gemini-3.5-flash-lite",
  reservation_status: "reconciled",
  actual_input_tokens: 800,
  actual_output_tokens: 200,
  actual_cost_micros_sgd: 1_000,
  projected_recommended_cost_micros_sgd: 8_000,
  latency_ms: 900,
  safety_outcome: "accepted",
};

function mockSuccess(items = [decision], nextCursor: string | null = null) {
  adminRequestMock.mockImplementation(async (path: string) => {
    if (path === "tutor-routing/status") return status;
    if (path.startsWith("tutor-usage?")) return usage;
    if (path.startsWith("tutor-routing/decisions?")) {
      return { usage_month: "2026-10", items, next_cursor: nextCursor };
    }
    throw new Error(`Unexpected request: ${path}`);
  });
}

afterEach(() => {
  cleanup();
  adminRequestMock.mockReset();
});

describe("TutorRoutingEvidencePanel", () => {
  it("renders status, server aggregates and decision evidence", async () => {
    mockSuccess();

    render(<TutorRoutingEvidencePanel />);

    expect(
      await screen.findByText("Shadow premium executions: 0"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("math-tutor-routing-v1")).toHaveLength(2);
    expect(screen.getByText("20.0% of route decisions")).toBeInTheDocument();
    expect(screen.getByTitle("15,000 micro-SGD")).toBeInTheDocument();
    expect(
      screen.getAllByText("alternative explanation").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("high_difficulty")).toBeInTheDocument();
    expect(screen.getAllByText(/gpt-4o/).length).toBeGreaterThan(0);
  });

  it("shows an empty state and sends filters to the server", async () => {
    mockSuccess([]);
    render(<TutorRoutingEvidencePanel />);

    expect(
      await screen.findByText("No routing decisions found"),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Recommended tier"), {
      target: { value: "premium" },
    });

    await waitFor(() =>
      expect(adminRequestMock).toHaveBeenCalledWith(
        expect.stringContaining("recommended_tier=premium"),
      ),
    );
  });

  it("appends the next cursor page", async () => {
    const secondDecision = {
      ...decision,
      decision_id: "22222222-2222-4222-8222-222222222222",
      tutor_mode: "lesson_recommendation",
    };
    adminRequestMock.mockImplementation(async (path: string) => {
      if (path === "tutor-routing/status") return status;
      if (path.startsWith("tutor-usage?")) return usage;
      if (path.includes("cursor=next-page")) {
        return {
          usage_month: "2026-10",
          items: [secondDecision],
          next_cursor: null,
        };
      }
      return {
        usage_month: "2026-10",
        items: [decision],
        next_cursor: "next-page",
      };
    });
    render(<TutorRoutingEvidencePanel />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Load more decisions" }),
    );

    expect(
      await screen.findByText("lesson recommendation"),
    ).toBeInTheDocument();
    expect(adminRequestMock).toHaveBeenCalledWith(
      expect.stringContaining("cursor=next-page"),
    );
  });

  it("explains an unavailable learning service and supports retry", async () => {
    adminRequestMock.mockRejectedValue(
      new ApiRequestError(
        "Learning API returned 503.",
        503,
        "unavailable",
        "request-1",
      ),
    );
    render(<TutorRoutingEvidencePanel />);

    expect(
      (await screen.findAllByText("The learning service is unavailable"))
        .length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Render cold start/).length).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("button", { name: "Retry evidence" }).length,
    ).toBeGreaterThan(0);
  });

  it("identifies an API that has not deployed the routing evidence schema", async () => {
    adminRequestMock.mockImplementation(async (path: string) => {
      if (path === "tutor-routing/status") return status;
      if (path.startsWith("tutor-usage?")) {
        const { shadow_premium_executions: omitted, ...oldUsage } = usage;
        void omitted;
        return oldUsage;
      }
      return { usage_month: "2026-10", items: [], next_cursor: null };
    });

    render(<TutorRoutingEvidencePanel />);

    expect(
      await screen.findByText("Routing evidence is not ready"),
    ).toBeInTheDocument();
    expect(screen.getByText(/required database migration/)).toBeInTheDocument();
  });

  it("raises an alert when a shadow decision executed premium", async () => {
    mockSuccess();
    adminRequestMock.mockImplementation(async (path: string) => {
      if (path === "tutor-routing/status") return status;
      if (path.startsWith("tutor-usage?")) {
        return { ...usage, shadow_premium_executions: 1 };
      }
      return { usage_month: "2026-10", items: [], next_cursor: null };
    });

    render(<TutorRoutingEvidencePanel />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Shadow premium executions: 1");
    expect(alert).toHaveTextContent("Stop the evidence run");
  });
});
