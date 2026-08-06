from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

REQUIRED_AUTHORITIES = frozenset({"LEGAL", "PRIVACY_DATA_RIGHTS"})


class AuthorityDecisionValue(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class AuthorityStatus(StrEnum):
    MISSING = "MISSING"
    INCOMPLETE = "INCOMPLETE"
    ACTIVE = "ACTIVE"
    EXPIRING = "EXPIRING"
    URGENT = "URGENT"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    INVALID_BINDING = "INVALID_BINDING"


class RenewalPhase(StrEnum):
    NO_CURRENT_APPROVAL = "NO_CURRENT_APPROVAL"
    NOT_DUE = "NOT_DUE"
    RENEWAL_WINDOW_OPEN = "RENEWAL_WINDOW_OPEN"
    URGENT_RENEWAL = "URGENT_RENEWAL"
    EXPIRED = "EXPIRED"


class ChangeClass(StrEnum):
    NO_MATERIAL_CHANGE = "NO_MATERIAL_CHANGE"
    BASELINE_REQUIRED = "BASELINE_REQUIRED"
    MATERIAL_TECHNICAL_CHANGE = "MATERIAL_TECHNICAL_CHANGE"
    MATERIAL_TERMS_CHANGE = "MATERIAL_TERMS_CHANGE"
    AUTHORITY_SURFACE_CHANGE = "AUTHORITY_SURFACE_CHANGE"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"


class TypedAuthorityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authority: str = Field(min_length=1)
    decision: AuthorityDecisionValue
    scope: str = Field(min_length=1)
    manifest_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    timestamp: datetime
    expiry: datetime
    conditions: tuple[str, ...] = Field(min_length=1)
    signature: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_decision(self) -> TypedAuthorityDecision:
        if self.authority not in REQUIRED_AUTHORITIES:
            raise ValueError("Unsupported approval authority")
        if self.timestamp.tzinfo is None or self.expiry.tzinfo is None:
            raise ValueError("Approval timestamps require timezones")
        if self.expiry <= self.timestamp:
            raise ValueError("Approval expiry must be after its timestamp")
        return self


class AuthorityEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    manifest_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    decisions: tuple[TypedAuthorityDecision, ...]

    @model_validator(mode="after")
    def validate_decisions(self) -> AuthorityEnvelope:
        authorities = [item.authority for item in self.decisions]
        if len(authorities) != len(set(authorities)):
            raise ValueError("Duplicate authority decisions are forbidden")
        return self


@dataclass(frozen=True)
class AuthorityEvaluation:
    status: AuthorityStatus
    phase: RenewalPhase
    execution_authorised: bool
    effective_expiry: datetime | None
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DeltaEvaluation:
    change_class: ChangeClass
    changed_relevant_paths: tuple[str, ...]
    changed_technical_paths: tuple[str, ...]
    reasons: tuple[str, ...]


def _normalise_now(now: datetime) -> datetime:
    if now.tzinfo is None:
        raise ValueError("Current time must include a timezone")
    return now.astimezone(UTC)


def evaluate_authority(
    envelope: AuthorityEnvelope | None,
    *,
    expected_head_sha: str,
    expected_manifest_digest: str,
    now: datetime,
    renewal_window_days: int,
    urgent_window_days: int,
) -> AuthorityEvaluation:
    current = _normalise_now(now)
    if envelope is None:
        return AuthorityEvaluation(
            status=AuthorityStatus.MISSING,
            phase=RenewalPhase.NO_CURRENT_APPROVAL,
            execution_authorised=False,
            effective_expiry=None,
            reasons=("No typed authority envelope is available",),
        )

    if (
        envelope.head_sha != expected_head_sha
        or envelope.manifest_digest != expected_manifest_digest
    ):
        return AuthorityEvaluation(
            status=AuthorityStatus.INVALID_BINDING,
            phase=RenewalPhase.NO_CURRENT_APPROVAL,
            execution_authorised=False,
            effective_expiry=None,
            reasons=("Approval does not bind to the current exact head and manifest",),
        )

    decisions = {item.authority: item for item in envelope.decisions}
    missing = REQUIRED_AUTHORITIES.difference(decisions)
    if missing:
        return AuthorityEvaluation(
            status=AuthorityStatus.INCOMPLETE,
            phase=RenewalPhase.NO_CURRENT_APPROVAL,
            execution_authorised=False,
            effective_expiry=None,
            reasons=(f"Missing authority decisions: {', '.join(sorted(missing))}",),
        )

    for authority, decision in decisions.items():
        if (
            decision.head_sha != envelope.head_sha
            or decision.manifest_digest != envelope.manifest_digest
        ):
            return AuthorityEvaluation(
                status=AuthorityStatus.INVALID_BINDING,
                phase=RenewalPhase.NO_CURRENT_APPROVAL,
                execution_authorised=False,
                effective_expiry=None,
                reasons=(f"{authority} decision binding differs from the envelope",),
            )
        if decision.decision is AuthorityDecisionValue.REJECT:
            return AuthorityEvaluation(
                status=AuthorityStatus.REJECTED,
                phase=RenewalPhase.NO_CURRENT_APPROVAL,
                execution_authorised=False,
                effective_expiry=min(item.expiry for item in decisions.values()),
                reasons=(f"{authority} rejected the requested scope",),
            )

    effective_expiry = min(item.expiry for item in decisions.values()).astimezone(UTC)
    if current >= effective_expiry:
        return AuthorityEvaluation(
            status=AuthorityStatus.EXPIRED,
            phase=RenewalPhase.EXPIRED,
            execution_authorised=False,
            effective_expiry=effective_expiry,
            reasons=("Typed authority has expired",),
        )

    remaining = effective_expiry - current
    if remaining <= timedelta(days=urgent_window_days):
        return AuthorityEvaluation(
            status=AuthorityStatus.URGENT,
            phase=RenewalPhase.URGENT_RENEWAL,
            execution_authorised=True,
            effective_expiry=effective_expiry,
            reasons=("Typed authority is valid but inside the urgent renewal window",),
        )
    if remaining <= timedelta(days=renewal_window_days):
        return AuthorityEvaluation(
            status=AuthorityStatus.EXPIRING,
            phase=RenewalPhase.RENEWAL_WINDOW_OPEN,
            execution_authorised=True,
            effective_expiry=effective_expiry,
            reasons=("Typed authority is valid and the renewal window is open",),
        )
    return AuthorityEvaluation(
        status=AuthorityStatus.ACTIVE,
        phase=RenewalPhase.NOT_DUE,
        execution_authorised=True,
        effective_expiry=effective_expiry,
        reasons=("Typed authority is current",),
    )


def classify_delta(
    *,
    current_relevant_files: dict[str, str],
    previous_relevant_files: dict[str, str] | None,
    current_terms: dict[str, dict[str, Any]],
    previous_terms: dict[str, dict[str, Any]] | None,
    technical_paths_changed: tuple[str, ...] = (),
) -> DeltaEvaluation:
    unavailable = sorted(
        document_id
        for document_id, observation in current_terms.items()
        if observation.get("status") != "PASS"
    )
    if unavailable:
        return DeltaEvaluation(
            change_class=ChangeClass.EVIDENCE_UNAVAILABLE,
            changed_relevant_paths=(),
            changed_technical_paths=tuple(sorted(technical_paths_changed)),
            reasons=(f"Official evidence unavailable or invalid: {', '.join(unavailable)}",),
        )

    if previous_relevant_files is None or previous_terms is None:
        return DeltaEvaluation(
            change_class=ChangeClass.BASELINE_REQUIRED,
            changed_relevant_paths=(),
            changed_technical_paths=tuple(sorted(technical_paths_changed)),
            reasons=("No prior renewal package is available for delta comparison",),
        )

    terms_changed = sorted(
        document_id
        for document_id, observation in current_terms.items()
        if previous_terms.get(document_id, {}).get("content_sha256")
        != observation.get("content_sha256")
    )
    if terms_changed:
        return DeltaEvaluation(
            change_class=ChangeClass.MATERIAL_TERMS_CHANGE,
            changed_relevant_paths=(),
            changed_technical_paths=tuple(sorted(technical_paths_changed)),
            reasons=(f"Official terms content changed: {', '.join(terms_changed)}",),
        )

    changed_relevant = tuple(
        sorted(
            path
            for path in set(current_relevant_files) | set(previous_relevant_files)
            if current_relevant_files.get(path) != previous_relevant_files.get(path)
        )
    )
    if changed_relevant:
        return DeltaEvaluation(
            change_class=ChangeClass.AUTHORITY_SURFACE_CHANGE,
            changed_relevant_paths=changed_relevant,
            changed_technical_paths=tuple(sorted(technical_paths_changed)),
            reasons=("One or more authority-bound files changed",),
        )

    if technical_paths_changed:
        return DeltaEvaluation(
            change_class=ChangeClass.MATERIAL_TECHNICAL_CHANGE,
            changed_relevant_paths=(),
            changed_technical_paths=tuple(sorted(technical_paths_changed)),
            reasons=("Relevant runtime implementation changed outside the approval manifest",),
        )

    return DeltaEvaluation(
        change_class=ChangeClass.NO_MATERIAL_CHANGE,
        changed_relevant_paths=(),
        changed_technical_paths=(),
        reasons=("No material terms, authority-surface or runtime change detected",),
    )
