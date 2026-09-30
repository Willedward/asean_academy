import type { components } from "./schema";
import { apiRequestError } from "./errors";

export type Overview = components["schemas"]["AdminAnalyticsOverviewResponse"];
export type Students = components["schemas"]["AdminStudentListResponse"];
export type StudentDetail = components["schemas"]["AdminStudentDetailResponse"];
export type Diagnostics =
  components["schemas"]["AdminStudentDiagnosticsResponse"];
export type Questions =
  components["schemas"]["AdminQuestionAnalyticsListResponse"];
export type Users = components["schemas"]["AdminUserListResponse"];
export type Preview = components["schemas"]["CurriculumPreviewResponse"];
export type MigrationInput =
  components["schemas"]["CurriculumMigrationRequest"];
export type Role = components["schemas"]["AdminUserRoleResponse"]["role"];
export type Operations = components["schemas"]["DeploymentStatusResponse"];
export type ContentStatus = components["schemas"]["ContentStatusResponse"];
export type Audit = components["schemas"]["AuditEventListResponse"];
export type Reports = components["schemas"]["AdminQuestionReportListResponse"];
export type Report = components["schemas"]["AdminQuestionReportResponse"];
export type ResetDiagnosticResult =
  components["schemas"]["ResetDiagnosticResponse"];
export type ContentQueue = components["schemas"]["ContentReviewQueueResponse"];
export type ContentItem = components["schemas"]["ContentReviewItemResponse"];
export type ContentPreview =
  components["schemas"]["ContentStudentPreviewResponse"];
export type ReviewInput = components["schemas"]["RecordContentReviewRequest"];
export type LifecycleInput = components["schemas"]["CreateLifecycleRequest"];

export async function adminRequest<T>(
  path: string,
  body?: unknown,
  method = "POST",
): Promise<T> {
  const response = await fetch(`/api/v1/admin/${path}`, {
    method: body === undefined ? "GET" : method,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": crypto.randomUUID(),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data: unknown = await response.json();
  if (!response.ok) throw apiRequestError(data, response.status);
  return data as T;
}
