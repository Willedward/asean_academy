import type { components } from "./schema";
import { createApiClient } from "./client";

export type HealthResponse = components["schemas"]["HealthResponse"];

const healthFixture: HealthResponse = {
  status: "ok",
  service: "learning-api",
  version: "fixture",
  environment: "development",
  request_id: "fixture-request",
  dependencies: {
    course_content: "draft_placeholders",
    authentication: "planned_stage_4",
    tutor: "disabled",
  },
};

export async function getHealth(): Promise<HealthResponse> {
  if (process.env.NEXT_PUBLIC_USE_API_FIXTURES === "true") {
    return healthFixture;
  }

  const { data, error, response } = await createApiClient().GET("/api/v1/health");
  if (error || !data) {
    const message =
      typeof error === "object" && error && "error" in error
        ? error.error.message
        : `Learning API returned ${response.status}.`;
    throw new Error(message);
  }
  return data;
}
