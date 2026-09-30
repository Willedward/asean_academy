import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AdminDiagnosticReset } from "./admin-diagnostic-reset";

afterEach(cleanup);

describe("AdminDiagnosticReset", () => {
  it("requires an audit reason before resetting an exceptional attempt", async () => {
    const reset = vi.fn(async () => ({
      learner_id: "20000000-0000-4000-8000-000000000001",
      purpose: "baseline" as const,
      reset: true as const,
      reset_at: "2026-09-30T12:00:00Z",
    }));
    const onReset = vi.fn();
    render(
      <AdminDiagnosticReset
        learnerId="20000000-0000-4000-8000-000000000001"
        purpose="baseline"
        reset={reset}
        onReset={onReset}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Review baseline reset" }),
    );
    const confirm = screen.getByRole("button", {
      name: "Confirm diagnostic reset",
    });
    expect(confirm).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Reason for baseline reset"), {
      target: { value: "Attempt invalidated by a verified interruption." },
    });
    fireEvent.click(confirm);

    await waitFor(() =>
      expect(reset).toHaveBeenCalledWith(
        "20000000-0000-4000-8000-000000000001",
        "baseline",
        "Attempt invalidated by a verified interruption.",
      ),
    );
    expect(onReset).toHaveBeenCalledOnce();
  });
});
