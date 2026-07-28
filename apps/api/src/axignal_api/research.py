from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/prototype", tags=["prototype-research"])

ResearchState = Literal["ADMISSION_QUEUED"]
Domain = Literal["EXTERNAL_AUTHORISED", "TENANT_PRIVATE", "AXIGNAL_GLOBAL"]
SourceClass = Literal["OFFICIAL_API", "AUTHORISED_BROWSER", "TENANT_PRIVATE"]


class ResearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8_000)
    opportunity_id: Literal["opp_moscow_ramenki"] = "opp_moscow_ramenki"
    include_private_knowledge: bool = False


class ResearchSource(BaseModel):
    source_result_id: str
    label: str
    domain: Domain
    source_class: SourceClass
    status: Literal["USED", "NOT_AUTHORISED", "IGNORED_INJECTION"]
    primary: bool
    evidence_ids: list[str]
    note: str


class ResearchEvidence(BaseModel):
    evidence_id: str
    title: str
    source: str
    relationship: Literal["SUPPORT", "CONTRADICT", "UNKNOWN"]
    domain: Domain
    source_class: Literal[
        "OFFICIAL_API",
        "AUTHORISED_BROWSER",
        "TENANT_PRIVATE",
        "CANONICAL",
    ]
    rights_status: Literal["RIGHTS_VALID", "PRIVATE_USE"]
    content_hash: str
    provisional: Literal[True] = True
    injection_detected: bool = False
    synthetic: Literal[True] = True


class CandidateProducer(BaseModel):
    producer_type: Literal["DETERMINISTIC_PARSER", "LOCAL_MODEL_FIXTURE"]
    producer_id: str
    method_version: str


class CandidateClaim(BaseModel):
    candidate_claim_id: str
    opportunity_id: str
    kind: Literal["SUPPORT", "CONTRADICTION"]
    text: str
    state: ResearchState = "ADMISSION_QUEUED"
    evidence_ids: list[str]
    producer: CandidateProducer
    canonical_claim_id: None = None
    tenant_scope: Literal["GLOBAL"] = "GLOBAL"
    synthetic: Literal[True] = True


class ResearchUnknown(BaseModel):
    unknown_id: str
    text: str
    reason: str


class DossierSection(BaseModel):
    section_id: str
    title: str
    text: str
    evidence_ids: list[str]
    candidate_claim_ids: list[str]


class ResearchDossier(BaseModel):
    dossier_id: str
    title: str
    status: Literal["TRACEABLE_PROVISIONAL"] = "TRACEABLE_PROVISIONAL"
    summary: str
    sections: list[DossierSection]
    private_context_used: bool
    synthetic: Literal[True] = True


class ResearchBudget(BaseModel):
    max_searches: int = 6
    max_documents: int = 8
    max_input_tokens: int = 120_000
    max_output_tokens: int = 12_000
    max_cost_minor_units: int = 25
    currency: Literal["EUR"] = "EUR"


class ResearchUsage(BaseModel):
    searches: int = 0
    documents: int
    input_tokens: int = 0
    output_tokens: int = 0
    cost_minor_units: int = 0


class ResearchRun(BaseModel):
    research_run_id: str
    context_id: Literal["ctx_moscow_real_estate_v01"]
    opportunity_id: Literal["opp_moscow_ramenki"]
    question: str
    state: ResearchState
    source_plan: list[ResearchSource]
    budgets: ResearchBudget
    actual_usage: ResearchUsage
    evidence_ids: list[str]
    candidate_claim_ids: list[str]
    unknown_ids: list[str]
    dossier_id: str
    admission_batch_id: str
    private_knowledge_authorised: bool
    created_at: datetime
    updated_at: datetime
    synthetic: Literal[True] = True


class ResearchContextUpdate(BaseModel):
    rail_mode: Literal["RESEARCH"] = "RESEARCH"
    selected_run_id: str
    selected_run_state: ResearchState
    provisional_evidence_ids: list[str]
    candidate_claim_ids: list[str]
    dossier_id: str
    admission_batch_id: str
    history_event_type: Literal["RESEARCH_ADMISSION_QUEUED"]


class ResearchResponse(BaseModel):
    run: ResearchRun
    evidence: list[ResearchEvidence]
    candidate_claims: list[CandidateClaim]
    unknowns: list[ResearchUnknown]
    dossier: ResearchDossier
    context_update: ResearchContextUpdate
    explanation: str


def build_research_response(request: ResearchRequest) -> ResearchResponse:
    fixed = datetime(2026, 7, 27, 18, tzinfo=UTC)
    official = ResearchEvidence(
        evidence_id="ev_research_official_permits",
        title="Residential permit and completion indicators",
        source="Moscow housing indicators API fixture",
        relationship="SUPPORT",
        domain="EXTERNAL_AUTHORISED",
        source_class="OFFICIAL_API",
        rights_status="RIGHTS_VALID",
        content_hash="sha256:fixture-official-permits-v1",
    )
    browser = ResearchEvidence(
        evidence_id="ev_research_browser_financing",
        title="Urban housing finance policy bulletin",
        source="Authorised institutional Browser fixture",
        relationship="CONTRADICT",
        domain="EXTERNAL_AUTHORISED",
        source_class="AUTHORISED_BROWSER",
        rights_status="RIGHTS_VALID",
        content_hash="sha256:fixture-browser-policy-v1",
        injection_detected=True,
    )
    unknown_evidence = ResearchEvidence(
        evidence_id="ev_research_tax_unknown",
        title="Foreign-buyer tax-policy coverage gap",
        source="AXIGNAL coverage registry fixture",
        relationship="UNKNOWN",
        domain="AXIGNAL_GLOBAL",
        source_class="CANONICAL",
        rights_status="RIGHTS_VALID",
        content_hash="sha256:fixture-tax-gap-v1",
    )
    private = ResearchEvidence(
        evidence_id="ev_private_commute_note",
        title="Tenant note about commute sensitivity",
        source="Tenant-private note fixture",
        relationship="UNKNOWN",
        domain="TENANT_PRIVATE",
        source_class="TENANT_PRIVATE",
        rights_status="PRIVATE_USE",
        content_hash="sha256:fixture-private-note-v1",
    )

    support = CandidateClaim(
        candidate_claim_id="ccl_ramenki_permit_resilience",
        opportunity_id=request.opportunity_id,
        kind="SUPPORT",
        text=(
            "Los indicadores oficiales sintéticos muestran continuidad de permisos "
            "y finalizaciones residenciales en el ámbito analizado."
        ),
        evidence_ids=[official.evidence_id],
        producer=CandidateProducer(
            producer_type="DETERMINISTIC_PARSER",
            producer_id="official-api-fixture-parser",
            method_version="research-fixture@1.0.0",
        ),
    )
    contradiction = CandidateClaim(
        candidate_claim_id="ccl_ramenki_financing_pressure",
        opportunity_id=request.opportunity_id,
        kind="CONTRADICTION",
        text=(
            "El contexto de financiación descrito por la fuente institucional "
            "sintética puede reducir la absorción y retrasar promociones."
        ),
        evidence_ids=[browser.evidence_id],
        producer=CandidateProducer(
            producer_type="LOCAL_MODEL_FIXTURE",
            producer_id="local-research-worker-fixture",
            method_version="candidate-claim-proposal@1.0.0",
        ),
    )
    unknown = ResearchUnknown(
        unknown_id="unk_ramenki_foreign_buyer_tax",
        text=(
            "No existe cobertura suficiente para determinar cambios futuros "
            "en la fiscalidad de compradores extranjeros."
        ),
        reason="No se encontró una fuente autorizada vigente dentro del presupuesto.",
    )

    evidence = [official, browser, unknown_evidence]
    if request.include_private_knowledge:
        evidence.append(private)

    sources = [
        ResearchSource(
            source_result_id="srcres_official_api",
            label="Moscow housing indicators API fixture",
            domain="EXTERNAL_AUTHORISED",
            source_class="OFFICIAL_API",
            status="USED",
            primary=True,
            evidence_ids=[official.evidence_id],
            note="Fuente estructurada priorizada antes del Browser.",
        ),
        ResearchSource(
            source_result_id="srcres_authorised_browser",
            label="Institutional policy document Browser fixture",
            domain="EXTERNAL_AUTHORISED",
            source_class="AUTHORISED_BROWSER",
            status="IGNORED_INJECTION",
            primary=True,
            evidence_ids=[browser.evidence_id],
            note=(
                "Una instrucción hostil fue ignorada y no modificó herramientas, "
                "presupuesto ni autoridad."
            ),
        ),
        ResearchSource(
            source_result_id="srcres_private_note",
            label="Tenant-private note fixture",
            domain="TENANT_PRIVATE",
            source_class="TENANT_PRIVATE",
            status="USED" if request.include_private_knowledge else "NOT_AUTHORISED",
            primary=False,
            evidence_ids=[private.evidence_id] if request.include_private_knowledge else [],
            note=(
                "Usada solo como contexto privado; no alimenta Candidate Claims globales."
                if request.include_private_knowledge
                else "No utilizada porque no fue autorizada para este ResearchRun."
            ),
        ),
    ]

    sections = [
        DossierSection(
            section_id="sec_official_context",
            title="Contexto socioeconómico",
            text="La API oficial sintética aporta una señal estructurada provisional.",
            evidence_ids=[official.evidence_id],
            candidate_claim_ids=[support.candidate_claim_id],
        ),
        DossierSection(
            section_id="sec_adverse_context",
            title="Evidencia adversa",
            text=(
                "La fuente institucional sintética introduce presión de financiación; "
                "la instrucción hostil del documento fue aislada."
            ),
            evidence_ids=[browser.evidence_id],
            candidate_claim_ids=[contradiction.candidate_claim_id],
        ),
        DossierSection(
            section_id="sec_unknowns",
            title="Unknowns",
            text=unknown.text,
            evidence_ids=[unknown_evidence.evidence_id],
            candidate_claim_ids=[],
        ),
    ]
    if request.include_private_knowledge:
        sections.append(
            DossierSection(
                section_id="sec_private_context",
                title="Contexto privado autorizado",
                text=(
                    "La nota privada sintética se limita al dossier privado y no "
                    "participa en el admission batch global."
                ),
                evidence_ids=[private.evidence_id],
                candidate_claim_ids=[],
            )
        )

    dossier = ResearchDossier(
        dossier_id="dos_moscow_ramenki_0001",
        title="Dossier regulatorio y socioeconómico · Distrito de Ramenki",
        summary=(
            "La investigación sintética encontró una señal de continuidad, una "
            "presión adversa de financiación y un vacío fiscal. Ningún resultado "
            "ha sido admitido como claim canónico."
        ),
        sections=sections,
        private_context_used=request.include_private_knowledge,
    )
    evidence_ids = [item.evidence_id for item in evidence]
    candidate_ids = [support.candidate_claim_id, contradiction.candidate_claim_id]
    run = ResearchRun(
        research_run_id="rr_moscow_ramenki_0001",
        context_id="ctx_moscow_real_estate_v01",
        opportunity_id=request.opportunity_id,
        question=request.question,
        state="ADMISSION_QUEUED",
        source_plan=sources,
        budgets=ResearchBudget(),
        actual_usage=ResearchUsage(documents=len(evidence)),
        evidence_ids=evidence_ids,
        candidate_claim_ids=candidate_ids,
        unknown_ids=[unknown.unknown_id],
        dossier_id=dossier.dossier_id,
        admission_batch_id="adm_moscow_ramenki_0001",
        private_knowledge_authorised=request.include_private_knowledge,
        created_at=fixed,
        updated_at=fixed,
    )
    return ResearchResponse(
        run=run,
        evidence=evidence,
        candidate_claims=[support, contradiction],
        unknowns=[unknown],
        dossier=dossier,
        context_update=ResearchContextUpdate(
            selected_run_id=run.research_run_id,
            selected_run_state=run.state,
            provisional_evidence_ids=[
                item.evidence_id for item in evidence if item.domain != "TENANT_PRIVATE"
            ],
            candidate_claim_ids=candidate_ids,
            dossier_id=dossier.dossier_id,
            admission_batch_id=run.admission_batch_id,
            history_event_type="RESEARCH_ADMISSION_QUEUED",
        ),
        explanation=(
            "ResearchRun sintético completado. Evidence Objects y Candidate Claims "
            "quedan en propuesta; la admisión canónica sigue pendiente."
        ),
    )


@router.post("/research-runs", response_model=ResearchResponse)
def create_research_run(request: ResearchRequest) -> ResearchResponse:
    """Execute a bounded fixture with no live network or canonical writes."""
    return build_research_response(request)
