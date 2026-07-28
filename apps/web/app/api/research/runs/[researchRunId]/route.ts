import { NextResponse } from "next/server";

import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity,
  isPersistentResearchUiEnabled
} from "../../../../../lib/server-auth";

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function GET(
  _request: Request,
  context: { params: Promise<{ researchRunId: string }> }
) {
  if (!isPersistentResearchUiEnabled()) {
    return NextResponse.json({ error: "Persistent ResearchRun UI is disabled." }, { status: 404 });
  }
  const identity = await getAuthenticatedIdentity();
  if (!identity) return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  const { researchRunId } = await context.params;
  if (!uuidPattern.test(researchRunId)) {
    return NextResponse.json({ error: "Invalid ResearchRun identifier." }, { status: 400 });
  }
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl) return NextResponse.json({ error: "AXIGNAL_API_URL is required." }, { status: 503 });

  try {
    const response = await fetch(`${apiUrl}/v1/research-runs/${researchRunId}`, {
      headers: { "X-AXIGNAL-Identity-Assertion": buildApiIdentityAssertion(identity) },
      cache: "no-store",
      signal: AbortSignal.timeout(8_000)
    });
    const responseBody = await response.json().catch(() => ({ error: "Invalid API response." }));
    return NextResponse.json(responseBody, {
      status: response.status,
      headers: { "cache-control": "no-store" }
    });
  } catch {
    return NextResponse.json({ error: "Persistent ResearchRun API unavailable." }, { status: 503 });
  }
}
