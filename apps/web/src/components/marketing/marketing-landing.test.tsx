import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MarketingLanding } from "./marketing-landing";

describe("MarketingLanding", () => {
  it("connects public product information to the existing invitation sign-in flow", () => {
    render(<MarketingLanding signInHref="/login?next=%2Flearn" />);

    expect(
      screen.getByRole("heading", {
        name: "Build the skills to face the test with confidence.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Marketing" }),
    ).toBeInTheDocument();
    const callsToAction = screen.getAllByRole("link", {
      name: /join the beta|start with an invitation|use your invitation|sign in to nextscholar/i,
    });
    expect(callsToAction).toHaveLength(4);
    for (const link of callsToAction) {
      expect(link).toHaveAttribute("href", "/login?next=%2Flearn");
    }
    expect(
      screen.getByText("Mathematics and English in Layer 1"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not claim to reproduce confidential papers/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/guaranteed|raise.*grade|improve.*score/i),
    ).not.toBeInTheDocument();
  });
});
