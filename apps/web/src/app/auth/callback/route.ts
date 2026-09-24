import { NextResponse } from "next/server";

import { getSiteOrigin, safeNextPath } from "@/lib/auth/navigation";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const next = safeNextPath(requestUrl.searchParams.get("next"));

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      let origin: string;
      try {
        origin = getSiteOrigin();
      } catch {
        origin = requestUrl.origin;
      }
      return NextResponse.redirect(new URL(next, origin));
    }
  }

  const failed = new URL("/login", requestUrl.origin);
  failed.searchParams.set("error", "auth_callback_failed");
  return NextResponse.redirect(failed);
}
