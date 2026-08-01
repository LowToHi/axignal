export type IntelligenceLens = "AUTO" | "GLOBE" | "GRAPH" | "DUAL";

export type IntelligenceViewState =
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

export type ClaimKind = "fact" | "inference" | "prediction" | "contradiction" | "unknown";

export type NavigatorMessage = {
  id: string;
  actor: "subscriber" | "axignal";
  body: string;
  occurredAt: string;
  actionLabel?: string;
};

export type Opportunity = {
  id: string;
  name: string;
  level: string;
  expectedReturn: string | null;
  confidence: number | null;
  trend: readonly number[];
  latitude: number;
  longitude: number;
};

export type EvidenceClaim = {
  id: string;
  kind: ClaimKind;
  statement: string;
  sourceLabel: string | null;
  asOf: string | null;
  supportCount: number | null;
  originalLanguage?: string;
  translationStatus?: "original" | "translated" | "machine_translated" | "unavailable";
};

export type GraphEntity = {
  id: string;
  label: string;
  kind: "geography" | "opportunity" | "driver" | "risk" | "source";
};

export type GraphRelationship = {
  id: string;
  from: string;
  to: string;
  label: string;
  epistemicStatus: "support" | "inferred" | "contradiction" | "unknown";
};

export type TimelinePoint = {
  id: string;
  label: string;
  date: string;
  status: "observed" | "current" | "forecast" | "unknown";
};

export type IntelligenceMetric = {
  id: string;
  label: string;
  value: string;
  detail: string;
  trend?: readonly number[];
};

export type InvestigationContextSummary = {
  geography: string;
  universe: string;
  horizon: string;
  selectedOpportunityId: string | null;
  asOf: string | null;
  coverageLabel: string;
};

export type IntelligenceWorkspaceData = {
  context: InvestigationContextSummary;
  messages: readonly NavigatorMessage[];
  opportunities: readonly Opportunity[];
  claims: readonly EvidenceClaim[];
  graphEntities: readonly GraphEntity[];
  graphRelationships: readonly GraphRelationship[];
  timeline: readonly TimelinePoint[];
  metrics: readonly IntelligenceMetric[];
};

export type IntelligenceWorkspaceProps = {
  data: IntelligenceWorkspaceData;
  state: IntelligenceViewState;
  lens: IntelligenceLens;
  fixtureMode?: boolean;
  readOnlyReason?: string;
  copy?: Partial<IntelligenceWorkspaceCopy>;
  className?: string;
  onLensChange: (lens: IntelligenceLens) => void;
  onOpportunitySelect: (opportunityId: string) => void;
  onClaimSelect?: (claimId: string) => void;
  onTimelineSelect?: (pointId: string) => void;
  onNavigatorSubmit?: (message: string) => Promise<void> | void;
  onRetry?: () => void;
};

export type IntelligenceWorkspaceCopy = {
  navigatorTitle: string;
  online: string;
  composerPlaceholder: string;
  send: string;
  lensLabel: string;
  opportunitiesTitle: string;
  orderByPotential: string;
  expectedReturn: string;
  confidence: string;
  claimsTitle: string;
  allClaims: string;
  fact: string;
  inference: string;
  prediction: string;
  contradiction: string;
  unknown: string;
  view: string;
  fixtureNotice: string;
  stateTitle: string;
  retry: string;
};
