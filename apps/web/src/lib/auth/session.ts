import "server-only";

import { cache } from "react";
import { redirect } from "next/navigation";

import { isSupabaseConfigured } from "@/lib/supabase/config";
import { createClient } from "@/lib/supabase/server";

export type VerifiedSession = {
  accessToken: string;
  email: string | null;
  subject: string;
};

export const getVerifiedSession = cache(async (): Promise<VerifiedSession | null> => {
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

export async function requireVerifiedSession(): Promise<VerifiedSession | null> {
  if (!isSupabaseConfigured()) return null;
  const session = await getVerifiedSession();
  if (!session) redirect("/login");
  return session;
}
