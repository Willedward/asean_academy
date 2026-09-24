import createClient from "openapi-fetch";

import type { paths } from "./schema";

export function createApiClient(accessToken?: string) {
  return createClient<paths>({
    baseUrl: "",
    headers: {
      "X-Request-ID": crypto.randomUUID(),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
  });
}
