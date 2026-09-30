import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { Hornbill } from "./hornbill";

afterEach(cleanup);

describe("Hornbill", () => {
  it("exposes independently animated parts through every mascot instance", () => {
    render(
      <Hornbill
        size={160}
        label="NextScholar hornbill celebrating"
        mood="happy"
        outfit="scarf"
        pose="cheer"
      />,
    );

    const mascot = screen.getByRole("img", {
      name: "NextScholar hornbill celebrating",
    });
    expect(mascot).toHaveAttribute("data-animation", "idle");
    expect(mascot).toHaveAttribute("data-mood", "happy");
    expect(mascot).toHaveAttribute("data-pose", "cheer");
    for (const part of ["tail", "body", "wing", "feet", "head", "beak", "eyes", "accessory"]) {
      expect(mascot.querySelector(`[data-mascot-part="${part}"]`)).toBeInTheDocument();
    }
  });

  it("remains decorative and can be rendered without motion", () => {
    const { container } = render(<Hornbill animated={false} size={48} />);
    const mascot = container.querySelector("svg");

    expect(mascot).toHaveAttribute("aria-hidden", "true");
    expect(mascot).toHaveAttribute("data-animation", "off");
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
