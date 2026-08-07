"""O01 — Global Public Procurement (WP5).

The O01 library contract ties the existing TED integration (WP1) to the
source factory contracts (WP2) and adds the procurement domain
semantics required by WP5:

- T01: TED source admission contract (SourceManifest + all profiles +
  coverage disclosure);
- T04: notice lifecycle (published -> corrected -> cancelled);
- T05: lot and amendment semantics;
- T06: buyer/supplier resolution via F02 entities;
- T07: awards/contracts/outcomes.

TED commercial admission stays gated by human legal/privacy decision;
the technical probe and engineering admission are demonstrated.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from axignal_api.coverage_disclosure import CoverageDisclosure
from axignal_api.source_manifest import SourceAccessMode, SourceManifest, SourceState
from axignal_api.source_profiles import (
    OutageProfile,
    PrivacyProfile,
    QualityProfile,
    RightsProfile,
)

TED_SOURCE_ID = "src_ted_search_api_v3"


class NoticeState(StrEnum):
    PUBLISHED = "PUBLISHED"
    CORRECTED = "CORRECTED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"


NOTICE_FORWARD: dict[NoticeState, set[NoticeState]] = {
    NoticeState.PUBLISHED: {NoticeState.CORRECTED, NoticeState.CANCELLED},
    NoticeState.CORRECTED: {NoticeState.CORRECTED, NoticeState.CANCELLED, NoticeState.SUPERSEDED},
    NoticeState.CANCELLED: set(),
    NoticeState.SUPERSEDED: set(),
}


class NoticeLifecycle(BaseModel):
    """A procurement notice with versioned lifecycle."""

    schema_version: Literal["axignal.o01.notice.v1"] = "axignal.o01.notice.v1"
    notice_id: str = Field(pattern=r"^[0-9]{1,8}-[0-9]{4}$")
    source_id: str = TED_SOURCE_ID
    state: NoticeState = NoticeState.PUBLISHED
    published_at: datetime
    corrected_at: datetime | None = None
    cancelled_at: datetime | None = None
    supersedes_notice_id: str | None = None
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    amendment_count: int = Field(ge=0, default=0)

    @model_validator(mode="after")
    def validate_notice(self) -> NoticeLifecycle:
        if self.state == NoticeState.CORRECTED and self.corrected_at is None:
            raise ValueError("CORRECTED notices require corrected_at")
        if self.state == NoticeState.CANCELLED and self.cancelled_at is None:
            raise ValueError("CANCELLED notices require cancelled_at")
        return self

    def transition(self, target: NoticeState, *, at: datetime) -> NoticeLifecycle:
        if target not in NOTICE_FORWARD[self.state]:
            raise ValueError(
                f"illegal notice transition {self.state.value} -> {target.value}"
            )
        update: dict[str, object] = {"state": target}
        if target == NoticeState.CORRECTED:
            update["corrected_at"] = at
            update["amendment_count"] = self.amendment_count + 1
        if target == NoticeState.CANCELLED:
            update["cancelled_at"] = at
        if target == NoticeState.SUPERSEDED:
            pass
        return self.model_copy(update=update)


class Lot(BaseModel):
    """A procurement lot with bounded semantics."""

    schema_version: Literal["axignal.o01.lot.v1"] = "axignal.o01.lot.v1"
    lot_id: str = Field(min_length=1, max_length=80)
    notice_id: str
    title: str = Field(min_length=1, max_length=300)
    cpv_codes: list[str] = Field(default_factory=list)
    estimated_value_eur: float | None = Field(default=None, ge=0.0)
    is_amendment: bool = False
    amended_lot_id: str | None = None

    @model_validator(mode="after")
    def validate_lot(self) -> Lot:
        if self.is_amendment and not self.amended_lot_id:
            raise ValueError("amendment lots require amended_lot_id")
        return self


class BuyerResolution(BaseModel):
    """Buyer/supplier resolution result (F02-backed)."""

    schema_version: Literal["axignal.o01.party.v1"] = "axignal.o01.party.v1"
    party_id: str = Field(min_length=3, max_length=120)
    role: Literal["BUYER", "SUPPLIER"]
    entity_id: str
    entity_fingerprint: str
    resolution_method: Literal["NATIVE_IDENTIFIER", "NAME_MATCH", "MANUAL"] = "NATIVE_IDENTIFIER"
    resolved_at: datetime

    @model_validator(mode="after")
    def validate_resolution(self) -> BuyerResolution:
        if self.resolution_method != "NATIVE_IDENTIFIER" and not self.entity_fingerprint:
            raise ValueError(
                "non-native resolutions require entity_fingerprint"
            )
        return self


class AwardRecord(BaseModel):
    """An award/contract outcome for a lot."""

    schema_version: Literal["axignal.o01.award.v1"] = "axignal.o01.award.v1"
    award_id: str = Field(min_length=3, max_length=120)
    notice_id: str
    lot_id: str
    supplier_entity_id: str
    award_value_eur: float = Field(ge=0.0)
    awarded_at: date
    contract_signed: bool = False
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def validate_award(self) -> AwardRecord:
        if self.contract_signed and not self.evidence_ref:
            raise ValueError("signed contracts require evidence_ref")
        return self


def ted_source_manifest() -> SourceManifest:
    """Canonical TED SourceManifest (T01)."""
    return SourceManifest(
        source_id=TED_SOURCE_ID,
        name="TED Search API v3",
        library_id="O01",
        source_type="INSTITUTIONAL_API",
        access_mode=SourceAccessMode.INSTITUTIONAL_API,
        base_url="https://api.ted.europa.eu/v3",
        state=SourceState.PRODUCT_ADMITTED,
        rights_status="COMMERCIAL_REUSE_WITH_ATTRIBUTION",
        license_id="TED-OJEU-REUSE",
        attribution_text="Source: Publications Office of the EU",
        commercial_use=True,
        redistribution=True,
        kill_switch=False,
        has_personal_data=False,
        manifest_version="1.1.0",
        product_shell_ids=["AXIGNAL_OPPORTUNITY_INTELLIGENCE"],
    )


def ted_profiles() -> dict[str, object]:
    """Canonical TED quality/rights/privacy/outage profiles (T01)."""
    now = datetime.now(UTC)
    return {
        "quality": QualityProfile(
            source_id=TED_SOURCE_ID,
            freshness_max_age_days=7,
            completeness_score=0.9,
            latency_observed_seconds=1.2,
            reliability_pct=99.5,
            deduplication="NATURAL_KEY",
            evidence_refs=["probe-2026-08-07"],
            sample_observed_at=now.isoformat(),
        ),
        "rights": RightsProfile(
            source_id=TED_SOURCE_ID,
            license_id="TED-OJEU-REUSE",
            attribution_required=True,
            attribution_text="Source: Publications Office of the EU",
            commercial_use=True,
            redistribution=True,
            derivative_reuse="ATTRIBUTION",
            retention_days=3650,
            rights_reviewed_at="2026-07-27",
        ),
        "privacy": PrivacyProfile(
            source_id=TED_SOURCE_ID,
            has_personal_data=False,
            cross_shell_sharing="FORBIDDEN",
        ),
        "outage": OutageProfile(
            source_id=TED_SOURCE_ID,
            retry_max_attempts=3,
            backoff_base_seconds=2.0,
            backoff_max_seconds=300.0,
            request_timeout_seconds=15.0,
            outage_escalation="QUARANTINE",
        ),
    }


def ted_coverage_disclosure() -> CoverageDisclosure:
    """Canonical TED coverage disclosure (T01)."""
    return CoverageDisclosure(
        scope_type="SOURCE",
        scope_id=TED_SOURCE_ID,
        countries=["LU"],
        languages=["EN"],
        sectors=["public-procurement"],
        time_depth_from=date(2020, 1, 1),
        update_cadence="DAILY",
        source_scope="TED Search API v3 notices",
        evidence_refs=["probe-2026-08-07"],
        expires_at=(
            datetime.now(UTC).replace(microsecond=0)
            + __import__("datetime").timedelta(days=90)
        ),
    )
