import { NextResponse } from "next/server";

import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity
} from "./server-auth";

/**
 * Server-side proxy for the /v1/opportunities API.
 * Reuses the authenticated identity assertion pattern (same as billing).
 */
export async function proxyOpportunityRequest(
  path: string,
  init: RequestInit = {}
): Promise<NextResponse> {
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return NextResponse.json(
      { error: "Authentication required." },
      { status: 401 }
    );
  }
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl) {
    return NextResponse.json(
      { error: "AXIGNAL_API_URL is required." },
      { status: 503 }
    );
  }
  const headers = new Headers(init.headers);
  headers.set("content-type", "application/json");
  headers.set("X-AXIGNAL-Identity-Assertion", buildApiIdentityAssertion(identity));
  try {
    const response = await fetch(`${apiUrl}${path}`, {
      ...init,
      headers,
      cache: "no-store",
      signal: AbortSignal.timeout(8_000)
    });
    const body = await response
      .json()
      .catch(() => ({ error: "Invalid API response." }));
    return NextResponse.json(body, {
      status: response.status,
      headers: { "cache-control": "no-store" }
    });
  } catch {
    return NextResponse.json(
      { error: "Opportunity API unavailable." },
      { status: 503 }
    );
  }
}
