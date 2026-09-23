import createClient from "openapi-fetch";

import type { paths } from "./schema";

export function createApiClient() {
  return createClient<paths>({
    baseUrl: "",
    headers: { "X-Request-ID": crypto.randomUUID() },
  });
}
