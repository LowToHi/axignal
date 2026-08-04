import { NextRequest, NextResponse } from "next/server";
import { isLocale } from "@/lib/i18n";

export function proxy(request: NextRequest) {
  const firstSegment = request.nextUrl.pathname.split("/").filter(Boolean)[0];
  if (firstSegment === "en") {
    const destination = request.nextUrl.clone();
    destination.pathname = request.nextUrl.pathname.replace(/^\/en(?=\/|$)/, "") || "/";
    return NextResponse.redirect(destination, 308);
  }

  const locale = firstSegment && isLocale(firstSegment) ? firstSegment : "en";
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-axignal-locale", locale);
  return NextResponse.next({ request: { headers: requestHeaders } });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|webp|ico)$).*)"]
};
