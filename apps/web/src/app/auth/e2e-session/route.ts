import { type NextRequest, NextResponse } from "next/server";

import {
  authorizeE2ERequest,
  E2E_SECRET_HEADER,
  E2E_SESSION_COOKIE,
  isE2EAuthenticationEnabled,
  issueE2EToken,
} from "@/lib/auth/e2e-session";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function POST(request: NextRequest) {
  if (!isE2EAuthenticationEnabled()) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }
  if (!authorizeE2ERequest(request.headers.get(E2E_SECRET_HEADER))) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }
  let body: { learner_id?: unknown; email?: unknown };
  try {
    body = await request.json() as typeof body;
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
  if (
    typeof body.learner_id !== "string" ||
    !UUID.test(body.learner_id) ||
    typeof body.email !== "string" ||
    !body.email.includes("@") ||
    body.email.length > 254
  ) {
    return NextResponse.json({ error: "Invalid identity" }, { status: 422 });
  }
  const response = NextResponse.json({ authenticated: true });
  response.cookies.set(E2E_SESSION_COOKIE, issueE2EToken(body.learner_id, body.email), {
    httpOnly: true,
    maxAge: 60 * 60,
    path: "/",
    sameSite: "lax",
    secure: false,
  });
  return response;
}
