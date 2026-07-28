import { NextResponse } from "next/server";

import {
  authenticateCredentials,
  createSessionToken,
  sessionCookieOptions
} from "../../../../lib/server-auth";

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as {
    email?: unknown;
    password?: unknown;
  } | null;
  if (!body || typeof body.email !== "string" || typeof body.password !== "string") {
    return NextResponse.json({ error: "Email and password are required." }, { status: 400 });
  }

  try {
    const claims = authenticateCredentials(body.email, body.password);
    if (!claims) {
      return NextResponse.json({ error: "Invalid credentials." }, { status: 401 });
    }
    const response = NextResponse.json({ authenticated: true, email: claims.email });
    response.cookies.set({ ...sessionCookieOptions(), value: createSessionToken(claims) });
    return response;
  } catch {
    return NextResponse.json({ error: "Authentication is not configured." }, { status: 503 });
  }
}
