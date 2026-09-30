"use server";

import { redirect } from "next/navigation";

import {
  getSiteOrigin,
  loginErrorPath,
  safeNextPath,
} from "@/lib/auth/navigation";
import { createClient } from "@/lib/supabase/server";

export async function signInWithGoogle(formData: FormData) {
  const next = safeNextPath(String(formData.get("next") ?? ""));

  let siteOrigin: string;
  try {
    siteOrigin = getSiteOrigin();
  } catch {
    redirect(loginErrorPath("site_url_missing", next));
  }

  const supabase = await createClient();
  const callback = new URL("/auth/callback", siteOrigin);
  callback.searchParams.set("next", next);
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: callback.toString() },
  });

  if (error || !data.url) redirect(loginErrorPath("oauth_start_failed", next));
  redirect(data.url);
}
