import { NextResponse } from "next/server";

import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity
} from "../../../../../../lib/server-auth";

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function POST(
  request: Request,
  context: { params: Promise<{ caseId: string }> }
) {
  if (process.env.AXIGNAL_HUMAN_REVIEW_UI_ENABLED !== "true") {
    return NextResponse.json({ error: "Human Review UI is disabled." }, { status: 404 });
  }
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }
  const { caseId } = await context.params;
  if (!uuidPattern.test(caseId)) {
    return NextResponse.json({ error: "Invalid Human Review case identifier." }, { status: 400 });
  }
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl) {
    return NextResponse.json({ error: "AXIGNAL_API_URL is required." }, { status: 503 });
  }
  const payload = await request.json().catch(() => null);
  if (!payload || typeof payload !== "object") {
    return NextResponse.json({ error: "Invalid Human Review action." }, { status: 400 });
  }
  try {
    const response = await fetch(
      `${apiUrl}/v1/human-review-cases/${caseId}/actions`,
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "X-AXIGNAL-Identity-Assertion": buildApiIdentityAssertion(identity)
        },
        body: JSON.stringify(payload),
        cache: "no-store",
        signal: AbortSignal.timeout(8_000)
      }
    );
    const body = await response.json().catch(() => ({ error: "Invalid API response." }));
    return NextResponse.json(body, {
      status: response.status,
      headers: { "cache-control": "no-store" }
    });
  } catch {
    return NextResponse.json({ error: "Human Review API unavailable." }, { status: 503 });
  }
}
