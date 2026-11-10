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

  it("keeps a space between consecutive authored text blocks", () => {
    const { container } = render(
      <p>
        <MathContent
          blocks={[
            { type: "text", text: "Exterior angles total 360°." },
            { type: "text", text: "To find n, divide 360° by one angle." },
            { type: "text", text: " Already spaced." },
          ]}
        />
      </p>,
    );

    expect(container.textContent).toBe(
      "Exterior angles total 360°. To find n, divide 360° by one angle. Already spaced.",
    );
  });

  it("adds no space between text and inline maths", () => {
    const { container } = render(
      <p>
        <MathContent
          blocks={[
            { type: "text", text: "Value (" },
            { type: "inline_math", latex: "x" },
            { type: "text", text: ")." },
          ]}
        />
      </p>,
    );

    const text = container.textContent ?? "";
    expect(text.startsWith("Value (")).toBe(true);
    expect(text.endsWith(").")).toBe(true);
    expect(text).not.toMatch(/\( | \)/);
  });

  it("keeps touching punctuation on the same line as inline maths", () => {
    const { container } = render(
      <p>
        <MathContent
          blocks={[
            { type: "text", text: "Calculate (" },
            { type: "inline_math", latex: "12\\times 8" },
            { type: "text", text: ")." },
            { type: "text", text: "Then compare " },
            { type: "inline_math", latex: "a" },
            { type: "text", text: ", " },
            { type: "inline_math", latex: "b" },
          ]}
        />
      </p>,
    );

    const groups = container.querySelectorAll("span.whitespace-nowrap");
    expect(groups).toHaveLength(2);
    expect(groups[0]!.firstChild?.textContent).toBe("(");
    expect(groups[0]!.lastChild?.textContent).toBe(").");
    expect(groups[1]!.lastChild?.textContent).toBe(",");
    const paragraph = container.querySelector("p")!;
    const plainText = [...paragraph.childNodes]
      .filter((node) => node.nodeType === Node.TEXT_NODE)
      .map((node) => node.textContent)
      .join("|");
    // Each punctuation mark appears once: the text blocks lose what moved.
    expect(plainText).toBe("Calculate | Then compare | ");
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
