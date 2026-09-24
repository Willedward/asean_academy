import { type NextRequest, NextResponse } from "next/server";

import { getVerifiedSession } from "@/lib/auth/session";
import { isSupabaseConfigured } from "@/lib/supabase/config";

const FORWARDED_REQUEST_HEADERS = [
  "accept",
  "content-type",
  "idempotency-key",
  "x-request-id",
] as const;
const FORWARDED_RESPONSE_HEADERS = [
  "content-type",
  "retry-after",
  "x-request-id",
] as const;
const PUBLIC_PATHS = new Set(["health"]);

type Context = { params: Promise<{ path: string[] }> };

function learningApiBaseUrl(): string {
  return (process.env.LEARNING_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
}

function authenticationError() {
  const requestId = crypto.randomUUID();
  return NextResponse.json(
    {
      error: {
        code: "authentication_required",
        message: "Sign in before using the learning application.",
        request_id: requestId,
        details: null,
      },
    },
    {
      status: 401,
      headers: {
        "Cache-Control": "private, no-store",
        "WWW-Authenticate": "Bearer",
        "X-Request-ID": requestId,
      },
    },
  );
}

async function forward(request: NextRequest, context: Context): Promise<Response> {
  const { path } = await context.params;
  const relativePath = path.join("/");
  const target = new URL(`/api/v1/${relativePath}`, learningApiBaseUrl());
  target.search = request.nextUrl.search;

  const headers = new Headers();
  FORWARDED_REQUEST_HEADERS.forEach((name) => {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  });

  if (isSupabaseConfigured() && !PUBLIC_PATHS.has(relativePath)) {
    const session = await getVerifiedSession();
    if (!session) return authenticationError();
    headers.set("Authorization", `Bearer ${session.accessToken}`);
  }

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
      cache: "no-store",
      redirect: "manual",
    });
  } catch {
    const requestId = headers.get("x-request-id") ?? crypto.randomUUID();
    return NextResponse.json(
      {
        error: {
          code: "learning_api_unavailable",
          message: "The learning service could not be reached.",
          request_id: requestId,
          details: null,
        },
      },
      {
        status: 503,
        headers: { "Cache-Control": "no-store", "X-Request-ID": requestId },
      },
    );
  }

  const responseHeaders = new Headers({ "Cache-Control": "private, no-store" });
  FORWARDED_RESPONSE_HEADERS.forEach((name) => {
    const value = upstream.headers.get(name);
    if (value) responseHeaders.set(name, value);
  });
  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
export const HEAD = forward;
export const OPTIONS = forward;
