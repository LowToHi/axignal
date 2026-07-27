from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="AXIGNAL Product API",
    version="0.0.1",
    description="Executable spine for AXIGNAL. Prototype data is synthetic.",
)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["axignal-api"] = "axignal-api"
    contract_version: str = "0.0.1"


class CommandRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    locale: Literal["en", "es", "fr", "de", "pt-BR", "zh-Hans"] = "en"


class CommandPlan(BaseModel):
    intent: Literal["DISCOVER_OPPORTUNITIES"]
    universe: Literal["REAL_ESTATE"]
    geography: str
    horizon: str
    selected_lens: Literal["GLOBE"]
    synthetic: Literal[True] = True


class Opportunity(BaseModel):
    name: str
    expected_return_label: str
    confidence: float = Field(ge=0, le=1)
    evidence_count: int = Field(ge=0)
    contradiction_count: int = Field(ge=0)
    synthetic: Literal[True] = True


class CommandResponse(BaseModel):
    plan: CommandPlan
    opportunities: list[Opportunity]
    explanation: str


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/v1/navigator/commands:interpret", response_model=CommandResponse, tags=["navigator"])
def interpret_command(command: CommandRequest) -> CommandResponse:
    """Return a deterministic prototype plan for the canonical Moscow fixture.

    This endpoint does not write canonical claims and does not provide investment advice.
    """

    return CommandResponse(
        plan=CommandPlan(
            intent="DISCOVER_OPPORTUNITIES",
            universe="REAL_ESTATE",
            geography="Moscow, Russia",
            horizon="12-24 months",
            selected_lens="GLOBE",
        ),
        opportunities=[
            Opportunity(
                name="Ramenki District",
                expected_return_label="18.7% prototype estimate",
                confidence=0.78,
                evidence_count=4,
                contradiction_count=1,
            ),
            Opportunity(
                name="ZIL Zone",
                expected_return_label="16.2% prototype estimate",
                confidence=0.72,
                evidence_count=3,
                contradiction_count=1,
            ),
        ],
        explanation=(
            "Synthetic prototype response. AXIGNAL would navigate to Moscow, expose "
            "supporting, contradicting and unknown claims, and preserve the source trail."
        ),
    )
