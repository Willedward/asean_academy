const DEFAULT_AFTER_SIGN_IN = "/onboarding";

export function safeNextPath(value: string | null | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) {
    return DEFAULT_AFTER_SIGN_IN;
  }

  try {
    const parsed = new URL(value, "https://app.invalid");
    if (parsed.origin !== "https://app.invalid") return DEFAULT_AFTER_SIGN_IN;
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return DEFAULT_AFTER_SIGN_IN;
  }
}

export function normalizeSiteOrigin(value: string): string {
  const withProtocol = value.startsWith("http://") || value.startsWith("https://")
    ? value
    : `https://${value}`;
  const parsed = new URL(withProtocol);
  if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password) {
    throw new Error("The application site URL is invalid.");
  }
  return parsed.origin;
}

export function getSiteOrigin(): string {
  const configured = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (configured) return normalizeSiteOrigin(configured);

  const railwayDomain = process.env.RAILWAY_PUBLIC_DOMAIN?.trim();
  if (railwayDomain) return normalizeSiteOrigin(railwayDomain);

  const vercelDomain = process.env.VERCEL_URL?.trim();
  if (vercelDomain) return normalizeSiteOrigin(vercelDomain);

  if (process.env.NODE_ENV !== "production") return "http://localhost:3000";
  throw new Error("Set NEXT_PUBLIC_SITE_URL for hosted authentication.");
}
