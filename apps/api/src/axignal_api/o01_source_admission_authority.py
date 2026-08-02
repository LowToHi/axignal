from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

REQUIRED_AUTHORITIES = frozenset(
    {
        "PRODUCT",
        "SECURITY",
        "PRIVACY_DATA_RIGHTS",
        "LEGAL",
        "SOURCE_QUALITY",
        "UX_ACCESSIBILITY",
        "HUMAN_COVERAGE_AUTHORITY",
    }
)
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
_AUTHORITY_PATTERN = "|".join(sorted(REQUIRED_AUTHORITIES, key=len, reverse=True))
_SIGNATURE_RE = re.compile(
    rf"^github-identity-v1:([A-Za-z0-9](?:[A-Za-z0-9-]{{0,38}})):"
    rf"({_AUTHORITY_PATTERN}):sha256:([0-9a-f]{{64}})$"
)


class AdmissionDecisionValue(StrEnum):
    APPROVE = "APPROVE"
    APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS"
    REJECT = "REJECT"


class SourceAdmissionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authority: str = Field(min_length=1)
    decision: AdmissionDecisionValue
    scope: str = Field(min_length=24)
    manifest_reference: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    reviewed_at: datetime
    expires_at: datetime
    signature: str = Field(min_length=32)
    conditions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_decision(self) -> SourceAdmissionDecision:
        if self.authority not in REQUIRED_AUTHORITIES:
            raise ValueError("Unsupported source-admission authority")
        if self.reviewed_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("Decision timestamps require timezones")
        if self.expires_at <= self.reviewed_at:
            raise ValueError("Decision expiry must be after review time")
        if any(not item.strip() for item in self.conditions):
            raise ValueError("Decision conditions must be non-empty")
        return self


@dataclass(frozen=True)
class VerifiedDecision:
    decision: SourceAdmissionDecision
    issue_number: int
    comment_id: int
    comment_url: str | None
    comment_author: str
    comment_user_type: str
    comment_created_at: str | None
    comment_updated_at: str | None


@dataclass(frozen=True)
class SourceAdmissionEvaluation:
    status: str
    admitted: bool
    effective_expiry: datetime | None
    authority_status: dict[str, str]
    head_match: bool
    manifest_match: bool
    scope_match: bool
    issue_match: bool
    signatures_human: bool
    expiry_within_evidence: bool
    evidence_ready: bool
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


def canonical_unsigned_payload(decision: SourceAdmissionDecision) -> bytes:
    payload = decision.model_dump(mode="json")
    payload.pop("signature")
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def unsigned_payload_digest(decision: SourceAdmissionDecision) -> str:
    return hashlib.sha256(canonical_unsigned_payload(decision)).hexdigest()


def build_github_identity_signature(
    decision: SourceAdmissionDecision,
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
    decision: SourceAdmissionDecision,
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


def evaluate_source_admission_authority(
    decisions: dict[str, VerifiedDecision],
    *,
    expected_head_sha: str,
    expected_manifest_reference: str,
    expected_issues: dict[str, int],
    expected_scopes: dict[str, str],
    evidence_expires_at: datetime,
    decision_max_expires_at: datetime,
    evidence_ready: bool,
    evidence_reasons: tuple[str, ...] = (),
    now: datetime,
) -> SourceAdmissionEvaluation:
    current = parse_utc(now)
    evidence_expiry = parse_utc(evidence_expires_at)
    decision_max = parse_utc(decision_max_expires_at)

    missing = REQUIRED_AUTHORITIES.difference(decisions)
    authority_status = {
        authority: ("MISSING" if authority in missing else "PRESENT_UNEVALUATED")
        for authority in sorted(REQUIRED_AUTHORITIES)
    }
    if missing:
        return SourceAdmissionEvaluation(
            status=(
                "MISSING"
                if len(missing) == len(REQUIRED_AUTHORITIES)
                else "INCOMPLETE"
            ),
            admitted=False,
            effective_expiry=None,
            authority_status=authority_status,
            head_match=False,
            manifest_match=False,
            scope_match=False,
            issue_match=False,
            signatures_human=False,
            expiry_within_evidence=False,
            evidence_ready=evidence_ready,
            reasons=(f"Missing human authorities: {', '.join(sorted(missing))}",),
        )

    values = {authority: item.decision for authority, item in decisions.items()}
    head_match = all(item.head_sha == expected_head_sha for item in values.values())
    manifest_match = all(
        item.manifest_reference == expected_manifest_reference
        for item in values.values()
    )
    scope_match = all(
        values[authority].scope == expected_scopes[authority]
        for authority in REQUIRED_AUTHORITIES
    )
    issue_match = all(
        decisions[authority].issue_number == expected_issues[authority]
        for authority in REQUIRED_AUTHORITIES
    )
    signatures_human = all(
        verify_human_signature(
            item.decision,
            comment_author=item.comment_author,
            comment_user_type=item.comment_user_type,
        )
        for item in decisions.values()
    )
    expiry_within_evidence = all(
        parse_utc(item.expires_at) <= decision_max
        and parse_utc(item.expires_at) < evidence_expiry
        for item in values.values()
    )

    reasons: list[str] = list(evidence_reasons)
    if not evidence_ready:
        reasons.append("Frozen source-admission evidence is not ready")
    if not head_match:
        reasons.append("One or more decisions target a different exact admission head")
    if not manifest_match:
        reasons.append("One or more decisions target a different admission manifest")
    if not scope_match:
        reasons.append(
            "One or more decisions use an authority scope not frozen by the manifest"
        )
    if not issue_match:
        reasons.append("One or more decisions were posted outside the assigned authority issue")
    if not signatures_human:
        reasons.append("One or more decisions lack a valid human GitHub identity signature")
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
        if item.decision is AdmissionDecisionValue.REJECT
    ]
    if rejected:
        reasons.append(f"Source admission rejected by: {', '.join(sorted(rejected))}")

    for authority, decision in values.items():
        if parse_utc(decision.expires_at) <= current:
            authority_status[authority] = "EXPIRED"
        elif decision.decision is AdmissionDecisionValue.REJECT:
            authority_status[authority] = "REJECTED_CURRENT"
        else:
            authority_status[authority] = "APPROVED_CURRENT"

    admitted = not reasons and all(
        item.decision
        in {
            AdmissionDecisionValue.APPROVE,
            AdmissionDecisionValue.APPROVE_WITH_CONDITIONS,
        }
        for item in values.values()
    )
    return SourceAdmissionEvaluation(
        status="APPROVED_CURRENT" if admitted else "BLOCKED",
        admitted=admitted,
        effective_expiry=effective_expiry,
        authority_status=authority_status,
        head_match=head_match,
        manifest_match=manifest_match,
        scope_match=scope_match,
        issue_match=issue_match,
        signatures_human=signatures_human,
        expiry_within_evidence=expiry_within_evidence,
        evidence_ready=evidence_ready,
        reasons=(
            tuple(reasons)
            if reasons
            else ("All seven human authorities are current",)
        ),
    )


def result_payload(
    evaluation: SourceAdmissionEvaluation,
    *,
    manifest_reference: str,
    target_head_sha: str,
    evidence_expires_at: datetime,
    decision_sources: dict[str, VerifiedDecision],
) -> dict[str, Any]:
    admitted = evaluation.admitted
    return {
        "status": "PASS" if admitted else "BLOCKED",
        "output": (
            "O01_TED_SOURCE_ADMISSION_PASS"
            if admitted
            else "O01_TED_SOURCE_ADMISSION_BLOCKED"
        ),
        "decision": "ADMIT" if admitted else "BLOCK",
        "previous_state": "CANDIDATE",
        "next_state": "PRODUCT_ADMITTED" if admitted else "CANDIDATE",
        "product_admitted": admitted,
        "bounded_product_use_authorised": admitted,
        "bounded_claim_contribution": False,
        "global_coverage_claim_authorised": False,
        "public_launch": "NO_GO",
        "head_match": evaluation.head_match,
        "manifest_match": evaluation.manifest_match,
        "scope_match": evaluation.scope_match,
        "issue_match": evaluation.issue_match,
        "signatures_human": evaluation.signatures_human,
        "expiry_within_evidence": evaluation.expiry_within_evidence,
        "evidence_ready": evaluation.evidence_ready,
        "effective_expiry": (
            evaluation.effective_expiry.isoformat().replace("+00:00", "Z")
            if evaluation.effective_expiry
            else None
        ),
        "evidence_expires_at": (
            parse_utc(evidence_expires_at).isoformat().replace("+00:00", "Z")
        ),
        "target_head_sha": target_head_sha,
        "manifest_reference": manifest_reference,
        "authorities": evaluation.authority_status,
        "decision_sources": {
            authority: {
                "issue_number": source.issue_number,
                "comment_id": source.comment_id,
                "comment_url": source.comment_url,
                "comment_author": source.comment_author,
                "comment_created_at": source.comment_created_at,
                "comment_updated_at": source.comment_updated_at,
                "decision": source.decision.decision.value,
                "scope": source.decision.scope,
                "expires_at": (
                    source.decision.expires_at.astimezone(UTC)
                    .isoformat()
                    .replace("+00:00", "Z")
                ),
                "conditions": list(source.decision.conditions),
            }
            for authority, source in sorted(decision_sources.items())
        },
        "permanent_boundary": {
            "public_redistribution_authorised": False,
            "contact_marketing_authorised": False,
            "model_training_authorised": False,
            "bid_submission_authorised": False,
            "external_notification_delivery_authorised": False,
            "global_coverage_claim_authorised": False,
            "public_launch": "NO_GO",
            "gate7_closed": False,
        },
        "reasons": list(evaluation.reasons),
    }
