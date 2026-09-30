import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AdminShell } from "./admin-shell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/users",
}));

afterEach(cleanup);

describe("AdminShell", () => {
  it("shows academic-only tools and marks the current destination", () => {
    render(
      <AdminShell
        identity={{
          displayName: "William",
          email: "william@example.com",
          role: "academic_admin",
        }}
      >
        <h1>Users, roles and course revisions</h1>
      </AdminShell>,
    );

    expect(screen.getByRole("link", { name: "Users & roles" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(
      screen.getByRole("link", { name: "System status" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Academic administrator")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Users, roles and course revisions",
      }),
    ).toBeInTheDocument();
  });

  it("does not expose academic-only destinations to content admins", () => {
    render(
      <AdminShell
        identity={{
          displayName: "Editor",
          email: "editor@example.com",
          role: "content_admin",
        }}
      >
        <h1>Content review</h1>
      </AdminShell>,
    );

    expect(
      screen.queryByRole("link", { name: "Users & roles" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "System status" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("Content administrator")).toBeInTheDocument();
  });
});
