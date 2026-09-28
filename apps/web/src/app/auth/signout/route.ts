import { revalidatePath } from "next/cache";
import { type NextRequest, NextResponse } from "next/server";

import { E2E_SESSION_COOKIE, isE2EAuthenticationEnabled } from "@/lib/auth/e2e-session";
import { createClient } from "@/lib/supabase/server";

export async function POST(request: NextRequest) {
  if (isE2EAuthenticationEnabled()) {
    revalidatePath("/", "layout");
    const response = NextResponse.redirect(new URL("/login", request.url), { status: 303 });
    response.cookies.delete(E2E_SESSION_COOKIE);
    return response;
  }
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  if (data?.claims) await supabase.auth.signOut();

  revalidatePath("/", "layout");
  return NextResponse.redirect(new URL("/login", request.url), { status: 303 });
}
