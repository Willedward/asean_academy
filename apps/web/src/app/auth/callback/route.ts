import { NextResponse } from "next/server";

import {
  getSiteOrigin,
  loginErrorPath,
  safeNextPath,
} from "@/lib/auth/navigation";
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

  return NextResponse.redirect(
    new URL(loginErrorPath("auth_callback_failed", next), requestUrl.origin),
  );
}
