import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { isLocale } from "@/lib/i18n";
import {
  evaluateMutationSecurity,
  MUTATION_ORIGIN_EXEMPT_PATHS,
} from "@/lib/security-boundaries";

export function proxy(request: NextRequest) {
  const decision = evaluateMutationSecurity({
    method: request.method,
    pathname: request.nextUrl.pathname,
    origin: request.headers.get("origin"),
    secFetchSite: request.headers.get("sec-fetch-site"),
    configuredPublicOrigin: process.env.AXIGNAL_PUBLIC_ORIGIN,
    requestOrigin: request.nextUrl.origin,
    environment: process.env.NODE_ENV,
    legacyPasswordLoginEnabled:
      process.env.AXIGNAL_LEGACY_PASSWORD_LOGIN_ENABLED,
    exemptPaths: MUTATION_ORIGIN_EXEMPT_PATHS,
  });

  if (!decision.allowed) {
    return NextResponse.json(
      {
        error: "request_rejected",
        code: decision.code,
      },
      {
        status: decision.status,
        headers: {
          "cache-control": "no-store",
          "x-axignal-security-boundary": decision.code,
        },
      },
    );
  }

  const firstSegment = request.nextUrl.pathname.split("/").filter(Boolean)[0];
  if (firstSegment === "en") {
    const destination = request.nextUrl.clone();
    destination.pathname =
      request.nextUrl.pathname.replace(/^\/en(?=\/|$)/, "") || "/";
    return NextResponse.redirect(destination, 308);
  }

  const locale = firstSegment && isLocale(firstSegment) ? firstSegment : "en";
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-axignal-locale", locale);

  // The proxy is the canonical mutation-origin boundary. Once it admits a
  // request, remove the external Origin header before dispatching to route
  // handlers whose internal URL may use a container hostname.
  if (request.method !== "GET" && request.method !== "HEAD") {
    requestHeaders.delete("origin");
  }

  return NextResponse.next({ request: { headers: requestHeaders } });
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|webp|ico)$).*)",
  ],
};
