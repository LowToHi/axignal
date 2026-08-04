import assert from "node:assert/strict";
import test from "node:test";

import type { SubscriberWorkspaceAuditEvent } from "../lib/subscriber-workspace-contract";
import {
  projectSubscriberWorkspaceActionResult,
  projectSubscriberWorkspaceAuditEvent,
  projectSubscriberWorkspaceEventsResult
} from "../lib/subscriber-workspace-event-projection";

function event(
  objectType: string,
  details: SubscriberWorkspaceAuditEvent["details"]
): SubscriberWorkspaceAuditEvent {
  return {
    cursor: 1,
    id: "axfx_evt_projection_001",
    tenant_id: "axfx_tenant_test",
    workspace_id: "axfx_ws_eu_cloud_001",
    actor_id: "axfx_usr_owner",
    type: "decision.recorded",
    object_type: objectType,
    object_id: "axfx_object_projection_001",
    occurred_at: "2026-08-04T00:00:00.000Z",
    tenant_revision: 2,
    details
  };
}

test("projects generic fixture mutations into precise canonical event types", () => {
  assert.equal(
    projectSubscriberWorkspaceAuditEvent(
      event("clarification", { state: "draft" })
    ).type,
    "clarification.drafted"
  );
  assert.equal(
    projectSubscriberWorkspaceAuditEvent(
      event("commercial_model", { updated: true })
    ).type,
    "commercial.updated"
  );
  assert.equal(
    projectSubscriberWorkspaceAuditEvent(
      event("commercial_model", { approved: true })
    ).type,
    "commercial.approved"
  );
  assert.equal(
    projectSubscriberWorkspaceAuditEvent(
      event("submission_package", { status: "ready" })
    ).type,
    "submission.prepared"
  );
  assert.equal(
    projectSubscriberWorkspaceAuditEvent(
      event("submission_package", { approved: true })
    ).type,
    "submission.approved"
  );
});

test("preserves qualification decisions and projects action and stream results consistently", () => {
  const qualification = event("qualification_decision", { decision: "pursue" });
  assert.equal(
    projectSubscriberWorkspaceAuditEvent(qualification).type,
    "decision.recorded"
  );

  const draft = event("clarification", { state: "draft" });
  const actionResult = projectSubscriberWorkspaceActionResult({
    action_id: "ax_action_projection_001",
    action_type: "clarification.draft",
    mutation_state: "persisted",
    idempotent_replay: false,
    tenant_revision: 2,
    event: draft,
    bootstrap: {} as never
  });
  const streamResult = projectSubscriberWorkspaceEventsResult({
    events: [draft, qualification],
    next_cursor: 2
  });

  assert.equal(actionResult.event?.type, "clarification.drafted");
  assert.deepEqual(
    streamResult.events.map((item) => item.type),
    ["clarification.drafted", "decision.recorded"]
  );
  assert.equal(streamResult.next_cursor, 2);
});
