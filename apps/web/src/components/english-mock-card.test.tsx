import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EnglishMockCard } from "./english-mock-card";

const push = vi.fn();
const listEnglishMocks = vi.fn();
const createEnglishMockSession = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
vi.mock("@/lib/api/english", () => ({
  listEnglishMocks: () => listEnglishMocks(),
  createEnglishMockSession: (purpose: string) =>
    createEnglishMockSession(purpose),
}));

const base = { estimated_minutes: 90, expected_part_count: 38 };

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("EnglishMockCard", () => {
  it("starts an available mock and shows that the next is locked", async () => {
    listEnglishMocks.mockResolvedValue([
      { ...base, purpose: "mock_a", status: "start", title: "Mock A", message: "Ready" },
      { ...base, purpose: "mock_b", status: "locked", title: "Mock B", message: "Complete mock A first." },
    ]);
    createEnglishMockSession.mockResolvedValue({ session_id: "session-1" });

    render(<EnglishMockCard />);
    fireEvent.click(await screen.findByRole("button", { name: "Start mock" }));

    await waitFor(() =>
      expect(push).toHaveBeenCalledWith("/english/diagnostics/session-1"),
    );
    expect(createEnglishMockSession).toHaveBeenCalledWith("mock_a");
    expect(screen.getByText("Locked")).toBeInTheDocument();
  });

  it("links a finished mock to its result", async () => {
    listEnglishMocks.mockResolvedValue([
      { ...base, purpose: "mock_a", status: "completed", title: "Mock A", message: "Done", result_session_id: "done-1" },
    ]);

    render(<EnglishMockCard />);

    expect(await screen.findByRole("link", { name: "View results" })).toHaveAttribute(
      "href",
      "/english/diagnostics/done-1/result",
    );
  });
});
