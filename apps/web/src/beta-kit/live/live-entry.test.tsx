import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  LiveOnboardingFormView,
  LiveOnboardingShell,
  LiveSignInScreen,
} from "./live-entry";

afterEach(cleanup);

describe("live entry screens", () => {
  it("submits the safe destination through the Google sign-in action", () => {
    const action = vi.fn(async () => undefined);
    const { container } = render(
      <LiveSignInScreen
        configured
        error={null}
        googleAction={action}
        next="/onboarding?code=invite-token"
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Sign in to NextScholar" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Continue with Google" }),
    ).toBeInTheDocument();
    expect(container.querySelector('input[name="next"]')).toHaveValue(
      "/onboarding?code=invite-token",
    );
    expect(screen.queryByText(/\bXP\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/streak/i)).not.toBeInTheDocument();
  });

  it("shows an honest unavailable state when hosted authentication is absent", () => {
    render(
      <LiveSignInScreen
        configured={false}
        error={null}
        googleAction={vi.fn()}
        next="/onboarding"
      />,
    );

    expect(
      screen.getByText("Hosted authentication is not configured."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Continue with Google" }),
    ).not.toBeInTheDocument();
  });

  it("uses a POST action when switching the signed-in Google account", () => {
    render(
      <LiveOnboardingShell>
        <p>Onboarding form</p>
      </LiveOnboardingShell>,
    );

    const switchButtons = screen.getAllByRole("button", {
      name: "Sign out and use another account",
    });
    expect(switchButtons).toHaveLength(2);
    switchButtons.forEach((switchButton) => {
      expect(switchButton.closest("form")).toHaveAttribute(
        "action",
        "/auth/signout",
      );
      expect(switchButton.closest("form")).toHaveAttribute("method", "post");
    });
  });

  it("gives onboarding a single h1 for the activation form", () => {
    render(
      <LiveOnboardingShell>
        <LiveOnboardingFormView
          codeFromLink={false}
          displayName=""
          email="student@example.com"
          error={null}
          invitationCode=""
          onDisplayNameChange={vi.fn()}
          onInvitationCodeChange={vi.fn()}
          onSubmit={vi.fn()}
          submitting={false}
        />
      </LiveOnboardingShell>,
    );

    const headings = screen.getAllByRole("heading", { level: 1 });
    expect(headings).toHaveLength(1);
    expect(headings[0]).toHaveTextContent("Activate student access");
    expect(screen.getByText("Welcome to the beta.").tagName).toBe("P");
  });

  it("keeps static callouts out of live regions and does not nest them in the alert", () => {
    render(
      <LiveSignInScreen
        configured
        error="This Google account has no invitation."
        googleAction={vi.fn()}
        next="/onboarding"
      />,
    );

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("This Google account has no invitation.");
    expect(within(alert).queryByRole("status")).not.toBeInTheDocument();
    expect(screen.queryAllByRole("status")).toHaveLength(0);
    expect(screen.getByText("Invitation-bound access")).toBeInTheDocument();
  });
});
