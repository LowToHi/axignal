export type LiveEvidence = {
  evidence_id: string;
  source_id: string;
  title: string;
  relationship: string;
  observed_at: string;
  rights_status: string;
  provisional: boolean;
  payload: Record<string, unknown>;
};

export type LiveCandidateClaim = {
  candidate_claim_id: string;
  statement: string;
  kind: string;
  state: string;
  producer_type: string;
  method_version: string;
  canonical_claim_id: string | null;
  rejection_reasons: string[];
};

export type LiveCanonicalClaim = {
  canonical_claim_id: string;
  statement: string;
  state: "ADMITTED";
  epistemic_class: string;
};

export type LiveDossier = {
  dossier_id: string;
  status: string;
  title: string;
  summary: string;
  sections: Array<Record<string, unknown>>;
  attribution: Record<string, unknown>;
};

export type LiveResearchRun = {
  research_run_id: string;
  context_id: string;
  opportunity_id: string;
  question: string;
  state: string;
  private_knowledge_authorised: boolean;
  source_plan: Array<Record<string, unknown>>;
  budgets: Record<string, unknown>;
  actual_usage: Record<string, unknown>;
  evidence: LiveEvidence[];
  candidate_claims: LiveCandidateClaim[];
  canonical_claims: LiveCanonicalClaim[];
  dossier: LiveDossier | null;
  admission_batch_id: string | null;
  error_code: string | null;
  error_detail: string | null;
  created_at: string;
  updated_at: string;
  synthetic: false;
};

export type LiveWorkspace = {
  workspace_id: string;
  tenant_id: string;
  research_run_id: string;
  opportunity_id: string;
  title: string;
  state: "ACTIVE" | "CLOSED";
  owner_subject: string;
  revision: number;
  created_at: string;
  updated_at: string;
};

export type LiveDocument = {
  document_id: string;
  tenant_id: string;
  workspace_id: string;
  title: string;
  body: string;
  version: number;
  status: "DRAFT" | "READY";
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type LiveExport = {
  export_id: string;
  tenant_id: string;
  workspace_id: string;
  document_id: string | null;
  format: "MARKDOWN";
  filename: string;
  content_hash: string;
  created_by: string;
  created_at: string;
};

export type LiveAuditEvent = {
  audit_event_id: string;
  tenant_id: string;
  workspace_id: string | null;
  actor_subject: string;
  event_type:
    | "WORKSPACE_CREATED"
    | "WORKSPACE_OPENED"
    | "DOCUMENT_CREATED"
    | "DOCUMENT_UPDATED"
    | "EXPORT_CREATED";
  object_type: string;
  object_id: string;
  details: Record<string, unknown>;
  occurred_at: string;
};

export type LiveEntitlement = {
  entitlement_id?: string;
  entitlement_kind?: "TRIAL" | "PAID_MONTHLY";
  plan_code?: string;
  state?: "ACTIVE" | "READ_ONLY" | "SUSPENDED" | "CANCELLED";
  expires_at?: string | null;
  token_budget_total?: number | null;
  token_budget_reserved?: number;
  token_budget_consumed?: number;
} | null;

export type LiveSeatSummary = {
  active_seats?: number;
  reserved_seats?: number;
  occupied_seats?: number;
  available_seats?: number;
  seat_entitlement?: {
    plan_code?: string;
    state?: string;
    seat_capacity?: number;
  };
} | null;

export type SubscriberLiveBootstrap = {
  schema_version: "axignal.subscriber-live-workspace/v1";
  state: "READY";
  generated_at: string;
  identity: {
    subject: string;
    email: string;
    tenant_id: string;
    session_id: string | null;
    assurance_level: string | null;
    roles: string[];
    seat_state: string | null;
    seat_plan_code: string | null;
  };
  organisation: {
    tenant_id: string;
    display_name: string;
  };
  entitlement: LiveEntitlement;
  seats: LiveSeatSummary;
  capabilities: string[];
  fixture_boundary: {
    active: false;
    mode: "PERSISTENT_REAL_ADAPTER";
    fallback_allowed: false;
  };
  research_runs: LiveResearchRun[];
  workspaces: LiveWorkspace[];
  documents: LiveDocument[];
  exports: LiveExport[];
  audit: LiveAuditEvent[];
};

export type LiveResearchAccepted = {
  research_run_id: string;
  context_id: string;
  opportunity_id: string;
  state: "QUEUED";
  queue_delivery: "PUBLISHED" | "OUTBOX_PENDING";
  source_ids: string[];
  synthetic: false;
};

export type ApiError = {
  error?: string;
  detail?: string;
};
