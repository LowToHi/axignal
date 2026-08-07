"""Source profiles — WP2-T05..T08.

Shared, validated profiles attached to a SourceManifest:

- QualityProfile (T05): freshness, completeness, latency, reliability,
  deduplication and provenance-quality dimensions with bounded values;
- RightsProfile (T06): license, attribution, commercial use,
  redistribution, derivative reuse, retention and kill-switch fields;
- PrivacyProfile (T07): personal-data declaration, purpose limitation,
  retention, consent, deletion contract and data minimisation;
- OutageProfile (T08): retry policy, backoff, timeouts, outage
  classification and quarantine escalation.

All profiles are declarative data contracts; they do not by themselves
admit sources, grant rights or authorise anything.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class QualityProfile(BaseModel):
    """Declared quality dimensions of a source (contract 8/11)."""

    schema_version: Literal["axignal.quality-profile.v1"] = "axignal.quality-profile.v1"
    source_id: str
    freshness_max_age_days: int = Field(ge=0, le=3650)
    completeness_score: float = Field(ge=0.0, le=1.0)
    latency_observed_seconds: float = Field(ge=0.0)
    reliability_pct: float = Field(ge=0.0, le=100.0)
    deduplication: Literal["NONE", "CONTENT_HASH", "NATURAL_KEY", "BOTH"] = "CONTENT_HASH"
    provenance_traceable: bool = True
    sample_observed_at: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_evidence_when_scored(self) -> QualityProfile:
        if self.completeness_score > 0.0 and not self.evidence_refs:
            raise ValueError(
                "quality scores require evidence_refs (measured, not assumed)"
            )
        return self


class RightsProfile(BaseModel):
    """Declared rights dimensions of a source (contract 11 / F06)."""

    schema_version: Literal["axignal.rights-profile.v1"] = "axignal.rights-profile.v1"
    source_id: str
    license_id: str
    attribution_required: bool = True
    attribution_text: str | None = None
    commercial_use: bool = False
    redistribution: bool = False
    derivative_reuse: Literal["NOT_ALLOWED", "ATTRIBUTION", "SAME_LICENSE", "OPEN"] = "NOT_ALLOWED"
    retention_days: int | None = Field(default=None, ge=1, le=36500)
    kill_switch_available: bool = True
    rights_reviewed_at: str | None = None

    @model_validator(mode="after")
    def validate_rights_consistency(self) -> RightsProfile:
        if self.attribution_required and not self.attribution_text:
            raise ValueError(
                "attribution_required=true requires attribution_text"
            )
        if self.commercial_use and self.derivative_reuse == "NOT_ALLOWED":
            # Commercial use may still forbid derivatives; this is allowed.
            pass
        return self


class PrivacyProfile(BaseModel):
    """Declared privacy dimensions of a source (contract 11.4 / section 16)."""

    schema_version: Literal["axignal.privacy-profile.v1"] = "axignal.privacy-profile.v1"
    source_id: str
    has_personal_data: bool = False
    data_categories: list[str] = Field(default_factory=list)
    purpose_limitation: str | None = None
    retention_days: int | None = Field(default=None, ge=1, le=36500)
    consent_required: bool = False
    deletion_contract: Literal["NONE", "DSAR", "AUTOMATED_EXPIRY", "DSAR_AND_EXPIRY"] = "NONE"
    data_minimisation: bool = True
    cross_shell_sharing: Literal["FORBIDDEN", "SAME_LEGAL_BASIS", "AUTHORIZED"] = "FORBIDDEN"

    @model_validator(mode="after")
    def validate_personal_data_rules(self) -> PrivacyProfile:
        if self.has_personal_data:
            if not self.purpose_limitation:
                raise ValueError(
                    "personal-data sources require purpose_limitation"
                )
            if self.deletion_contract == "NONE":
                raise ValueError(
                    "personal-data sources require a deletion_contract"
                )
            if self.retention_days is None:
                raise ValueError(
                    "personal-data sources require retention_days"
                )
            if self.data_categories and not self.data_minimisation:
                raise ValueError(
                    "declared data_categories require data_minimisation=true"
                )
        return self


class OutageProfile(BaseModel):
    """Declared outage/retry dimensions of a source (contract 11.2 / 8)."""

    schema_version: Literal["axignal.outage-profile.v1"] = "axignal.outage-profile.v1"
    source_id: str
    retry_max_attempts: int = Field(ge=1, le=10, default=3)
    backoff_base_seconds: float = Field(ge=0.5, le=3600.0, default=2.0)
    backoff_max_seconds: float = Field(ge=1.0, le=86400.0, default=300.0)
    request_timeout_seconds: float = Field(ge=1.0, le=300.0, default=15.0)
    outage_escalation: Literal["NONE", "QUARANTINE", "KILL_SWITCH", "HUMAN_REVIEW"] = "QUARANTINE"
    partial_failure_policy: Literal[
        "FAIL_FAST", "PARTIAL_RESULT", "RETRY_PARTIAL"
    ] = "PARTIAL_RESULT"

    @model_validator(mode="after")
    def validate_backoff(self) -> OutageProfile:
        if self.backoff_max_seconds < self.backoff_base_seconds:
            raise ValueError("backoff_max_seconds must be >= backoff_base_seconds")
        return self
