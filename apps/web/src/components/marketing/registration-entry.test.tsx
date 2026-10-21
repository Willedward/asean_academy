import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RegistrationEntry } from "./registration-entry";

describe("RegistrationEntry", () => {
  it("routes invited students into the existing authentication flow", () => {
    render(<RegistrationEntry />);

    expect(
      screen.getByRole("heading", {
        name: "Register your interest in NextScholar.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "I have an invitation" }),
    ).toHaveAttribute("href", "/login?next=%2Flearn");
    expect(
      screen.getByText(/no email submitted here creates an account/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });
});
