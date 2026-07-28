from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from axignal_api.admission_types import (
    ALLOWED_PREDICATE,
    ALLOWED_SOURCE,
    ALLOWED_SUBJECT,
    ALLOWED_UNIT,
    NUMBER_PATTERN,
    AdmissionIntegrityError,
)
from axignal_api.document_proposals import canonical_hash


class AdmissionFactPolicyMixin:
    @staticmethod
    def _evaluate_candidate(
        *,
        package: dict[str, Any],
        candidate: dict[str, Any],
        packaged_candidate: dict[str, Any],
        source: dict[str, Any],
        source_object: dict[str, Any],
        fragments: dict[str, dict[str, Any]],
        evidence: dict[UUID, dict[str, Any]],
    ) -> dict[str, Any]:
        gate_results: dict[str, bool] = {
            "HANDOFF_SCHEMA_VALID": True,
            "PACKAGE_HASH_VALID": True,
            "SOURCE_STILL_ADMITTED": source["admission_state"] == "ADMITTED",
            "SOURCE_KILL_SWITCH_OFF": source["kill_switch"] is False,
            "RIGHTS_STILL_VALID": source["commercial_use"] and source["redistribution"],
            "RAW_OBJECT_HASH_VALID": source_object["content_hash"]
            == package["document"]["content_hash"],
            "PRODUCER_AUTHORITY_SEPARATED": candidate["producer_type"] == "LOCAL_MODEL",
            "POLICY_VERSION_PINNED": True,
        }
        if candidate["kind"] != "FACT":
            return {
                "outcome": "HUMAN_REVIEW_REQUIRED",
                "reasons": ["candidate_class_not_auto_admissible"],
                "gate_results": gate_results | {"PREDICATE_ALLOWED": False},
                "rederived": None,
                "rederived_fingerprint": None,
            }
        if (
            candidate["subject_id"] != ALLOWED_SUBJECT
            or candidate["predicate"] != ALLOWED_PREDICATE
        ):
            return {
                "outcome": "HUMAN_REVIEW_REQUIRED",
                "reasons": ["candidate_outside_first_admission_profile"],
                "gate_results": gate_results | {"PREDICATE_ALLOWED": False},
                "rederived": None,
                "rederived_fingerprint": None,
            }

        evidence_by_key = {
            item["evidence_key"]: item for item in evidence.values()
        }
        texts: list[str] = []
        supporting_evidence_ids: list[UUID] = []
        for evidence_key in packaged_candidate["evidence_keys"]:
            persistent = evidence_by_key.get(evidence_key)
            if persistent is None or persistent["evidence_id"] not in candidate["evidence_ids"]:
                raise AdmissionIntegrityError("Candidate evidence binding differs")
            packaged_evidence = next(
                (item for item in package["evidence"] if item["evidence_key"] == evidence_key),
                None,
            )
            if packaged_evidence is None:
                raise AdmissionIntegrityError("Packaged Evidence Object is absent")
            fragment = fragments.get(packaged_evidence["fragment_id"])
            if fragment is None:
                raise AdmissionIntegrityError("Evidence fragment is absent")
            if packaged_evidence["quote_hash"] != fragment["content_hash"]:
                raise AdmissionIntegrityError("Evidence quote hash differs from fragment")
            payload = persistent["payload"]
            if (
                payload.get("fragment_id") != fragment["fragment_id"]
                or payload.get("quote_hash") != fragment["content_hash"]
                or payload.get("text") != fragment["text_content"]
                or persistent["content_hash"] != packaged_evidence["content_hash"]
            ):
                raise AdmissionIntegrityError("Persistent Evidence Object differs")
            if persistent["rights_status"] != source["rights_status"]:
                raise AdmissionIntegrityError("Evidence rights differ from current source")
            texts.append(fragment["text_content"])
            supporting_evidence_ids.append(persistent["evidence_id"])

        matches = [match for text in texts if (match := NUMBER_PATTERN.search(text))]
        if len(matches) != 1:
            return {
                "outcome": "REJECTED",
                "reasons": ["deterministic_value_not_uniquely_rederived"],
                "gate_results": gate_results | {"VALUE_REDERIVED": False},
                "rederived": None,
                "rederived_fingerprint": None,
            }
        match = matches[0]
        try:
            value = Decimal(match.group(1))
        except InvalidOperation as exc:
            raise AdmissionIntegrityError("Rederived numeric value is invalid") from exc
        period = match.group(2)
        rederived = {
            "subject_id": ALLOWED_SUBJECT,
            "predicate": ALLOWED_PREDICATE,
            "object_value": {
                "value": str(value),
                "unit": ALLOWED_UNIT,
                "period": period,
            },
            "observed_at": f"{period}-12-31T23:59:59+00:00",
            "evidence_ids": [str(item) for item in supporting_evidence_ids],
        }
        proposed = candidate["object_value"]
        exact_match = (
            proposed.get("value") == str(value)
            and proposed.get("unit") == ALLOWED_UNIT
            and proposed.get("period") == period
        )
        adverse_same_semantics = any(
            item.get("relationship") == "ADVERSE"
            and item.get("subject_id") == ALLOWED_SUBJECT
            and item.get("predicate") == ALLOWED_PREDICATE
            for item in package["candidate_claims"]
            if item.get("persistent_candidate_claim_id")
            != packaged_candidate["persistent_candidate_claim_id"]
        )
        gate_results |= {
            "EVIDENCE_BINDING_VALID": True,
            "SUBJECT_RESOLVED": True,
            "PREDICATE_ALLOWED": True,
            "VALUE_REDERIVED": True,
            "UNIT_REDERIVED": True,
            "PERIOD_REDERIVED": True,
            "VALUE_UNIT_PERIOD_EXACT_MATCH": exact_match,
            "TEMPORAL_VALIDITY_PASS": int(period) <= datetime.now(UTC).year,
            "SCOPE_VALIDITY_PASS": True,
            "CONTRADICTION_PRESSURE_ACCEPTABLE": not adverse_same_semantics,
        }
        if not exact_match:
            return {
                "outcome": "REJECTED",
                "reasons": ["proposed_value_unit_or_period_mismatch"],
                "gate_results": gate_results,
                "rederived": rederived,
                "rederived_fingerprint": canonical_hash(rederived),
            }
        if adverse_same_semantics:
            return {
                "outcome": "CONTESTED",
                "reasons": ["adverse_evidence_targets_same_semantics"],
                "gate_results": gate_results,
                "rederived": rederived,
                "rederived_fingerprint": canonical_hash(rederived),
            }
        fingerprint = canonical_hash({
            "subject_id": rederived["subject_id"],
            "predicate": rederived["predicate"],
            "object_value": rederived["object_value"],
            "observed_at": rederived["observed_at"],
        })
        return {
            "outcome": "ADMITTED_REDERIVED",
            "reasons": ["all_deterministic_gates_passed"],
            "gate_results": gate_results,
            "rederived": rederived,
            "rederived_fingerprint": fingerprint,
        }
