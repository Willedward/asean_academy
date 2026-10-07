import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TutorContent } from "./tutor-content";

describe("TutorContent", () => {
  it("renders text, display mathematics, and bullet response blocks", () => {
    render(
      <TutorContent
        blocks={[
          {
            type: "text",
            content: "Compare the two masses in the stated order.",
          },
          { type: "display_math", content: "2.4\\div0.8" },
          {
            type: "bullets",
            content: "- Identify the first mass\n- Identify the second mass",
          },
        ]}
      />,
    );

    expect(
      screen.getByText("Compare the two masses in the stated order."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("2.4\\div0.8")).toBeInTheDocument();
    expect(screen.getByText("Identify the first mass")).toBeInTheDocument();
    expect(screen.getByText("Identify the second mass")).toBeInTheDocument();
  });
});
