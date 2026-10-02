import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { OnboardingLoadState } from "./onboarding-load-state";

const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

beforeEach(() => {
  refresh.mockReset();
});

afterEach(cleanup);

describe("OnboardingLoadState", () => {
  it("shows the request ID and lets the learner retry", () => {
    render(
      <OnboardingLoadState
        code="learning_api_error"
        message="The learner account could not be loaded."
        requestId="request-123"
        retryAutomatically={false}
      />,
    );

    expect(screen.getByText("Request ID: request-123")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Try again now" }));
    expect(refresh).toHaveBeenCalledOnce();
  });

  it("directs an expired session through sign-out", () => {
    render(
      <OnboardingLoadState
        code="authentication_required"
        message="Sign in before using the learning application."
        retryAutomatically={false}
      />,
    );

    expect(
      screen.getByText("Your sign-in session could not be verified."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Sign out and try again" }),
    ).toHaveAttribute("type", "submit");
  });
});
