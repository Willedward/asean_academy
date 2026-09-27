import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { UsersPanel, QuestionsPanel, OperationsPanel } from "./admin-dashboard";

afterEach(() => {
  vi.unstubAllGlobals();
});
const user = {
  learner_id: "00000000-0000-4000-8000-000000000001",
  email: "student@example.test",
  display_name: "Student",
  role: "student",
  updated_at: "2026-09-27T00:00:00Z",
  enrolments: [],
};

describe("administrator dashboard", () => {
  it("requires an explicit confirmation before changing a role", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ users: [user], total: 1, limit: 25, offset: 0 }),
        ),
      );
    fetcher.mockImplementation(
      async (_url: string, init: RequestInit) =>
        new Response(
          JSON.stringify(
            init.method === "PATCH"
              ? { ...user, role: "content_admin" }
              : { users: [user], total: 1, limit: 25, offset: 0 },
          ),
        ),
    );
    vi.stubGlobal("fetch", fetcher);
    render(<UsersPanel selfId="another-user" />);
    const role = await screen.findByRole("combobox", {
      name: "Role for student@example.test",
    });
    fireEvent.change(role, { target: { value: "content_admin" } });
    expect(
      fetcher.mock.calls.filter((call) => call[1].method === "PATCH"),
    ).toHaveLength(0);
    fireEvent.click(screen.getByText("Review role change"));
    fireEvent.click(screen.getByText("Confirm role change"));
    await waitFor(() =>
      expect(
        fetcher.mock.calls.filter((call) => call[1].method === "PATCH"),
      ).toHaveLength(1),
    );
  });

  it("does not offer confirmation for a blocked curriculum preview", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async (url: string) =>
          new Response(
            JSON.stringify(
              url.includes("curriculum-preview")
                ? {
                    learner_id: user.learner_id,
                    course_key: "g3-sec1-math",
                    from_revision: 1,
                    target_revision: 2,
                    target_hash: "a".repeat(64),
                    active_sessions: 1,
                    incompatible_lessons: [],
                    allowed: false,
                    blockers: [
                      "Finish active practice/checkpoint sessions before moving.",
                    ],
                  }
                : {
                    users: [
                      {
                        ...user,
                        enrolments: [
                          {
                            course_key: "g3-sec1-math",
                            course_revision: 1,
                            status: "active",
                          },
                        ],
                      },
                    ],
                    total: 1,
                  },
            ),
          ),
      ),
    );
    render(<UsersPanel selfId="another-user" />);
    fireEvent.click(await screen.findByText("Preview course update"));
    await screen.findByText(
      "Finish active practice/checkpoint sessions before moving.",
    );
    expect(screen.queryByText("Confirm course update")).not.toBeInTheDocument();
  });

  it("sends difficulty and outcome filters to the backend", async () => {
    const fetcher = vi.fn(
      async () =>
        new Response(
          JSON.stringify({ questions: [], total: 0, limit: 25, offset: 0 }),
        ),
    );
    vi.stubGlobal("fetch", fetcher);
    render(<QuestionsPanel />);
    fireEvent.change(screen.getByLabelText("Difficulty"), {
      target: { value: "2" },
    });
    fireEvent.change(screen.getByLabelText("Outcome"), {
      target: { value: "1.1" },
    });
    fireEvent.click(screen.getByText("Apply filters"));
    await waitFor(() =>
      expect(fetcher).toHaveBeenCalledWith(
        expect.stringContaining("difficulty=2&outcome=1.1"),
        expect.anything(),
      ),
    );
  });

  it("shows actionable content errors independently of system status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              error: {
                code: "content_out_of_sync",
                message: "Import required",
                request_id: "req-123",
              },
            }),
            { status: 503 },
          ),
      ),
    );
    render(<OperationsPanel />);
    await waitFor(() =>
      expect(
        screen.getAllByText("Import required Request ID: req-123"),
      ).toHaveLength(2),
    );
  });
});
