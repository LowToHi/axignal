import { NextResponse } from "next/server";

import { axentDeleteResult, axentExportResult } from "@/lib/axent-server";
import { subscriberWorkspaceEnabled } from "@/lib/subscriber-workspace-server";

export const dynamic = "force-dynamic";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

type RouteContext = { params: Promise<{ conversationId: string }> };

function response(result: { status: number; body: unknown }) {
  return NextResponse.json(result.body, {
    status: result.status,
    headers: { "cache-control": "no-store" }
  });
}

async function conversationId(context: RouteContext): Promise<string | null> {
  const value = (await context.params).conversationId;
  return UUID_PATTERN.test(value) ? value : null;
}

export async function GET(_request: Request, context: RouteContext) {
  if (!subscriberWorkspaceEnabled()) {
    return NextResponse.json({ error: "Not found", code: "not_found" }, { status: 404 });
  }
  const id = await conversationId(context);
  if (!id) {
    return NextResponse.json(
      { error: "Invalid conversation identifier.", code: "invalid_request" },
      { status: 400, headers: { "cache-control": "no-store" } }
    );
  }
  return response(await axentExportResult(id));
}

export async function DELETE(_request: Request, context: RouteContext) {
  if (!subscriberWorkspaceEnabled()) {
    return NextResponse.json({ error: "Not found", code: "not_found" }, { status: 404 });
  }
  const id = await conversationId(context);
  if (!id) {
    return NextResponse.json(
      { error: "Invalid conversation identifier.", code: "invalid_request" },
      { status: 400, headers: { "cache-control": "no-store" } }
    );
  }
  return response(await axentDeleteResult(id, new Date().toISOString()));
}
