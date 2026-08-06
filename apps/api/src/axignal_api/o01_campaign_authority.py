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
        "head_sha",
        "reviewed_at",
        "expires_at",
        "signature",
        "conditions",
    }
)
_SIGNATURE_RE = re.compile(
    r"^github-identity-v1:([A-Za-z0-9](?:[A-Za-z0-9-]{0,38})):"
    r"(LEGAL|PRIVACY_DATA_RIGHTS):sha256:([0-9a-f]{64})$"
)


class CampaignDecisionValue(StrEnum):
    APPROVE = "APPROVE"
    APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"
    REJECT = "REJECT"


class CampaignAuthorityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authority: str = Field(min_length=1)
    decision: CampaignDecisionValue
    scope: str = Field(min_length=24)
    manifest_reference: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    reviewed_at: datetime
    expires_at: datetime
    signature: str = Field(min_length=32)
    conditions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_decision(self) -> CampaignAuthorityDecision:
        if self.authority not in REQUIRED_AUTHORITIES:
            raise ValueError("Unsupported campaign authority")
        if self.reviewed_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("Decision timestamps require timezones")
        if self.expires_at <= self.reviewed_at:
            raise ValueError("Decision expiry must be after review time")
        if any(not item.strip() for item in self.conditions):
            raise ValueError("Decision conditions must be non-empty")
        return self


@dataclass(frozen=True)
class VerifiedDecision:
    decision: CampaignAuthorityDecision
    comment_id: int
    comment_url: str | None
    comment_author: str
    comment_created_at: str | None
    comment_updated_at: str | None


@dataclass(frozen=True)
class CampaignAuthorityEvaluation:
    status: str
    execution_authorised: bool
    effective_expiry: datetime | None
    legal: str
    privacy_data_rights: str
    head_match: bool
    manifest_match: bool
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


def canonical_unsigned_payload(decision: CampaignAuthorityDecision) -> bytes:
    payload = decision.model_dump(mode="json")
    payload.pop("signature")
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def unsigned_payload_digest(decision: CampaignAuthorityDecision) -> str:
    return hashlib.sha256(canonical_unsigned_payload(decision)).hexdigest()


def build_github_identity_signature(
    decision: CampaignAuthorityDecision,
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
    decision: CampaignAuthorityDecision,
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
    signature_login, signature_authority, signature_digest = match.groups()
    return (
        signature_login.casefold() == lowered
        and signature_authority == decision.authority
        and signature_digest == unsigned_payload_digest(decision)
    )


def evaluate_campaign_authority(
    decisions: dict[str, VerifiedDecision],
    *,
    expected_head_sha: str,
    expected_manifest_reference: str,
    evidence_expires_at: datetime,
    decision_max_expires_at: datetime,
    now: datetime,
) -> CampaignAuthorityEvaluation:
    current = parse_utc(now)
    evidence_expiry = parse_utc(evidence_expires_at)
    decision_max = parse_utc(decision_max_expires_at)
    missing = REQUIRED_AUTHORITIES.difference(decisions)
    if missing:
        return CampaignAuthorityEvaluation(
            status="MISSING" if len(missing) == 2 else "INCOMPLETE",
            execution_authorised=False,
            effective_expiry=None,
            legal="MISSING" if "LEGAL" in missing else "PRESENT_UNEVALUATED",
            privacy_data_rights=(
                "MISSING"
                if "PRIVACY_DATA_RIGHTS" in missing
                else "PRESENT_UNEVALUATED"
            ),
            head_match=False,
            manifest_match=False,
            signatures_human=False,
            expiry_within_evidence=False,
            reasons=(f"Missing human authorities: {', '.join(sorted(missing))}",),
        )

    values = {authority: item.decision for authority, item in decisions.items()}
    head_match = all(item.head_sha == expected_head_sha for item in values.values())
    manifest_match = all(
        item.manifest_reference == expected_manifest_reference
        for item in values.values()
    )
    signatures_human = True  # Only verified decisions enter this function.
    expiry_within_evidence = all(
        parse_utc(item.expires_at) <= decision_max
        and parse_utc(item.expires_at) < evidence_expiry
        for item in values.values()
    )

    reasons: list[str] = []
    if not head_match:
        reasons.append("One or more decisions target a different exact campaign head")
    if not manifest_match:
        reasons.append("One or more decisions target a different manifest")
    if not expiry_within_evidence:
        reasons.append("One or more decisions outlive the permitted evidence boundary")
    if any(parse_utc(item.reviewed_at) > current for item in values.values()):
        reasons.append("One or more review timestamps are in the future")
    effective_expiry = min(parse_utc(item.expires_at) for item in values.values())
    if current >= effective_expiry:
        reasons.append("One or more human decisions have expired")

    rejected = [
        authority
        for authority, item in values.items()
        if item.decision is CampaignDecisionValue.REJECT
    ]
    if rejected:
        reasons.append(f"Campaign rejected by: {', '.join(sorted(rejected))}")

    legal_status = _authority_status(values["LEGAL"], current)
    privacy_status = _authority_status(values["PRIVACY_DATA_RIGHTS"], current)
    authorised = not reasons and all(
        item.decision
        in {
            CampaignDecisionValue.APPROVE,
            CampaignDecisionValue.APPROVE_WITH_CONDITIONS,
        }
        for item in values.values()
    )
    return CampaignAuthorityEvaluation(
        status="APPROVED_CURRENT" if authorised else "BLOCKED",
        execution_authorised=authorised,
        effective_expiry=effective_expiry,
        legal=legal_status,
        privacy_data_rights=privacy_status,
        head_match=head_match,
        manifest_match=manifest_match,
        signatures_human=signatures_human,
        expiry_within_evidence=expiry_within_evidence,
        reasons=tuple(reasons) if reasons else ("Both human authorities are current",),
    )


def _authority_status(
    decision: CampaignAuthorityDecision,
    now: datetime,
) -> str:
    if decision.decision is CampaignDecisionValue.REJECT:
        return "REJECTED_CURRENT" if parse_utc(decision.expires_at) > now else "EXPIRED"
    return "APPROVED_CURRENT" if parse_utc(decision.expires_at) > now else "EXPIRED"


def result_payload(
    evaluation: CampaignAuthorityEvaluation,
    *,
    manifest_reference: str,
    target_head_sha: str,
    evidence_expires_at: datetime,
    decision_sources: dict[str, VerifiedDecision],
) -> dict[str, Any]:
    authorised = evaluation.execution_authorised
    return {
        "status": "PASS" if authorised else "BLOCKED",
        "output": (
            "O01_CAMPAIGN_AUTHORISED"
            if authorised
            else "O01_CAMPAIGN_AUTHORITY_BLOCKED"
        ),
        "legal": evaluation.legal,
        "privacy_data_rights": evaluation.privacy_data_rights,
        "head_match": evaluation.head_match,
        "manifest_match": evaluation.manifest_match,
        "signatures_human": evaluation.signatures_human,
        "expiry_within_evidence": evaluation.expiry_within_evidence,
        "execution_authorised": authorised,
        "effective_expiry": (
            evaluation.effective_expiry.isoformat().replace("+00:00", "Z")
            if evaluation.effective_expiry
            else None
        ),
        "evidence_expires_at": parse_utc(evidence_expires_at)
        .isoformat()
        .replace("+00:00", "Z"),
        "target_head_sha": target_head_sha,
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
            }
            for authority, source in sorted(decision_sources.items())
        },
        "authority_boundary": {
            "ted_product_admitted": False,
            "public_claims_authorised": False,
            "public_redistribution_authorised": False,
            "contact_marketing_authorised": False,
            "model_training_authorised": False,
            "bid_submission_authorised": False,
            "public_launch": "NO_GO",
        },
        "reasons": list(evaluation.reasons),
    }
