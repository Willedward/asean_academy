import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MarketingLanding } from "./marketing-landing";

describe("MarketingLanding", () => {
  it("connects public product information to registration and sign-in", () => {
    render(
      <MarketingLanding
        signInHref="/login?next=%2Flearn"
        registerHref="/register"
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: "Build the skills to face the test with confidence.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Marketing" }),
    ).toBeInTheDocument();
    const registrationCallsToAction = screen.getAllByRole("link", {
      name: /register/i,
    });
    expect(registrationCallsToAction).toHaveLength(4);
    for (const link of registrationCallsToAction) {
      expect(link).toHaveAttribute("href", "/register");
    }
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/login?next=%2Flearn",
    );
    expect(
      screen.getByText("Mathematics and English in Layer 1"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not claim to reproduce confidential papers/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/guaranteed|raise.*grade|improve.*score/i),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("No public testimonial has been approved yet.", {
        exact: false,
      }),
    ).toBeInTheDocument();
  });
});
