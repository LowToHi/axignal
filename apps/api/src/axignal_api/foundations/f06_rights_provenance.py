"""F06 — Rights, Sources and Provenance (WP3-T06).

Complete source rights record per contract F06:

Each source requires:
- owner; endpoint/access mechanism; ToS/licence; commercial use;
  redistribution; documents; personal data; retention; attribution;
  rate limits; revocation; review date; legal decision;
  privacy/data-rights decision; kill switch; quarantine.

Plus evidence provenance (chain of custody):
- where/when/by whom observed, content hash, request hash, retrieval
  mode, source version, record version.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SourceRightsRecord(BaseModel):
    """Complete rights record of an evidence source."""

    schema_version: Literal["axignal.f06.rights-record.v1"] = "axignal.f06.rights-record.v1"
    source_id: str = Field(min_length=3, max_length=120)
    owner: str = Field(min_length=2, max_length=200)
    access_endpoint: str | None = None
    access_mechanism: str | None = None
    tos_license_ref: str | None = None
    commercial_use: bool = False
    redistribution: bool = False
    documents_ref: str | None = None
    has_personal_data: bool = False
    retention_days: int | None = Field(default=None, ge=1, le=36500)
    attribution_required: bool = True
    attribution_text: str | None = None
    rate_limit_note: str | None = None
    revocable: bool = True
    last_reviewed_at: date | None = None
    legal_decision: Literal["PENDING", "APPROVED", "REJECTED"] = "PENDING"
    privacy_decision: Literal["PENDING", "APPROVED", "REJECTED"] = "PENDING"
    kill_switch: bool = False
    quarantined: bool = False

    @model_validator(mode="after")
    def validate_rights_record(self) -> SourceRightsRecord:
        if self.attribution_required and not self.attribution_text:
            raise ValueError(
                "attribution_required=true requires attribution_text"
            )
        if self.has_personal_data and self.privacy_decision != "APPROVED":
            raise ValueError(
                "personal-data sources require privacy_decision=APPROVED"
            )
        if self.has_personal_data and self.retention_days is None:
            raise ValueError("personal-data sources require retention_days")
        if self.quarantined and not self.kill_switch:
            raise ValueError("quarantined=true requires kill_switch=true")
        return self


class EvidenceProvenance(BaseModel):
    """Chain of custody of an evidence object."""

    schema_version: Literal["axignal.f06.provenance.v1"] = "axignal.f06.provenance.v1"
    evidence_id: str = Field(min_length=3, max_length=120)
    source_id: str
    source_version: str | None = None
    retrieved_at: datetime
    retrieved_by: str | None = None
    retrieval_mode: Literal[
        "LIVE_API_TECHNICAL_PROBE",
        "FROZEN_FIXTURE",
        "MANUAL_UPLOAD",
        "SYNDICATED",
    ] = "LIVE_API_TECHNICAL_PROBE"
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    request_hash: str = Field(min_length=8, max_length=200)
    original_url: str | None = None
    original_language: str | None = None
    record_version: int = Field(ge=1, default=1)

    @model_validator(mode="after")
    def validate_provenance(self) -> EvidenceProvenance:
        if self.retrieval_mode == "FROZEN_FIXTURE" and not self.original_url:
            raise ValueError(
                "FROZEN_FIXTURE provenance requires original_url "
                "(fixtures are never final evidence)"
            )
        return self
