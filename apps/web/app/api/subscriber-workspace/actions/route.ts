import { NextResponse } from "next/server";

import {
  subscriberWorkspaceActionResult,
  subscriberWorkspaceEnabled
} from "@/lib/subscriber-workspace-server";

export const dynamic = "force-dynamic";

const MAX_ACTION_BYTES = 256 * 1024;

export async function POST(request: Request) {
  if (!subscriberWorkspaceEnabled()) {
    return NextResponse.json(
      {
        error: "Subscriber workspace is disabled.",
        code: "not_found",
        state: "rejected",
        recoverable: false
      },
      { status: 404, headers: { "cache-control": "no-store" } }
    );
  }

  const contentLength = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(contentLength) && contentLength > MAX_ACTION_BYTES) {
    return NextResponse.json(
      {
        error: "Action request is too large.",
        code: "invalid_request",
        state: "rejected",
        recoverable: false
      },
      { status: 413, headers: { "cache-control": "no-store" } }
    );
  }

  const raw = await request.text();
  if (Buffer.byteLength(raw, "utf8") > MAX_ACTION_BYTES) {
    return NextResponse.json(
      {
        error: "Action request is too large.",
        code: "invalid_request",
        state: "rejected",
        recoverable: false
      },
      { status: 413, headers: { "cache-control": "no-store" } }
    );
  }

  let input: unknown;
  try {
    input = JSON.parse(raw);
  } catch {
    return NextResponse.json(
      {
        error: "Invalid JSON action request.",
        code: "invalid_request",
        state: "rejected",
        recoverable: false
      },
      { status: 400, headers: { "cache-control": "no-store" } }
    );
  }

  const result = await subscriberWorkspaceActionResult(input);
  return NextResponse.json(result.body, {
    status: result.status,
    headers: { "cache-control": "no-store" }
  });
}
