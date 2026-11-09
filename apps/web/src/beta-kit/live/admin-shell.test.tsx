import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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

  it("offers a first-stop skip link to the focusable main region", () => {
    const { container } = render(
      <AdminShell
        identity={{
          displayName: "William",
          email: "william@example.com",
          role: "academic_admin",
        }}
      >
        <h1>Learning overview</h1>
      </AdminShell>,
    );

    const skip = screen.getByRole("link", { name: "Skip to content" });
    expect(container.querySelector("a[href]")).toBe(skip);
    expect(skip).toHaveAttribute("href", "#main-content");
    const main = screen.getByRole("main");
    expect(main).toHaveAttribute("id", "main-content");
    expect(main).toHaveAttribute("tabindex", "-1");
  });

  it("opens the mobile navigation with focus and closes it with Escape", () => {
    render(
      <AdminShell
        identity={{
          displayName: "William",
          email: "william@example.com",
          role: "academic_admin",
        }}
      >
        <h1>Learning overview</h1>
      </AdminShell>,
    );

    const open = screen.getByRole("button", {
      name: "Open administrator navigation",
    });
    fireEvent.click(open);

    expect(
      screen.getByRole("button", { name: "Close administrator navigation" }),
    ).toHaveAttribute("aria-expanded", "true");
    expect(
      screen.getAllByRole("link", { name: "Overview" }).at(-1),
    ).toHaveFocus();

    fireEvent.keyDown(document, { key: "Escape" });

    expect(
      screen.getByRole("button", { name: "Open administrator navigation" }),
    ).toHaveFocus();
  });
});
