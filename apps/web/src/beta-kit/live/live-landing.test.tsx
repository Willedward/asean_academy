import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LiveLandingScreen } from "./live-landing";

describe("LiveLandingScreen", () => {
  it("describes supported beta learning without sample rewards", () => {
    render(<LiveLandingScreen signInHref="/login" />);

    expect(
      screen.getByRole("heading", {
        name: "Learn the idea. Practise it. Know what to improve next.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Sign in with your invitation" }),
    ).toHaveAttribute("href", "/login");
    expect(screen.queryByText(/\bXP\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/league|streak|badge/i)).not.toBeInTheDocument();
  });
});
