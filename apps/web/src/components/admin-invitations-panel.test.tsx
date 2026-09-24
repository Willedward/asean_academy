import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  AuditEventList,
  CreatedInvitation,
  InvitationList,
  OperationsSummary,
} from "@/lib/api/admin";

import { AdminInvitationsPanel } from "./admin-invitations-panel";

const invitation: InvitationList["invitations"][number] = {
  invitation_id: "33333333-3333-4333-8333-333333333333",
  email: "student@example.test",
  course_key: "g3-sec1-math",
  course_revision: 1,
  status: "active",
  use_count: 0,
  max_uses: 1,
  expires_at: "2026-10-09T08:00:00Z",
  revoked_at: null,
  created_at: "2026-09-25T08:00:00Z",
  created_by: "11111111-1111-4111-8111-111111111111",
};

const summary: OperationsSummary = {
  total_students: 4,
  active_students: 3,
  enrolments_last_7_days: 2,
  invitations_active: 1,
  invitations_expired: 1,
  invitations_exhausted: 0,
  invitations_revoked: 1,
};

const audit: AuditEventList = {
  events: [
    {
      event_id: "44444444-4444-4444-8444-444444444444",
      event_type: "invitation_created",
      actor_user_id: "11111111-1111-4111-8111-111111111111",
      invitation_id: invitation.invitation_id,
      target_user_id: null,
      request_id: "request-create-1",
      metadata: { course_key: "g3-sec1-math" },
      created_at: "2026-09-25T08:00:00Z",
    },
  ],
};

const created: CreatedInvitation = {
  ...invitation,
  invitation_code: "raw-code-visible-once",
};

afterEach(cleanup);

describe("AdminInvitationsPanel", () => {
  it("loads beta operations and creates an invitation whose raw code is shown once", async () => {
    const api = {
      listInvitations: vi.fn(async () => ({ invitations: [invitation], total: 1 })),
      getOperationsSummary: vi.fn(async () => summary),
      listAuditEvents: vi.fn(async () => audit),
      createInvitation: vi.fn(async () => created),
      revokeInvitation: vi.fn(async () => ({ ...invitation, status: "revoked" as const })),
    };

    render(<AdminInvitationsPanel api={api} />);

    expect(await screen.findByText("student@example.test")).toBeInTheDocument();
    expect(screen.queryByText("Student onboarded")).not.toBeInTheDocument();
    expect(screen.getByText("Invitation created")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Student email"), {
      target: { value: " New.Student@Example.test " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create invitation" }));

    expect(await screen.findByText("raw-code-visible-once")).toBeInTheDocument();
    expect(api.createInvitation).toHaveBeenCalledWith({
      email: "New.Student@Example.test",
      course_key: "g3-sec1-math",
      expires_days: 14,
      max_uses: 1,
    });
    expect(api.listInvitations).toHaveBeenCalledTimes(2);
  });

  it("revokes an active invitation and reloads operations", async () => {
    const api = {
      listInvitations: vi.fn(async () => ({ invitations: [invitation], total: 1 })),
      getOperationsSummary: vi.fn(async () => summary),
      listAuditEvents: vi.fn(async () => audit),
      createInvitation: vi.fn(async () => created),
      revokeInvitation: vi.fn(async () => ({ ...invitation, status: "revoked" as const })),
    };

    render(<AdminInvitationsPanel api={api} />);
    fireEvent.click(await screen.findByRole("button", { name: "Revoke" }));

    await waitFor(() => {
      expect(api.revokeInvitation).toHaveBeenCalledWith(invitation.invitation_id);
      expect(api.listInvitations).toHaveBeenCalledTimes(2);
    });
  });
});
