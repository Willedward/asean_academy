import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiRequestError } from "./errors";

export type Invitation = components["schemas"]["InvitationResponse"];
export type CreatedInvitation = components["schemas"]["CreatedInvitationResponse"];
export type InvitationList = components["schemas"]["InvitationListResponse"];
export type OperationsSummary = components["schemas"]["BetaOperationsSummaryResponse"];
export type AuditEventList = components["schemas"]["AuditEventListResponse"];
export type CreateInvitationInput = components["schemas"]["CreateInvitationRequest"];

export async function listInvitations(): Promise<InvitationList> {
  const { data, error, response } = await createApiClient().GET("/api/v1/admin/invitations", {
    params: { query: { limit: 100, offset: 0 } },
  });
  if (error || !data) throw apiRequestError(error, response.status);
  return data;
}

export async function createInvitation(
  input: CreateInvitationInput,
): Promise<CreatedInvitation> {
  const { data, error, response } = await createApiClient().POST("/api/v1/admin/invitations", {
    body: input,
  });
  if (error || !data) throw apiRequestError(error, response.status);
  return data;
}

export async function revokeInvitation(invitationId: string): Promise<Invitation> {
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/admin/invitations/{invitation_id}/revoke",
    { params: { path: { invitation_id: invitationId } } },
  );
  if (error || !data) throw apiRequestError(error, response.status);
  return data;
}

export async function getOperationsSummary(): Promise<OperationsSummary> {
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/admin/operations/summary",
  );
  if (error || !data) throw apiRequestError(error, response.status);
  return data;
}

export async function listAuditEvents(): Promise<AuditEventList> {
  const { data, error, response } = await createApiClient().GET(
    "/api/v1/admin/audit-events",
    { params: { query: { limit: 50 } } },
  );
  if (error || !data) throw apiRequestError(error, response.status);
  return data;
}
