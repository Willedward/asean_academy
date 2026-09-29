import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { updateSession } from "@/lib/supabase/proxy";

function betaKitIsDisabled(request: NextRequest): boolean {
  const isBetaKitRoute =
    request.nextUrl.pathname === "/beta-kit" ||
    request.nextUrl.pathname.startsWith("/beta-kit/");
  return (
    isBetaKitRoute &&
    process.env.NODE_ENV === "production" &&
    process.env.NEXT_PUBLIC_BETA_KIT !== "true"
  );
}

export async function proxy(request: NextRequest) {
  if (betaKitIsDisabled(request)) {
    return new NextResponse("Not Found", {
      status: 404,
      headers: { "Cache-Control": "no-store" },
    });
  }
  return updateSession(request);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
