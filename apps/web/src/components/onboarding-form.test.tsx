import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { InvitationAcceptanceResponse } from "@/lib/api/identity";
import { ApiRequestError } from "@/lib/api/errors";

import { OnboardingForm } from "./onboarding-form";

const replace = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, refresh }),
}));

const accepted: InvitationAcceptanceResponse = {
  accepted: true,
  profile: {
    learner_id: "bd9f63f0-87fb-4b2a-a33b-1d58a18a91cf",
    email: "student@example.test",
    display_name: "Student",
    role: "student",
    target_track: "g3-sec1-math",
  },
  enrolments: [
    {
      course_key: "g3-sec1-math",
      course_revision: 1,
      enrolled_at: "2026-09-24T12:00:00Z",
      status: "active",
    },
  ],
};

beforeEach(() => {
  replace.mockReset();
  refresh.mockReset();
});

afterEach(cleanup);

describe("OnboardingForm", () => {
  it("submits the invitation and enters the learner course", async () => {
    const acceptInvitation = vi.fn(async () => accepted);
    render(
      <OnboardingForm
        acceptInvitation={acceptInvitation}
        email="student@example.test"
        initialCode="invitation-code-123"
      />,
    );

    fireEvent.change(screen.getByLabelText("Name shown in the academy"), {
      target: { value: "  Student  " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Join the beta course" }));

    await waitFor(() => {
      expect(acceptInvitation).toHaveBeenCalledWith("invitation-code-123", "Student");
    });
    expect(replace).toHaveBeenCalledWith("/learn");
    expect(refresh).toHaveBeenCalledOnce();
  });

  it("shows a safe backend error with its request ID", async () => {
    const acceptInvitation = vi.fn(async () => {
      throw new ApiRequestError(
        "Sign in with the email address that received this invitation.",
        403,
        "invitation_email_mismatch",
        "request-123",
      );
    });
    render(
      <OnboardingForm
        acceptInvitation={acceptInvitation}
        email="other@example.test"
        initialCode="invitation-code-123"
      />,
    );

    fireEvent.change(screen.getByLabelText("Name shown in the academy"), {
      target: { value: "Student" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Join the beta course" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Sign in with the email address that received this invitation. Request ID: request-123",
    );
    expect(replace).not.toHaveBeenCalled();
  });
});
