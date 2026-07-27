from copy import deepcopy
from datetime import UTC, datetime
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

Locale = Literal["en", "es", "fr", "de", "pt-BR", "zh-Hans"]
Lens = Literal["AUTO", "GLOBE", "GRAPH", "DUAL"]
ClaimKind = Literal[
    "HECHO",
    "INFERENCIA",
    "PREDICCIÓN",
    "CONTRADICCIÓN",
    "DESCONOCIDO",
]

app = FastAPI(
    title="AXIGNAL Product API",
    version="0.1.0",
    description=(
        "Executable AXIGNAL spine. The prototype endpoints expose synthetic fixtures only, "
        "write no canonical claims and provide no personalised investment advice."
    ),
)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["axignal-api"] = "axignal-api"
    contract_version: str = "0.1.0"


class CommandRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    locale: Locale = "en"


class CommandPlan(BaseModel):
    intent: Literal["DISCOVER_OPPORTUNITIES"]
    universe: Literal["REAL_ESTATE"]
    geography: str
    horizon: str
    selected_lens: Literal["GLOBE"]
    synthetic: Literal[True] = True


class LegacyOpportunity(BaseModel):
    name: str
    expected_return_label: str
    confidence: float = Field(ge=0, le=1)
    evidence_count: int = Field(ge=0)
    contradiction_count: int = Field(ge=0)
    synthetic: Literal[True] = True


class CommandResponse(BaseModel):
    plan: CommandPlan
    opportunities: list[LegacyOpportunity]
    explanation: str


class Evidence(BaseModel):
    evidence_id: str
    title: str
    source: str
    as_of: str
    relationship: Literal["SUPPORT", "CONTRADICT", "UNKNOWN"]
    synthetic: Literal[True] = True


class Claim(BaseModel):
    claim_id: str
    kind: ClaimKind
    text: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_ids: list[str]
    synthetic: Literal[True] = True


class Opportunity(BaseModel):
    opportunity_id: str
    name: str
    expected_return_label: str
    confidence: float = Field(ge=0, le=1)
    level: Literal["ALTA", "MEDIA", "MEDIA-BAJA"]
    claim_ids: list[str]
    evidence_count: int = Field(ge=0)
    contradiction_count: int = Field(ge=0)
    synthetic: Literal[True] = True


class ContextTime(BaseModel):
    mode: Literal["CURRENT", "AS_OF", "RANGE", "COMPARE"] = "CURRENT"
    horizon_label: Literal["12M", "24M", "36M"] = "24M"


class Selection(BaseModel):
    opportunity_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    graph_node_ids: list[str] = Field(default_factory=list)


class Coverage(BaseModel):
    status: Literal[
        "AVAILABLE",
        "PARTIAL",
        "UNAVAILABLE",
        "UNLICENSED",
        "UNKNOWN",
    ]
    summary: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class HistoryEvent(BaseModel):
    event_id: str
    event_type: str
    occurred_at: datetime
    command_plan_id: str | None = None


class InvestigationContext(BaseModel):
    context_id: str = Field(pattern=r"^ctx_[A-Za-z0-9_-]{8,}$")
    version: int = Field(ge=1)
    locale: Locale
    original_query: str | None = None
    query_language: str | None = None
    lens: Lens
    lens_reason: str | None = None
    time: ContextTime
    geographies: list[str]
    entities: list[str]
    universes: list[str]
    filters: dict[str, str | int | float | bool | None]
    selection: Selection
    coverage: Coverage
    rail_mode: Literal[
        "CONTEXT",
        "OPPORTUNITY",
        "CLAIM",
        "EVIDENCE",
        "EXPLANATION",
        "COVERAGE",
    ]
    history: list[HistoryEvent]
    entitlement_snapshot_id: str | None = None
    saved_trail_id: str | None = None
    updated_at: datetime
    synthetic: Literal[True] = True


class Focus(BaseModel):
    opportunity_id: str | None = None
    claim_id: str | None = None
    evidence_id: str | None = None


class PrototypeInvestigationPayload(BaseModel):
    context: InvestigationContext
    opportunities: list[Opportunity]
    claims: list[Claim]
    evidence: list[Evidence]
    explanation: str
    focus: Focus


class PrototypeCommandRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    locale: Locale = "es"
    payload: PrototypeInvestigationPayload | None = None


EVIDENCE = [
    Evidence(
        evidence_id="ev_cbr_rent",
        title="Rental market research",
        source="CBR Research",
        as_of="2024-04-15",
        relationship="SUPPORT",
    ),
    Evidence(
        evidence_id="ev_transport_model",
        title="Transport accessibility model",
        source="AXIGNAL synthetic model fixture",
        as_of="2024-03-03",
        relationship="SUPPORT",
    ),
    Evidence(
        evidence_id="ev_supply_model",
        title="Premium housing supply model",
        source="AXIGNAL synthetic model fixture",
        as_of="2024-02-28",
        relationship="SUPPORT",
    ),
    Evidence(
        evidence_id="ev_bank_rates",
        title="Mortgage rate environment",
        source="Banco de Rusia",
        as_of="2024-05-10",
        relationship="CONTRADICT",
    ),
    Evidence(
        evidence_id="ev_coverage_gap",
        title="Tax-policy coverage gap",
        source="Coverage registry",
        as_of="2024-05-10",
        relationship="UNKNOWN",
    ),
    Evidence(
        evidence_id="ev_zil_plan",
        title="ZIL regeneration programme",
        source="Moscow urban plan fixture",
        as_of="2024-04-02",
        relationship="SUPPORT",
    ),
]

CLAIMS = [
    Claim(
        claim_id="clm_ramenki_rent",
        kind="HECHO",
        text="Los precios de alquiler en Ramenki han crecido un 14% interanual.",
        confidence=0.86,
        evidence_ids=["ev_cbr_rent"],
    ),
    Claim(
        claim_id="clm_ramenki_metro",
        kind="INFERENCIA",
        text="La nueva línea de metro aumentaría la demanda en un 15–20%.",
        confidence=0.68,
        evidence_ids=["ev_transport_model"],
    ),
    Claim(
        claim_id="clm_ramenki_supply",
        kind="PREDICCIÓN",
        text="Se espera escasez de oferta de vivienda premium en 2025.",
        confidence=0.61,
        evidence_ids=["ev_supply_model"],
    ),
    Claim(
        claim_id="clm_ramenki_rates",
        kind="CONTRADICCIÓN",
        text="Altas tasas hipotecarias podrían reducir la demanda en 2025.",
        confidence=0.79,
        evidence_ids=["ev_bank_rates"],
    ),
    Claim(
        claim_id="clm_ramenki_tax",
        kind="DESCONOCIDO",
        text="No hay evidencia suficiente sobre futuros cambios fiscales.",
        evidence_ids=["ev_coverage_gap"],
    ),
    Claim(
        claim_id="clm_zil_regeneration",
        kind="HECHO",
        text="La regeneración urbana de ZIL mantiene inversión pública comprometida.",
        confidence=0.82,
        evidence_ids=["ev_zil_plan"],
    ),
    Claim(
        claim_id="clm_zil_transport",
        kind="INFERENCIA",
        text="La conectividad adicional puede acelerar la absorción residencial.",
        confidence=0.66,
        evidence_ids=["ev_transport_model"],
    ),
    Claim(
        claim_id="clm_zil_rates",
        kind="CONTRADICCIÓN",
        text="El coste de financiación puede retrasar nuevas promociones.",
        confidence=0.73,
        evidence_ids=["ev_bank_rates"],
    ),
    Claim(
        claim_id="clm_khamovniki_supply",
        kind="HECHO",
        text="La oferta disponible en Khamovniki continúa limitada.",
        confidence=0.8,
        evidence_ids=["ev_supply_model"],
    ),
    Claim(
        claim_id="clm_basmanniy_demand",
        kind="INFERENCIA",
        text="La demanda de alquiler profesional permanece resiliente.",
        confidence=0.57,
        evidence_ids=["ev_cbr_rent"],
    ),
]

OPPORTUNITIES = [
    Opportunity(
        opportunity_id="opp_moscow_ramenki",
        name="Distrito de Ramenki",
        expected_return_label="18.7%",
        confidence=0.78,
        level="ALTA",
        claim_ids=[
            "clm_ramenki_rent",
            "clm_ramenki_metro",
            "clm_ramenki_supply",
            "clm_ramenki_rates",
            "clm_ramenki_tax",
        ],
        evidence_count=4,
        contradiction_count=1,
    ),
    Opportunity(
        opportunity_id="opp_moscow_zil",
        name="Zona ZIL",
        expected_return_label="16.2%",
        confidence=0.72,
        level="ALTA",
        claim_ids=["clm_zil_regeneration", "clm_zil_transport", "clm_zil_rates"],
        evidence_count=3,
        contradiction_count=1,
    ),
    Opportunity(
        opportunity_id="opp_moscow_khamovniki",
        name="Khamovniki",
        expected_return_label="12.1%",
        confidence=0.64,
        level="MEDIA",
        claim_ids=["clm_khamovniki_supply", "clm_ramenki_rates"],
        evidence_count=2,
        contradiction_count=1,
    ),
    Opportunity(
        opportunity_id="opp_moscow_basmanniy",
        name="Basmanniy",
        expected_return_label="9.8%",
        confidence=0.48,
        level="MEDIA-BAJA",
        claim_ids=["clm_basmanniy_demand", "clm_ramenki_tax"],
        evidence_count=1,
        contradiction_count=0,
    ),
]


def utc_now() -> datetime:
    return datetime.now(UTC)


def initial_payload(locale: Locale = "es") -> PrototypeInvestigationPayload:
    fixed = datetime(2026, 7, 27, tzinfo=UTC)
    return PrototypeInvestigationPayload(
        context=InvestigationContext(
            context_id="ctx_moscow_real_estate_v01",
            version=1,
            locale=locale,
            original_query="Quiero ver si hay oportunidades inmobiliarias en Moscú",
            query_language="es",
            lens="GLOBE",
            lens_reason="La intención principal es geográfica.",
            time=ContextTime(),
            geographies=["geo_moscow_ru"],
            entities=["entity_moscow"],
            universes=["REAL_ESTATE"],
            filters={
                "geography": "Moscú, Rusia",
                "universe": "Real Estate",
                "horizon": "12–24 meses",
            },
            selection=Selection(
                opportunity_ids=["opp_moscow_ramenki"],
                graph_node_ids=["entity_moscow", "opp_moscow_ramenki"],
            ),
            coverage=Coverage(
                status="PARTIAL",
                summary="Fixture sintética con cobertura deliberadamente incompleta.",
                source_ids=[item.evidence_id for item in EVIDENCE],
            ),
            rail_mode="OPPORTUNITY",
            history=[
                HistoryEvent(
                    event_id="evt_0001",
                    event_type="INVESTIGATION_CREATED",
                    occurred_at=fixed,
                    command_plan_id="plan_0001",
                )
            ],
            updated_at=fixed,
        ),
        opportunities=deepcopy(OPPORTUNITIES),
        claims=deepcopy(CLAIMS),
        evidence=deepcopy(EVIDENCE),
        explanation="Contexto sintético inicial cargado.",
        focus=Focus(opportunity_id="opp_moscow_ramenki"),
    )


def selected_opportunity(payload: PrototypeInvestigationPayload) -> Opportunity:
    if not payload.opportunities:
        raise HTTPException(status_code=400, detail="Synthetic opportunity fixture is empty")
    selected_ids = payload.context.selection.opportunity_ids
    selected_id = selected_ids[0] if selected_ids else "opp_moscow_ramenki"
    return next(
        (
            item
            for item in payload.opportunities
            if item.opportunity_id == selected_id
        ),
        payload.opportunities[0],
    )


def execute_prototype_command(
    request: PrototypeCommandRequest,
) -> PrototypeInvestigationPayload:
    payload = (
        deepcopy(request.payload)
        if request.payload is not None
        else initial_payload(request.locale)
    )
    if (
        payload.context.context_id != "ctx_moscow_real_estate_v01"
        or not payload.context.synthetic
    ):
        raise HTTPException(
            status_code=400,
            detail="Unsupported or non-synthetic InvestigationContext",
        )

    context = payload.context
    lower = request.message.strip().casefold()
    plan_id = f"plan_{context.version + 1:04d}"
    event_type = "NAVIGATOR_COMMAND_EXECUTED"
    explanation = (
        "He conservado el contexto y añadido la orden al Investigation Trail."
    )

    if "grafo" in lower or "graph" in lower:
        context.lens = "GRAPH"
        context.lens_reason = "El usuario ha solicitado una lectura relacional."
        event_type = "LENS_CHANGED"
        explanation = (
            "He cambiado a Graph y conservado geografía, oportunidad, claims, "
            "evidencia y horizonte."
        )
    elif "dual" in lower or "compara" in lower:
        context.lens = "DUAL"
        context.lens_reason = (
            "El usuario ha solicitado comparar geografía y relaciones."
        )
        event_type = "LENS_CHANGED"
        explanation = "He activado Dual sin perder la selección ni el historial."
    elif any(token in lower for token in ("globo", "globe", "mapa")):
        context.lens = "GLOBE"
        context.lens_reason = "El usuario ha solicitado una lectura geográfica."
        event_type = "LENS_CHANGED"
        explanation = "He cambiado a Globe y mantenido el contexto de investigación."

    requested = next(
        (
            item
            for item in payload.opportunities
            if item.name.casefold() in lower
        ),
        None,
    )
    if requested is not None:
        context.selection = Selection(
            opportunity_ids=[requested.opportunity_id],
            graph_node_ids=["entity_moscow", requested.opportunity_id],
        )
        context.rail_mode = "OPPORTUNITY"
        payload.focus = Focus(opportunity_id=requested.opportunity_id)
        event_type = "OPPORTUNITY_SELECTED"
        explanation = (
            f"He seleccionado {requested.name} y sincronizado todas las superficies."
        )

    if "contradic" in lower:
        selected = selected_opportunity(payload)
        contradiction = next(
            (
                claim
                for claim in payload.claims
                if claim.claim_id in selected.claim_ids
                and claim.kind == "CONTRADICCIÓN"
            ),
            None,
        )
        if contradiction is not None:
            evidence_id = (
                contradiction.evidence_ids[0]
                if contradiction.evidence_ids
                else None
            )
            context.selection.claim_ids = [contradiction.claim_id]
            context.selection.evidence_ids = [evidence_id] if evidence_id else []
            context.rail_mode = "CLAIM"
            payload.focus = Focus(
                opportunity_id=selected.opportunity_id,
                claim_id=contradiction.claim_id,
                evidence_id=evidence_id,
            )
            event_type = "CONTRADICTION_FOCUSED"
            explanation = (
                f"He aislado la contradicción material de {selected.name} "
                "y su evidencia asociada."
            )
        else:
            context.rail_mode = "COVERAGE"
            explanation = (
                "No existe una contradicción admitida en la fixture seleccionada."
            )

    if "guardar" in lower or "save trail" in lower:
        context.saved_trail_id = (
            context.saved_trail_id or "trail_moscow_real_estate_v01"
        )
        event_type = "TRAIL_SAVED"
        explanation = (
            "He guardado el Investigation Trail sintético con el contexto actual."
        )

    if "36" in lower:
        context.time.horizon_label = "36M"
        context.filters["horizon"] = "36 meses"
        event_type = "TIME_HORIZON_CHANGED"
        explanation = (
            "He ampliado el horizonte a 36 meses y conservado el resto del contexto."
        )

    context.locale = request.locale
    context.version += 1
    context.updated_at = utc_now()
    context.history.append(
        HistoryEvent(
            event_id=f"evt_{context.version:04d}",
            event_type=event_type,
            occurred_at=context.updated_at,
            command_plan_id=plan_id,
        )
    )
    payload.explanation = explanation
    return payload


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health() -> HealthResponse:
    return HealthResponse()


@app.post(
    "/v1/navigator/commands:interpret",
    response_model=CommandResponse,
    tags=["navigator"],
)
def interpret_command(command: CommandRequest) -> CommandResponse:
    """Keep the legacy bounded command-plan endpoint available."""
    return CommandResponse(
        plan=CommandPlan(
            intent="DISCOVER_OPPORTUNITIES",
            universe="REAL_ESTATE",
            geography="Moscow, Russia",
            horizon="12-24 months",
            selected_lens="GLOBE",
        ),
        opportunities=[
            LegacyOpportunity(
                name=item.name,
                expected_return_label=(
                    f"{item.expected_return_label} prototype estimate"
                ),
                confidence=item.confidence,
                evidence_count=item.evidence_count,
                contradiction_count=item.contradiction_count,
            )
            for item in OPPORTUNITIES[:2]
        ],
        explanation=(
            "Synthetic bounded command plan. No canonical claim write "
            "or personalised advice."
        ),
    )


@app.get(
    "/v1/prototype/investigations/{context_id}",
    response_model=PrototypeInvestigationPayload,
    tags=["prototype"],
)
def get_prototype_investigation(
    context_id: str,
    locale: Locale = "es",
) -> PrototypeInvestigationPayload:
    if context_id != "ctx_moscow_real_estate_v01":
        raise HTTPException(
            status_code=404,
            detail="Synthetic InvestigationContext not found",
        )
    return initial_payload(locale)


@app.post(
    "/v1/prototype/navigator/commands:run",
    response_model=PrototypeInvestigationPayload,
    tags=["prototype"],
)
def run_prototype_command(
    command: PrototypeCommandRequest,
) -> PrototypeInvestigationPayload:
    """Evolve the bounded synthetic context without canonical writes."""
    return execute_prototype_command(command)
