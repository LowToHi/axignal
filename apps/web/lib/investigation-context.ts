export type Lens = "AUTO" | "GLOBE" | "GRAPH" | "DUAL";
export type Theme = "dark" | "light";
export type Locale = "en" | "es" | "fr" | "de" | "pt-BR" | "zh-Hans";
export type ClaimKind = "HECHO" | "INFERENCIA" | "PREDICCIÓN" | "CONTRADICCIÓN" | "DESCONOCIDO";
export type RailMode = "CONTEXT" | "OPPORTUNITY" | "CLAIM" | "EVIDENCE" | "EXPLANATION" | "COVERAGE";

export type Message = {
  id: string;
  actor: "user" | "axignal";
  text: string;
  occurredAt: string;
};

export type Evidence = {
  evidence_id: string;
  title: string;
  source: string;
  as_of: string;
  relationship: "SUPPORT" | "CONTRADICT" | "UNKNOWN";
  synthetic: true;
};

export type Claim = {
  claim_id: string;
  kind: ClaimKind;
  text: string;
  confidence: number | null;
  evidence_ids: string[];
  synthetic: true;
};

export type Opportunity = {
  opportunity_id: string;
  name: string;
  expected_return_label: string;
  confidence: number;
  level: "ALTA" | "MEDIA" | "MEDIA-BAJA";
  claim_ids: string[];
  evidence_count: number;
  contradiction_count: number;
  synthetic: true;
};

export type InvestigationHistoryEvent = {
  event_id: string;
  event_type: string;
  occurred_at: string;
  command_plan_id: string | null;
};

export type InvestigationContext = {
  context_id: string;
  version: number;
  locale: Locale;
  original_query: string | null;
  query_language: string | null;
  lens: Lens;
  lens_reason: string | null;
  time: {
    mode: "CURRENT" | "AS_OF" | "RANGE" | "COMPARE";
    horizon_label: "12M" | "24M" | "36M";
  };
  geographies: string[];
  entities: string[];
  universes: string[];
  filters: Record<string, string | number | boolean | null>;
  selection: {
    opportunity_ids: string[];
    claim_ids: string[];
    evidence_ids: string[];
    graph_node_ids: string[];
  };
  coverage: {
    status: "AVAILABLE" | "PARTIAL" | "UNAVAILABLE" | "UNLICENSED" | "UNKNOWN";
    summary: string | null;
    source_ids: string[];
  };
  rail_mode: RailMode;
  history: InvestigationHistoryEvent[];
  entitlement_snapshot_id: string | null;
  saved_trail_id: string | null;
  updated_at: string;
  synthetic: true;
};

export type PrototypeInvestigationPayload = {
  context: InvestigationContext;
  opportunities: Opportunity[];
  claims: Claim[];
  evidence: Evidence[];
  explanation: string;
  focus: {
    opportunity_id: string | null;
    claim_id: string | null;
    evidence_id: string | null;
  };
};

export type PersistedShellState = {
  schemaVersion: 1;
  payload: PrototypeInvestigationPayload;
  messages: Message[];
  theme: Theme;
};

const FIXED_TIME = "2026-07-27T00:00:00Z";

const opportunities: Opportunity[] = [
  {
    opportunity_id: "opp_moscow_ramenki",
    name: "Distrito de Ramenki",
    expected_return_label: "18.7%",
    confidence: 0.78,
    level: "ALTA",
    claim_ids: ["clm_ramenki_rent", "clm_ramenki_metro", "clm_ramenki_supply", "clm_ramenki_rates", "clm_ramenki_tax"],
    evidence_count: 4,
    contradiction_count: 1,
    synthetic: true
  },
  {
    opportunity_id: "opp_moscow_zil",
    name: "Zona ZIL",
    expected_return_label: "16.2%",
    confidence: 0.72,
    level: "ALTA",
    claim_ids: ["clm_zil_regeneration", "clm_zil_transport", "clm_zil_rates"],
    evidence_count: 3,
    contradiction_count: 1,
    synthetic: true
  },
  {
    opportunity_id: "opp_moscow_khamovniki",
    name: "Khamovniki",
    expected_return_label: "12.1%",
    confidence: 0.64,
    level: "MEDIA",
    claim_ids: ["clm_khamovniki_supply", "clm_ramenki_rates"],
    evidence_count: 2,
    contradiction_count: 1,
    synthetic: true
  },
  {
    opportunity_id: "opp_moscow_basmanniy",
    name: "Basmanniy",
    expected_return_label: "9.8%",
    confidence: 0.48,
    level: "MEDIA-BAJA",
    claim_ids: ["clm_basmanniy_demand", "clm_ramenki_tax"],
    evidence_count: 1,
    contradiction_count: 0,
    synthetic: true
  }
];

const claims: Claim[] = [
  { claim_id: "clm_ramenki_rent", kind: "HECHO", text: "Los precios de alquiler en Ramenki han crecido un 14% interanual.", confidence: 0.86, evidence_ids: ["ev_cbr_rent"], synthetic: true },
  { claim_id: "clm_ramenki_metro", kind: "INFERENCIA", text: "La nueva línea de metro aumentaría la demanda en un 15–20%.", confidence: 0.68, evidence_ids: ["ev_transport_model"], synthetic: true },
  { claim_id: "clm_ramenki_supply", kind: "PREDICCIÓN", text: "Se espera escasez de oferta de vivienda premium en 2025.", confidence: 0.61, evidence_ids: ["ev_supply_model"], synthetic: true },
  { claim_id: "clm_ramenki_rates", kind: "CONTRADICCIÓN", text: "Altas tasas hipotecarias podrían reducir la demanda en 2025.", confidence: 0.79, evidence_ids: ["ev_bank_rates"], synthetic: true },
  { claim_id: "clm_ramenki_tax", kind: "DESCONOCIDO", text: "No hay evidencia suficiente sobre futuros cambios fiscales.", confidence: null, evidence_ids: ["ev_coverage_gap"], synthetic: true },
  { claim_id: "clm_zil_regeneration", kind: "HECHO", text: "La regeneración urbana de ZIL mantiene inversión pública comprometida.", confidence: 0.82, evidence_ids: ["ev_zil_plan"], synthetic: true },
  { claim_id: "clm_zil_transport", kind: "INFERENCIA", text: "La conectividad adicional puede acelerar la absorción residencial.", confidence: 0.66, evidence_ids: ["ev_transport_model"], synthetic: true },
  { claim_id: "clm_zil_rates", kind: "CONTRADICCIÓN", text: "El coste de financiación puede retrasar nuevas promociones.", confidence: 0.73, evidence_ids: ["ev_bank_rates"], synthetic: true },
  { claim_id: "clm_khamovniki_supply", kind: "HECHO", text: "La oferta disponible en Khamovniki continúa limitada.", confidence: 0.8, evidence_ids: ["ev_supply_model"], synthetic: true },
  { claim_id: "clm_basmanniy_demand", kind: "INFERENCIA", text: "La demanda de alquiler profesional permanece resiliente.", confidence: 0.57, evidence_ids: ["ev_cbr_rent"], synthetic: true }
];

const evidence: Evidence[] = [
  { evidence_id: "ev_cbr_rent", title: "Rental market research", source: "CBR Research", as_of: "2024-04-15", relationship: "SUPPORT", synthetic: true },
  { evidence_id: "ev_transport_model", title: "Transport accessibility model", source: "AXIGNAL synthetic model fixture", as_of: "2024-03-03", relationship: "SUPPORT", synthetic: true },
  { evidence_id: "ev_supply_model", title: "Premium housing supply model", source: "AXIGNAL synthetic model fixture", as_of: "2024-02-28", relationship: "SUPPORT", synthetic: true },
  { evidence_id: "ev_bank_rates", title: "Mortgage rate environment", source: "Banco de Rusia", as_of: "2024-05-10", relationship: "CONTRADICT", synthetic: true },
  { evidence_id: "ev_coverage_gap", title: "Tax-policy coverage gap", source: "Coverage registry", as_of: "2024-05-10", relationship: "UNKNOWN", synthetic: true },
  { evidence_id: "ev_zil_plan", title: "ZIL regeneration programme", source: "Moscow urban plan fixture", as_of: "2024-04-02", relationship: "SUPPORT", synthetic: true }
];

export const initialMessages: Message[] = [
  { id: "msg_0001", actor: "user", text: "Quiero ver si hay oportunidades inmobiliarias en Moscú", occurredAt: FIXED_TIME },
  { id: "msg_0002", actor: "axignal", text: "He centrado la investigación en Moscú, Rusia, en oportunidades inmobiliarias para 12–24 meses.", occurredAt: FIXED_TIME },
  { id: "msg_0003", actor: "axignal", text: "He identificado oportunidades sintéticas y he separado apoyo, contradicción y cobertura desconocida.", occurredAt: FIXED_TIME }
];

export function createInitialInvestigation(locale: Locale = "es"): PrototypeInvestigationPayload {
  return {
    context: {
      context_id: "ctx_moscow_real_estate_v01",
      version: 1,
      locale,
      original_query: "Quiero ver si hay oportunidades inmobiliarias en Moscú",
      query_language: "es",
      lens: "GLOBE",
      lens_reason: "La intención principal es geográfica.",
      time: { mode: "CURRENT", horizon_label: "24M" },
      geographies: ["geo_moscow_ru"],
      entities: ["entity_moscow"],
      universes: ["REAL_ESTATE"],
      filters: { geography: "Moscú, Rusia", universe: "Real Estate", horizon: "12–24 meses" },
      selection: {
        opportunity_ids: ["opp_moscow_ramenki"],
        claim_ids: [],
        evidence_ids: [],
        graph_node_ids: ["entity_moscow", "opp_moscow_ramenki"]
      },
      coverage: {
        status: "PARTIAL",
        summary: "Fixture sintética con cobertura deliberadamente incompleta.",
        source_ids: evidence.map((item) => item.evidence_id)
      },
      rail_mode: "OPPORTUNITY",
      history: [{ event_id: "evt_0001", event_type: "INVESTIGATION_CREATED", occurred_at: FIXED_TIME, command_plan_id: "plan_0001" }],
      entitlement_snapshot_id: null,
      saved_trail_id: null,
      updated_at: FIXED_TIME,
      synthetic: true
    },
    opportunities: structuredClone(opportunities),
    claims: structuredClone(claims),
    evidence: structuredClone(evidence),
    explanation: "Contexto sintético inicial cargado.",
    focus: { opportunity_id: "opp_moscow_ramenki", claim_id: null, evidence_id: null }
  };
}

export function nextHistoryEvent(context: InvestigationContext, eventType: string, commandPlanId: string | null = null): InvestigationHistoryEvent {
  const nextVersion = context.version + 1;
  return {
    event_id: `evt_${String(nextVersion).padStart(4, "0")}`,
    event_type: eventType,
    occurred_at: new Date().toISOString(),
    command_plan_id: commandPlanId
  };
}

export function updateContext(
  payload: PrototypeInvestigationPayload,
  updater: (context: InvestigationContext) => InvestigationContext,
  explanation: string
): PrototypeInvestigationPayload {
  const context = updater(structuredClone(payload.context));
  context.version += 1;
  context.updated_at = new Date().toISOString();
  return { ...payload, context, explanation };
}

export function findSelectedOpportunity(payload: PrototypeInvestigationPayload): Opportunity {
  const selectedId = payload.context.selection.opportunity_ids[0];
  return payload.opportunities.find((item) => item.opportunity_id === selectedId) ?? payload.opportunities[0];
}

export function claimsForSelectedOpportunity(payload: PrototypeInvestigationPayload): Claim[] {
  const selected = findSelectedOpportunity(payload);
  const claimIds = new Set(selected.claim_ids);
  return payload.claims.filter((claim) => claimIds.has(claim.claim_id));
}

export function evidenceForClaim(payload: PrototypeInvestigationPayload, claim: Claim): Evidence[] {
  const evidenceIds = new Set(claim.evidence_ids);
  return payload.evidence.filter((item) => evidenceIds.has(item.evidence_id));
}
