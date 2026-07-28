import { NextResponse } from "next/server";

import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity
} from "../../../../lib/server-auth";

export async function GET(request: Request) {
  if (process.env.AXIGNAL_HUMAN_REVIEW_UI_ENABLED !== "true") {
    return NextResponse.json({ error: "Human Review UI is disabled." }, { status: 404 });
  }
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl) {
    return NextResponse.json({ error: "AXIGNAL_API_URL is required." }, { status: 503 });
  }
  const query = new URL(request.url).searchParams.get("research_run_id");
  const suffix = query ? `?research_run_id=${encodeURIComponent(query)}` : "";
  try {
    const response = await fetch(`${apiUrl}/v1/human-review-cases${suffix}`, {
      headers: { "X-AXIGNAL-Identity-Assertion": buildApiIdentityAssertion(identity) },
      cache: "no-store",
      signal: AbortSignal.timeout(8_000)
    });
    const body = await response.json().catch(() => ({ error: "Invalid API response." }));
    return NextResponse.json(body, {
      status: response.status,
      headers: { "cache-control": "no-store" }
    });
  } catch {
    return NextResponse.json({ error: "Human Review API unavailable." }, { status: 503 });
  }
}
