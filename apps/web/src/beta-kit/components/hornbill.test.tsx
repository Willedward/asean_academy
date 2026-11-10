import { readFileSync } from "node:fs";
import { join } from "node:path";

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

  it("stops decorative loops within five seconds (WCAG 2.2.2)", () => {
    const mascotCss = readFileSync(join(__dirname, "hornbill.module.css"), "utf8");
    const themeCss = readFileSync(join(__dirname, "../theme.css"), "utf8");

    expect(mascotCss).not.toMatch(/infinite/);
    const tokens = [...themeCss.matchAll(/--animate-ns-[\w-]+:\s*([^;]+);/g)].map((match) => match[1] ?? "");
    expect(tokens.length).toBeGreaterThan(0);
    for (const token of tokens) {
      expect(token, token).not.toMatch(/infinite/);
      const seconds = Number(/(\d*\.?\d+)s\b/.exec(token)?.[1]);
      const count = Number(/\s(\d+)(?:\s|$)/.exec(token.replace(/cubic-bezier\([^)]*\)/, ""))?.[1] ?? 1);
      expect(seconds * count, token).toBeLessThanOrEqual(5);
    }
    for (const match of mascotCss.matchAll(/animation:\s*hornbill-[\w-]+\s+(\d*\.?\d+)(ms|s)\b[^;]*?\s(\d+)(?:\s+forwards)?;/g)) {
      const seconds = Number(match[1]) / (match[2] === "ms" ? 1000 : 1);
      expect(seconds * Number(match[3]), match[0]).toBeLessThanOrEqual(5);
    }
  });
});
