"use client";

import { createBrowserClient } from "@supabase/ssr";

import { getSupabasePublicConfig } from "./config";

export function createClient() {
  const config = getSupabasePublicConfig();
  if (!config) {
    throw new Error("Supabase authentication is not configured for this deployment.");
  }
  return createBrowserClient(config.url, config.publishableKey);
}
