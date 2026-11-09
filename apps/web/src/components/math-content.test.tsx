import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MathContent } from "./math-content";

describe("MathContent", () => {
  it("renders an authenticated authored diagram with its alt text", () => {
    render(
      <MathContent
        assets={[
          {
            asset_key: "similar-triangles",
            alt_text: "Two similar triangles with corresponding sides marked.",
            width: 940,
            height: 390,
          },
        ]}
        assetScope={{ kind: "lesson", stableKey: "g2-lesson-03" }}
        blocks={[{ type: "asset_ref", asset_key: "similar-triangles" }]}
      />,
    );

    const diagram = screen.getByRole("img", {
      name: "Two similar triangles with corresponding sides marked.",
    });
    expect(diagram).toHaveAttribute(
      "src",
      "/api/v1/content-assets/lesson/g2-lesson-03/similar-triangles",
    );
    expect(diagram).toHaveAttribute("width", "940");
    expect(diagram).toHaveAttribute("height", "390");
  });

  it("leaves KaTeX's MathML to name the maths", () => {
    const { container } = render(
      <MathContent
        blocks={[
          { type: "inline_math", latex: "x+1" },
          { type: "display_math", latex: "y=2" },
        ]}
      />,
    );

    expect(container.querySelector("[aria-label]")).toBeNull();
    expect(container.querySelectorAll("math")).toHaveLength(2);
  });

  it("makes an over-wide display equation a named keyboard scroll stop", () => {
    const scrollWidth = vi
      .spyOn(HTMLElement.prototype, "scrollWidth", "get")
      .mockReturnValue(500);
    render(<MathContent blocks={[{ type: "display_math", latex: "y=2" }]} />);

    const region = screen.getByRole("group", {
      name: "Equation, scrolls sideways",
    });
    expect(region).toHaveAttribute("tabindex", "0");
    scrollWidth.mockRestore();
  });

  it("shows a neutral fallback when the asset metadata is unavailable", () => {
    render(
      <MathContent blocks={[{ type: "asset_ref", asset_key: "missing" }]} />,
    );

    expect(screen.getByText("[Diagram unavailable]")).toBeInTheDocument();
  });
});
