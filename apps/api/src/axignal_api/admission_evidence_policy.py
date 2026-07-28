from __future__ import annotations

from typing import Any
from uuid import UUID

from axignal_api.admission_types import AdmissionIntegrityError


class AdmissionEvidencePolicyMixin:
    @staticmethod
    def _load_candidates(
        cursor: Any,
        candidate_ids: list[UUID],
    ) -> dict[UUID, dict[str, Any]]:
        cursor.execute(
            "SELECT * FROM axignal_global.candidate_claims "
            "WHERE candidate_claim_id = ANY(%s)",
            (candidate_ids,),
        )
        rows = cursor.fetchall()
        if len(rows) != len(candidate_ids):
            raise AdmissionIntegrityError("Candidate Claim persistence set is incomplete")
        return {row["candidate_claim_id"]: row for row in rows}

    @staticmethod
    def _validate_candidate_set(
        package: dict[str, Any],
        candidate_ids: list[UUID],
    ) -> None:
        packaged_ids = [
            UUID(item["persistent_candidate_claim_id"])
            for item in package["candidate_claims"]
        ]
        if packaged_ids != candidate_ids:
            raise AdmissionIntegrityError("Candidate Claim handoff order or identity differs")
        boundaries = package["admission_boundary_results"]
        if len(boundaries) != len(candidate_ids):
            raise AdmissionIntegrityError("Admission boundary result count differs")
        boundary_ids = [item.get("candidate_claim_id") for item in boundaries]
        draft_ids = [item.get("candidate_claim_id") for item in package["candidate_claims"]]
        if boundary_ids != draft_ids:
            raise AdmissionIntegrityError("Admission boundary identities differ")

    @staticmethod
    def _validate_all_evidence(
        *,
        package: dict[str, Any],
        fragments: dict[str, dict[str, Any]],
        evidence: dict[UUID, dict[str, Any]],
        source: dict[str, Any],
    ) -> None:
        packaged_ids: set[UUID] = set()
        for packaged in package["evidence"]:
            evidence_id = UUID(packaged["persistent_evidence_id"])
            packaged_ids.add(evidence_id)
            persistent = evidence.get(evidence_id)
            if persistent is None:
                raise AdmissionIntegrityError("Packaged Evidence Object is absent")
            fragment = fragments.get(packaged["fragment_id"])
            if fragment is None:
                raise AdmissionIntegrityError("Evidence fragment is absent")
            payload = persistent["payload"]
            checks = (
                persistent["evidence_key"] == packaged["evidence_key"],
                persistent["source_id"] == packaged["source_id"],
                persistent["content_hash"] == packaged["content_hash"],
                persistent["rights_status"] == source["rights_status"],
                packaged["rights_status"] == source["rights_status"],
                packaged["license_id"] == source["license_id"],
                packaged["quote_hash"] == fragment["content_hash"],
                packaged["text"] == fragment["text_content"],
                payload.get("fragment_id") == fragment["fragment_id"],
                payload.get("quote_hash") == fragment["content_hash"],
                payload.get("text") == fragment["text_content"],
            )
            if not all(checks):
                raise AdmissionIntegrityError("Evidence Object differs from immutable inputs")
        expected_ids = {
            evidence_id
            for candidate in package["candidate_claims"]
            for evidence_id in [
                UUID(item["persistent_evidence_id"])
                for item in package["evidence"]
                if item["evidence_key"] in candidate["evidence_keys"]
            ]
        }
        if packaged_ids != expected_ids or packaged_ids != set(evidence):
            raise AdmissionIntegrityError("Evidence handoff set differs")

    @staticmethod
    def _load_evidence(
        cursor: Any,
        candidates: dict[UUID, dict[str, Any]],
    ) -> dict[UUID, dict[str, Any]]:
        evidence_ids = list({
            evidence_id
            for candidate in candidates.values()
            for evidence_id in candidate["evidence_ids"]
        })
        cursor.execute(
            "SELECT * FROM axignal_global.evidence_objects WHERE evidence_id = ANY(%s)",
            (evidence_ids,),
        )
        rows = cursor.fetchall()
        if len(rows) != len(evidence_ids):
            raise AdmissionIntegrityError("Evidence persistence set is incomplete")
        return {row["evidence_id"]: row for row in rows}

    @staticmethod
    def _validate_candidate_record(
        candidate: dict[str, Any],
        packaged: dict[str, Any],
    ) -> None:
        fields = (
            "fingerprint",
            "opportunity_id",
            "subject_id",
            "predicate",
            "object_value",
            "statement",
            "kind",
            "relationshhip",
            "producer_type",
            "producer_id",
            "model_version",
            "method_version",
            "prompt_version",
            "assumptions",
            "unknowns",
      )
        if any(candidate[field] != packaged[field] for field in fields):
            raise AdmissionIntegrityError("Candidate Claim differs from handoff package")
        if float(candidate["extraction_confidence"]) != float(
            packaged["extraction_confidence"]
        ):
            raise AdmissionIntegrityError("Candidate extraction confidence differs")
        if packaged.get("state") != "ADMISSION_QUEUED":
            raise AdmissionIntegrityError("Packaged Candidate Claim state differs")
        if packaged.get("canonical_claim_id") is not None:
            raise AdmissionIntegrityError("Packaged Candidate Claim is already canonical")
        if candidate["state"] != "ADMISSION_QUEUED":
            raise AdmissionIntegrityError("Persistent Candidate Claim state differs")
        if candidate["producer_type"] != "LOCAL_MODEL":
            raise AdmissionIntegrityError("Expected proposal producer type LOCAL_MODEL")
        if candidate["canonical_claim_id"] is not None:
            raise AdmissionIntegrityError("Candidate already carries a canonical claim")
