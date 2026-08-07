"""WP18 — Copy manifest, landing gates and SEO (T15-T35).

Implements the public-surface copy and discovery contract without
publishing anything:

- T16: corporate landing with clear product choice;
- T17/T18: per-shell landings (Shell 1 live-ready; Shell 2 draft/
  staging, non-indexed);
- T19: independent pricing page per shell;
- T20: O01-O09 pages inside Shell 1, never as independent shells;
- T21: versioned CopyManifest per route, shell, audience and locale;
- T22: commercial claims linked to evidence, coverage and expiry;
- T23: superlatives and unprovable guarantees prohibited;
- T24: visible disclosures (coverage, freshness, rights, limits);
- T25: navigation that never mixes procurement with public employment;
- T26: technical SEO (canonical, hreflang, sitemap, robots per state);
- T27: Public Employment indexing blocked while unauthorized;
- T28: analytics per shell/product/route/locale without unnecessary PII;
- T29: independent funnels;
- T30: consent management and preferences;
- T31: experiment governance without dark patterns or price
  discrimination;
- T32: attribution and campaign parameters with governed retention;
- T33: copy validated in six languages without authority divergence;
- T34: loading/empty/partial/stale/restricted/error/recovery states;
- T35: distribution, support entrypoints and copy/config rollback.

Platform/ops tasks (T01-T14: deploy, topology, secrets, SLO, backup,
DR, incident, security scanning) are BLOCKED by the inherited scope
prohibition on infra/, .github/ and production deployment.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import ClassVar, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

PRODUCT_LANGUAGES = ("en", "es", "fr", "de", "pt", "it")
SHELL_1 = "AXIGNAL_OPPORTUNITY_INTELLIGENCE"
SHELL_2 = "AXIGNAL_PUBLIC_EMPLOYMENT"


class CopyEntry(BaseModel):
    """A single copy entry with version, audience and language."""

    schema_version: Literal["axignal.copy.entry.v1"] = "axignal.copy.entry.v1"
    copy_id: str = Field(min_length=3, max_length=120)
    route: str = Field(min_length=1, max_length=300)
    shell_id: str
    audience: str = Field(min_length=2, max_length=120)
    locale: str = Field(pattern=r"^[a-z]{2}$")
    text: str = Field(min_length=1, max_length=5000)
    version: int = Field(ge=1, default=1)
    status: Literal["DRAFT", "REVIEW", "APPROVED", "RETIRED"] = "DRAFT"
    approved_by: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_copy(self) -> CopyEntry:
        if self.locale not in PRODUCT_LANGUAGES:
            raise ValueError(
                f"locale {self.locale!r} not in product languages {PRODUCT_LANGUAGES}"
            )
        if self.shell_id not in (SHELL_1, SHELL_2):
            raise ValueError(f"unknown shell {self.shell_id!r}")
        if self.status == "APPROVED" and not self.approved_by:
            raise ValueError("APPROVED copy requires approved_by")
        return self


class CommercialClaim(BaseModel):
    """A commercial claim linked to evidence, coverage and expiry (T22)."""

    schema_version: Literal["axignal.copy.claim.v1"] = "axignal.copy.claim.v1"
    claim_id: str = Field(min_length=3, max_length=120)
    copy_id: str
    claim_text: str = Field(min_length=5, max_length=1000)
    evidence_refs: list[str] = Field(default_factory=list)
    coverage_ref: str | None = None
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_claim(self) -> CommercialClaim:
        if not self.evidence_refs and not self.coverage_ref:
            raise ValueError(
                "commercial claims require evidence_refs or coverage_ref "
                "(no unprovable claims)"
            )
        return self

    def is_expired(self, now: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        return (now or datetime.now(UTC)) > self.expires_at


class SuperlativeGuard(BaseModel):
    """Guards against superlatives and unprovable guarantees (T23)."""

    schema_version: Literal["axignal.copy.guard.v1"] = "axignal.copy.guard.v1"
    copy_id: str
    text: str

    FORBIDDEN_PATTERNS: ClassVar[tuple[str, ...]] = (
        "best",
        "the best",
        "guaranteed",
        "guarantee",
        "always",
        "never fails",
        "100%",
        "perfect",
        "leading",
        "number one",
        "top-rated",
        "most reliable",
    )

    @model_validator(mode="after")
    def validate_no_superlatives(self) -> SuperlativeGuard:
        lowered = self.text.casefold()
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in lowered:
                raise ValueError(
                    f"forbidden superlative/guarantee {pattern!r} in copy {self.copy_id}"
                )
        return self


class Disclosure(BaseModel):
    """A visible disclosure (coverage, freshness, rights, limits) (T24)."""

    schema_version: Literal["axignal.copy.disclosure.v1"] = "axignal.copy.disclosure.v1"
    disclosure_id: str = Field(min_length=3, max_length=120)
    route: str
    kind: Literal[
        "COVERAGE",
        "FRESHNESS",
        "RIGHTS",
        "LIMITS",
        "LEGAL",
        "PRIVACY",
        "PRICING_HYPOTHESIS",
    ]
    text: str = Field(min_length=10, max_length=2000)
    visible: bool = True
    required: bool = True

    @model_validator(mode="after")
    def validate_disclosure(self) -> Disclosure:
        if self.required and not self.visible:
            raise ValueError("required disclosures must be visible")
        return self


class SeoState(StrEnum):
    NO_INDEX = "NO_INDEX"
    INDEXABLE = "INDEXABLE"
    DRAFT = "DRAFT"


class SeoRoute(BaseModel):
    """Technical SEO metadata per route and state (T26/T27)."""

    schema_version: Literal["axignal.copy.seo.v1"] = "axignal.copy.seo.v1"
    route: str = Field(min_length=1, max_length=300)
    shell_id: str
    state: SeoState = SeoState.DRAFT
    canonical: str | None = None
    hreflang: dict[str, str] = Field(default_factory=dict)
    robots: str = "noindex, nofollow"
    in_sitemap: bool = False

    @model_validator(mode="after")
    def validate_seo(self) -> SeoRoute:
        if self.shell_id == SHELL_2:
            if self.state == SeoState.INDEXABLE:
                raise ValueError(
                    "Public Employment routes cannot be indexable "
                    "(blocked until authorized)"
                )
            if self.state == SeoState.DRAFT:
                self.robots = "noindex, nofollow"
                self.in_sitemap = False
        return self


class AnalyticsEvent(BaseModel):
    """Analytics event without unnecessary PII (T28)."""

    schema_version: Literal["axignal.copy.analytics.v1"] = "axignal.copy.analytics.v1"
    event_id: str = Field(min_length=3, max_length=120)
    shell_id: str
    product_id: str | None = None
    route: str
    locale: str = Field(pattern=r"^[a-z]{2}$")
    event_type: str = Field(min_length=2, max_length=80)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    consent_granted: bool = False

    @model_validator(mode="after")
    def validate_analytics(self) -> AnalyticsEvent:
        if self.event_type != "PAGE_VIEW" and not self.consent_granted:
            raise ValueError("non-page-view events require consent")
        return self


class ConsentPreference(BaseModel):
    """Consent management and preferences (T30)."""

    schema_version: Literal["axignal.copy.consent.v1"] = "axignal.copy.consent.v1"
    preference_id: str = Field(min_length=3, max_length=120)
    tenant_id: UUID
    analytics: bool = False
    marketing: bool = False
    functional: bool = True
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExperimentVariant(BaseModel):
    """Experiment governance without dark patterns (T31)."""

    schema_version: Literal["axignal.copy.experiment.v1"] = "axignal.copy.experiment.v1"
    experiment_id: str = Field(min_length=3, max_length=120)
    variant_id: str = Field(min_length=3, max_length=120)
    shell_id: str
    description: str = Field(min_length=5, max_length=1000)
    price_impact: bool = False
    opt_out_available: bool = True

    @model_validator(mode="after")
    def validate_experiment(self) -> ExperimentVariant:
        if self.price_impact:
            raise ValueError(
                "experiments cannot change prices per user "
                "(no price discrimination)"
            )
        if not self.opt_out_available:
            raise ValueError("experiments require opt-out (no dark patterns)")
        return self


class UiState(BaseModel):
    """Validated UI states (T34)."""

    schema_version: Literal["axignal.copy.ui-state.v1"] = "axignal.copy.ui-state.v1"
    state_id: str = Field(min_length=3, max_length=120)
    route: str
    state: Literal[
        "LOADING",
        "EMPTY",
        "PARTIAL",
        "STALE",
        "RESTRICTED",
        "ERROR",
        "RECOVERY",
    ]
    copy_ref: str | None = None

    @model_validator(mode="after")
    def validate_state(self) -> UiState:
        if self.state == "ERROR" and not self.copy_ref:
            raise ValueError("ERROR states require a copy_ref")
        return self


class CopyManifest:
    """Versioned copy manifest with distribution and rollback (T21/T35)."""

    def __init__(self) -> None:
        self._entries: dict[str, CopyEntry] = {}
        self._history: dict[str, list[CopyEntry]] = {}
        self._claims: dict[str, CommercialClaim] = {}

    def add(self, entry: CopyEntry) -> None:
        if entry.copy_id in self._entries:
            self._history.setdefault(entry.copy_id, []).append(self._entries[entry.copy_id])
        self._entries[entry.copy_id] = entry

    def get(self, copy_id: str) -> CopyEntry | None:
        return self._entries.get(copy_id)

    def get_effective(self, route: str, locale: str, audience: str = "public") -> CopyEntry | None:
        for entry in self._entries.values():
            if (
                entry.route == route
                and entry.locale == locale
                and entry.audience == audience
                and entry.status == "APPROVED"
            ):
                return entry
        return None

    def rollback(self, copy_id: str) -> CopyEntry | None:
        """Roll back to the previous version (T35)."""
        history = self._history.get(copy_id, [])
        if not history:
            return None
        previous = history[-1]
        self._history[copy_id] = history[:-1]
        self._entries[copy_id] = previous
        return previous

    def add_claim(self, claim: CommercialClaim) -> None:
        self._claims[claim.claim_id] = claim

    def claims_for(self, copy_id: str) -> tuple[CommercialClaim, ...]:
        return tuple(
            claim for claim in self._claims.values() if claim.copy_id == copy_id
        )

    def __len__(self) -> int:
        return len(self._entries)


class LandingRoutes:
    """Landing and navigation structure without audience mixing (T16-T20/T25)."""

    def __init__(self) -> None:
        self._routes: dict[str, dict[str, object]] = {}

    def register(
        self,
        route: str,
        shell_id: str,
        *,
        kind: str,
        indexable: bool,
        state: str = "LIVE",
    ) -> None:
        if kind == "SHELL2_LANDING" and indexable:
            raise ValueError(
                "Public Employment landing must not be indexable"
            )
        self._routes[route] = {
            "route": route,
            "shell_id": shell_id,
            "kind": kind,
            "indexable": indexable,
            "state": state,
        }

    def routes_for(self, shell_id: str) -> tuple[dict[str, object], ...]:
        return tuple(
            r for r in self._routes.values() if r["shell_id"] == shell_id
        )

    def __len__(self) -> int:
        return len(self._routes)


def build_landing_routes() -> LandingRoutes:
    """The canonical landing structure (nothing is published)."""
    routes = LandingRoutes()
    # Corporate landing with clear product choice (T16).
    routes.register("/", "AXIGNAL_PLATFORM", kind="CORPORATE_LANDING", indexable=True)
    # Shell 1 landing (T17).
    routes.register("/opportunity-intelligence", SHELL_1, kind="SHELL1_LANDING", indexable=True)
    # Shell 2 landing: draft, non-indexed (T18).
    routes.register(
        "/empleo-publico",
        SHELL_2,
        kind="SHELL2_LANDING",
        indexable=False,
        state="DRAFT_HIDDEN",
    )
    # Pricing per shell (T19).
    routes.register("/opportunity-intelligence/precios", SHELL_1, kind="PRICING", indexable=True)
    routes.register(
        "/empleo-publico/precios",
        SHELL_2,
        kind="PRICING",
        indexable=False,
        state="DRAFT_HIDDEN",
    )
    # O01-O09 pages inside Shell 1 (T20).
    for library_id in ("O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09"):
        routes.register(
            f"/opportunity-intelligence/{library_id.lower()}",
            SHELL_1,
            kind="LIBRARY_PAGE",
            indexable=True,
        )
    return routes
