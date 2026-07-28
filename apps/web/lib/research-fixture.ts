import {
  findSelectedOpportunity,
  nextHistoryEvent,
  normaliseInvestigationPayload,
  type CandidateClaim,
  type Evidence,
  type Locale,
  type PrototypeInvestigationPayload,
  type ResearchDossier,
  type ResearchRun,
  type ResearchSourceResult,
  type ResearchUnknown
} from "./investigation-context";

export type ResearchRunRequest = {
  question: string;
  locale: Locale;
  includePrivateKnowledge: boolean;
  payload: PrototypeInvestigationPayload;
};

const FIXTURE_TIME = "2026-07-27T18:00:00Z";

function uniqueById<T extends Record<K, string>, K extends keyof T>(items: T[], key: K): T[] {
  return [...new Map(items.map((item) => [item[key], item])).values()];
}

export function executeSyntheticResearchRun(request: ResearchRunRequest): PrototypeInvestigationPayload {
  const current = normaliseInvestigationPayload(structuredClone(request.payload));
  if (current.context.context_id !== "ctx_moscow_real_estate_v01" || current.context.synthetic !== true) {
    throw new Error("Unsupported or non-synthetic InvestigationContext.");
  }

  const opportunity = findSelectedOpportunity(current);
  const runId = `rr_${opportunity.opportunity_id.slice(4)}_0001`;
  const dossierId = `dos_${opportunity.opportunity_id.slice(4)}_0001`;
  const admissionBatchId = `adm_${opportunity.opportunity_id.slice(4)}_0001`;

  const officialEvidence: Evidence = {
    evidence_id: "ev_research_official_permits",
    title: "Residential permit and completion indicators",
    source: "Moscow housing indicators API fixture",
    as_of: "2026-06-30",
    relationship: "SUPPORT",
    domain: "EXTERNAL_AUTHORISED",
    source_class: "OFFICIAL_API",
    rights_status: "RIGHTS_VALID",
    content_hash: "sha256:fixture-official-permits-v1",
    provisional: true,
    synthetic: true
  };

  const browserEvidence: Evidence = {
    evidence_id: "ev_research_browser_financing",
    title: "Urban housing finance policy bulletin",
    source: "Authorised institutional Browser fixture",
    as_of: "2026-07-01",
    relationship: "CONTRADICT",
    domain: "EXTERNAL_AUTHORISED",
    source_class: "AUTHORISED_BROWSER",
    rights_status: "RIGHTS_VALID",
    content_hash: "sha256:fixture-browser-policy-v1",
    provisional: true,
    injection_detected: true,
    synthetic: true
  };

  const unknownEvidence: Evidence = {
    evidence_id: "ev_research_tax_unknown",
    title: "Foreign-buyer tax-policy coverage gap",
    source: "AXIGNAL coverage registry fixture",
    as_of: "2026-07-27",
    relationship: "UNKNOWN",
    domain: "AXIGNAL_GLOBAL",
    source_class: "CANONICAL",
    rights_status: "RIGHTS_VALID",
    content_hash: "sha256:fixture-tax-gap-v1",
    provisional: true,
    synthetic: true
  };

  const privateEvidence: Evidence = {
    evidence_id: "ev_private_commute_note",
    title: "Tenant note about commute sensitivity",
    source: "Tenant-private note fixture",
    as_of: "2026-07-27",
    relationship: "UNKNOWN",
    domain: "TENANT_PRIVATE",
    source_class: "TENANT_PRIVATE",
    rights_status: "PRIVATE_USE",
    content_hash: "sha256:fixture-private-note-v1",
    provisional: true,
    synthetic: true
  };

  const supportClaim: CandidateClaim = {
    candidate_claim_id: "ccl_ramenki_permit_resilience",
    opportunity_id: opportunity.opportunity_id,
    kind: "SUPPORT",
    text: "Los indicadores oficiales sintéticos muestran continuidad de permisos y finalizaciones residenciales en el ámbito analizado.",
    state: "ADMISSION_QUEUED",
    evidence_ids: [officialEvidence.evidence_id],
    producer: {
      producer_type: "DETERMINISTIC_PARSER",
      producer_id: "official-api-fixture-parser",
      method_version: "research-fixture@1.0.0"
    },
    canonical_claim_id: null,
    tenant_scope: "GLOBAL",
    synthetic: true
  };

  const contradictionClaim: CandidateClaim = {
    candidate_claim_id: "ccl_ramenki_financing_pressure",
    opportunity_id: opportunity.opportunity_id,
    kind: "CONTRADICTION",
    text: "El contexto de financiación descrito por la fuente institucional sintética puede reducir la absorción y retrasar nuevas promociones.",
    state: "ADMISSION_QUEUED",
    evidence_ids: [browserEvidence.evidence_id],
    producer: {
      producer_type: "LOCAL_MODEL_FIXTURE",
      producer_id: "local-research-worker-fixture",
      method_version: "candidate-claim-proposal@1.0.0"
    },
    canonical_claim_id: null,
    tenant_scope: "GLOBAL",
    synthetic: true
  };

  const unknown: ResearchUnknown = {
    unknown_id: "unk_ramenki_foreign_buyer_tax",
    text: "No existe cobertura suficiente para determinar cambios futuros en la fiscalidad aplicable a compradores extranjeros.",
    reason: "No se encontró una fuente autorizada y vigente dentro del presupuesto de la fixture."
  };

  const sources: ResearchSourceResult[] = [
    {
      source_result_id: "srcres_official_api",
      label: "Moscow housing indicators API fixture",
      domain: "EXTERNAL_AUTHORISED",
      source_class: "OFFICIAL_API",
      status: "USED",
      primary: true,
      evidence_ids: [officialEvidence.evidence_id],
      note: "Fuente estructurada priorizada antes del Browser."
    },
    {
      source_result_id: "srcres_authorised_browser",
      label: "Institutional policy document Browser fixture",
      domain: "EXTERNAL_AUTHORISED",
      source_class: "AUTHORISED_BROWSER",
      status: "IGNORED_INJECTION",
      primary: true,
      evidence_ids: [browserEvidence.evidence_id],
      note: "El contenido incluía una instrucción hostil de fixture; fue ignorada y no cambió herramientas, presupuesto ni autoridad."
    },
    {
      source_result_id: "srcres_private_note",
      label: "Tenant-private note fixture",
      domain: "TENANT_PRIVATE",
      source_class: "TENANT_PRIVATE",
      status: request.includePrivateKnowledge ? "USED" : "NOT_AUTHORISED",
      primary: false,
      evidence_ids: request.includePrivateKnowledge ? [privateEvidence.evidence_id] : [],
      note: request.includePrivateKnowledge
        ? "Usada solo como contexto privado; no alimenta Candidate Claims globales."
        : "No utilizada porque la memoria privada no fue autorizada para este ResearchRun."
    }
  ];

  const dossier: ResearchDossier = {
    dossier_id: dossierId,
    title: `Dossier regulatorio y socioeconómico · ${opportunity.name}`,
    status: "TRACEABLE_PROVISIONAL",
    summary: "La investigación sintética encontró una señal de continuidad residencial, una presión adversa de financiación y un vacío fiscal material. Ningún resultado ha sido admitido como claim canónico.",
    sections: [
      {
        section_id: "sec_official_context",
        title: "Contexto socioeconómico",
        text: "La fixture de API oficial aporta una señal estructurada de continuidad de actividad residencial. Requiere validación temporal, cuantitativa y de fuente antes de cualquier admisión.",
        evidence_ids: [officialEvidence.evidence_id],
        candidate_claim_ids: [supportClaim.candidate_claim_id]
      },
      {
        section_id: "sec_adverse_context",
        title: "Evidencia adversa",
        text: "La fixture institucional recuperada mediante Browser autorizado introduce presión de financiación. La instrucción hostil contenida en el documento fue aislada e ignorada.",
        evidence_ids: [browserEvidence.evidence_id],
        candidate_claim_ids: [contradictionClaim.candidate_claim_id]
      },
      {
        section_id: "sec_unknowns",
        title: "Unknowns",
        text: unknown.text,
        evidence_ids: [unknownEvidence.evidence_id],
        candidate_claim_ids: []
      },
      ...(request.includePrivateKnowledge
        ? [{
            section_id: "sec_private_context",
            title: "Contexto privado autorizado",
            text: "La nota privada sintética señala sensibilidad al tiempo de desplazamiento. Se muestra únicamente en este dossier privado y no participa en el admission batch global.",
            evidence_ids: [privateEvidence.evidence_id],
            candidate_claim_ids: []
          }]
        : [])
    ],
    source_result_ids: sources.map((item) => item.source_result_id),
    candidate_claim_ids: [supportClaim.candidate_claim_id, contradictionClaim.candidate_claim_id],
    unknown_ids: [unknown.unknown_id],
    private_context_used: request.includePrivateKnowledge,
    synthetic: true
  };

  const evidenceIds = [officialEvidence.evidence_id, browserEvidence.evidence_id, unknownEvidence.evidence_id];
  if (request.includePrivateKnowledge) evidenceIds.push(privateEvidence.evidence_id);

  const run: ResearchRun = {
    research_run_id: runId,
    context_id: current.context.context_id,
    opportunity_id: opportunity.opportunity_id,
    question: request.question,
    state: "ADMISSION_QUEUED",
    source_plan: sources,
    budgets: {
      max_searches: 6,
      max_documents: 8,
      max_input_tokens: 120_000,
      max_output_tokens: 12_000,
      max_cost_minor_units: 25,
      currency: "EUR"
    },
    actual_usage: {
      searches: 0,
      documents: request.includePrivateKnowledge ? 3 : 2,
      input_tokens: 0,
      output_tokens: 0,
      cost_minor_units: 0
    },
    progress: [
      { step: "Plan de investigación", status: "COMPLETED" },
      { step: "API oficial sintética", status: "COMPLETED" },
      { step: "Browser autorizado sintético", status: "COMPLETED" },
      { step: "Evidence Objects", status: "COMPLETED" },
      { step: "Candidate Claims", status: "COMPLETED" },
      { step: "Dossier trazable", status: "COMPLETED" },
      { step: "Admission runtime", status: "QUEUED" }
    ],
    evidence_ids: evidenceIds,
    candidate_claim_ids: [supportClaim.candidate_claim_id, contradictionClaim.candidate_claim_id],
    unknown_ids: [unknown.unknown_id],
    dossier_id: dossierId,
    admission_batch_id: admissionBatchId,
    private_knowledge_authorised: request.includePrivateKnowledge,
    created_at: FIXTURE_TIME,
    updated_at: FIXTURE_TIME,
    synthetic: true
  };

  const nextContext = structuredClone(current.context);
  nextContext.version += 1;
  nextContext.updated_at = FIXTURE_TIME;
  nextContext.rail_mode = "RESEARCH";
  nextContext.research = {
    active_run_ids: [],
    selected_run_id: runId,
    last_completed_run_id: runId,
    selected_run_state: run.state,
    provisional_evidence_ids: evidenceIds.filter((id) => id !== privateEvidence.evidence_id),
    candidate_claim_ids: run.candidate_claim_ids,
    dossier_id: dossierId,
    admission_batch_id: admissionBatchId
  };
  nextContext.history.push(
    nextHistoryEvent(
      { ...nextContext, version: nextContext.version - 1 },
      "RESEARCH_ADMISSION_QUEUED",
      `cmd_research_${String(nextContext.version).padStart(4, "0")}`,
      runId
    )
  );

  return {
    ...current,
    context: nextContext,
    evidence: uniqueById([...current.evidence, officialEvidence, browserEvidence, unknownEvidence, ...(request.includePrivateKnowledge ? [privateEvidence] : [])], "evidence_id"),
    research_runs: uniqueById([...current.research_runs, run], "research_run_id"),
    candidate_claims: uniqueById([...current.candidate_claims, supportClaim, contradictionClaim], "candidate_claim_id"),
    dossiers: uniqueById([...current.dossiers, dossier], "dossier_id"),
    unknowns: uniqueById([...current.unknowns, unknown], "unknown_id"),
    explanation: "ResearchRun completado sobre fixtures autorizadas. He generado Evidence Objects, dos Candidate Claims, una contradicción, un unknown y un dossier. La admisión canónica sigue pendiente.",
    focus: { opportunity_id: opportunity.opportunity_id, claim_id: null, evidence_id: officialEvidence.evidence_id }
  };
}
