import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

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

  it("shows a neutral fallback when the asset metadata is unavailable", () => {
    render(
      <MathContent blocks={[{ type: "asset_ref", asset_key: "missing" }]} />,
    );

    expect(screen.getByText("[Diagram unavailable]")).toBeInTheDocument();
  });
});
