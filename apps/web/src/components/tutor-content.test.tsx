import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TutorContent } from "./tutor-content";

describe("TutorContent", () => {
  it("renders inline and display mathematics with surrounding tutor prose", () => {
    render(
      <TutorContent
        blocks={[
          {
            type: "text",
            content: "Compare ",
          },
          { type: "inline_math", content: "\\frac{5}{6}:\\frac{7}{9}" },
          { type: "text", content: " in the stated order." },
          { type: "display_math", content: "2.4\\div0.8" },
          {
            type: "bullets",
            content: "- Identify the first mass\n- Identify the second mass",
          },
        ]}
      />,
    );

    expect(screen.getByText(/Compare/)).toBeInTheDocument();
    expect(
      screen.getByLabelText("\\frac{5}{6}:\\frac{7}{9}"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("2.4\\div0.8")).toBeInTheDocument();
    expect(screen.getByText("Identify the first mass")).toBeInTheDocument();
    expect(screen.getByText("Identify the second mass")).toBeInTheDocument();
  });
});
