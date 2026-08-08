import { NextRequest, NextResponse } from "next/server";
export const dynamic = "force-dynamic";

import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity,
} from "../../../../../../lib/server-auth";

/**
 * Server proxy for AXENT confirmation resolution. Uses the authenticated
 * identity assertion pattern (same as the other /api/axent proxies); the
 * API executes the pending invocation only after the confirmation is
 * resolved.
 */
export async function POST(
  request: NextRequest,
  context: { params: Promise<{ confirmationId: string }> }
) {
  const { confirmationId } = await context.params;
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return NextResponse.json({ detail: "identity required" }, { status: 401 });
  }
  const body = await request.json().catch(() => null);
  const apiUrl = process.env.AXIGNAL_API_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(
    `${apiUrl}/v1/axent/confirmations/${confirmationId}/resolve`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-AXIGNAL-Identity-Assertion": buildApiIdentityAssertion(identity),
      },
      body: JSON.stringify(body ?? {}),
      cache: "no-store",
    }
  );
  const payload = await response.json().catch(() => ({}));
  return NextResponse.json(payload, { status: response.status });
}
