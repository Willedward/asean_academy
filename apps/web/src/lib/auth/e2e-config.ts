export function getE2EAuthSecret(): string | null {
  if (process.env.ASEAN_ACADEMY_ENV !== "test") return null;
  const value = process.env.ASEAN_ACADEMY_E2E_AUTH_SECRET?.trim() ?? "";
  return value.length >= 32 ? value : null;
}

export function isE2EAuthenticationEnabled(): boolean {
  return getE2EAuthSecret() !== null;
}
