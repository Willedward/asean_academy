type ErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
    request_id?: string;
  };
};

function envelope(error: unknown): ErrorEnvelope | null {
  return typeof error === "object" && error !== null ? error as ErrorEnvelope : null;
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

export function apiErrorMessage(error: unknown, status: number): string {
  return envelope(error)?.error?.message ?? `Learning API returned ${status}.`;
}

export function apiRequestError(error: unknown, status: number): ApiRequestError {
  const detail = envelope(error)?.error;
  return new ApiRequestError(
    detail?.message ?? `Learning API returned ${status}.`,
    status,
    detail?.code ?? "learning_api_error",
    detail?.request_id,
  );
}
