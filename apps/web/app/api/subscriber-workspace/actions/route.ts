import { NextResponse } from "next/server";

import type {
  SubscriberWorkspaceActionResult,
  SubscriberWorkspaceActionType,
  SubscriberWorkspaceBootstrap
} from "@/lib/subscriber-workspace-contract";
import { projectSubscriberWorkspaceActionResult } from "@/lib/subscriber-workspace-event-projection";
import {
  subscriberWorkspaceActionResult,
  subscriberWorkspaceBootstrapResult,
  subscriberWorkspaceEnabled
} from "@/lib/subscriber-workspace-server";

export const dynamic = "force-dynamic";

const MAX_ACTION_BYTES = 256 * 1024;
const GUARDED_ACTIONS = new Set<SubscriberWorkspaceActionType>([
  "requirement.update",
  "submission.prepare",
  "submission.approve"
]);

function rejected(
  error: string,
  code: "invalid_request" | "state_conflict",
  status: 400 | 409
) {
  return NextResponse.json(
    {
      error,
      code,
      state: "rejected",
      recoverable: false
    },
    { status, headers: { "cache-control": "no-store" } }
  );
}

function recordValue(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

async function enforceServerPreconditions(input: unknown): Promise<NextResponse | null> {
  const action = recordValue(input);
  if (
    !action ||
    typeof action.action_type !== "string" ||
    !GUARDED_ACTIONS.has(action.action_type as SubscriberWorkspaceActionType)
  ) {
    return null;
  }
  const payload = recordValue(action.payload);
  if (!payload || typeof payload.workspace_id !== "string") {
    return rejected(
      "A workspace-scoped action requires workspace_id.",
      "invalid_request",
      400
    );
  }

  const bootstrapResult = await subscriberWorkspaceBootstrapResult();
  if (bootstrapResult.status < 200 || bootstrapResult.status >= 300) {
    return NextResponse.json(bootstrapResult.body, {
      status: bootstrapResult.status,
      headers: { "cache-control": "no-store" }
    });
  }
  const bootstrap = bootstrapResult.body as SubscriberWorkspaceBootstrap;
  const workspace = bootstrap.route_data.workspaces.find(
    (item) => item.id === payload.workspace_id
  );
  if (!workspace) {
    return rejected("Subscriber workspace not found.", "state_conflict", 409);
  }

  if (action.action_type === "requirement.update" && payload.status === "met") {
    if (typeof payload.requirement_id !== "string") {
      return rejected("requirement_id is required.", "invalid_request", 400);
    }
    const requirement = workspace.requirements.find(
      (item) => item.id === payload.requirement_id
    );
    if (!requirement) {
      return rejected("Requirement not found.", "state_conflict", 409);
    }
    const verifiedEvidence = workspace.evidence.some(
      (item) =>
        requirement.evidence_ids.includes(item.id) && item.status === "verified"
    );
    if (!verifiedEvidence) {
      return rejected(
        "A requirement cannot be marked met without linked verified evidence.",
        "state_conflict",
        409
      );
    }
  }

  if (action.action_type === "submission.prepare") {
    const blockingRequirement = workspace.requirements.some(
      (item) =>
        item.blocking && !["met", "not_applicable"].includes(item.status)
    );
    const unacknowledgedAmendment = workspace.amendments.some(
      (item) => !item.acknowledged
    );
    if (blockingRequirement || unacknowledgedAmendment) {
      return rejected(
        "Submission preparation is blocked until mandatory requirements and amendments are revalidated.",
        "state_conflict",
        409
      );
    }
    if (!workspace.commercial.approved_by) {
      return rejected(
        "Submission preparation requires an approved commercial baseline.",
        "state_conflict",
        409
      );
    }
  }

  if (
    action.action_type === "submission.approve" &&
    workspace.submission.preflight_status !== "ready"
  ) {
    return rejected(
      "Submission approval requires a completed ready preflight.",
      "state_conflict",
      409
    );
  }

  return null;
}

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

  const preconditionFailure = await enforceServerPreconditions(input);
  if (preconditionFailure) return preconditionFailure;

  const result = await subscriberWorkspaceActionResult(input);
  const body =
    result.status >= 200 && result.status < 300
      ? projectSubscriberWorkspaceActionResult(
          result.body as SubscriberWorkspaceActionResult
        )
      : result.body;
  return NextResponse.json(body, {
    status: result.status,
    headers: { "cache-control": "no-store" }
  });
}
