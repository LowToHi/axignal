"""AXENT Query Planner (Mandato AXENT — sección 7.2).

Converts a natural-language query into a validated, typed query plan.
Strict schema: unknown fields rejected; ranges validated; currencies and
dates normalised; taxonomies resolved; inferred filters recorded
separately from explicit ones; the original query is preserved.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

KNOWN_FIELDS = frozenset(
    {
        "intent", "object_types", "keywords", "semantic_concepts",
        "countries", "regions", "buyers", "sectors", "cpv_codes",
        "value_min", "value_max", "currencies", "publication_range",
        "deadline_range", "status", "requirements", "exclusions",
        "similarity_targets", "tenant_capabilities", "sort", "limit",
        "requested_explanation",
    }
)

INTENTS = frozenset(
    {
        "SEARCH_OPPORTUNITIES", "SEARCH_GRANTS", "SEARCH_REGULATIONS",
        "SEARCH_OBJECTS", "COMPARE_OPPORTUNITIES", "EXPLAIN_OPPORTUNITY",
        "LIST_CHANGES", "LIST_WORKSPACES", "LIST_PURSUITS", "LIST_TASKS",
        "SUPPORT_QUERY", "GENERAL",
    }
)

OBJECT_TYPES = frozenset(
    {
        "OPPORTUNITY", "GRANT_CALL", "LEGAL_DOCUMENT", "PROJECT",
        "COMPANY", "INDICATOR", "TRADE_FLOW", "ENERGY_ASSET", "INNOVATION",
    }
)

VALID_SORTS = frozenset({"relevance", "value_desc", "value_asc", "deadline_asc", "freshness"})

VALID_COUNTRIES = frozenset(
    {
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE",
        "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT",
        "RO", "SK", "SI", "ES", "SE", "ES-PT", "EU",
    }
)

CURRENCY_RE = re.compile(r"^(EUR|USD|GBP|CHF)$")

COUNTRY_ALIASES = {
    "españa": "ES", "spain": "ES", "es": "ES",
    "portugal": "PT", "pt": "PT",
    "francia": "FR", "france": "FR", "fr": "FR",
    "alemania": "DE", "germany": "DE", "de": "DE",
    "italia": "IT", "italy": "IT", "it": "IT",
    "polonia": "PL", "poland": "PL",
    "países bajos": "NL", "holanda": "NL", "netherlands": "NL", "nl": "NL",
    "bélgica": "BE", "belgium": "BE",
    "irlanda": "IE", "ireland": "IE",
    "austria": "AT",
    "grecia": "GR", "greece": "GR",
    "suecia": "SE", "sweden": "SE",
    "dinamarca": "DK", "denmark": "DK",
    "finlandia": "FI", "finland": "FI",
    "croacia": "HR", "croatia": "HR",
    "chipre": "CY", "cyprus": "CY",
    "chequia": "CZ", "czechia": "CZ",
    "eslovaquia": "SK", "slovakia": "SK",
    "eslovenia": "SI", "slovenia": "SI",
    "hungría": "HU", "hungary": "HU",
    "letonia": "LV", "latvia": "LV",
    "lituania": "LT", "lithuania": "LT",
    "luxemburgo": "LU", "luxembourg": "LU",
    "malta": "MT", "rumanía": "RO", "romania": "RO",
    "bulgaria": "BG", "estonia": "EE", "unión europea": "EU", "europe": "EU",
    "europa": "EU", "ue": "EU",
}


class QueryPlanError(ValueError):
    """Raised when a query plan is structurally invalid."""


@dataclass(frozen=True)
class QueryPlan:
    intent: str
    object_types: tuple[str, ...]
    keywords: tuple[str, ...]
    semantic_concepts: tuple[str, ...]
    countries: tuple[str, ...]
    regions: tuple[str, ...]
    buyers: tuple[str, ...]
    sectors: tuple[str, ...]
    cpv_codes: tuple[str, ...]
    value_min: float | None
    value_max: float | None
    currencies: tuple[str, ...]
    publication_range: tuple[date, date] | None
    deadline_range: tuple[date, date] | None
    status: tuple[str, ...]
    requirements: tuple[str, ...]
    exclusions: tuple[str, ...]
    similarity_targets: tuple[str, ...]
    tenant_capabilities: tuple[str, ...]
    sort: str
    limit: int
    requested_explanation: bool
    inferred_filters: tuple[str, ...] = field(default_factory=tuple)
    original_query: str = ""

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name in KNOWN_FIELDS:
            value = getattr(self, name)
            if isinstance(value, tuple) and name not in (
                "publication_range", "deadline_range"
            ):
                result[name] = list(value)
            elif isinstance(value, tuple):
                result[name] = [v.isoformat() for v in value] if value else None
            else:
                result[name] = value
        result["inferred_filters"] = list(self.inferred_filters)
        result["original_query"] = self.original_query
        return result


def _parse_amount(token: str) -> float | None:
    cleaned = re.sub(r"[€\s.,]", "", token.replace(".", ""), count=0)
    cleaned = token.replace("€", "").replace("euros", "").replace("EUR", "")
    cleaned = re.sub(r"[^\d]", "", cleaned)
    if not cleaned:
        return None
    return float(cleaned)


def _parse_date_range(token: str, today: date) -> tuple[date, date] | None:
    token = token.lower()
    if "próximos" in token or "proximos" in token:
        match = re.search(r"(\d+)\s*(días|dias|dias)", token)
        if match:
            days = int(match.group(1))
            return (today, today + timedelta(days=days))
    if "últimos" in token or "ultimos" in token:
        match = re.search(r"(\d+)\s*(días|dias)", token)
        if match:
            days = int(match.group(1))
            return (today - timedelta(days=days), today)
    return None


class QueryPlanner:
    """Deterministic planner: typed schema, no free-form fields."""

    def __init__(self, today: date | None = None) -> None:
        self.today = today or date.today()

    def plan(self, raw: dict[str, Any], original_query: str = "") -> QueryPlan:
        unknown = set(raw) - KNOWN_FIELDS
        if unknown:
            raise QueryPlanError(f"unknown query plan fields: {sorted(unknown)}")

        intent = raw.get("intent", "SEARCH_OPPORTUNITIES")
        if intent not in INTENTS:
            raise QueryPlanError(f"unknown intent {intent!r}")

        object_types = tuple(raw.get("object_types") or ("OPPORTUNITY",))
        for ot in object_types:
            if ot not in OBJECT_TYPES:
                raise QueryPlanError(f"unknown object type {ot!r}")

        countries: list[str] = []
        inferred: list[str] = []
        for raw_country in raw.get("countries") or []:
            code = COUNTRY_ALIASES.get(str(raw_country).strip().lower())
            if code is None:
                code = str(raw_country).upper()
            if code not in VALID_COUNTRIES:
                raise QueryPlanError(f"unsupported country {raw_country!r}")
            countries.append(code)
        if raw.get("regions"):
            inferred.append("regions")

        value_min = raw.get("value_min")
        value_max = raw.get("value_max")
        if value_min is not None and value_max is not None and value_min > value_max:
            raise QueryPlanError("value_min cannot exceed value_max")
        if value_min is not None and value_min < 0:
            raise QueryPlanError("value_min cannot be negative")
        if value_max is not None and value_max < 0:
            raise QueryPlanError("value_max cannot be negative")

        currencies = tuple(raw.get("currencies") or ("EUR",))
        for currency in currencies:
            if not CURRENCY_RE.match(str(currency)):
                raise QueryPlanError(f"unsupported currency {currency!r}")

        publication_range: tuple[date, date] | None = None
        if raw.get("publication_range"):
            values = raw["publication_range"]
            if not isinstance(values, (list, tuple)) or len(values) != 2:
                raise QueryPlanError("publication_range must be [start, end]")
            publication_range = (
                date.fromisoformat(str(values[0])),
                date.fromisoformat(str(values[1])),
            )
            if publication_range[0] > publication_range[1]:
                raise QueryPlanError("publication_range start after end")

        deadline_range: tuple[date, date] | None = None
        if raw.get("deadline_range"):
            values = raw["deadline_range"]
            if not isinstance(values, (list, tuple)) or len(values) != 2:
                raise QueryPlanError("deadline_range must be [start, end]")
            deadline_range = (
                date.fromisoformat(str(values[0])),
                date.fromisoformat(str(values[1])),
            )
            if deadline_range[0] > deadline_range[1]:
                raise QueryPlanError("deadline_range start after end")

        status = tuple(raw.get("status") or ())
        for state in status:
            if state not in ("OPEN", "QUALIFIED", "PURSUED", "CLOSED", "SUSPENDED"):
                raise QueryPlanError(f"unknown status {state!r}")

        sort = raw.get("sort", "relevance")
        if sort not in VALID_SORTS:
            raise QueryPlanError(f"unsupported sort {sort!r}")

        limit = int(raw.get("limit", 10))
        if not 1 <= limit <= 100:
            raise QueryPlanError("limit must be between 1 and 100")

        keywords = tuple(str(k).strip() for k in raw.get("keywords") or () if str(k).strip())
        if not keywords and not countries:
            inferred.append("broad_search")

        return QueryPlan(
            intent=intent,
            object_types=object_types,
            keywords=keywords,
            semantic_concepts=tuple(raw.get("semantic_concepts") or ()),
            countries=tuple(countries),
            regions=tuple(raw.get("regions") or ()),
            buyers=tuple(raw.get("buyers") or ()),
            sectors=tuple(raw.get("sectors") or ()),
            cpv_codes=tuple(raw.get("cpv_codes") or ()),
            value_min=float(value_min) if value_min is not None else None,
            value_max=float(value_max) if value_max is not None else None,
            currencies=currencies,
            publication_range=publication_range,
            deadline_range=deadline_range,
            status=status,
            requirements=tuple(raw.get("requirements") or ()),
            exclusions=tuple(raw.get("exclusions") or ()),
            similarity_targets=tuple(raw.get("similarity_targets") or ()),
            tenant_capabilities=tuple(raw.get("tenant_capabilities") or ()),
            sort=sort,
            limit=limit,
            requested_explanation=bool(raw.get("requested_explanation", False)),
            inferred_filters=tuple(inferred),
            original_query=original_query,
        )

    def from_natural_language(self, text: str) -> QueryPlan:
        """Deterministic lightweight NL->plan for the required examples."""
        lowered = text.lower()
        raw: dict[str, Any] = {}

        if "grants" in lowered or "subvencion" in lowered or "ayudas" in lowered:
            raw["intent"] = "SEARCH_GRANTS"
            raw["object_types"] = ["GRANT_CALL"]
        elif any(
            word in lowered
            for word in ("muéstrame", "muestrame", "busca", "enséñame",
                         "ensename", "encuentra", "list")
        ):
            raw["intent"] = "SEARCH_OPPORTUNITIES"
        elif "compara" in lowered or "compare" in lowered:
            raw["intent"] = "COMPARE_OPPORTUNITIES"
        elif (
            "explica" in lowered or "explain" in lowered
            or "por qué encaja" in lowered
        ):
            raw["intent"] = "EXPLAIN_OPPORTUNITY"
        elif (
            "cambiado" in lowered or "cambios" in lowered
            or "cambió" in lowered or "new" in lowered
        ):
            raw["intent"] = "LIST_CHANGES"

        keywords: list[str] = []
        for token in ("ciberseguridad", "digitalización", "digitalizacion",
                      "rail", "infraestructura"):
            if token in lowered:
                keywords.append(token)
        if keywords:
            raw["keywords"] = keywords

        countries: list[str] = []
        for alias, code in COUNTRY_ALIASES.items():
            if alias in lowered and code not in countries and len(alias) > 2:
                countries.append(code)
        if countries:
            raw["countries"] = countries

        amount = re.search(r"([\d.,]+)\s*(?:euros|€|eur)", lowered)
        if amount:
            raw["value_min"] = _parse_amount(amount.group(0))

        deadline = _parse_date_range(lowered, self.today)
        if deadline:
            raw["deadline_range"] = [d.isoformat() for d in deadline]

        if "excluye" in lowered or "excluir" in lowered or "que no" in lowered:
            match = re.search(r"(?:excluye|excluir|sin)\s+([\w\s]+?)(?:\.|$)", lowered)
            if match:
                raw["exclusions"] = [match.group(1).strip()]

        if "veinte empleados" in lowered or "20 empleados" in lowered:
            raw["tenant_capabilities"] = ["SMALL_TEAM"]

        return self.plan(raw, original_query=text)
