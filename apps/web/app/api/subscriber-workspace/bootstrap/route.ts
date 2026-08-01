import { NextResponse } from "next/server";

import {
  subscriberWorkspaceBootstrapResult,
  subscriberWorkspaceEnabled
} from "@/lib/subscriber-workspace-server";

export const dynamic = "force-dynamic";

export async function GET() {
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
  const result = await subscriberWorkspaceBootstrapResult();
  return NextResponse.json(result.body, {
    status: result.status,
    headers: { "cache-control": "no-store" }
  });
}
