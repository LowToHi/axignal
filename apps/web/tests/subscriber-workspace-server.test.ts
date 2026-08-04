import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { readFile, rm } from "node:fs/promises";
import path from "node:path";
import test from "node:test";

import type { SubscriberWorkspaceActionRequest } from "../lib/subscriber-workspace-contract";
import {
  capabilitiesForRoles,
  capabilitiesForEntitlement,
  executeSubscriberWorkspaceFixtureAction,
  getSubscriberWorkspaceFixtureBootstrap,
  getSubscriberWorkspaceFixtureEvents,
  parseSubscriberWorkspaceAction,
  subscriberWorkspaceEnabled,
  subscriberWorkspaceFixtureConfiguration,
  type SubscriberWorkspaceServerActor
} from "../lib/subscriber-workspace-server";

const owner: SubscriberWorkspaceServerActor = {
  id: "axfx_usr_owner",
  email: "owner@fixture.invalid",
  displayName: "Engineering Owner",
  tenantId: "axfx_tenant_test",
  roles: ["OWNER"],
  assuranceLevel: "AAL2"
};

function action(
  actionId: string,
  actionType: SubscriberWorkspaceActionRequest["action_type"],
  tenantRevision: number,
  payload: Record<string, unknown>,
  confirmed = false
): SubscriberWorkspaceActionRequest {
  return {
    action_id: actionId,
    action_type: actionType,
    tenant_revision: tenantRevision,
    payload,
    ...(confirmed
      ? { confirmation: { confirmed: true as const, authority: "subscriber" as const } }
      : {})
  };
}

function isolatedStore() {
  const testNamespace = `test_${randomUUID().replaceAll("-", "")}`;
  return {
    options: { testNamespace },
    directory: path.join(
      process.cwd(),
      ".data",
      "subscriber-workspace",
      "__tests__",
      testNamespace
    )
  };
}

test("fixture mode is explicit and rejected in unmarked production", () => {
  assert.deepEqual(
    subscriberWorkspaceFixtureConfiguration({
      NODE_ENV: "production",
      AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE: "explicit"
    }),
    { requested: true, allowed: false, rejected: true }
  );
  assert.deepEqual(
    subscriberWorkspaceFixtureConfiguration({
      NODE_ENV: "production",
      AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE: "explicit",
      AXIGNAL_SUBSCRIBER_WORKSPACE_ENVIRONMENT: "preview"
    }),
    { requested: true, allowed: true, rejected: false }
  );
  assert.deepEqual(subscriberWorkspaceFixtureConfiguration({ NODE_ENV: "test" }), {
    requested: false,
    allowed: false,
    rejected: false
  });
});

test("roles resolve capabilities without plan-label inference", () => {
  assert.deepEqual(capabilitiesForRoles(["VIEWER"]), ["workspace:view"]);
  assert.ok(capabilitiesForRoles(["REVIEWER"]).includes("submission:approve"));
  assert.ok(!capabilitiesForRoles(["REVIEWER"]).includes("submission:prepare"));
  assert.ok(!capabilitiesForRoles(["ADMIN"]).includes("billing:manage"));
  assert.deepEqual(capabilitiesForRoles(["OWNER"]), [
    "workspace:view",
    "workspace:create",
    "workspace:qualify",
    "workspace:edit",
    "requirement:edit",
    "evidence:attach",
    "document:manage",
    "work:assign",
    "clarification:draft",
    "clarification:approve",
    "clarification:confirm_sent",
    "commercial:view",
    "commercial:edit",
    "commercial:approve",
    "submission:prepare",
    "submission:approve",
    "submission:confirm_external",
    "outcome:record",
    "audit:view",
    "export:create",
    "team:manage",
    "billing:view",
    "billing:manage",
    "settings:manage"
  ]);
  assert.deepEqual(capabilitiesForEntitlement(["OWNER"], "read_only"), [
    "workspace:view",
    "commercial:view",
    "audit:view",
    "billing:view"
  ]);
  assert.deepEqual(capabilitiesForEntitlement(["OWNER"], "suspended"), [
    "billing:view"
  ]);
});

test("action parser rejects client-defined authority and malformed identifiers", () => {
  assert.throws(
    () =>
      parseSubscriberWorkspaceAction({
        action_id: "client-action",
        action_type: "workspace.open",
        tenant_revision: 1,
        payload: {},
        roles: ["OWNER"],
        capabilities: ["billing:manage"]
      }),
    /Invalid action request/
  );
  const parsed = parseSubscriberWorkspaceAction({
    action_id: "ax_action_open_001",
    action_type: "workspace.open",
    tenant_revision: 1,
    payload: { workspace_id: "axfx_ws_eu_cloud_001" },
    roles: ["OWNER"]
  });
  assert.equal("roles" in parsed, false);
});

test("fixture actions persist once, replay idempotently and append a bounded audit event", async () => {
  const { directory, options } = isolatedStore();
  try {
    const initial = await getSubscriberWorkspaceFixtureBootstrap(owner, options);
    assert.equal(initial.tenant.revision, 1);
    assert.equal(initial.fixture_boundary.label, "ENGINEERING FIXTURE · NOT LIVE DATA");

    const request = action(
      "axfx_action_requirement_001",
      "requirement.update",
      1,
      {
        tenant_id: owner.tenantId,
        workspace_id: "axfx_ws_eu_cloud_001",
        requirement_id: "axfx_req_turnover_003",
        status: "blocked"
      }
    );
    const first = await executeSubscriberWorkspaceFixtureAction(owner, request, options);
    assert.equal(first.idempotent_replay, false);
    assert.equal(first.tenant_revision, 2);
    assert.equal(first.event?.type, "requirement.updated");
    assert.deepEqual(first.event?.details, { status: "blocked" });

    const replay = await executeSubscriberWorkspaceFixtureAction(owner, request, options);
    assert.equal(replay.idempotent_replay, true);
    assert.equal(replay.tenant_revision, 2);

    const events = await getSubscriberWorkspaceFixtureEvents(owner, 0, options);
    assert.equal(events.events.length, 1);
    const stored = JSON.parse(
      await readFile(path.join(directory, `${owner.tenantId}.json`), "utf8")
    ) as { events: unknown[]; action_receipts: Record<string, unknown> };
    assert.equal(stored.events.length, 1);
    assert.equal(Object.keys(stored.action_receipts).length, 1);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("subscriber kill switch preserves the tenant ledger and restores the exact workspace context", async () => {
  const previousEnabled = process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED;
  const { directory, options } = isolatedStore();
  const ledgerPath = path.join(directory, `${owner.tenantId}.json`);

  try {
    process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED = "true";
    assert.equal(subscriberWorkspaceEnabled(), true);

    const initial = await getSubscriberWorkspaceFixtureBootstrap(owner, options);
    const mutation = await executeSubscriberWorkspaceFixtureAction(
      owner,
      action(
        `axfx_action_rollback_${randomUUID().replaceAll("-", "")}`,
        "requirement.update",
        initial.tenant.revision,
        {
          workspace_id: "axfx_ws_eu_cloud_001",
          requirement_id: "axfx_req_turnover_003",
          status: "blocked"
        }
      ),
      options
    );
    const ledgerBeforeDisable = await readFile(ledgerPath, "utf8");

    process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED = "false";
    assert.equal(subscriberWorkspaceEnabled(), false);
    assert.equal(await readFile(ledgerPath, "utf8"), ledgerBeforeDisable);

    process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED = "true";
    assert.equal(subscriberWorkspaceEnabled(), true);

    const restored = await getSubscriberWorkspaceFixtureBootstrap(owner, options);
    const restoredEvents = await getSubscriberWorkspaceFixtureEvents(owner, 0, options);
    const restoredRequirement = restored.route_data.workspaces
      .find((workspace) => workspace.id === "axfx_ws_eu_cloud_001")
      ?.requirements.find((requirement) => requirement.id === "axfx_req_turnover_003");

    assert.equal(restored.tenant.revision, mutation.tenant_revision);
    assert.equal(restoredRequirement?.status, "blocked");
    assert.equal(restoredEvents.events.length, 1);
    assert.equal(restoredEvents.events[0]?.type, "requirement.updated");
    assert.equal(await readFile(ledgerPath, "utf8"), ledgerBeforeDisable);
  } finally {
    if (previousEnabled === undefined) {
      delete process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED;
    } else {
      process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED = previousEnabled;
    }
    await rm(directory, { recursive: true, force: true });
  }
});

test("cross-tenant workspace scope fails as a generic 404", async () => {
  const { directory, options } = isolatedStore();
  try {
    const request = action("axfx_action_foreign_001", "workspace.open", 1, {
      tenant_id: "axfx_tenant_foreign",
      workspace_id: "axfx_ws_eu_cloud_001"
    });
    await assert.rejects(
      () =>
        executeSubscriberWorkspaceFixtureAction(owner, request, options),
      (error: unknown) => {
        assert.equal((error as { status?: number }).status, 404);
        assert.equal((error as { code?: string }).code, "not_found");
        assert.equal((error as Error).message, "Subscriber workspace not found.");
        return true;
      }
    );
    await assert.rejects(
      () =>
        executeSubscriberWorkspaceFixtureAction(owner, request, options),
      (error: unknown) => {
        assert.equal((error as { status?: number }).status, 404);
        return true;
      }
    );
    const events = await getSubscriberWorkspaceFixtureEvents(owner, 0, options);
    assert.equal(events.events.length, 1);
    assert.equal(events.events[0]?.type, "mutation.denied");
    assert.deepEqual(events.events[0]?.details, { code: "not_found" });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("clarification author cannot self-approve and external confirmation never executes an action", async () => {
  const { directory, options } = isolatedStore();
  const author: SubscriberWorkspaceServerActor = {
    ...owner,
    id: "axfx_usr_contributor"
  };
  try {
    await assert.rejects(
      () =>
        executeSubscriberWorkspaceFixtureAction(
          author,
          action(
            "axfx_action_clarification_001",
            "clarification.approve",
            1,
            {
              workspace_id: "axfx_ws_eu_cloud_001",
              clarification_id: "axfx_clar_security_001"
            },
            true
          ),
          options
        ),
      (error: unknown) => {
        assert.equal(
          (error as { code?: string }).code,
          "separation_of_duties_required"
        );
        return true;
      }
    );

    await assert.rejects(
      () =>
        executeSubscriberWorkspaceFixtureAction(
          owner,
          action("axfx_action_submission_001", "external_action.confirm", 1, {
            workspace_id: "axfx_ws_eu_cloud_001",
            target_type: "submission"
          }),
          options
        ),
      (error: unknown) => {
        assert.equal((error as { code?: string }).code, "confirmation_required");
        return true;
      }
    );
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
