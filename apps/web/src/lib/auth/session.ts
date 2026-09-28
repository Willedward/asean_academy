import "server-only";

import { cache } from "react";
import { redirect } from "next/navigation";

import { getE2EVerifiedSession, isE2EAuthenticationEnabled } from "@/lib/auth/e2e-session";
import { safeNextPath } from "@/lib/auth/navigation";
import { isSupabaseConfigured } from "@/lib/supabase/config";
import { createClient } from "@/lib/supabase/server";

export type VerifiedSession = {
  accessToken: string;
  email: string | null;
  subject: string;
};

export function isAuthenticationConfigured(): boolean {
  return isE2EAuthenticationEnabled() || isSupabaseConfigured();
}

export const getVerifiedSession = cache(async (): Promise<VerifiedSession | null> => {
  const e2eSession = await getE2EVerifiedSession();
  if (e2eSession) return e2eSession;
  if (!isSupabaseConfigured()) return null;

  const supabase = await createClient();
  const { data: claimsData, error: claimsError } = await supabase.auth.getClaims();
  const claims = claimsData?.claims;
  if (claimsError || !claims || typeof claims.sub !== "string") return null;

  // getClaims() above establishes identity. The session is read only to forward
  // its access token to the independently-verifying Python learning API.
  const { data: sessionData } = await supabase.auth.getSession();
  if (!sessionData.session?.access_token) return null;

  return {
    accessToken: sessionData.session.access_token,
    email: typeof claims.email === "string" ? claims.email : null,
    subject: claims.sub,
  };
});

export async function requireVerifiedSession(
  nextPath = "/onboarding",
): Promise<VerifiedSession | null> {
  if (!isAuthenticationConfigured()) return null;
  const session = await getVerifiedSession();
  if (!session) {
    const next = encodeURIComponent(safeNextPath(nextPath));
    redirect(`/login?next=${next}`);
  }
  return session;
}
