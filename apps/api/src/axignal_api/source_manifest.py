"""SourceManifest — WP2-T02 base contract.

Declares the canonical, versioned contract of an evidence source exactly as
governed by AX-GE2E-FINISH-004 v2.1.0 section 11:

- source states: DISCOVERED, LEGAL_REVIEW, PRIVACY_REVIEW, TECHNICAL_PROBE,
  EVIDENCE_READY, PRODUCT_ADMITTED, COMMERCIAL, SUSPENDED, REVOKED, REJECTED;
- a source blocker propagates only to that source, its derived data, its
  dependent claims, its specific E2E and its commercial coverage claims —
  never to other sources, libraries, Core, shells, billing or general UX;
- a REJECTED source is not consulted in commercial runtime, produces no
  commercial Evidence Objects and does not contribute to coverage;
- personal-data sources require purpose limitation, retention, consent and
  deletion contracts.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from axignal_api.library_manifest import (
    ALL_LIBRARIES,
    CANONICAL_SHELLS,
    LibraryType,
)

LOGGER = logging.getLogger(__name__)

# Canonical source-state vocabulary (contract 11.1).
class SourceState(StrEnum):
    DISCOVERED = "DISCOVERED"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    PRIVACY_REVIEW = "PRIVACY_REVIEW"
    TECHNICAL_PROBE = "TECHNICAL_PROBE"
    EVIDENCE_READY = "EVIDENCE_READY"
    PRODUCT_ADMITTED = "PRODUCT_ADMITTED"
    COMMERCIAL = "COMMERCIAL"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"


# Maps database admission_state values to the canonical vocabulary.
DB_STATE_MAP = {
    "DISCOVERED": SourceState.DISCOVERED,
    "LEGAL_REVIEW": SourceState.LEGAL_REVIEW,
    "PRIVACY_REVIEW": SourceState.PRIVACY_REVIEW,
    "TECHNICAL_PROBE": SourceState.TECHNICAL_PROBE,
    "EVIDENCE_READY": SourceState.EVIDENCE_READY,
    "ADMITTED": SourceState.PRODUCT_ADMITTED,
    "COMMERCIAL": SourceState.COMMERCIAL,
    "SUSPENDED": SourceState.SUSPENDED,
    "QUARANTINED": SourceState.SUSPENDED,
    "REVOKED": SourceState.REVOKED,
    "REJECTED": SourceState.REJECTED,
}


class SourceAccessMode(StrEnum):
    INSTITUTIONAL_API = "INSTITUTIONAL_API"
    INSTITUTIONAL_WEB = "INSTITUTIONAL_WEB"
    PUBLIC_API = "PUBLIC_API"
    PUBLIC_DOWNLOAD = "PUBLIC_DOWNLOAD"
    LICENSED_FEED = "LICENSED_FEED"
    MANUAL_UPLOAD = "MANUAL_UPLOAD"


class SourceManifest(BaseModel):
    """Canonical, versioned contract of a single evidence source."""

    schema_version: Literal["axignal.source-manifest.v1"] = "axignal.source-manifest.v1"
    source_id: str = Field(min_length=3, max_length=120, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str = Field(min_length=3, max_length=200)
    library_id: str = Field(pattern=r"^[FO]\d{2}$")
    source_type: str = Field(min_length=2, max_length=80)
    access_mode: SourceAccessMode
    base_url: str | None = None
    state: SourceState = SourceState.DISCOVERED
    rights_status: str | None = None
    license_id: str | None = None
    attribution_text: str | None = None
    commercial_use: bool = False
    redistribution: bool = False
    kill_switch: bool = False
    has_personal_data: bool = False
    coverage: dict[str, Any] = Field(default_factory=dict)
    quality_profile: dict[str, Any] = Field(default_factory=dict)
    privacy_profile: dict[str, Any] = Field(default_factory=dict)
    outage_profile: dict[str, Any] = Field(default_factory=dict)
    manifest_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    product_shell_ids: list[str] = Field(default_factory=list)
    is_shell: Literal[False] = False
    exact_head: str | None = None

    @model_validator(mode="after")
    def validate_source_rules(self) -> SourceManifest:
        if self.library_id not in ALL_LIBRARIES:
            raise ValueError(
                f"library_id must be one of {ALL_LIBRARIES}; got {self.library_id!r}"
            )
        for shell_id in self.product_shell_ids:
            if shell_id not in CANONICAL_SHELLS:
                raise ValueError(
                    f"unknown shell {shell_id!r}; only {CANONICAL_SHELLS} are canonical"
                )
        if self.kill_switch and self.state in (
            SourceState.COMMERCIAL,
            SourceState.PRODUCT_ADMITTED,
        ):
            raise ValueError(
                "kill_switch=true is incompatible with "
                "COMMERCIAL/PRODUCT_ADMITTED state; use SUSPENDED/REVOKED instead"
            )
        if self.has_personal_data and not self.privacy_profile:
            raise ValueError(
                "personal-data sources require a privacy_profile "
                "(purpose, retention, consent, deletion)"
            )
        if self.state == SourceState.REJECTED and self.commercial_use:
            raise ValueError("a REJECTED source cannot be commercial_use=true")
        return self


def state_from_db(admission_state: str | None) -> SourceState:
    """Map a database admission_state to the canonical vocabulary."""
    if not admission_state:
        return SourceState.DISCOVERED
    state = DB_STATE_MAP.get(admission_state.upper())
    if state is None:
        LOGGER.warning("unknown db admission_state %r; falling back to DISCOVERED", admission_state)
        return SourceState.DISCOVERED
    return state


def source_manifest_from_db_row(row: dict[str, Any]) -> SourceManifest:
    """Build a SourceManifest from an axignal_global.sources row."""
    shell_ids = [CANONICAL_SHELLS[0]] if row.get("commercial_use") else []
    return SourceManifest(
        source_id=row["source_id"],
        name=row["name"],
        library_id=_library_for_source(row["source_id"]),
        source_type=row.get("source_type") or "UNKNOWN",
        access_mode=_access_mode(row.get("access_mode")),
        base_url=row.get("base_url"),
        state=state_from_db(row.get("admission_state")),
        rights_status=row.get("rights_status"),
        license_id=row.get("license_id"),
        attribution_text=row.get("attribution_text"),
        commercial_use=bool(row.get("commercial_use")),
        redistribution=bool(row.get("redistribution")),
        kill_switch=bool(row.get("kill_switch")),
        manifest_version="1.0.0",
        product_shell_ids=shell_ids,
    )


def _library_for_source(source_id: str) -> str:
    """Resolve the canonical library for a known source id."""
    mapping = {
        "src_ted_search_api_v3": "O01",
        "world-bank-wdi": "O01",
        "world-bank-rer41": "O01",
        "bank-of-russia-statistics": "O06",
    }
    return mapping.get(source_id, "O01")


def _access_mode(value: str | None) -> SourceAccessMode:
    normalized = (value or "").upper()
    for mode in SourceAccessMode:
        if mode.value == normalized:
            return mode
    return SourceAccessMode.PUBLIC_API


def load_source_manifests_from_db(repository: Any) -> list[SourceManifest]:
    """Load all source manifests from the sources repository."""
    rows = repository.list_sources() if hasattr(repository, "list_sources") else []
    return [source_manifest_from_db_row(row) for row in rows]


def library_type_for(library_id: str) -> LibraryType:
    """Return the canonical library type for a library id."""
    if library_id in ("F01", "F02", "F03", "F04", "F05", "F06", "F07"):
        return LibraryType.FOUNDATIONAL
    return LibraryType.OPPORTUNITY
