import { NextResponse } from "next/server";

import { mutateFounderAdmin } from "@/lib/organic-server";
import { getAuthenticatedIdentity } from "@/lib/server-auth";

export async function POST(request: Request) {
  const identity = await getAuthenticatedIdentity();
  if (!identity) {
    return NextResponse.json({ error: "Authentication required." }, { status: 401 });
  }
  let body: Record<string, unknown>;
  try {
    body = (await request.json()) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }
  const action = body.action;
  if (
    action !== "evaluate" &&
    action !== "publish" &&
    action !== "record-citation" &&
    action !== "test-bootstrap"
  ) {
    return NextResponse.json({ error: "Unsupported action." }, { status: 422 });
  }
  try {
    const result = await mutateFounderAdmin(identity, action, body);
    return NextResponse.json(result, {
      headers: { "cache-control": "no-store" }
    });
  } catch {
    return NextResponse.json(
      { error: "Founder operation was denied or unavailable." },
      { status: 403 }
    );
  }
}
