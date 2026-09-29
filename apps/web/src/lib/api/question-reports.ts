import type { components } from "./schema";
import { createApiClient } from "./client";
import { apiErrorMessage } from "./errors";

export type QuestionReport = components["schemas"]["QuestionReportResponse"];
export type ReportCategory = components["schemas"]["CreateQuestionReportRequest"]["category"];

export async function createQuestionReport(input: {
  session_id: string;
  question_key: string;
  question_revision: number;
  category: ReportCategory;
  comment: string;
}): Promise<QuestionReport> {
  const { data, error, response } = await createApiClient().POST(
    "/api/v1/question-reports",
    { body: input },
  );
  if (error || !data) throw new Error(apiErrorMessage(error, response.status));
  return data;
}
