from __future__ import annotations

import json
from pathlib import Path

from axignal_api.document_proposals import (
    FrozenProposalAdapter,
    InstitutionalDocument,
    LocalDocumentProposalPipeline,
    ProposalBatch,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "apps" / "api" / "tests" / "fixtures"
EXPECTED_GATES = {
    "DOCUMENT_PROCESSED": True,
    "EVIDENCE_BOUND": True,
    "CANDIDATES_PROPOSED": True,
    "ADMISSION_INDEPENDENT": True,
    "CI_REPRODUCIBLE": True,
    "MODEL_AUTHORITY_BLOCKED": True,
}


def main() -> int:
    document = InstitutionalDocument.model_validate_json(
        (FIXTURES / "world_bank_rer41_document.json").read_text(encoding="utf-8")
    )
    proposal = ProposalBatch.model_validate_json(
        (FIXTURES / "world_bank_rer41_proposal.json").read_text(encoding="utf-8")
    )
    pipeline = LocalDocumentProposalPipeline(
        model_gateway=FrozenProposalAdapter(proposal)
    )
    result = pipeline.execute(
        document=document,
        opportunity_id="opportunity_moscow_real_estate",
        research_question="What macro evidence supports or limits this opportunity?",
    )

    gates = result.gates.model_dump()
    if gates != EXPECTED_GATES:
        raise RuntimeError(f"Local document proposal gates failed: {gates}")
    if result.canonical_claims:
        raise RuntimeError("Proposal-only pipeline produced canonical claims")
    if not all(item.canonical_claim_id is None for item in result.admission_results):
        raise RuntimeError("A local model proposal acquired canonical authority")

    summary = {
        "pipeline_version": result.pipeline_version,
        "document_id": result.document.document_id,
        "fragments": len(result.fragments),
        "evidence_objects": len(result.evidence),
        "candidate_claims": len(result.candidate_claims),
        "canonical_claims": len(result.canonical_claims),
        "dossier_status": result.dossier.status,
        "reproducibility_hash": result.actual_usage["reproducibility_hash"],
        "gates": gates,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
