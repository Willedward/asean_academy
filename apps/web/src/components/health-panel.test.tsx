import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HealthPanel } from "./health-panel";

describe("HealthPanel", () => {
  it("shows the connected foundation state", async () => {
    const loadHealth = vi.fn().mockResolvedValue({
      status: "ok",
      service: "learning-api",
      version: "0.1.0",
      environment: "test",
      request_id: "test-request",
      dependencies: {
        course_content: "draft_placeholders",
        authentication: "planned_stage_4",
        tutor: "disabled",
      },
    });

    render(<HealthPanel loadHealth={loadHealth} />);

    expect(screen.getByText("Checking the learning API")).toBeInTheDocument();
    expect(await screen.findByText("Foundation connected")).toBeInTheDocument();
    expect(loadHealth).toHaveBeenCalledOnce();
  });

  it("shows a useful failure state", async () => {
    render(<HealthPanel loadHealth={() => Promise.reject(new Error("Connection refused"))} />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Connection refused");
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
  });
});
