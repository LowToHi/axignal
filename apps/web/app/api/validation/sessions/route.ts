import { NextResponse } from "next/server";

import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity
} from "../../../../lib/server-auth";

export async function POST(request: Request) {
  if (process.env.AXIGNAL_VALIDATION_UI_ENABLED !== "true") {
    return NextResponse.json({ error: "Validation UI is disabled." }, { status: 404 });
  }
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl) {
    return NextResponse.json({ error: "AXIGNAL_API_URL is required." }, { status: 503 });
  }
  const payload = await request.json().catch(() => null);
  if (!payload || typeof payload !== "object") {
    return NextResponse.json({ error: "Invalid validation session." }, { status: 400 });
  }
  try {
    const response = await fetch(`${apiUrl}/v1/validation/sessions`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "X-AXIGNAL-Identity-Assertion": buildApiIdentityAssertion(identity)
      },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal: AbortSignal.timeout(8_000)
    });
    const body = await response.json().catch(() => ({ error: "Invalid API response." }));
    return NextResponse.json(body, {
      status: response.status,
      headers: { "cache-control": "no-store" }
    });
  } catch {
    return NextResponse.json({ error: "Validation API unavailable." }, { status: 503 });
  }
}
