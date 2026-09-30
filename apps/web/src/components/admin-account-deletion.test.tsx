import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  AccountDeletionPreview,
  AccountDeletionResult,
} from "@/lib/api/admin";

import { AdminAccountDeletion } from "./admin-account-deletion";

afterEach(cleanup);

const learnerId = "20000000-0000-4000-8000-000000000001";
const preview: AccountDeletionPreview = {
  learner_id: learnerId,
  email: "student@example.test",
  display_name: "Student",
  counts: { attempts: 12, enrolments: 1 },
  retained_records: ["audit_events", "deletion_tombstone"],
  preview_token: "signed-preview-token-that-is-long-enough-for-the-api",
  expires_at: "2026-09-30T12:00:00Z",
  confirmation_value: "student@example.test",
};
const result: AccountDeletionResult = {
  deleted: true,
  target_reference: "a".repeat(64),
  completed_at: "2026-09-30T11:00:00Z",
  retained_records: ["audit_events", "deletion_tombstone"],
};

describe("AdminAccountDeletion", () => {
  it("requires a signed preview, exact email, and audit reason before execution", async () => {
    const api = {
      preview: vi.fn(async () => preview),
      execute: vi.fn(async () => result),
    };
    render(
      <AdminAccountDeletion
        api={api}
        learnerId={learnerId}
        studentEmail={preview.email}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Preview account deletion" }),
    );
    expect(
      await screen.findByText("Permanent deletion preview"),
    ).toBeInTheDocument();
    expect(api.preview).toHaveBeenCalledWith(learnerId);
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(
      screen.getByText(/audit events, deletion tombstone/i),
    ).toBeInTheDocument();

    const execute = screen.getByRole("button", {
      name: "Permanently delete learner",
    });
    expect(execute).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/Type student@example.test/), {
      target: { value: "wrong@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Audit reason"), {
      target: { value: "Parent requested account closure." },
    });
    expect(execute).toBeDisabled();
    expect(
      screen.getByText("The confirmation email does not match."),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Type student@example.test/), {
      target: { value: " STUDENT@EXAMPLE.TEST " },
    });
    expect(execute).toBeEnabled();
    fireEvent.click(execute);

    await waitFor(() =>
      expect(api.execute).toHaveBeenCalledWith(learnerId, {
        preview_token: preview.preview_token,
        confirmation_email: "STUDENT@EXAMPLE.TEST",
        reason: "Parent requested account closure.",
      }),
    );
    expect(
      await screen.findByRole("heading", { name: "Learner account deleted" }),
    ).toBeInTheDocument();
    expect(screen.getByText(result.target_reference)).toBeInTheDocument();
  });
});
