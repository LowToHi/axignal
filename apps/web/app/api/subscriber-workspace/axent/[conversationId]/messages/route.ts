import { NextResponse } from "next/server";

import { axentAppendMessageResult } from "@/lib/axent-server";
import { subscriberWorkspaceEnabled } from "@/lib/subscriber-workspace-server";

export const dynamic = "force-dynamic";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const REQUEST_ID = /^axent_req_[A-Za-z0-9_-]{8,120}$/;

type RouteContext = { params: Promise<{ conversationId: string }> };

export async function POST(request: Request, context: RouteContext) {
  if (!subscriberWorkspaceEnabled()) {
    return NextResponse.json({ error: "Not found", code: "not_found" }, { status: 404 });
  }
  const { conversationId } = await context.params;
  const input = (await request.json().catch(() => null)) as Record<string, unknown> | null;
  const requestId = typeof input?.request_id === "string" ? input.request_id : "";
  const role = typeof input?.role === "string" ? input.role : "";
  const content = typeof input?.content === "string" ? input.content.trim() : "";
  if (
    !UUID_PATTERN.test(conversationId) ||
    !REQUEST_ID.test(requestId) ||
    !["USER", "ASSISTANT", "SYSTEM"].includes(role) ||
    !content ||
    content.length > 4_000
  ) {
    return NextResponse.json(
      { error: "Invalid AXENT message request.", code: "invalid_request" },
      { status: 400, headers: { "cache-control": "no-store" } }
    );
  }
  const result = await axentAppendMessageResult(conversationId, {
    request_id: requestId,
    role: role as "USER" | "ASSISTANT" | "SYSTEM",
    content
  });
  return NextResponse.json(result.body, {
    status: result.status,
    headers: { "cache-control": "no-store" }
  });
}
