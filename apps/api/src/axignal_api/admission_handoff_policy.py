from __future__ import annotations

from typing import Any

from axignal_api.admission_queue import AdmissionReviewJob
from axignal_api.admission_types import AdmissionIntegrityError
from axignal_api.document_proposals import canonical_hash


class AdmissionHandoffPolicyMixin:
    @staticmethod
    def _load_handoff(cursor: Any, job: AdmissionReviewJob) -> dict[str, Any]:
        cursor.execute(
            """
            SELECT * FROM axignal_global.admission_handoffs
            WHERE admission_handoff_id = %s AND tenant_id = %s
              AND research_run_id = %s
            FOR UPDATE
            """,
            (job.admission_handoff_id, job.tenant_id, job.research_run_id),
        )
        handoff = cursor.fetchone()
        if handoff is None:
            raise AdmissionIntegrityError("Admission handoff is absent or tenant-mismatched")
        return handoff

    @staticmethod
    def _validate_package(
        handoff: dict[str, Any],
        job: AdmissionReviewJob,
    ) -> dict[str, Any]:
        package = handoff["package"]
        if not isinstance(package, dict):
            raise AdmissionIntegrityError("Admission package is not an object")
        actual_hash = canonical_hash(package)
        if actual_hash != handoff["package_hash"] or actual_hash != job.expected_package_hash:
            raise AdmissionIntegrityError("Admission package hash does not match")
        required = {
            "schema_version",
            "tenant_id",
            "research_run_id",
            "pipeline_version",
            "document",
            "source",
            "fragments",
            "evidence",
            "candidate_claims",
            "admission_boundary_results",
            "dossier",
            "actual_usage",
            "human_review_state",
            "canonical_claim_ids",
        }
        if required != set(package):
            raise AdmissionIntegrityError("Admission package schema keys differ")
        if package["schema_version"] != 1:
            raise AdmissionIntegrityError("Admission package schema version differs")
        if package["tenant_id"] != str(job.tenant_id):
            raise AdmissionIntegrityError("Admission package tenant differs")
        if package["research_run_id"] != str(job.research_run_id):
            raise AdmissionIntegrityError("Admission package ResearchRun differs")
        if package["pipeline_version"] != "local-document-proposal-pipeline@0.1.0":
            raise AdmissionIntegrityError("Proposal pipeline version differs")
        if package["human_review_state"] != "NOT_REQUESTED":
            raise AdmissionIntegrityError("Unexpected pre-admission human review state")
        if package["canonical_claim_ids"] != []:
            raise AdmissionIntegrityError("Proposal handoff already contains canonical claims")
        boundaries = package["admission_boundary_results"]
        if not boundaries or any(
            item.get("admitted") is not False
            or item.get("canonical_claim_id") is not None
            for item in boundaries
        ):
            raise AdmissionIntegrityError("Proposal authority boundary is not preserved")
        return package

    @staticmethod
    def _load_run(cursor: Any, job: AdmissionReviewJob) -> dict[str, Any]:
        cursor.execute(
            """
            SELECT * FROM tenant_private.research_runs
            WHERE research_run_id = %s AND tenant_id = %s
            FOR UPDATE
            """,
            (job.research_run_id, job.tenant_id),
        )
        run = cursor.fetchone()
        if run is None:
            raise AdmissionIntegrityError("Tenant-scoped ResearchRun is absent")
        if run["job_kind"] != "DOCUMENT_PROPOSAL":
            raise AdmissionIntegrityError("ResearchRun is not a document proposal")
        if run["admission_handoff_id"] != job.admission_handoff_id:
            raise AdmissionIntegrityError("ResearchRun handoff reference differs")
        return run
