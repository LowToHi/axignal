from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Any

from axignal_api.connectors.ted import FIXED_FIELDS, SOURCE_ID, TEDSearchPage

POLICY_VERSION = "ted-search-observed-field@0.1.0"
PROFILE_ID = "ted-search-non-personal-projection@0.1.0"
RIGHTS_STATUS = "COMMERCIAL_REUSE_WITH_ATTRIBUTION"
PROHIBITED_TOKENS = ("contact", "email", "person", "phone", "telephone")
FIELD_PREDICATES = {
    "publication-number": "procurement_notice_publication_number",
    "notice-title": "procurement_notice_title",
    "buyer-name": "procurement_buyer_official_name",
    "notice-type": "procurement_notice_type",
}


@dataclass(frozen=True)
class TEDEvidenceArtifact:
    evidence_key: str
    title: str
    relationship: str
    subject_id: str
    predicate: str
    observed_at: datetime
    payload: dict[str, Any]
    content_hash: str
    rights_status: str = RIGHTS_STATUS


@dataclass(frozen=True)
class TEDCandidateArtifact:
    fingerprint: str
    opportunity_id: str
    subject_id: str
    predicate: str
    object_value: dict[str, Any]
    statement: str
    kind: str = "FACT"
    producer_type: str = "DETERMINISTIC_PARSER"
    producer_id: str = "ted-search-projection-parser"
    method_version: str = POLICY_VERSION


@dataclass(frozen=True)
class TEDAdmissionDecision:
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


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
    return f"sha256:{sha256(encoded.encode('utf-8')).hexdigest()}"


def sanitised_projection(page: TEDSearchPage) -> dict[str, Any]:
    return {
        "source_id": page.source_id,
        "query": page.query,
        "requested_fields": list(page.requested_fields),
        "total_notice_count": page.total_notice_count,
        "notices": [
            {
                field: notice.fields.get(field)
                for field in FIXED_FIELDS
                if notice.fields.get(field) is not None
            }
            for notice in page.notices
        ],
        "retrieval_mode": page.retrieval_mode,
    }


def build_ted_search_artifacts(
    *,
    page: TEDSearchPage,
    opportunity_id: str,
) -> tuple[
    tuple[TEDEvidenceArtifact, ...],
    tuple[TEDCandidateArtifact, ...],
]:
    if page.source_id != SOURCE_ID:
        raise ValueError("TED page source identifier is outside the admitted profile")
    if tuple(page.requested_fields) != FIXED_FIELDS:
        raise ValueError("TED requested fields differ from the admitted allowlist")
    if len(page.notices) > 3:
        raise ValueError("TED page exceeds the admitted notice budget")

    evidence: list[TEDEvidenceArtifact] = []
    candidates: list[TEDCandidateArtifact] = []
    seen_bindings: set[tuple[str, str]] = set()

    for notice in page.notices:
        subject_id = f"ted_notice_{notice.publication_number.replace('-', '_')}"
        for field in FIXED_FIELDS:
            value = notice.fields.get(field)
            if value is None:
                continue
            lowered = field.casefold()
            if any(token in lowered for token in PROHIBITED_TOKENS):
                raise ValueError("TED field includes prohibited personal-data semantics")
            predicate = FIELD_PREDICATES[field]
            binding = (subject_id, predicate)
            if binding in seen_bindings:
                raise ValueError("Duplicate TED subject and predicate binding")
            seen_bindings.add(binding)

            object_value = {
                "publication_number": notice.publication_number,
                "field": field,
                "value": value,
                "source_request_hash": page.request_hash,
            }
            evidence_key = canonical_hash(
                {
                    "source_id": SOURCE_ID,
                    "subject_id": subject_id,
                    "predicate": predicate,
                    "object_value": object_value,
                    "source_content_hash": page.content_hash,
                    "profile_id": PROFILE_ID,
                }
            )
            statement = _statement(
                publication_number=notice.publication_number,
                field=field,
                value=value,
            )
            fingerprint = canonical_hash(
                {
                    "subject_id": subject_id,
                    "predicate": predicate,
                    "object_value": object_value,
                    "evidence_key": evidence_key,
                    "method_version": POLICY_VERSION,
                }
            )
            evidence.append(
                TEDEvidenceArtifact(
                    evidence_key=evidence_key,
                    title=f"TED {notice.publication_number} · {field}",
                    relationship="SUPPORT",
                    subject_id=subject_id,
                    predicate=predicate,
                    observed_at=page.retrieved_at,
                    payload=object_value,
                    content_hash=canonical_hash(
                        {
                            "evidence_key": evidence_key,
                            "statement": statement,
                            "source_content_hash": page.content_hash,
                        }
                    ),
                )
            )
            candidates.append(
                TEDCandidateArtifact(
                    fingerprint=fingerprint,
                    opportunity_id=opportunity_id,
                    subject_id=subject_id,
                    predicate=predicate,
                    object_value=object_value,
                    statement=statement,
                )
            )

    if not evidence:
        raise ValueError("TED projection produced no admissible evidence")
    return tuple(evidence), tuple(candidates)


def evaluate_ted_observed_field(
    *,
    source: dict[str, Any],
    evidence: TEDEvidenceArtifact,
    candidate: TEDCandidateArtifact,
) -> TEDAdmissionDecision:
    reasons: list[str] = []
    config = source.get("config")
    if not isinstance(config, dict):
        config = {}

    if source.get("source_id") != SOURCE_ID:
        reasons.append("unexpected_source")
    if source.get("admission_state") != "ADMITTED":
        reasons.append("source_not_admitted")
    if bool(source.get("kill_switch")):
        reasons.append("source_kill_switch_enabled")
    if source.get("rights_status") != RIGHTS_STATUS:
        reasons.append("rights_not_commercially_reusable")
    if not bool(source.get("commercial_use")):
        reasons.append("commercial_use_not_permitted")
    if config.get("product_profile") != PROFILE_ID:
        reasons.append("product_profile_not_admitted")
    if config.get("api_redistribution_allowed") is not False:
        reasons.append("api_redistribution_guard_missing")
    if candidate.kind != "FACT":
        reasons.append("candidate_not_observed_fact")
    if candidate.producer_type != "DETERMINISTIC_PARSER":
        reasons.append("generative_producer_cannot_auto_admit")
    if candidate.predicate not in FIELD_PREDICATES.values():
        reasons.append("predicate_outside_profile")
    if candidate.predicate != evidence.predicate:
        reasons.append("candidate_evidence_predicate_mismatch")
    if candidate.subject_id != evidence.subject_id:
        reasons.append("candidate_evidence_subject_mismatch")
    if candidate.object_value != evidence.payload:
        reasons.append("candidate_evidence_value_mismatch")
    if evidence.rights_status != source.get("rights_status"):
        reasons.append("evidence_rights_snapshot_mismatch")
    if not evidence.content_hash.startswith("sha256:"):
        reasons.append("evidence_hash_missing")
    if evidence.payload.get("field") not in FIXED_FIELDS:
        reasons.append("evidence_field_outside_allowlist")

    return TEDAdmissionDecision(
        admitted=not reasons,
        policy_version=POLICY_VERSION,
        reasons=tuple(reasons) if reasons else ("all_ted_projection_gates_passed",),
        epistemic_class="OBSERVED_FACT" if not reasons else None,
    )


def _display_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for language in ("spa", "eng"):
            candidate = value.get(language)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        for candidate in value.values():
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _statement(*, publication_number: str, field: str, value: Any) -> str:
    displayed = _display_value(value)
    if field == "publication-number":
        return f"TED identifica el anuncio publicado con el número {publication_number}."
    if field == "notice-title":
        return f"El anuncio TED {publication_number} declara el título: {displayed}."
    if field == "buyer-name":
        return f"El anuncio TED {publication_number} identifica al comprador: {displayed}."
    if field == "notice-type":
        return f"El anuncio TED {publication_number} declara el tipo de aviso: {displayed}."
    raise ValueError("TED field is outside the admitted profile")
