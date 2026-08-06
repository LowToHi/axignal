export const SUBSCRIBER_WORKSPACE_SCHEMA_VERSION =
  "axignal.subscriber-workspace/v1" as const;

export const SUBSCRIBER_WORKSPACE_ROLES = [
  "OWNER",
  "ADMIN",
  "BID_MANAGER",
  "CONTRIBUTOR",
  "REVIEWER",
  "FINANCE",
  "VIEWER"
] as const;

export type SubscriberWorkspaceRole =
  (typeof SUBSCRIBER_WORKSPACE_ROLES)[number];

export const SUBSCRIBER_WORKSPACE_CAPABILITIES = [
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
] as const;

export type SubscriberWorkspaceCapability =
  (typeof SUBSCRIBER_WORKSPACE_CAPABILITIES)[number];

export const SUBSCRIBER_WORKSPACE_SURFACE_STATES = [
  "loading",
  "empty",
  "ready",
  "partial",
  "stale",
  "restricted",
  "read_only",
  "source_unavailable",
  "recoverable_error",
  "terminal_error"
] as const;

export type SubscriberWorkspaceSurfaceState =
  (typeof SUBSCRIBER_WORKSPACE_SURFACE_STATES)[number];

export const SUBSCRIBER_WORKSPACE_MUTATION_STATES = [
  "idle",
  "pending",
  "persisted",
  "partial_failure",
  "rejected",
  "recovery_available"
] as const;

export type SubscriberWorkspaceMutationState =
  (typeof SUBSCRIBER_WORKSPACE_MUTATION_STATES)[number];

export const SUBSCRIBER_WORKSPACE_EVENT_TYPES = [
  "route.viewed",
  "lens.changed",
  "opportunity.selected",
  "workspace.opened",
  "decision.recorded",
  "requirement.updated",
  "evidence.attached",
  "task.assigned",
  "clarification.approved",
  "handoff.opened",
  "external_action.confirmed",
  "amendment.acknowledged",
  "preflight.completed",
  "outcome.recorded",
  "mutation.denied",
  "recovery.requested"
] as const;

export type SubscriberWorkspaceEventType =
  (typeof SUBSCRIBER_WORKSPACE_EVENT_TYPES)[number];

export const SUBSCRIBER_WORKSPACE_ACTION_TYPES = [
  "route.view",
  "lens.change",
  "opportunity.select",
  "workspace.open",
  "workspace.create",
  "decision.record",
  "requirement.update",
  "evidence.attach",
  "task.assign",
  "clarification.draft",
  "clarification.approve",
  "handoff.open",
  "external_action.confirm",
  "amendment.acknowledge",
  "commercial.update",
  "commercial.approve",
  "submission.prepare",
  "submission.approve",
  "preflight.complete",
  "outcome.record",
  "recovery.request"
] as const;

export type SubscriberWorkspaceActionType =
  (typeof SUBSCRIBER_WORKSPACE_ACTION_TYPES)[number];

export type SubscriberWorkspaceLocale = "en" | "es" | "fr" | "de" | "pt" | "it";
export type SubscriberWorkspaceTheme = "dark" | "light" | "system";

export type SubscriberWorkspaceIdentity = {
  id: string;
  email: string;
  display_name: string;
  assurance_level: string | null;
};

export type SubscriberWorkspaceTenant = {
  id: string;
  name: string;
  revision: number;
};

export type SubscriberWorkspaceEntitlement = {
  status: "trial" | "active" | "read_only" | "suspended";
  plan_code: string;
  seat_limit: number | null;
  seats_used: number;
  source: "server" | "engineering_fixture";
};

export type SubscriberWorkspaceRightsSnapshot = {
  source_id: string;
  source_version: string;
  rights_status: "admitted" | "restricted" | "review_required";
  attribution_required: boolean;
  redistribution_allowed: boolean;
  retrieved_at: string;
  expires_at: string | null;
};

export type SubscriberWorkspaceFixtureBoundary = {
  active: boolean;
  label: "ENGINEERING FIXTURE · NOT LIVE DATA" | null;
  mode: "explicit" | "real_adapter";
  persistent: boolean;
  reset_automatically: false;
};

export type SubscriberWorkspaceOpportunity = {
  id: string;
  version: string;
  title: string;
  buyer: string;
  jurisdiction: string;
  deadline: string;
  status: "new" | "qualified" | "pursuing" | "not_pursuing";
  fit: "high" | "medium" | "low" | "unknown";
  confidence: number | null;
  source_id: string;
  source_url: string;
  observed_at: string;
  unknowns: string[];
};

export type SubscriberWorkspaceRequirement = {
  id: string;
  workspace_id: string;
  title: string;
  category: string;
  status: "unknown" | "met" | "partial" | "blocked" | "not_applicable";
  blocking: boolean;
  owner_id: string | null;
  evidence_ids: string[];
  source_reference: string;
  updated_at: string;
};

export type SubscriberWorkspaceEvidence = {
  id: string;
  workspace_id: string;
  requirement_id: string | null;
  title: string;
  evidence_type: "source" | "subscriber_document" | "calculation" | "unknown";
  status: "candidate" | "verified" | "expired" | "rejected";
  source_reference: string | null;
  uploaded_by: string | null;
  updated_at: string;
};

export type SubscriberWorkspaceClarification = {
  id: string;
  workspace_id: string;
  question: string;
  rationale: string;
  state:
    | "draft"
    | "internal_review"
    | "approved"
    | "handoff_opened"
    | "sent_confirmed"
    | "answered"
    | "closed";
  created_by: string;
  approved_by: string | null;
  handoff_opened_at: string | null;
  sent_confirmed_by: string | null;
  updated_at: string;
};

export type SubscriberWorkspaceTask = {
  id: string;
  workspace_id: string;
  title: string;
  owner_id: string | null;
  status: "open" | "in_progress" | "blocked" | "done";
  due_at: string | null;
};

export type SubscriberWorkspaceAuditEvent = {
  cursor: number;
  id: string;
  tenant_id: string;
  workspace_id: string | null;
  actor_id: string;
  type: SubscriberWorkspaceEventType;
  object_type: string;
  object_id: string;
  occurred_at: string;
  tenant_revision: number;
  details: Record<string, string | number | boolean | null>;
};

export type SubscriberWorkspaceRecord = {
  id: string;
  opportunity_id: string;
  title: string;
  state:
    | "qualifying"
    | "go_review"
    | "preparing"
    | "subscriber_approved"
    | "submitted_confirmed"
    | "closed";
  owner_id: string;
  deadline: string;
  decision: "undecided" | "pursue" | "do_not_pursue";
  requirements: SubscriberWorkspaceRequirement[];
  evidence: SubscriberWorkspaceEvidence[];
  clarifications: SubscriberWorkspaceClarification[];
  tasks: SubscriberWorkspaceTask[];
  amendments: Array<{
    id: string;
    title: string;
    acknowledged: boolean;
    observed_at: string;
  }>;
  commercial: {
    currency: string;
    candidate_value: number | null;
    margin_percent: number | null;
    approved_by: string | null;
  };
  submission: {
    package_status: "not_started" | "preparing" | "ready" | "approved";
    prepared_by: string | null;
    approved_by: string | null;
    preflight_status: "not_run" | "blocked" | "ready";
    handoff_opened_at: string | null;
    externally_confirmed_by: string | null;
    externally_confirmed_at: string | null;
  };
  outcome: {
    status: "unknown" | "pending" | "awarded" | "not_awarded" | "withdrawn";
    observed_at: string | null;
    source_reference: string | null;
  };
};

export type SubscriberWorkspaceRouteData = {
  summary: {
    opportunities: number;
    active_workspaces: number;
    blocking_requirements: number;
    deadlines_next_30_days: number;
  };
  opportunities: SubscriberWorkspaceOpportunity[];
  investigations: Array<{
    id: string;
    title: string;
    status: "active" | "paused" | "complete";
    updated_at: string;
    opportunity_ids: string[];
  }>;
  workspaces: SubscriberWorkspaceRecord[];
};

export type SubscriberWorkspaceBootstrap = {
  schema_version: typeof SUBSCRIBER_WORKSPACE_SCHEMA_VERSION;
  state: SubscriberWorkspaceSurfaceState;
  generated_at: string;
  identity: SubscriberWorkspaceIdentity;
  tenant: SubscriberWorkspaceTenant;
  roles: SubscriberWorkspaceRole[];
  capabilities: SubscriberWorkspaceCapability[];
  entitlement: SubscriberWorkspaceEntitlement;
  locale: SubscriberWorkspaceLocale;
  theme: SubscriberWorkspaceTheme;
  route_data: SubscriberWorkspaceRouteData;
  rights_snapshot: SubscriberWorkspaceRightsSnapshot[];
  fixture_boundary: SubscriberWorkspaceFixtureBoundary;
  events_cursor: number;
};

export type SubscriberWorkspaceActionRequest = {
  action_id: string;
  action_type: SubscriberWorkspaceActionType;
  tenant_revision: number;
  payload: Record<string, unknown>;
  confirmation?: {
    confirmed: boolean;
    authority: "subscriber";
  };
};

export type SubscriberWorkspaceActionResult = {
  action_id: string;
  action_type: SubscriberWorkspaceActionType;
  mutation_state: SubscriberWorkspaceMutationState;
  idempotent_replay: boolean;
  tenant_revision: number;
  event: SubscriberWorkspaceAuditEvent | null;
  bootstrap: SubscriberWorkspaceBootstrap;
};

export type SubscriberWorkspaceErrorCode =
  | "authentication_required"
  | "invalid_request"
  | "not_found"
  | "capability_denied"
  | "stale_revision"
  | "separation_of_duties_required"
  | "confirmation_required"
  | "state_conflict"
  | "fixture_mode_rejected"
  | "source_unavailable"
  | "upstream_error";

export type SubscriberWorkspaceError = {
  error: string;
  code: SubscriberWorkspaceErrorCode;
  state: SubscriberWorkspaceSurfaceState | SubscriberWorkspaceMutationState;
  recoverable: boolean;
};

export function isSubscriberWorkspaceRole(
  value: unknown
): value is SubscriberWorkspaceRole {
  return (
    typeof value === "string" &&
    (SUBSCRIBER_WORKSPACE_ROLES as readonly string[]).includes(value)
  );
}

export function isSubscriberWorkspaceActionType(
  value: unknown
): value is SubscriberWorkspaceActionType {
  return (
    typeof value === "string" &&
    (SUBSCRIBER_WORKSPACE_ACTION_TYPES as readonly string[]).includes(value)
  );
}
