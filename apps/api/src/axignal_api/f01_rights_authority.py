from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

REQUIRED_AUTHORITIES = frozenset({"LEGAL", "PRIVACY_DATA_RIGHTS"})
REQUIRED_DECISION_FIELDS = frozenset(
    {
        "authority",
        "decision",
        "scope",
        "manifest_reference",
        "technical_head_sha",
        "reviewed_at",
        "expires_at",
        "signature",
        "conditions",
        "assertions",
    }
)
LEGAL_REQUIRED_ASSERTIONS = {
    "attribution_required": True,
    "derived_classification_permitted": True,
    "iso_publication_redistribution_permitted": False,
    "iso_standard_text_ingestion_permitted": False,
    "no_distortion_required": True,
    "private_access_permitted": True,
    "public_claims_permitted": False,
    "public_redistribution_permitted": False,
    "source_version_disclosure_required": True,
    "temporary_evidence_retention_permitted": True,
    "third_party_components_separately_authorised": False,
}
PRIVACY_REQUIRED_ASSERTIONS = {
    "contact_values_ingested": False,
    "personal_data_expected": False,
    "private_reference_data_processing_permitted": True,
    "profiling_or_marketing_use": False,
    "public_claims_permitted": False,
    "public_redistribution_permitted": False,
    "temporary_evidence_retention_permitted": True,
}
REQUIRED_ASSERTIONS = {
    "LEGAL": LEGAL_REQUIRED_ASSERTIONS,
    "PRIVACY_DATA_RIGHTS": PRIVACY_REQUIRED_ASSERTIONS,
}
_SIGNATURE_RE = re.compile(
    r"^github-identity-v1:([A-Za-z0-9](?:[A-Za-z0-9-]{0,38})):"
    r"(LEGAL|PRIVACY_DATA_RIGHTS):sha256:([0-9a-f]{64})$"
)


class RightsDecisionValue(StrEnum):
    APPROVE = "APPROVE"
    APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"
    REJECT = "REJECT"


AUTHORISING_DECISIONS = frozenset(
    {
        RightsDecisionValue.APPROVE,
        RightsDecisionValue.APPROVE_WITH_CONDITIONS,
    }
)


class F01RightsAuthorityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authority: str = Field(min_length=1)
    decision: RightsDecisionValue
    scope: str = Field(min_length=24)
    manifest_reference: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    technical_head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    reviewed_at: datetime
    expires_at: datetime
    signature: str = Field(min_length=32)
    conditions: tuple[str, ...] = Field(min_length=1)
    assertions: dict[str, bool]

    @model_validator(mode="after")
    def validate_decision(self) -> F01RightsAuthorityDecision:
        if self.authority not in REQUIRED_AUTHORITIES:
            raise ValueError("Unsupported F01 authority")
        if self.reviewed_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("Decision timestamps require timezones")
        if self.expires_at <= self.reviewed_at:
            raise ValueError("Decision expiry must be after review time")
        if any(not item.strip() for item in self.conditions):
            raise ValueError("Decision conditions must be non-empty")
        required = REQUIRED_ASSERTIONS[self.authority]
        if set(self.assertions) != set(required):
            raise ValueError("Authority assertion keys do not match contract")
        if self.decision in AUTHORISING_DECISIONS and self.assertions != required:
            raise ValueError("Authorising assertions do not match safe contract")
        return self


@dataclass(frozen=True)
class VerifiedDecision:
    decision: F01RightsAuthorityDecision
    comment_id: int
    comment_url: str | None
    comment_author: str
    comment_created_at: str | None
    comment_updated_at: str | None


@dataclass(frozen=True)
class F01RightsAuthorityEvaluation:
    status: str
    campaign_authorised: bool
    effective_expiry: datetime | None
    legal: str
    privacy_data_rights: str
    technical_head_match: bool
    manifest_match: bool
    assertions_match: bool
    signatures_human: bool
    expiry_within_evidence: bool
    reasons: tuple[str, ...]


def parse_utc(value: str | datetime) -> datetime:
    parsed = (
        value
        if isinstance(value, datetime)
        else datetime.fromisoformat(value.replace("Z", "+00:00"))
    )
    if parsed.tzinfo is None:
        raise ValueError("Time boundary requires a timezone")
    return parsed.astimezone(UTC)


def canonical_unsigned_payload(decision: F01RightsAuthorityDecision) -> bytes:
    payload = decision.model_dump(mode="json")
    payload.pop("signature")
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def unsigned_payload_digest(decision: F01RightsAuthorityDecision) -> str:
    return hashlib.sha256(canonical_unsigned_payload(decision)).hexdigest()


def build_github_identity_signature(
    decision: F01RightsAuthorityDecision,
    *,
    github_login: str,
) -> str:
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", github_login):
        raise ValueError("Invalid GitHub login for identity signature")
    return (
        f"github-identity-v1:{github_login}:{decision.authority}:"
        f"sha256:{unsigned_payload_digest(decision)}"
    )


def verify_human_signature(
    decision: F01RightsAuthorityDecision,
    *,
    comment_author: str,
    comment_user_type: str,
) -> bool:
    if comment_user_type != "User":
        return False
    lowered = comment_author.casefold()
    if lowered.endswith("[bot]") or lowered in {"github-actions", "dependabot"}:
        return False
    match = _SIGNATURE_RE.fullmatch(decision.signature)
    if match is None:
        return False
    login, authority, digest = match.groups()
    return (
        login.casefold() == lowered
        and authority == decision.authority
        and digest == unsigned_payload_digest(decision)
    )


def _authority_status(
    decision: F01RightsAuthorityDecision,
    now: datetime,
) -> str:
    if parse_utc(decision.expires_at) <= now:
        return "EXPIRED"
    if decision.decision is RightsDecisionValue.REJECT:
        return "REJECTED_CURRENT"
    return "APPROVED_CURRENT"


def evaluate_f01_rights_authority(
    decisions: dict[str, VerifiedDecision],
    *,
    expected_technical_head_sha: str,
    expected_manifest_reference: str,
    evidence_expires_at: datetime,
    decision_max_expires_at: datetime,
    now: datetime,
) -> F01RightsAuthorityEvaluation:
    current = parse_utc(now)
    evidence_expiry = parse_utc(evidence_expires_at)
    decision_max = parse_utc(decision_max_expires_at)
    missing = REQUIRED_AUTHORITIES.difference(decisions)
    if missing:
        return F01RightsAuthorityEvaluation(
            status="MISSING" if len(missing) == 2 else "INCOMPLETE",
            campaign_authorised=False,
            effective_expiry=None,
            legal="MISSING" if "LEGAL" in missing else "PRESENT_UNEVALUATED",
            privacy_data_rights=(
                "MISSING"
                if "PRIVACY_DATA_RIGHTS" in missing
                else "PRESENT_UNEVALUATED"
            ),
            technical_head_match=False,
            manifest_match=False,
            assertions_match=False,
            signatures_human=False,
            expiry_within_evidence=False,
            reasons=(f"Missing human authorities: {', '.join(sorted(missing))}",),
        )

    values = {authority: item.decision for authority, item in decisions.items()}
    technical_head_match = all(
        item.technical_head_sha == expected_technical_head_sha
        for item in values.values()
    )
    manifest_match = all(
        item.manifest_reference == expected_manifest_reference
        for item in values.values()
    )
    assertions_match = all(
        item.assertions == REQUIRED_ASSERTIONS[authority]
        for authority, item in values.items()
        if item.decision in AUTHORISING_DECISIONS
    )
    expiry_within_evidence = all(
        parse_utc(item.expires_at) <= decision_max
        and parse_utc(item.expires_at) < evidence_expiry
        for item in values.values()
    )

    reasons: list[str] = []
    if not technical_head_match:
        reasons.append("One or more decisions target a different technical head")
    if not manifest_match:
        reasons.append("One or more decisions target a different manifest")
    if not assertions_match:
        reasons.append("One or more authorising assertion maps differ")
    if not expiry_within_evidence:
        reasons.append("One or more decisions outlive the evidence boundary")
    if any(parse_utc(item.reviewed_at) > current for item in values.values()):
        reasons.append("One or more review timestamps are in the future")
    effective_expiry = min(parse_utc(item.expires_at) for item in values.values())
    if current >= effective_expiry:
        reasons.append("One or more human decisions have expired")
    rejected = [
        authority
        for authority, item in values.items()
        if item.decision is RightsDecisionValue.REJECT
    ]
    if rejected:
        reasons.append(f"F01 rights rejected by: {', '.join(sorted(rejected))}")

    authorised = not reasons and all(
        item.decision in AUTHORISING_DECISIONS for item in values.values()
    )
    return F01RightsAuthorityEvaluation(
        status="APPROVED_CURRENT" if authorised else "BLOCKED",
        campaign_authorised=authorised,
        effective_expiry=effective_expiry,
        legal=_authority_status(values["LEGAL"], current),
        privacy_data_rights=_authority_status(
            values["PRIVACY_DATA_RIGHTS"],
            current,
        ),
        technical_head_match=technical_head_match,
        manifest_match=manifest_match,
        assertions_match=assertions_match,
        signatures_human=True,
        expiry_within_evidence=expiry_within_evidence,
        reasons=tuple(reasons) if reasons else ("Both human authorities are current",),
    )


def result_payload(
    evaluation: F01RightsAuthorityEvaluation,
    *,
    manifest_reference: str,
    technical_head_sha: str,
    evidence_expires_at: datetime,
    decision_sources: dict[str, VerifiedDecision],
) -> dict[str, Any]:
    authorised = evaluation.campaign_authorised
    return {
        "status": "PASS" if authorised else "BLOCKED",
        "output": (
            "F01_PRIVATE_CAMPAIGN_AUTHORISED"
            if authorised
            else "F01_RIGHTS_AUTHORITY_BLOCKED"
        ),
        "legal": evaluation.legal,
        "privacy_data_rights": evaluation.privacy_data_rights,
        "technical_head_match": evaluation.technical_head_match,
        "manifest_match": evaluation.manifest_match,
        "assertions_match": evaluation.assertions_match,
        "signatures_human": evaluation.signatures_human,
        "expiry_within_evidence": evaluation.expiry_within_evidence,
        "campaign_authorised": authorised,
        "effective_expiry": (
            evaluation.effective_expiry.isoformat().replace("+00:00", "Z")
            if evaluation.effective_expiry
            else None
        ),
        "evidence_expires_at": parse_utc(evidence_expires_at)
        .isoformat()
        .replace("+00:00", "Z"),
        "technical_head_sha": technical_head_sha,
        "manifest_reference": manifest_reference,
        "decision_sources": {
            authority: {
                "comment_id": source.comment_id,
                "comment_url": source.comment_url,
                "comment_author": source.comment_author,
                "comment_created_at": source.comment_created_at,
                "comment_updated_at": source.comment_updated_at,
                "decision": source.decision.decision.value,
                "expires_at": source.decision.expires_at.astimezone(UTC)
                .isoformat()
                .replace("+00:00", "Z"),
                "conditions": list(source.decision.conditions),
                "assertions": source.decision.assertions,
            }
            for authority, source in sorted(decision_sources.items())
        },
        "authority_boundary": {
            "source_state": "CANDIDATE",
            "product_admitted": False,
            "active_source": False,
            "public_claims_authorised": False,
            "public_redistribution_authorised": False,
            "iso_standard_text_ingestion_authorised": False,
            "iso_publication_redistribution_authorised": False,
            "model_training_authorised": False,
            "profiling_or_marketing_authorised": False,
            "f01_state": "BLOCKED",
            "claim_decision": "DENIED",
            "gate7": "IN_PROGRESS",
            "public_launch": "NO_GO",
        },
        "reasons": list(evaluation.reasons),
    }
