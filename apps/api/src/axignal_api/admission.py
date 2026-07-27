from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any

POLICY_VERSION = "observed-institutional-fact@1.0.0"


@dataclass(frozen=True)
class CandidateArtifact:
    fingerprint: str
    opportunity_id: str
    subject_id: str
    predicate: str
    object_value: dict[str, Any]
    statement: str
    kind: str
    producer_type: str
    producer_id: str
    method_version: str


@dataclass(frozen=True)
class EvidenceArtifact:
    evidence_key: str
    title: str
    relationship: str
    subject_id: str
    predicate: str
    observed_at: datetime
    valid_from: datetime | None
    valid_to: datetime | None
    numeric_value: Decimal
    unit: str
    payload: dict[str, Any]
    content_hash: str
    rights_status: str


@dataclass(frozen=True)
class AdmissionDecision:
    admitted: bool
    policy_version: str
    reasons: tuple[str, ...]
    epistemic_class: str | None

    def as_json(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "policy_version": self.policy_version,
            "reasons": list(self.reasons),
            "epistemic_class": self.epistemic_class,
        }


def canonical_fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return f"sha256:{sha256(canonical.encode('utf-8')).hexdigest()}"


def build_world_bank_inflation_artifacts(
    *,
    opportunity_id: str,
    period: str,
    value: float,
    source_content_hash: str,
) -> tuple[EvidenceArtifact, CandidateArtifact]:
    observed_at = datetime(int(period), 12, 31, 23, 59, 59, tzinfo=UTC)
    decimal_value = Decimal(str(value))
    subject_id = "geo_country_rus"
    predicate = "consumer_price_inflation_annual_pct"
    evidence_key = canonical_fingerprint(
        {
            "source": "world-bank-wdi",
            "indicator": "FP.CPI.TOTL.ZG",
            "country": "RUS",
            "period": period,
            "value": str(decimal_value),
            "source_content_hash": source_content_hash,
        }
    )
    statement = (
        "La inflación anual de precios al consumidor en la Federación Rusa fue "
        f"del {decimal_value}% en {period}."
    )
    object_value = {
        "value": str(decimal_value),
        "unit": "percent_annual",
        "period": period,
        "country_code": "RUS",
        "indicator_code": "FP.CPI.TOTL.ZG",
    }
    candidate_fingerprint = canonical_fingerprint(
        {
            "subject_id": subject_id,
            "predicate": predicate,
            "object_value": object_value,
            "evidence_key": evidence_key,
            "method_version": "world-bank-wdi-parser@1.0.0",
        }
    )
    evidence = EvidenceArtifact(
        evidence_key=evidence_key,
        title="World Bank WDI · Inflation, consumer prices (annual %) · Russian Federation",
        relationship="CONTEXT",
        subject_id=subject_id,
        predicate=predicate,
        observed_at=observed_at,
        valid_from=datetime(int(period), 1, 1, tzinfo=UTC),
        valid_to=datetime(int(period), 12, 31, 23, 59, 59, tzinfo=UTC),
        numeric_value=decimal_value,
        unit="percent_annual",
        payload=object_value,
        content_hash=canonical_fingerprint(
            {
                "evidence_key": evidence_key,
                "statement": statement,
                "source_content_hash": source_content_hash,
            }
        ),
        rights_status="COMMERCIAL_REUSE_WITH_ATTRIBUTION",
    )
    candidate = CandidateArtifact(
        fingerprint=candidate_fingerprint,
        opportunity_id=opportunity_id,
        subject_id=subject_id,
        predicate=predicate,
        object_value=object_value,
        statement=statement,
        kind="FACT",
        producer_type="DETERMINISTIC_PARSER",
        producer_id="world-bank-wdi-parser",
        method_version="world-bank-wdi-parser@1.0.0",
    )
    return evidence, candidate


def evaluate_observed_fact(
    *,
    source: dict[str, Any],
    evidence: EvidenceArtifact,
    candidate: CandidateArtifact,
) -> AdmissionDecision:
    reasons: list[str] = []

    if source.get("admission_state") != "ADMITTED":
        reasons.append("source_not_admitted")
    if bool(source.get("kill_switch")):
        reasons.append("source_kill_switch_enabled")
    if source.get("rights_status") != "COMMERCIAL_REUSE_WITH_ATTRIBUTION":
        reasons.append("rights_not_commercially_reusable")
    if not bool(source.get("commercial_use")):
        reasons.append("commercial_use_not_permitted")
    if not bool(source.get("redistribution")):
        reasons.append("redistribution_not_permitted")
    if source.get("license_id") != "CC-BY-4.0":
        reasons.append("unexpected_license")
    if candidate.kind != "FACT":
        reasons.append("candidate_not_observed_fact")
    if candidate.producer_type != "DETERMINISTIC_PARSER":
        reasons.append("generative_producer_cannot_auto_admit")
    if candidate.predicate != evidence.predicate or candidate.subject_id != evidence.subject_id:
        reasons.append("candidate_evidence_semantic_mismatch")
    if candidate.object_value.get("value") != str(evidence.numeric_value):
        reasons.append("candidate_evidence_value_mismatch")
    if candidate.object_value.get("unit") != evidence.unit:
        reasons.append("candidate_evidence_unit_mismatch")
    if evidence.rights_status != source.get("rights_status"):
        reasons.append("evidence_rights_snapshot_mismatch")
    if not evidence.content_hash.startswith("sha256:"):
        reasons.append("evidence_hash_missing")
    if evidence.observed_at > datetime.now(UTC):
        reasons.append("future_observation_not_admissible")

    return AdmissionDecision(
        admitted=not reasons,
        policy_version=POLICY_VERSION,
        reasons=tuple(reasons) if reasons else ("all_deterministic_gates_passed",),
        epistemic_class="OBSERVED_FACT" if not reasons else None,
    )
