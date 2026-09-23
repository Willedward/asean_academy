import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { courseMapFixture } from "@/lib/api/course";

import { CourseMapPanel } from "./course-map-panel";

describe("CourseMapPanel", () => {
  it("shows all seven draft lesson shells without claiming they are available", async () => {
    const loadCourseMap = vi.fn().mockResolvedValue(courseMapFixture);
    render(<CourseMapPanel courseKey="g3-sec1-math" loadCourseMap={loadCourseMap} />);

    expect(await screen.findByRole("heading", { name: courseMapFixture.title })).toBeInTheDocument();
    expect(screen.getAllByText("Material pending")).toHaveLength(7);
    expect(screen.getByRole("link", { name: /Primes and prime factorisation/ })).toHaveAttribute(
      "href",
      "/lessons/n1-lesson-01",
    );
    expect(loadCourseMap).toHaveBeenCalledWith("g3-sec1-math");
  });
});
