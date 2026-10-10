import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { courseMapFixture } from "@/lib/api/course";

import { CourseMapPanel } from "./course-map-panel";

describe("CourseMapPanel", () => {
  it("shows every draft N1 and N2 lesson without claiming availability", async () => {
    const loadCourseMap = vi.fn().mockResolvedValue(courseMapFixture);
    const lessonCount = courseMapFixture.units.reduce(
      (total, unit) => total + unit.lessons.length,
      0,
    );
    render(<CourseMapPanel courseKey="g3-sec1-math" loadCourseMap={loadCourseMap} />);

    expect(await screen.findByRole("heading", { name: courseMapFixture.title })).toBeInTheDocument();
    expect(screen.getAllByText("Material pending")).toHaveLength(lessonCount);
    expect(screen.getByText("Ratio and proportion")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Primes and prime factorisation/ })).toHaveAttribute(
      "href",
      "/lessons/n1-lesson-01",
    );
    expect(loadCourseMap).toHaveBeenCalledWith("g3-sec1-math");
  });
});
