import { NextResponse } from "next/server";

import {
  subscriberWorkspaceEnabled,
  subscriberWorkspaceEventsResult
} from "@/lib/subscriber-workspace-server";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  if (!subscriberWorkspaceEnabled()) {
    return NextResponse.json(
      {
        error: "Subscriber workspace is disabled.",
        code: "not_found",
        state: "restricted",
        recoverable: false
      },
      { status: 404, headers: { "cache-control": "no-store" } }
    );
  }
  const raw = new URL(request.url).searchParams.get("after") ?? "0";
  if (!/^\d{1,15}$/.test(raw)) {
    return NextResponse.json(
      {
        error: "Invalid event cursor.",
        code: "invalid_request",
        state: "rejected",
        recoverable: false
      },
      { status: 400, headers: { "cache-control": "no-store" } }
    );
  }
  const result = await subscriberWorkspaceEventsResult(Number(raw));
  return NextResponse.json(result.body, {
    status: result.status,
    headers: { "cache-control": "no-store" }
  });
}
