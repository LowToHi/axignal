import { NextResponse } from "next/server";

import { axentCreateResult, axentListResult } from "@/lib/axent-server";
import { subscriberWorkspaceEnabled } from "@/lib/subscriber-workspace-server";

export const dynamic = "force-dynamic";

const REQUEST_ID = /^axent_req_[A-Za-z0-9_-]{8,120}$/;

function response(result: { status: number; body: unknown }) {
  return NextResponse.json(result.body, {
    status: result.status,
    headers: { "cache-control": "no-store" }
  });
}

export async function GET() {
  if (!subscriberWorkspaceEnabled()) {
    return NextResponse.json({ error: "Not found", code: "not_found" }, { status: 404 });
  }
  return response(await axentListResult());
}

export async function POST(request: Request) {
  if (!subscriberWorkspaceEnabled()) {
    return NextResponse.json({ error: "Not found", code: "not_found" }, { status: 404 });
  }
  const input = (await request.json().catch(() => null)) as Record<string, unknown> | null;
  const requestId = typeof input?.request_id === "string" ? input.request_id : "";
  const title = typeof input?.title === "string" ? input.title.trim() : "";
  const retentionClass = input?.retention_class;
  if (
    !REQUEST_ID.test(requestId) ||
    !title ||
    title.length > 160 ||
    !["EPHEMERAL_30D", "STANDARD_90D"].includes(String(retentionClass))
  ) {
    return NextResponse.json(
      { error: "Invalid AXENT conversation request.", code: "invalid_request" },
      { status: 400, headers: { "cache-control": "no-store" } }
    );
  }
  return response(
    await axentCreateResult({
      request_id: requestId,
      title,
      retention_class: retentionClass as "EPHEMERAL_30D" | "STANDARD_90D"
    })
  );
}
