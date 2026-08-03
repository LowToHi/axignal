import { NextResponse } from "next/server";

import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity
} from "./server-auth";

export async function proxySubscriberJson(
  path: string,
  init: RequestInit = {}
): Promise<NextResponse> {
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl) {
    return NextResponse.json({ error: "AXIGNAL_API_URL is required." }, { status: 503 });
  }
  const headers = new Headers(init.headers);
  headers.set("content-type", "application/json");
  headers.set("X-AXIGNAL-Identity-Assertion", buildApiIdentityAssertion(identity));
  try {
    const response = await fetch(`${apiUrl}${path}`, {
      ...init,
      headers,
      cache: "no-store",
      signal: AbortSignal.timeout(10_000)
    });
    const body = await response.json().catch(() => ({ error: "Invalid API response." }));
    return NextResponse.json(body, {
      status: response.status,
      headers: { "cache-control": "private, no-store" }
    });
  } catch {
    return NextResponse.json(
      { error: "Subscriber workspace API unavailable." },
      { status: 503 }
    );
  }
}

export async function proxySubscriberDownload(path: string): Promise<Response> {
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }
  const apiUrl = process.env.AXIGNAL_API_URL?.replace(/\/$/, "");
  if (!apiUrl) {
    return NextResponse.json({ error: "AXIGNAL_API_URL is required." }, { status: 503 });
  }
  try {
    const response = await fetch(`${apiUrl}${path}`, {
      headers: { "X-AXIGNAL-Identity-Assertion": buildApiIdentityAssertion(identity) },
      cache: "no-store",
      signal: AbortSignal.timeout(10_000)
    });
    const body = await response.text();
    return new Response(body, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "text/plain; charset=utf-8",
        "content-disposition": response.headers.get("content-disposition") ?? "attachment",
        "cache-control": "private, no-store",
        ...(response.headers.get("etag") ? { etag: response.headers.get("etag")! } : {})
      }
    });
  } catch {
    return NextResponse.json(
      { error: "Subscriber workspace export unavailable." },
      { status: 503 }
    );
  }
}
