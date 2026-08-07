import { NextResponse } from "next/server";

import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity
} from "../../../../../lib/server-auth";

/**
 * Sandbox billing proxy: /api/billing/sandbox/* -> /v1/billing/sandbox/*.
 * Server-side only; no client keys involved.
 */
async function proxySandbox(path: string, init: RequestInit = {}) {
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
      { error: "Billing API unavailable." },
      { status: 503 }
    );
  }
}

/** /api/billing/sandbox/checkout */
export async function POST(request: Request) {
  const body = await request.text();
  return proxySandbox("/v1/billing/sandbox/checkout", { method: "POST", body });
}

/** /api/billing/sandbox/entitlements */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const path = url.pathname.replace(/^\/api\/billing\/sandbox/, "/v1/billing/sandbox");
  return proxySandbox(path);
}
