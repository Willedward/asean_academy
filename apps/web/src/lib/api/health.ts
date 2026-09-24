import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiErrorMessage } from "./errors";

export type HealthResponse = components["schemas"]["HealthResponse"];

const healthFixture: HealthResponse = {
  status: "ok",
  service: "learning-api",
  version: "fixture",
  environment: "development",
  request_id: "fixture-request",
  dependencies: {
    course_content: "draft_placeholders",
    authentication: "supabase_bearer",
    tutor: "disabled",
  },
};

export async function getHealth(): Promise<HealthResponse> {
  if (process.env.NEXT_PUBLIC_USE_API_FIXTURES === "true") {
    return healthFixture;
  }

  const { data, error, response } = await createApiClient().GET("/api/v1/health");
  if (error || !data) {
    throw new Error(apiErrorMessage(error, response.status));
  }
  return data;
}
