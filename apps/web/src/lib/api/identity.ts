import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiRequestError } from "./errors";

export type CurrentLearnerResponse = components["schemas"]["CurrentLearnerResponse"];
export type InvitationAcceptanceResponse =
  components["schemas"]["InvitationAcceptanceResponse"];

export async function getCurrentLearner(
  accessToken?: string,
): Promise<CurrentLearnerResponse> {
  const { data, error, response } = await createApiClient(accessToken).GET("/api/v1/me");
  if (error || !data) throw apiRequestError(error, response.status);
  return data;
}

export async function acceptBetaInvitation(
  invitationCode: string,
  displayName: string,
  accessToken?: string,
): Promise<InvitationAcceptanceResponse> {
  const { data, error, response } = await createApiClient(accessToken).POST(
    "/api/v1/onboarding/accept-invitation",
    { body: { invitation_code: invitationCode, display_name: displayName } },
  );
  if (error || !data) throw apiRequestError(error, response.status);
  return data;
}
