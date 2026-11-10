import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { LiveLandingScreen } from "./live-landing";

afterEach(cleanup);

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

  it("keeps feature headings one level below the page heading", () => {
    render(<LiveLandingScreen signInHref="/login" />);

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(
      screen.getByRole("heading", { level: 2, name: "Learn in course order" }),
    ).toBeInTheDocument();
    expect(screen.queryAllByRole("heading", { level: 3 })).toHaveLength(0);
  });
});
