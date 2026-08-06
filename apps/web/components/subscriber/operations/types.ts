export const tenderSections = [
  "overview",
  "qualification",
  "requirements",
  "evidence",
  "documents",
  "workplan",
  "clarifications",
  "changes",
  "commercial",
  "team",
  "submission",
  "outcome",
  "audit"
] as const;

export type TenderSection = (typeof tenderSections)[number];

export type TenderRouteState =
  | "loading"
  | "empty"
  | "ready"
  | "partial"
  | "stale"
  | "restricted"
  | "read_only"
  | "source_unavailable"
  | "recoverable_error"
  | "terminal_error";

export type MutationState =
  | "idle"
  | "pending"
  | "persisted"
  | "partial_failure"
  | "rejected"
  | "recovery_available";

export type Capability =
  | "workspace:view"
  | "workspace:create"
  | "workspace:qualify"
  | "workspace:edit"
  | "requirement:edit"
  | "evidence:attach"
  | "document:manage"
  | "work:assign"
  | "clarification:draft"
  | "clarification:approve"
  | "clarification:confirm_sent"
  | "commercial:view"
  | "commercial:edit"
  | "commercial:approve"
  | "submission:prepare"
  | "submission:approve"
  | "submission:confirm_external"
  | "outcome:record"
  | "audit:view"
  | "export:create"
  | "team:manage"
  | "billing:view"
  | "billing:manage"
  | "settings:manage";

export type ActionType =
  | "workspace.qualify"
  | "requirement.update"
  | "evidence.attach"
  | "document.create"
  | "task.assign"
  | "clarification.draft"
  | "clarification.approve"
  | "clarification.open_handoff"
  | "clarification.confirm_sent"
  | "amendment.acknowledge"
  | "commercial.update"
  | "commercial.approve"
  | "approval.record"
  | "submission.prepare"
  | "submission.approve"
  | "submission.open_handoff"
  | "submission.confirm_external"
  | "outcome.record"
  | "export.create"
  | "recovery.request";

export interface TenderOperationAction {
  actionType: ActionType;
  workspaceId: string;
  subjectId?: string;
  payload?: Readonly<Record<string, string | number | boolean | null>>;
  confirmation?: {
    acknowledged: boolean;
    authorityStatement: string;
  };
}

export interface MutationFeedback {
  state: MutationState;
  message?: string;
}

export interface WorkspaceMetric {
  label: string;
  value: string;
  detail?: string;
  tone?: "neutral" | "positive" | "warning" | "critical";
}

export interface RequirementRecord {
  id: string;
  code: string;
  title: string;
  category: string;
  status: "unreviewed" | "in_progress" | "satisfied" | "blocked" | "not_applicable";
  mandatory: boolean;
  owner?: string;
  dueAt?: string;
  evidenceCount: number;
  sourceReference?: string;
  lastUpdatedAt?: string;
}

export interface EvidenceRecord {
  id: string;
  title: string;
  kind: "fact" | "inference" | "prediction" | "contradiction" | "unknown";
  source: string;
  status: "candidate" | "verified" | "expired" | "rejected";
  requirementIds: readonly string[];
  freshness?: string;
}

export interface DocumentRecord {
  id: string;
  title: string;
  version: string;
  owner: string;
  status: "draft" | "review" | "approved" | "superseded";
  updatedAt: string;
  lockOwner?: string;
}

export interface WorkItemRecord {
  id: string;
  title: string;
  owner?: string;
  dueAt?: string;
  status: "todo" | "doing" | "blocked" | "done";
  dependency?: string;
}

export interface ClarificationRecord {
  id: string;
  question: string;
  author: string;
  approver?: string;
  status: "draft" | "pending_approval" | "approved" | "handoff_opened" | "sent_confirmed" | "answered";
  deadline?: string;
  officialUrl?: string;
}

export interface AmendmentRecord {
  id: string;
  title: string;
  publishedAt: string;
  acknowledgedAt?: string;
  affectedRequirements: number;
  impact: "low" | "medium" | "high";
}

export interface CommercialLineRecord {
  id: string;
  label: string;
  amount?: string;
  status: "unknown" | "estimated" | "reviewed" | "approved" | "redacted" | "not_applicable";
  owner?: string;
}

export interface TeamMemberRecord {
  id: string;
  name: string;
  role: string;
  responsibility: string;
  status: "active" | "invited" | "unavailable";
}

export interface ApprovalRecord {
  id: string;
  subject: string;
  status: "pending" | "approved" | "rejected";
  requestedFrom: string;
  decidedBy?: string;
  decidedAt?: string;
}

export interface AuditRecord {
  id: string;
  event: string;
  actor: string;
  occurredAt: string;
  detail: string;
  outcome: "accepted" | "denied" | "recorded";
}

export interface TenderWorkspaceData {
  workspaceId: string;
  tenderId: string;
  title: string;
  buyer: string;
  jurisdiction: string;
  procedure: string;
  sourceUrl?: string;
  dueAt?: string;
  updatedAt: string;
  revision: number;
  status: "discovery" | "qualifying" | "pursuing" | "preparing" | "ready" | "submitted_confirmed" | "closed";
  fixtureMode?: boolean;
  summary?: string;
  metrics?: readonly WorkspaceMetric[];
  requirements?: readonly RequirementRecord[];
  evidence?: readonly EvidenceRecord[];
  documents?: readonly DocumentRecord[];
  workItems?: readonly WorkItemRecord[];
  clarifications?: readonly ClarificationRecord[];
  amendments?: readonly AmendmentRecord[];
  commercial?: readonly CommercialLineRecord[];
  team?: readonly TeamMemberRecord[];
  approvals?: readonly ApprovalRecord[];
  audit?: readonly AuditRecord[];
  readiness?: {
    score: number;
    blockingItems: readonly string[];
    packagePrepared: boolean;
    subscriberApproved: boolean;
    handoffOpened: boolean;
    externalSubmissionConfirmed: boolean;
  };
  outcome?: {
    status: "unknown" | "submitted" | "shortlisted" | "not_selected" | "awarded" | "cancelled";
    recordedAt?: string;
    note?: string;
  };
}

export interface TenderOperationsWorkspaceProps {
  section: TenderSection;
  state: TenderRouteState;
  data: TenderWorkspaceData | null;
  capabilities: ReadonlySet<Capability>;
  mutationFeedback?: Readonly<Partial<Record<ActionType, MutationFeedback>>>;
  locale?: string;
  view?: "table" | "cards";
  selectedId?: string;
  stateMessage?: string;
  onNavigate: (section: TenderSection, selectedId?: string) => void;
  onViewChange?: (view: "table" | "cards") => void;
  onRetry?: () => void;
  onAction: (action: TenderOperationAction) => void | Promise<void>;
}
