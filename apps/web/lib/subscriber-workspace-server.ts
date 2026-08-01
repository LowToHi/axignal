import { createHash, randomUUID } from "node:crypto";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";

import {
  SUBSCRIBER_WORKSPACE_CAPABILITIES,
  SUBSCRIBER_WORKSPACE_SCHEMA_VERSION,
  isSubscriberWorkspaceActionType,
  isSubscriberWorkspaceRole,
  type SubscriberWorkspaceActionRequest,
  type SubscriberWorkspaceActionResult,
  type SubscriberWorkspaceAuditEvent,
  type SubscriberWorkspaceBootstrap,
  type SubscriberWorkspaceCapability,
  type SubscriberWorkspaceError,
  type SubscriberWorkspaceEventType,
  type SubscriberWorkspaceRole
} from "./subscriber-workspace-contract";
import {
  createSubscriberWorkspaceFixtureStore,
  FIXTURE_DISCLOSURE,
  type SubscriberWorkspaceFixtureStore
} from "./subscriber-workspace-fixture";
import {
  buildApiIdentityAssertion,
  getAuthenticatedIdentity,
  type AuthenticatedIdentity
} from "./server-auth";

export type SubscriberWorkspaceServerActor = {
  id: string;
  email: string;
  displayName: string;
  tenantId: string;
  roles: SubscriberWorkspaceRole[];
  assuranceLevel: string | null;
  authenticatedIdentity?: AuthenticatedIdentity;
};

export type SubscriberWorkspaceServerResult<T> = {
  status: number;
  body: T | SubscriberWorkspaceError;
};

type StoreOptions = { testNamespace?: string };

const FIXTURE_MODE = "explicit";
const ACTION_ID_PATTERN = /^(?:ax_action|axfx_action)_[A-Za-z0-9_-]{6,120}$/;
const SAFE_ID_PATTERN = /^axfx_[A-Za-z0-9_-]{3,180}$/;
const lockQueues = new Map<string, Promise<void>>();

const ALL_CAPABILITIES = [...SUBSCRIBER_WORKSPACE_CAPABILITIES];
const ROLE_CAPABILITIES: Record<
  SubscriberWorkspaceRole,
  readonly SubscriberWorkspaceCapability[]
> = {
  OWNER: ALL_CAPABILITIES,
  ADMIN: ALL_CAPABILITIES.filter((item) => item !== "billing:manage"),
  BID_MANAGER: [
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
    "submission:prepare",
    "submission:approve",
    "submission:confirm_external",
    "outcome:record",
    "audit:view",
    "export:create"
  ],
  CONTRIBUTOR: [
    "workspace:view",
    "workspace:edit",
    "requirement:edit",
    "evidence:attach",
    "document:manage",
    "work:assign",
    "clarification:draft",
    "commercial:view"
  ],
  REVIEWER: [
    "workspace:view",
    "clarification:approve",
    "commercial:view",
    "commercial:approve",
    "submission:approve",
    "audit:view",
    "export:create"
  ],
  FINANCE: [
    "workspace:view",
    "commercial:view",
    "commercial:edit",
    "commercial:approve",
    "billing:view",
    "export:create"
  ],
  VIEWER: ["workspace:view"]
};

const ACTION_POLICY: Record<
  SubscriberWorkspaceActionRequest["action_type"],
  { capability: SubscriberWorkspaceCapability; event: SubscriberWorkspaceEventType }
> = {
  "route.view": { capability: "workspace:view", event: "route.viewed" },
  "lens.change": { capability: "workspace:view", event: "lens.changed" },
  "opportunity.select": {
    capability: "workspace:view",
    event: "opportunity.selected"
  },
  "workspace.open": { capability: "workspace:view", event: "workspace.opened" },
  "workspace.create": {
    capability: "workspace:create",
    event: "workspace.opened"
  },
  "decision.record": {
    capability: "workspace:qualify",
    event: "decision.recorded"
  },
  "requirement.update": {
    capability: "requirement:edit",
    event: "requirement.updated"
  },
  "evidence.attach": {
    capability: "evidence:attach",
    event: "evidence.attached"
  },
  "task.assign": { capability: "work:assign", event: "task.assigned" },
  "clarification.draft": {
    capability: "clarification:draft",
    event: "decision.recorded"
  },
  "clarification.approve": {
    capability: "clarification:approve",
    event: "clarification.approved"
  },
  "handoff.open": {
    capability: "clarification:approve",
    event: "handoff.opened"
  },
  "external_action.confirm": {
    capability: "submission:confirm_external",
    event: "external_action.confirmed"
  },
  "amendment.acknowledge": {
    capability: "workspace:edit",
    event: "amendment.acknowledged"
  },
  "commercial.update": {
    capability: "commercial:edit",
    event: "decision.recorded"
  },
  "commercial.approve": {
    capability: "commercial:approve",
    event: "decision.recorded"
  },
  "submission.prepare": {
    capability: "submission:prepare",
    event: "decision.recorded"
  },
  "submission.approve": {
    capability: "submission:approve",
    event: "decision.recorded"
  },
  "preflight.complete": {
    capability: "submission:prepare",
    event: "preflight.completed"
  },
  "outcome.record": {
    capability: "outcome:record",
    event: "outcome.recorded"
  },
  "recovery.request": {
    capability: "workspace:view",
    event: "recovery.requested"
  }
};

class WorkspaceServerError extends Error {
  constructor(
    readonly status: number,
    readonly code: SubscriberWorkspaceError["code"],
    message: string,
    readonly recoverable = false
  ) {
    super(message);
  }
}

function errorResult(error: unknown): SubscriberWorkspaceServerResult<never> {
  if (error instanceof WorkspaceServerError) {
    return {
      status: error.status,
      body: {
        error: error.message,
        code: error.code,
        state: error.recoverable ? "recovery_available" : "rejected",
        recoverable: error.recoverable
      }
    };
  }
  return {
    status: 500,
    body: {
      error: "Subscriber workspace operation failed.",
      code: "upstream_error",
      state: "recoverable_error",
      recoverable: true
    }
  };
}

function boolEnv(name: string): boolean {
  return ["1", "true", "yes", "on"].includes(
    (process.env[name] ?? "").trim().toLowerCase()
  );
}

export function subscriberWorkspaceFixtureConfiguration(environment = process.env) {
  const requested = environment.AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE === FIXTURE_MODE;
  const production = environment.NODE_ENV === "production";
  const deploymentMarker = (
    environment.AXIGNAL_SUBSCRIBER_WORKSPACE_ENVIRONMENT ?? ""
  ).trim().toLowerCase();
  const markedNonProduction = ["local", "development", "test", "preview"].includes(
    deploymentMarker
  );
  return {
    requested,
    allowed: requested && (!production || markedNonProduction),
    rejected: requested && production && !markedNonProduction
  };
}

export function capabilitiesForRoles(
  roles: readonly SubscriberWorkspaceRole[]
): SubscriberWorkspaceCapability[] {
  const capabilities = new Set<SubscriberWorkspaceCapability>();
  for (const role of roles) {
    for (const capability of ROLE_CAPABILITIES[role]) capabilities.add(capability);
  }
  return SUBSCRIBER_WORKSPACE_CAPABILITIES.filter((item) => capabilities.has(item));
}

export function capabilitiesForEntitlement(
  roles: readonly SubscriberWorkspaceRole[],
  status: SubscriberWorkspaceFixtureStore["entitlement"]["status"]
): SubscriberWorkspaceCapability[] {
  const roleCapabilities = capabilitiesForRoles(roles);
  if (status === "active" || status === "trial") return roleCapabilities;
  const allowed =
    status === "read_only"
      ? new Set<SubscriberWorkspaceCapability>([
          "workspace:view",
          "commercial:view",
          "audit:view",
          "billing:view"
        ])
      : new Set<SubscriberWorkspaceCapability>(["billing:view"]);
  return roleCapabilities.filter((capability) => allowed.has(capability));
}

function hashIdentifier(value: string): string {
  return createHash("sha256").update(value).digest("hex").slice(0, 16);
}

function serverResolvedRoles(identity: AuthenticatedIdentity | null): SubscriberWorkspaceRole[] {
  const fromIdentity = (identity?.roles ?? []).filter(isSubscriberWorkspaceRole);
  if (fromIdentity.length > 0) return [...new Set(fromIdentity)];
  const fromEnvironment = (process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_ROLES ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(isSubscriberWorkspaceRole);
  if (fromEnvironment.length > 0) return [...new Set(fromEnvironment)];
  return subscriberWorkspaceFixtureConfiguration().allowed ? ["OWNER"] : ["VIEWER"];
}

export async function resolveSubscriberWorkspaceActor(): Promise<SubscriberWorkspaceServerActor | null> {
  const identity = await getAuthenticatedIdentity();
  const fixture = subscriberWorkspaceFixtureConfiguration();
  if (fixture.rejected) {
    throw new WorkspaceServerError(
      503,
      "fixture_mode_rejected",
      "Fixture mode is rejected without an explicit non-production environment marker."
    );
  }
  if (!identity && !fixture.allowed) return null;
  if (fixture.allowed) {
    const sourceTenant = identity?.tenantId ?? "local-engineering-tenant";
    const sourceActor = identity?.subject ?? "local-engineering-owner";
    const actorId = identity ? `axfx_usr_${hashIdentifier(sourceActor)}` : "axfx_usr_owner";
    return {
      id: actorId,
      email: identity?.email ?? "owner@fixture.invalid",
      displayName: identity?.email.split("@")[0] ?? "Engineering Owner",
      tenantId: identity
        ? `axfx_tenant_${hashIdentifier(sourceTenant)}`
        : "axfx_tenant_northstar",
      roles: serverResolvedRoles(identity),
      assuranceLevel: identity?.assuranceLevel ?? null,
      ...(identity ? { authenticatedIdentity: identity } : {})
    };
  }
  return {
    id: identity!.subject,
    email: identity!.email,
    displayName: identity!.email.split("@")[0] ?? identity!.email,
    tenantId: identity!.tenantId,
    roles: serverResolvedRoles(identity),
    assuranceLevel: identity!.assuranceLevel ?? null,
    authenticatedIdentity: identity!
  };
}

function storeDirectory(options?: StoreOptions): string {
  const base = path.join(process.cwd(), ".data", "subscriber-workspace");
  if (!options?.testNamespace) return base;
  if (!/^[A-Za-z0-9_-]{8,100}$/.test(options.testNamespace)) {
    throw new WorkspaceServerError(400, "invalid_request", "Invalid test store namespace.");
  }
  return path.join(base, "__tests__", options.testNamespace);
}

function storePath(actor: SubscriberWorkspaceServerActor, options?: StoreOptions): string {
  if (!SAFE_ID_PATTERN.test(actor.tenantId)) {
    throw new WorkspaceServerError(404, "not_found", "Subscriber workspace not found.");
  }
  return path.join(storeDirectory(options), `${actor.tenantId}.json`);
}

function assertFixtureStore(value: unknown, tenantId: string): SubscriberWorkspaceFixtureStore {
  if (
    !value ||
    typeof value !== "object" ||
    (value as { schema_version?: unknown }).schema_version !==
      "axignal.subscriber-workspace-store/v1"
  ) {
    throw new WorkspaceServerError(
      503,
      "source_unavailable",
      "Subscriber workspace store is invalid.",
      true
    );
  }
  const store = value as SubscriberWorkspaceFixtureStore;
  if (store.tenant.id !== tenantId) {
    throw new WorkspaceServerError(404, "not_found", "Subscriber workspace not found.");
  }
  return store;
}

async function loadFixtureStore(
  actor: SubscriberWorkspaceServerActor,
  options?: StoreOptions
): Promise<SubscriberWorkspaceFixtureStore> {
  const filename = storePath(actor, options);
  try {
    return assertFixtureStore(JSON.parse(await readFile(filename, "utf8")), actor.tenantId);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      if (error instanceof WorkspaceServerError) throw error;
      throw new WorkspaceServerError(
        503,
        "source_unavailable",
        "Subscriber workspace store is unavailable.",
        true
      );
    }
    const store = createSubscriberWorkspaceFixtureStore(actor.tenantId);
    await persistFixtureStore(actor, store, options);
    return store;
  }
}

async function persistFixtureStore(
  actor: SubscriberWorkspaceServerActor,
  store: SubscriberWorkspaceFixtureStore,
  options?: StoreOptions
): Promise<void> {
  const filename = storePath(actor, options);
  await mkdir(path.dirname(filename), { recursive: true });
  const temporary = `${filename}.${randomUUID()}.tmp`;
  await writeFile(temporary, `${JSON.stringify(store, null, 2)}\n`, {
    encoding: "utf8",
    mode: 0o600
  });
  await rename(temporary, filename);
}

async function withStoreLock<T>(key: string, operation: () => Promise<T>): Promise<T> {
  const previous = lockQueues.get(key) ?? Promise.resolve();
  let release!: () => void;
  const current = new Promise<void>((resolve) => {
    release = resolve;
  });
  const chained = previous.then(() => current);
  lockQueues.set(key, chained);
  await previous;
  try {
    return await operation();
  } finally {
    release();
    if (lockQueues.get(key) === chained) lockQueues.delete(key);
  }
}

function fixtureBootstrap(
  actor: SubscriberWorkspaceServerActor,
  store: SubscriberWorkspaceFixtureStore
): SubscriberWorkspaceBootstrap {
  const capabilities = capabilitiesForEntitlement(actor.roles, store.entitlement.status);
  const blockingRequirements = store.workspaces.reduce(
    (total, workspace) =>
      total +
      workspace.requirements.filter(
        (item) => item.blocking && !["met", "not_applicable"].includes(item.status)
      ).length,
    0
  );
  const displayName =
    store.members.find((member) => member.id === actor.id)?.display_name ??
    actor.displayName;
  return {
    schema_version: SUBSCRIBER_WORKSPACE_SCHEMA_VERSION,
    state:
      store.entitlement.status === "read_only"
        ? "read_only"
        : capabilities.includes("workspace:view")
          ? "ready"
          : "restricted",
    generated_at: new Date().toISOString(),
    identity: {
      id: actor.id,
      email: actor.email,
      display_name: displayName,
      assurance_level: actor.assuranceLevel
    },
    tenant: { ...store.tenant },
    roles: [...actor.roles],
    capabilities,
    entitlement: { ...store.entitlement },
    locale: store.preferences.locale,
    theme: store.preferences.theme,
    route_data: {
      summary: {
        opportunities: store.opportunities.length,
        active_workspaces: store.workspaces.filter((item) => item.state !== "closed").length,
        blocking_requirements: blockingRequirements,
        deadlines_next_30_days: store.workspaces.length
      },
      opportunities: store.opportunities,
      investigations: store.investigations,
      workspaces: store.workspaces
    },
    rights_snapshot: store.rights_snapshot,
    fixture_boundary: {
      active: true,
      label: FIXTURE_DISCLOSURE,
      mode: "explicit",
      persistent: true,
      reset_automatically: false
    },
    events_cursor: store.events.at(-1)?.cursor ?? 0
  };
}

function canonicalJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => `${JSON.stringify(key)}:${canonicalJson(item)}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function actionDigest(request: SubscriberWorkspaceActionRequest): string {
  return createHash("sha256").update(canonicalJson(request)).digest("hex");
}

function textField(payload: Record<string, unknown>, name: string): string {
  const value = payload[name];
  if (typeof value !== "string" || value.trim().length === 0 || value.length > 500) {
    throw new WorkspaceServerError(400, "invalid_request", `Invalid ${name}.`);
  }
  return value.trim();
}

function optionalText(payload: Record<string, unknown>, name: string): string | null {
  const value = payload[name];
  if (value === null || value === undefined || value === "") return null;
  return textField(payload, name);
}

function safeFixtureId(value: string, name: string): string {
  if (!SAFE_ID_PATTERN.test(value)) {
    throw new WorkspaceServerError(400, "invalid_request", `Invalid ${name}.`);
  }
  return value;
}

function workspaceForPayload(
  store: SubscriberWorkspaceFixtureStore,
  payload: Record<string, unknown>
) {
  const workspaceId = safeFixtureId(textField(payload, "workspace_id"), "workspace_id");
  const workspace = store.workspaces.find((item) => item.id === workspaceId);
  if (!workspace) {
    throw new WorkspaceServerError(404, "not_found", "Subscriber workspace not found.");
  }
  return workspace;
}

function optionalWorkspaceForPayload(
  store: SubscriberWorkspaceFixtureStore,
  payload: Record<string, unknown>
): string | null {
  if (payload.workspace_id === undefined || payload.workspace_id === null) return null;
  return workspaceForPayload(store, payload).id;
}

function requireConfirmation(request: SubscriberWorkspaceActionRequest): void {
  if (
    request.confirmation?.confirmed !== true ||
    request.confirmation.authority !== "subscriber"
  ) {
    throw new WorkspaceServerError(
      409,
      "confirmation_required",
      "Explicit subscriber confirmation is required."
    );
  }
}

function applyFixtureAction(
  actor: SubscriberWorkspaceServerActor,
  store: SubscriberWorkspaceFixtureStore,
  request: SubscriberWorkspaceActionRequest
): { workspaceId: string | null; objectType: string; objectId: string; details: SubscriberWorkspaceAuditEvent["details"] } {
  const payload = request.payload;
  if (payload.tenant_id !== undefined && payload.tenant_id !== actor.tenantId) {
    throw new WorkspaceServerError(404, "not_found", "Subscriber workspace not found.");
  }
  const now = new Date().toISOString();

  switch (request.action_type) {
    case "route.view":
      return {
        workspaceId: optionalWorkspaceForPayload(store, payload),
        objectType: "route",
        objectId: textField(payload, "route"),
        details: { route: textField(payload, "route") }
      };
    case "lens.change": {
      const lens = textField(payload, "lens");
      if (!["auto", "globe", "graph", "dual"].includes(lens)) {
        throw new WorkspaceServerError(400, "invalid_request", "Invalid lens.");
      }
      return { workspaceId: null, objectType: "lens", objectId: lens, details: { lens } };
    }
    case "opportunity.select": {
      const id = safeFixtureId(textField(payload, "opportunity_id"), "opportunity_id");
      if (!store.opportunities.some((item) => item.id === id)) {
        throw new WorkspaceServerError(404, "not_found", "Opportunity not found.");
      }
      return { workspaceId: null, objectType: "opportunity", objectId: id, details: {} };
    }
    case "workspace.open": {
      const workspace = workspaceForPayload(store, payload);
      return { workspaceId: workspace.id, objectType: "workspace", objectId: workspace.id, details: {} };
    }
    case "workspace.create": {
      const opportunityId = safeFixtureId(
        textField(payload, "opportunity_id"),
        "opportunity_id"
      );
      const opportunity = store.opportunities.find((item) => item.id === opportunityId);
      if (!opportunity) {
        throw new WorkspaceServerError(404, "not_found", "Opportunity not found.");
      }
      const id = `axfx_ws_${randomUUID().replaceAll("-", "")}`;
      store.workspaces.push({
        id,
        opportunity_id: opportunity.id,
        title: `${opportunity.title} bid`,
        state: "qualifying",
        owner_id: actor.id,
        deadline: opportunity.deadline,
        decision: "undecided",
        requirements: [],
        evidence: [],
        clarifications: [],
        tasks: [],
        amendments: [],
        commercial: {
          currency: "EUR",
          candidate_value: null,
          margin_percent: null,
          approved_by: null
        },
        submission: {
          package_status: "not_started",
          prepared_by: null,
          approved_by: null,
          preflight_status: "not_run",
          handoff_opened_at: null,
          externally_confirmed_by: null,
          externally_confirmed_at: null
        },
        outcome: { status: "unknown", observed_at: null, source_reference: null }
      });
      opportunity.status = "pursuing";
      return { workspaceId: id, objectType: "workspace", objectId: id, details: {} };
    }
    case "decision.record": {
      const workspace = workspaceForPayload(store, payload);
      const decision = textField(payload, "decision");
      if (!["pursue", "do_not_pursue"].includes(decision)) {
        throw new WorkspaceServerError(400, "invalid_request", "Invalid decision.");
      }
      workspace.decision = decision as "pursue" | "do_not_pursue";
      workspace.state = decision === "pursue" ? "preparing" : "closed";
      return {
        workspaceId: workspace.id,
        objectType: "qualification_decision",
        objectId: workspace.id,
        details: { decision }
      };
    }
    case "requirement.update": {
      const workspace = workspaceForPayload(store, payload);
      const requirementId = safeFixtureId(
        textField(payload, "requirement_id"),
        "requirement_id"
      );
      const requirement = workspace.requirements.find((item) => item.id === requirementId);
      if (!requirement) throw new WorkspaceServerError(404, "not_found", "Requirement not found.");
      const status = textField(payload, "status");
      if (!["unknown", "met", "partial", "blocked", "not_applicable"].includes(status)) {
        throw new WorkspaceServerError(400, "invalid_request", "Invalid requirement status.");
      }
      requirement.status = status as typeof requirement.status;
      requirement.updated_at = now;
      return {
        workspaceId: workspace.id,
        objectType: "requirement",
        objectId: requirement.id,
        details: { status }
      };
    }
    case "evidence.attach": {
      const workspace = workspaceForPayload(store, payload);
      const requirementId = safeFixtureId(
        textField(payload, "requirement_id"),
        "requirement_id"
      );
      const requirement = workspace.requirements.find((item) => item.id === requirementId);
      if (!requirement) throw new WorkspaceServerError(404, "not_found", "Requirement not found.");
      const evidenceId = `axfx_evd_${randomUUID().replaceAll("-", "")}`;
      workspace.evidence.push({
        id: evidenceId,
        workspace_id: workspace.id,
        requirement_id: requirement.id,
        title: textField(payload, "title"),
        evidence_type: "subscriber_document",
        status: "candidate",
        source_reference: optionalText(payload, "source_reference"),
        uploaded_by: actor.id,
        updated_at: now
      });
      requirement.evidence_ids.push(evidenceId);
      requirement.updated_at = now;
      return {
        workspaceId: workspace.id,
        objectType: "evidence",
        objectId: evidenceId,
        details: { requirement_id: requirement.id }
      };
    }
    case "task.assign": {
      const workspace = workspaceForPayload(store, payload);
      const taskId = safeFixtureId(textField(payload, "task_id"), "task_id");
      const task = workspace.tasks.find((item) => item.id === taskId);
      if (!task) throw new WorkspaceServerError(404, "not_found", "Task not found.");
      const requestedOwner = textField(payload, "owner_id");
      const ownerId =
        requestedOwner === "current_user"
          ? actor.id
          : safeFixtureId(requestedOwner, "owner_id");
      if (ownerId !== actor.id && !store.members.some((item) => item.id === ownerId)) {
        throw new WorkspaceServerError(404, "not_found", "Workspace member not found.");
      }
      task.owner_id = ownerId;
      task.status = "in_progress";
      return {
        workspaceId: workspace.id,
        objectType: "task",
        objectId: task.id,
        details: { assigned: true }
      };
    }
    case "clarification.draft": {
      const workspace = workspaceForPayload(store, payload);
      const id = `axfx_clar_${randomUUID().replaceAll("-", "")}`;
      workspace.clarifications.push({
        id,
        workspace_id: workspace.id,
        question: textField(payload, "question"),
        rationale: textField(payload, "rationale"),
        state: "draft",
        created_by: actor.id,
        approved_by: null,
        handoff_opened_at: null,
        sent_confirmed_by: null,
        updated_at: now
      });
      return { workspaceId: workspace.id, objectType: "clarification", objectId: id, details: { state: "draft" } };
    }
    case "clarification.approve": {
      const workspace = workspaceForPayload(store, payload);
      const id = safeFixtureId(textField(payload, "clarification_id"), "clarification_id");
      const clarification = workspace.clarifications.find((item) => item.id === id);
      if (!clarification) throw new WorkspaceServerError(404, "not_found", "Clarification not found.");
      if (clarification.created_by === actor.id) {
        throw new WorkspaceServerError(
          409,
          "separation_of_duties_required",
          "The clarification author cannot be its only external-handoff approver."
        );
      }
      requireConfirmation(request);
      clarification.state = "approved";
      clarification.approved_by = actor.id;
      clarification.updated_at = now;
      return { workspaceId: workspace.id, objectType: "clarification", objectId: id, details: { state: "approved" } };
    }
    case "handoff.open": {
      const workspace = workspaceForPayload(store, payload);
      const targetType = textField(payload, "target_type");
      if (targetType === "clarification") {
        const id = safeFixtureId(textField(payload, "clarification_id"), "clarification_id");
        const clarification = workspace.clarifications.find((item) => item.id === id);
        if (!clarification) throw new WorkspaceServerError(404, "not_found", "Clarification not found.");
        if (clarification.state !== "approved") {
          throw new WorkspaceServerError(409, "state_conflict", "Clarification is not approved.");
        }
        clarification.state = "handoff_opened";
        clarification.handoff_opened_at = now;
        clarification.updated_at = now;
        return { workspaceId: workspace.id, objectType: "clarification_handoff", objectId: id, details: { opened: true } };
      }
      if (targetType === "submission") {
        if (workspace.submission.package_status !== "approved" || workspace.submission.preflight_status !== "ready") {
          throw new WorkspaceServerError(409, "state_conflict", "Submission package is not approved and ready.");
        }
        workspace.submission.handoff_opened_at = now;
        return { workspaceId: workspace.id, objectType: "submission_handoff", objectId: workspace.id, details: { opened: true } };
      }
      throw new WorkspaceServerError(400, "invalid_request", "Invalid handoff target.");
    }
    case "external_action.confirm": {
      const workspace = workspaceForPayload(store, payload);
      requireConfirmation(request);
      const targetType = textField(payload, "target_type");
      if (targetType === "clarification") {
        if (
          !capabilitiesForEntitlement(actor.roles, store.entitlement.status).includes(
            "clarification:confirm_sent"
          )
        ) {
          throw new WorkspaceServerError(403, "capability_denied", "Capability denied.");
        }
        const id = safeFixtureId(textField(payload, "clarification_id"), "clarification_id");
        const clarification = workspace.clarifications.find((item) => item.id === id);
        if (!clarification) throw new WorkspaceServerError(404, "not_found", "Clarification not found.");
        if (clarification.state !== "handoff_opened") {
          throw new WorkspaceServerError(409, "state_conflict", "Official handoff has not been opened.");
        }
        clarification.state = "sent_confirmed";
        clarification.sent_confirmed_by = actor.id;
        clarification.updated_at = now;
        return { workspaceId: workspace.id, objectType: "clarification", objectId: id, details: { subscriber_confirmed: true } };
      }
      if (targetType === "submission") {
        if (!workspace.submission.handoff_opened_at) {
          throw new WorkspaceServerError(409, "state_conflict", "Official handoff has not been opened.");
        }
        workspace.submission.externally_confirmed_by = actor.id;
        workspace.submission.externally_confirmed_at = now;
        workspace.state = "submitted_confirmed";
        return { workspaceId: workspace.id, objectType: "submission", objectId: workspace.id, details: { subscriber_confirmed: true } };
      }
      throw new WorkspaceServerError(400, "invalid_request", "Invalid external action target.");
    }
    case "amendment.acknowledge": {
      const workspace = workspaceForPayload(store, payload);
      const id = safeFixtureId(textField(payload, "amendment_id"), "amendment_id");
      const amendment = workspace.amendments.find((item) => item.id === id);
      if (!amendment) throw new WorkspaceServerError(404, "not_found", "Amendment not found.");
      amendment.acknowledged = true;
      workspace.submission.preflight_status = "blocked";
      return { workspaceId: workspace.id, objectType: "amendment", objectId: id, details: { acknowledged: true, revalidation_required: true } };
    }
    case "commercial.update": {
      const workspace = workspaceForPayload(store, payload);
      const value = payload.candidate_value;
      const margin = payload.margin_percent;
      if (value !== null && (typeof value !== "number" || !Number.isFinite(value) || value < 0)) {
        throw new WorkspaceServerError(400, "invalid_request", "Invalid candidate value.");
      }
      if (margin !== null && (typeof margin !== "number" || !Number.isFinite(margin) || margin < -100 || margin > 100)) {
        throw new WorkspaceServerError(400, "invalid_request", "Invalid margin.");
      }
      workspace.commercial.candidate_value = value as number | null;
      workspace.commercial.margin_percent = margin as number | null;
      workspace.commercial.approved_by = null;
      return { workspaceId: workspace.id, objectType: "commercial_model", objectId: workspace.id, details: { updated: true } };
    }
    case "commercial.approve": {
      const workspace = workspaceForPayload(store, payload);
      requireConfirmation(request);
      workspace.commercial.approved_by = actor.id;
      return { workspaceId: workspace.id, objectType: "commercial_model", objectId: workspace.id, details: { approved: true } };
    }
    case "submission.prepare": {
      const workspace = workspaceForPayload(store, payload);
      workspace.submission.package_status = "ready";
      workspace.submission.prepared_by = actor.id;
      workspace.submission.approved_by = null;
      return { workspaceId: workspace.id, objectType: "submission_package", objectId: workspace.id, details: { status: "ready" } };
    }
    case "submission.approve": {
      const workspace = workspaceForPayload(store, payload);
      requireConfirmation(request);
      if (workspace.submission.package_status !== "ready") {
        throw new WorkspaceServerError(409, "state_conflict", "Submission package is not ready.");
      }
      if (workspace.submission.prepared_by === actor.id) {
        throw new WorkspaceServerError(
          409,
          "separation_of_duties_required",
          "Package preparation and subscriber approval require separate actors."
        );
      }
      workspace.submission.package_status = "approved";
      workspace.submission.approved_by = actor.id;
      return { workspaceId: workspace.id, objectType: "submission_package", objectId: workspace.id, details: { approved: true } };
    }
    case "preflight.complete": {
      const workspace = workspaceForPayload(store, payload);
      const blocked = workspace.requirements.some(
        (item) => item.blocking && !["met", "not_applicable"].includes(item.status)
      );
      const amendmentPending = workspace.amendments.some((item) => !item.acknowledged);
      workspace.submission.preflight_status = blocked || amendmentPending ? "blocked" : "ready";
      return {
        workspaceId: workspace.id,
        objectType: "submission_preflight",
        objectId: workspace.id,
        details: { ready: workspace.submission.preflight_status === "ready" }
      };
    }
    case "outcome.record": {
      const workspace = workspaceForPayload(store, payload);
      const status = textField(payload, "status");
      if (!["pending", "awarded", "not_awarded", "withdrawn"].includes(status)) {
        throw new WorkspaceServerError(400, "invalid_request", "Invalid outcome status.");
      }
      workspace.outcome.status = status as typeof workspace.outcome.status;
      workspace.outcome.observed_at = now;
      workspace.outcome.source_reference = optionalText(payload, "source_reference");
      if (["awarded", "not_awarded", "withdrawn"].includes(status)) workspace.state = "closed";
      return { workspaceId: workspace.id, objectType: "outcome", objectId: workspace.id, details: { status } };
    }
    case "recovery.request":
      return { workspaceId: optionalWorkspaceForPayload(store, payload), objectType: "recovery", objectId: request.action_id, details: { requested: true } };
  }
}

export function parseSubscriberWorkspaceAction(value: unknown): SubscriberWorkspaceActionRequest {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new WorkspaceServerError(400, "invalid_request", "Invalid action request.");
  }
  const input = value as Record<string, unknown>;
  if (
    typeof input.action_id !== "string" ||
    !ACTION_ID_PATTERN.test(input.action_id) ||
    !isSubscriberWorkspaceActionType(input.action_type) ||
    !Number.isSafeInteger(input.tenant_revision) ||
    (input.tenant_revision as number) < 1 ||
    !input.payload ||
    typeof input.payload !== "object" ||
    Array.isArray(input.payload)
  ) {
    throw new WorkspaceServerError(400, "invalid_request", "Invalid action request.");
  }
  let confirmation: SubscriberWorkspaceActionRequest["confirmation"];
  if (input.confirmation !== undefined) {
    if (
      !input.confirmation ||
      typeof input.confirmation !== "object" ||
      (input.confirmation as Record<string, unknown>).confirmed !== true ||
      (input.confirmation as Record<string, unknown>).authority !== "subscriber"
    ) {
      throw new WorkspaceServerError(400, "invalid_request", "Invalid confirmation.");
    }
    confirmation = { confirmed: true, authority: "subscriber" };
  }
  return {
    action_id: input.action_id,
    action_type: input.action_type,
    tenant_revision: input.tenant_revision as number,
    payload: input.payload as Record<string, unknown>,
    ...(confirmation ? { confirmation } : {})
  };
}

export async function getSubscriberWorkspaceFixtureBootstrap(
  actor: SubscriberWorkspaceServerActor,
  options?: StoreOptions
): Promise<SubscriberWorkspaceBootstrap> {
  const store = await loadFixtureStore(actor, options);
  return fixtureBootstrap(actor, store);
}

export async function executeSubscriberWorkspaceFixtureAction(
  actor: SubscriberWorkspaceServerActor,
  request: SubscriberWorkspaceActionRequest,
  options?: StoreOptions
): Promise<SubscriberWorkspaceActionResult> {
  const filename = storePath(actor, options);
  return withStoreLock(filename, async () => {
    const store = await loadFixtureStore(actor, options);
    const digest = actionDigest(request);
    const receipt = store.action_receipts[request.action_id];
    if (receipt) {
      if (receipt.digest !== digest || receipt.action_type !== request.action_type) {
        throw new WorkspaceServerError(
          409,
          "state_conflict",
          "Action identifier has already been used for a different request."
        );
      }
      if (receipt.outcome === "rejected" && receipt.error) {
        throw new WorkspaceServerError(
          receipt.error.status,
          receipt.error.code as SubscriberWorkspaceError["code"],
          receipt.error.message,
          receipt.error.recoverable
        );
      }
      return {
        action_id: request.action_id,
        action_type: request.action_type,
        mutation_state: "persisted",
        idempotent_replay: true,
        tenant_revision: receipt.tenant_revision,
        event: receipt.event,
        bootstrap: fixtureBootstrap(actor, store)
      };
    }

    const policy = ACTION_POLICY[request.action_type];
    try {
      const capabilities = capabilitiesForEntitlement(actor.roles, store.entitlement.status);
      if (!capabilities.includes(policy.capability)) {
        throw new WorkspaceServerError(403, "capability_denied", "Capability denied.");
      }
      if (request.tenant_revision !== store.tenant.revision) {
        throw new WorkspaceServerError(
          409,
          "stale_revision",
          "Tenant revision is stale. Refresh before retrying.",
          true
        );
      }

      const effect = applyFixtureAction(actor, store, request);
      store.tenant.revision += 1;
      const event: SubscriberWorkspaceAuditEvent = {
        cursor: (store.events.at(-1)?.cursor ?? 0) + 1,
        id: `axfx_evt_${randomUUID().replaceAll("-", "")}`,
        tenant_id: actor.tenantId,
        workspace_id: effect.workspaceId,
        actor_id: actor.id,
        type: policy.event,
        object_type: effect.objectType,
        object_id: effect.objectId,
        occurred_at: new Date().toISOString(),
        tenant_revision: store.tenant.revision,
        details: effect.details
      };
      store.events.push(event);
      store.action_receipts[request.action_id] = {
        digest,
        action_type: request.action_type,
        outcome: "persisted",
        tenant_revision: store.tenant.revision,
        event
      };
      await persistFixtureStore(actor, store, options);
      return {
        action_id: request.action_id,
        action_type: request.action_type,
        mutation_state: "persisted",
        idempotent_replay: false,
        tenant_revision: store.tenant.revision,
        event,
        bootstrap: fixtureBootstrap(actor, store)
      };
    } catch (error) {
      if (!(error instanceof WorkspaceServerError)) throw error;
      const deniedEvent: SubscriberWorkspaceAuditEvent = {
        cursor: (store.events.at(-1)?.cursor ?? 0) + 1,
        id: `axfx_evt_${randomUUID().replaceAll("-", "")}`,
        tenant_id: actor.tenantId,
        workspace_id: null,
        actor_id: actor.id,
        type: "mutation.denied",
        object_type: "action",
        object_id: request.action_id,
        occurred_at: new Date().toISOString(),
        tenant_revision: store.tenant.revision,
        details: { code: error.code }
      };
      store.events.push(deniedEvent);
      store.action_receipts[request.action_id] = {
        digest,
        action_type: request.action_type,
        outcome: "rejected",
        tenant_revision: store.tenant.revision,
        event: deniedEvent,
        error: {
          status: error.status,
          code: error.code,
          message: error.message,
          recoverable: error.recoverable
        }
      };
      await persistFixtureStore(actor, store, options);
      throw error;
    }
  });
}

export async function getSubscriberWorkspaceFixtureEvents(
  actor: SubscriberWorkspaceServerActor,
  after: number,
  options?: StoreOptions
) {
  const store = await loadFixtureStore(actor, options);
  const events = capabilitiesForEntitlement(
    actor.roles,
    store.entitlement.status
  ).includes("audit:view")
    ? store.events.filter((event) => event.cursor > after)
    : store.events
        .filter((event) => event.cursor > after && event.actor_id === actor.id)
        .map((event) => ({ ...event, details: {} }));
  return {
    events,
    next_cursor: store.events.at(-1)?.cursor ?? after,
    fixture_boundary: {
      active: true,
      label: FIXTURE_DISCLOSURE,
      mode: "explicit" as const
    }
  };
}

function upstreamBaseUrl(): string | null {
  const value =
    process.env.AXIGNAL_SUBSCRIBER_WORKSPACE_API_URL ?? process.env.AXIGNAL_API_URL;
  if (!value) return null;
  try {
    const parsed = new URL(value);
    if (!["http:", "https:"].includes(parsed.protocol)) return null;
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return null;
  }
}

async function upstreamRequest<T>(
  actor: SubscriberWorkspaceServerActor,
  pathName: string,
  init?: RequestInit
): Promise<SubscriberWorkspaceServerResult<T>> {
  const baseUrl = upstreamBaseUrl();
  if (!baseUrl || !actor.authenticatedIdentity) {
    return {
      status: 503,
      body: {
        error: "Subscriber workspace source is unavailable.",
        code: "source_unavailable",
        state: "source_unavailable",
        recoverable: true
      }
    };
  }
  try {
    const headers = new Headers(init?.headers);
    headers.set("accept", "application/json");
    if (init?.body) headers.set("content-type", "application/json");
    headers.set(
      "X-AXIGNAL-Identity-Assertion",
      buildApiIdentityAssertion(actor.authenticatedIdentity)
    );
    const response = await fetch(`${baseUrl}/v1/subscriber-workspace${pathName}`, {
      ...init,
      headers,
      cache: "no-store",
      signal: AbortSignal.timeout(10_000)
    });
    const body = (await response.json().catch(() => ({
      error: "Invalid subscriber workspace upstream response.",
      code: "upstream_error",
      state: "recoverable_error",
      recoverable: true
    }))) as T | SubscriberWorkspaceError;
    return { status: response.status, body };
  } catch {
    return {
      status: 503,
      body: {
        error: "Subscriber workspace source is unavailable.",
        code: "source_unavailable",
        state: "source_unavailable",
        recoverable: true
      }
    };
  }
}

async function actorOrAuthenticationError(): Promise<
  SubscriberWorkspaceServerActor | SubscriberWorkspaceServerResult<never>
> {
  try {
    const actor = await resolveSubscriberWorkspaceActor();
    if (actor) return actor;
    return {
      status: 401,
      body: {
        error: "Authentication required.",
        code: "authentication_required",
        state: "restricted",
        recoverable: false
      }
    };
  } catch (error) {
    return errorResult(error);
  }
}

function isResult(value: SubscriberWorkspaceServerActor | SubscriberWorkspaceServerResult<never>): value is SubscriberWorkspaceServerResult<never> {
  return "status" in value;
}

export async function subscriberWorkspaceBootstrapResult(): Promise<
  SubscriberWorkspaceServerResult<SubscriberWorkspaceBootstrap>
> {
  const resolved = await actorOrAuthenticationError();
  if (isResult(resolved)) return resolved;
  try {
    if (subscriberWorkspaceFixtureConfiguration().allowed) {
      return { status: 200, body: await getSubscriberWorkspaceFixtureBootstrap(resolved) };
    }
    return upstreamRequest<SubscriberWorkspaceBootstrap>(resolved, "/bootstrap");
  } catch (error) {
    return errorResult(error);
  }
}

export async function subscriberWorkspaceActionResult(
  input: unknown
): Promise<SubscriberWorkspaceServerResult<SubscriberWorkspaceActionResult>> {
  const resolved = await actorOrAuthenticationError();
  if (isResult(resolved)) return resolved;
  try {
    const request = parseSubscriberWorkspaceAction(input);
    if (subscriberWorkspaceFixtureConfiguration().allowed) {
      return {
        status: 200,
        body: await executeSubscriberWorkspaceFixtureAction(resolved, request)
      };
    }
    return upstreamRequest<SubscriberWorkspaceActionResult>(resolved, "/actions", {
      method: "POST",
      body: JSON.stringify(request)
    });
  } catch (error) {
    return errorResult(error);
  }
}

export async function subscriberWorkspaceEventsResult(
  after: number
): Promise<SubscriberWorkspaceServerResult<unknown>> {
  const resolved = await actorOrAuthenticationError();
  if (isResult(resolved)) return resolved;
  if (!Number.isSafeInteger(after) || after < 0) {
    return errorResult(
      new WorkspaceServerError(400, "invalid_request", "Invalid event cursor.")
    );
  }
  try {
    if (subscriberWorkspaceFixtureConfiguration().allowed) {
      return { status: 200, body: await getSubscriberWorkspaceFixtureEvents(resolved, after) };
    }
    return upstreamRequest(resolved, `/events?after=${after}`);
  } catch (error) {
    return errorResult(error);
  }
}

export function subscriberWorkspaceEnabled(): boolean {
  return boolEnv("AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED");
}
