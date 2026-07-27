import {
  nextHistoryEvent,
  type CandidateClaim,
  type Claim,
  type Evidence,
  type PrototypeInvestigationPayload,
  type ResearchDossier,
  type ResearchRun,
  type ResearchRunState
} from "./investigation-context";

export type PersistentResearchRunAccepted = {
  research_run_id: string;
  state: "QUEUED";
  queue_delivery: "PUBLISHED" | "OUTBOX_PENDING";
  source_ids: string[];
  synthetic: false;
};

export type PersistentResearchRunView = {
  research_run_id: string;
  context_id: string;
  opportunity_id: string;
  question: string;
  state: string;
  private_knowledge_authorised: boolean;
  source_plan: Array<Record<string, unknown>>;
  budgets: Record<string, unknown>;
  actual_usage: Record<string, unknown>;
  evidence: Array<{
    evidence_id: string;
    source_id: string;
    title: string;
    relationship: string;
    observed_at: string;
    rights_status: string;
    provisional: boolean;
    payload: Record<string, unknown>;
  }>;
  candidate_claims: Array<{
    candidate_claim_id: string;
    statement: string;
    kind: string;
    state: string;
    producer_type: string;
    method_version: string;
    canonical_claim_id: string | null;
    rejection_reasons: string[];
  }>;
  canonical_claims: Array<{
    canonical_claim_id: string;
    statement: string;
    state: "ADMITTED";
    epistemic_class: string;
  }>;
  dossier: {
    dossier_id: string;
    status: string;
    title: string;
    summary: string;
    sections: Array<Record<string, unknown>>;
    attribution: Record<string, unknown>;
  } | null;
  admission_batch_id: string | null;
  error_code: string | null;
  error_detail: string | null;
  created_at: string;
  updated_at: string;
  synthetic: false;
};

const terminalStates = new Set(["COMPLETED", "FAILED", "CANCELLED", "BUDGET_EXHAUSTED", "RIGHTS_BLOCKED", "INSUFFICIENT_EVIDENCE"]);
const progressSteps = ["QUEUED", "RETRIEVING", "CLAIMS_PROPOSED", "ADMISSION_QUEUED", "COMPLETED"] as const;

export function isTerminalPersistentState(state: string): boolean {
  return terminalStates.has(state);
}

function mappedState(state: string): ResearchRunState {
  if (state === "PROPOSING") return "CLAIMS_PROPOSED";
  if (state === "ADMISSION_PENDING") return "ADMISSION_QUEUED";
  if (state === "QUEUED" || state === "RETRIEVING" || state === "COMPLETED" || state === "FAILED") return state;
  if (state === "CANCELLED" || state === "BUDGET_EXHAUSTED" || state === "RIGHTS_BLOCKED" || state === "INSUFFICIENT_EVIDENCE") return state;
  return "FAILED";
}

function numberValue(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function sourceId(source: Record<string, unknown>, index: number): string {
  const value = source.source_id;
  return typeof value === "string" && value ? value : `source-${index + 1}`;
}

function upsertById<T>(items: T[], incoming: T[], getId: (item: T) => string): T[] {
  const ids = new Set(incoming.map(getId));
  return [...items.filter((item) => !ids.has(getId(item))), ...incoming];
}

function toEvidence(view: PersistentResearchRunView): Evidence[] {
  return view.evidence.map((item) => ({
    evidence_id: item.evidence_id,
    title: item.title,
    source: item.source_id,
    as_of: item.observed_at,
    relationship: item.relationship === "CONTRADICT" ? "CONTRADICT" : item.relationship === "UNKNOWN" ? "UNKNOWN" : "SUPPORT",
    domain: "AXIGNAL_GLOBAL",
    source_class: "OFFICIAL_API",
    rights_status: item.rights_status === "RESTRICTED" ? "RESTRICTED" : "RIGHTS_VALID",
    provisional: item.provisional,
    content_hash: typeof item.payload.content_hash === "string" ? item.payload.content_hash : undefined,
    synthetic: false
  } as unknown as Evidence));
}

function toCandidateClaims(view: PersistentResearchRunView): CandidateClaim[] {
  const evidenceIds = view.evidence.map((item) => item.evidence_id);
  return view.candidate_claims.map((item) => ({
    candidate_claim_id: item.candidate_claim_id,
    opportunity_id: view.opportunity_id,
    kind: item.kind.toUpperCase().includes("CONTRAD") ? "CONTRADICTION" : "SUPPORT",
    text: item.statement,
    state: item.state,
    evidence_ids: evidenceIds,
    producer: {
      producer_type: item.producer_type,
      producer_id: item.producer_type === "DETERMINISTIC_PARSER" ? "world-bank-wdi-parser" : "proposal-only-model",
      method_version: item.method_version
    },
    canonical_claim_id: item.canonical_claim_id,
    tenant_scope: "GLOBAL",
    synthetic: false
  } as unknown as CandidateClaim));
}

function toCanonicalClaims(view: PersistentResearchRunView): Claim[] {
  const evidenceIds = view.evidence.map((item) => item.evidence_id);
  return view.canonical_claims.map((item) => ({
    claim_id: item.canonical_claim_id,
    kind: "HECHO",
    text: item.statement,
    confidence: item.state === "ADMITTED" ? 1 : null,
    evidence_ids: evidenceIds,
    synthetic: false
  } as unknown as Claim));
}

function toDossier(view: PersistentResearchRunView): ResearchDossier | null {
  if (!view.dossier) return null;
  const candidateIds = view.candidate_claims.map((item) => item.candidate_claim_id);
  const evidenceIds = view.evidence.map((item) => item.evidence_id);
  return {
    dossier_id: view.dossier.dossier_id,
    title: view.dossier.title,
    status: view.dossier.status,
    summary: view.dossier.summary,
    sections: view.dossier.sections.map((section, index) => ({
      section_id: typeof section.section_id === "string" ? section.section_id : `section_${index + 1}`,
      title: typeof section.title === "string" ? section.title : `Sección ${index + 1}`,
      text: typeof section.text === "string" ? section.text : JSON.stringify(section),
      evidence_ids: Array.isArray(section.evidence_ids) ? section.evidence_ids.filter((item): item is string => typeof item === "string") : evidenceIds,
      candidate_claim_ids: Array.isArray(section.candidate_claim_ids) ? section.candidate_claim_ids.filter((item): item is string => typeof item === "string") : candidateIds
    })),
    source_result_ids: view.source_plan.map((source, index) => `${view.research_run_id}:${sourceId(source, index)}`),
    candidate_claim_ids: candidateIds,
    unknown_ids: [],
    private_context_used: view.private_knowledge_authorised,
    synthetic: false
  } as unknown as ResearchDossier;
}

function toResearchRun(view: PersistentResearchRunView): ResearchRun {
  const state = mappedState(view.state);
  const stateIndex = Math.max(0, progressSteps.indexOf(state as (typeof progressSteps)[number]));
  return {
    research_run_id: view.research_run_id,
    context_id: view.context_id,
    opportunity_id: view.opportunity_id,
    question: view.question,
    state,
    source_plan: view.source_plan.map((source, index) => ({
      source_result_id: `${view.research_run_id}:${sourceId(source, index)}`,
      label: sourceId(source, index),
      domain: "AXIGNAL_GLOBAL",
      source_class: "OFFICIAL_API",
      status: "USED",
      primary: index === 0,
      evidence_ids: view.evidence.filter((item) => item.source_id === sourceId(source, index)).map((item) => item.evidence_id),
      note: "Fuente institucional admitida; recuperación y parsing deterministas."
    })),
    budgets: {
      max_searches: numberValue(view.budgets.max_api_requests),
      max_documents: numberValue(view.budgets.max_documents),
      max_input_tokens: 0,
      max_output_tokens: 0,
      max_cost_minor_units: 0,
      currency: "EUR"
    },
    actual_usage: {
      searches: numberValue(view.actual_usage.api_requests),
      documents: numberValue(view.actual_usage.documents) + numberValue(view.actual_usage.fixture_reads),
      input_tokens: 0,
      output_tokens: 0,
      cost_minor_units: 0
    },
    progress: progressSteps.map((step, index) => ({
      step,
      status: index <= stateIndex && state !== "FAILED" ? "COMPLETED" : "QUEUED"
    })),
    evidence_ids: view.evidence.map((item) => item.evidence_id),
    candidate_claim_ids: view.candidate_claims.map((item) => item.candidate_claim_id),
    unknown_ids: [],
    dossier_id: view.dossier?.dossier_id ?? "",
    admission_batch_id: view.admission_batch_id ?? "",
    private_knowledge_authorised: view.private_knowledge_authorised,
    created_at: view.created_at,
    updated_at: view.updated_at,
    synthetic: false
  } as unknown as ResearchRun;
}

export function integratePersistentResearchRun(
  payload: PrototypeInvestigationPayload,
  view: PersistentResearchRunView
): PrototypeInvestigationPayload {
  const current = structuredClone(payload);
  const previousRun = current.research_runs.find((item) => item.research_run_id === view.research_run_id);
  const state = mappedState(view.state);
  const run = toResearchRun(view);
  const evidence = toEvidence(view);
  const candidates = toCandidateClaims(view);
  const canonicalClaims = toCanonicalClaims(view);
  const dossier = toDossier(view);

  current.research_runs = upsertById(current.research_runs, [run], (item) => item.research_run_id);
  current.evidence = upsertById(current.evidence, evidence, (item) => item.evidence_id);
  current.candidate_claims = upsertById(current.candidate_claims, candidates, (item) => item.candidate_claim_id);
  current.claims = upsertById(current.claims, canonicalClaims, (item) => item.claim_id);
  if (dossier) current.dossiers = upsertById(current.dossiers, [dossier], (item) => item.dossier_id);

  const opportunity = current.opportunities.find((item) => item.opportunity_id === view.opportunity_id);
  if (opportunity) {
    opportunity.claim_ids = [...new Set([...opportunity.claim_ids, ...canonicalClaims.map((item) => item.claim_id)])];
    opportunity.evidence_count = new Set([...current.evidence.filter((item) => opportunity.claim_ids.some((claimId) => current.claims.find((claim) => claim.claim_id === claimId)?.evidence_ids.includes(item.evidence_id)))]).size;
  }

  const terminal = isTerminalPersistentState(view.state);
  current.context.research.active_run_ids = terminal
    ? current.context.research.active_run_ids.filter((id) => id !== view.research_run_id)
    : [...new Set([...current.context.research.active_run_ids, view.research_run_id])];
  current.context.research.selected_run_id = view.research_run_id;
  current.context.research.selected_run_state = state;
  current.context.research.last_completed_run_id = view.state === "COMPLETED" ? view.research_run_id : current.context.research.last_completed_run_id;
  current.context.research.provisional_evidence_ids = evidence.filter((item) => item.provisional).map((item) => item.evidence_id);
  current.context.research.candidate_claim_ids = candidates.map((item) => item.candidate_claim_id);
  current.context.research.dossier_id = dossier?.dossier_id ?? null;
  current.context.research.admission_batch_id = view.admission_batch_id;
  current.context.coverage.source_ids = [...new Set([...current.context.coverage.source_ids, ...evidence.map((item) => item.evidence_id)])];
  current.context.coverage.status = view.state === "COMPLETED" ? "AVAILABLE" : current.context.coverage.status;
  current.context.coverage.summary = view.state === "COMPLETED"
    ? "ResearchRun persistente completada con evidencia institucional trazable."
    : `ResearchRun persistente en estado ${view.state}.`;
  current.context.rail_mode = dossier ? "DOSSIER" : "RESEARCH";
  current.context.selection.evidence_ids = evidence[0] ? [evidence[0].evidence_id] : current.context.selection.evidence_ids;
  current.context.selection.claim_ids = canonicalClaims[0] ? [canonicalClaims[0].claim_id] : current.context.selection.claim_ids;

  if (!previousRun || previousRun.state !== state) {
    current.context.history.push(nextHistoryEvent(
      current.context,
      `RESEARCH_${view.state}`,
      null,
      view.research_run_id
    ));
    current.context.version += 1;
  }
  current.context.updated_at = view.updated_at;
  current.focus = {
    opportunity_id: view.opportunity_id,
    claim_id: canonicalClaims[0]?.claim_id ?? null,
    evidence_id: evidence[0]?.evidence_id ?? null
  };
  current.explanation = view.state === "COMPLETED"
    ? "La ResearchRun persistente ha devuelto dossier, evidencia y claims al InvestigationContext."
    : view.state === "FAILED"
      ? `La ResearchRun falló de forma cerrada: ${view.error_code ?? "UNKNOWN"}.`
      : `ResearchRun persistente ${view.research_run_id} · ${view.state}.`;
  return current;
}
