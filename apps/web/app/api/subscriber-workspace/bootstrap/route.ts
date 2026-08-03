import { NextResponse } from "next/server";

import type { SubscriberWorkspaceBootstrap } from "@/lib/subscriber-workspace-contract";
import {
  subscriberWorkspaceBootstrapResult,
  subscriberWorkspaceEnabled
} from "@/lib/subscriber-workspace-server";

export const dynamic = "force-dynamic";

const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1_000;

function withCorrectDeadlineSummary(
  bootstrap: SubscriberWorkspaceBootstrap,
  now = Date.now()
): SubscriberWorkspaceBootstrap {
  const horizon = now + THIRTY_DAYS_MS;
  const deadlinesNext30Days = bootstrap.route_data.workspaces.filter((workspace) => {
    const deadline = Date.parse(workspace.deadline);
    return Number.isFinite(deadline) && deadline >= now && deadline <= horizon;
  }).length;

  return {
    ...bootstrap,
    route_data: {
      ...bootstrap.route_data,
      summary: {
        ...bootstrap.route_data.summary,
        deadlines_next_30_days: deadlinesNext30Days
      }
    }
  };
}

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
  const body = result.status >= 200 && result.status < 300
    ? withCorrectDeadlineSummary(result.body as SubscriberWorkspaceBootstrap)
    : result.body;
  return NextResponse.json(body, {
    status: result.status,
    headers: { "cache-control": "no-store" }
  });
}
