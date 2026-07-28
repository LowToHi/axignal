import { NextResponse } from "next/server";

import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity
} from "../../../../../../lib/server-auth";

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function POST(
  request: Request,
  context: { params: Promise<{ sessionId: string }> }
) {
  if (process.env.AXIGNAL_VALIDATION_UI_ENABLED !== "true") {
    return NextResponse.json({ error: "Validation UI is disabled." }, { status: 404 });
  }
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }
  const { sessionId } = await context.params;
  if (!uuidPattern.test(sessionId)) {
    return NextResponse.json({ error: "Invalid validation session identifier." }, { status: 400 });
  }
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  const payload = await request.json().catch(() => null);
  if (!apiUrl || !payload || typeof payload !== "object") {
    return NextResponse.json({ error: "Invalid validation response." }, { status: 400 });
  }
  try {
    const response = await fetch(`${apiUrl}/v1/validation/sessions/${sessionId}/complete`, {
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
    return NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json({ error: "Validation API unavailable." }, { status: 503 });
  }
}
