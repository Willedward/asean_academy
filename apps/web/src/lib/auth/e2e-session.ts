import "server-only";

import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

import { getE2EAuthSecret, isE2EAuthenticationEnabled } from "./e2e-config";

export const E2E_SESSION_COOKIE = "asean_academy_e2e_session";
export const E2E_SECRET_HEADER = "x-asean-e2e-secret";
const ISSUER = "asean-academy-e2e";
const AUDIENCE = "authenticated";

type Payload = {
  aud: string;
  email: string;
  exp: number;
  iat: number;
  iss: string;
  role: "authenticated";
  sub: string;
};

type E2EVerifiedSession = {
  accessToken: string;
  email: string | null;
  subject: string;
};

function encode(value: object): string {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

function signature(value: string, key: string): string {
  return createHmac("sha256", key).update(value).digest("base64url");
}

function equal(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  return leftBuffer.length === rightBuffer.length && timingSafeEqual(leftBuffer, rightBuffer);
}

export { isE2EAuthenticationEnabled };

export function authorizeE2ERequest(provided: string | null): boolean {
  const expected = getE2EAuthSecret();
  return Boolean(expected && provided && equal(expected, provided));
}

export function issueE2EToken(subject: string, email: string): string {
  const key = getE2EAuthSecret();
  if (!key) throw new Error("E2E authentication is disabled.");
  const now = Math.floor(Date.now() / 1000);
  const header = encode({ alg: "HS256", typ: "JWT" });
  const payload = encode({
    aud: AUDIENCE,
    email,
    exp: now + 60 * 60,
    iat: now,
    iss: ISSUER,
    role: "authenticated",
    sub: subject,
  } satisfies Payload);
  const unsigned = `${header}.${payload}`;
  return `${unsigned}.${signature(unsigned, key)}`;
}

export function verifyE2EToken(token: string): E2EVerifiedSession | null {
  const key = getE2EAuthSecret();
  if (!key) return null;
  const [header, encodedPayload, suppliedSignature, extra] = token.split(".");
  if (!header || !encodedPayload || !suppliedSignature || extra) return null;
  const unsigned = `${header}.${encodedPayload}`;
  if (!equal(signature(unsigned, key), suppliedSignature)) return null;
  try {
    const decodedHeader = JSON.parse(Buffer.from(header, "base64url").toString()) as {
      alg?: unknown;
      typ?: unknown;
    };
    if (decodedHeader.alg !== "HS256" || decodedHeader.typ !== "JWT") return null;
    const payload = JSON.parse(Buffer.from(encodedPayload, "base64url").toString()) as Payload;
    const now = Math.floor(Date.now() / 1000);
    if (
      payload.iss !== ISSUER ||
      payload.aud !== AUDIENCE ||
      payload.role !== "authenticated" ||
      payload.exp <= now ||
      payload.iat > now ||
      typeof payload.sub !== "string" ||
      typeof payload.email !== "string"
    ) {
      return null;
    }
    return { accessToken: token, email: payload.email, subject: payload.sub };
  } catch {
    return null;
  }
}

export async function getE2EVerifiedSession(): Promise<E2EVerifiedSession | null> {
  if (!isE2EAuthenticationEnabled()) return null;
  const store = await cookies();
  const token = store.get(E2E_SESSION_COOKIE)?.value;
  return token ? verifyE2EToken(token) : null;
}
