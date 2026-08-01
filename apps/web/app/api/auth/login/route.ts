import { NextResponse } from "next/server";

import { legacyPasswordLoginAllowed } from "../../../../lib/security-boundaries";
import {
  authenticateCredentials,
  createSessionToken,
  sessionCookieOptions
} from "../../../../lib/server-auth";

export async function POST(request: Request) {
  if (
    !legacyPasswordLoginAllowed({
      environment: process.env.NODE_ENV,
      enabled: process.env.AXIGNAL_LEGACY_PASSWORD_LOGIN_ENABLED
    })
  ) {
    return NextResponse.json(
      { error: "Not found." },
      { status: 404, headers: { "cache-control": "no-store" } }
    );
  }

  const body = (await request.json().catch(() => null)) as {
    email?: unknown;
    password?: unknown;
  } | null;
  if (!body || typeof body.email !== "string" || typeof body.password !== "string") {
    return NextResponse.json(
      { error: "Email and password are required." },
      { status: 400, headers: { "cache-control": "no-store" } }
    );
  }

  try {
    const claims = authenticateCredentials(body.email, body.password);
    if (!claims) {
      return NextResponse.json(
        { error: "Invalid credentials." },
        { status: 401, headers: { "cache-control": "no-store" } }
      );
    }
    const response = NextResponse.json(
      { authenticated: true, email: claims.email },
      { headers: { "cache-control": "no-store" } }
    );
    response.cookies.set({ ...sessionCookieOptions(), value: createSessionToken(claims) });
    return response;
  } catch {
    return NextResponse.json(
      { error: "Authentication is not configured." },
      { status: 503, headers: { "cache-control": "no-store" } }
    );
  }
}
