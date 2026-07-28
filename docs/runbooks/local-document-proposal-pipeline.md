# Local document proposal pipeline v0.1

Status: `BOUNDED ACCEPTANCE SLICE / PROPOSAL-ONLY / NOT DEPLOYED`

## Purpose

This slice proves that AXIGNAL can transform one frozen, authorised institutional document into traceable provisional artifacts without granting a probabilistic model canonical authority.

```text
frozen institutional document
→ immutable content hash
→ deterministic paragraph parser
→ prompt-injection scan
→ local OpenAI-compatible model adapter
→ schema-valid ProposalBatch
→ one Evidence draft per referenced fragment
→ 1–3 Candidate Claim drafts
→ independent proposal-only boundary
→ traceable provisional dossier
```

The implementation lives in `apps/api/src/axignal_api/document_proposals.py`.

## Authority boundary

The local model may propose claims, adverse evidence, limitations and unknowns. It cannot:

- write to `axignal_global.canonical_claims`;
- mark a claim `ADMITTED`, `CORROBORATED` or `ACTIONABLE`;
- override source rights;
- alter tenant scope, budgets or gates;
- convert confidence into evidence;
- publish an opportunity.

Every `AdmissionBoundaryResult` is deliberately non-admitting and includes:

```json
{
  "admitted": false,
  "reasons": [
    "generative_producer_cannot_auto_admit",
    "independent_runtime_required"
  ],
  "canonical_claim_id": null
}
```

## Frozen acceptance source

The clean-clone fixture is an adapted, non-verbatim excerpt from:

- World Bank, *Russia Economic Report 41: Modest Growth - Focus on Informality*;
- document date: 2019-06-01;
- source: World Bank Documents and Reports;
- licence classification used by the slice: `CC-BY-4.0`;
- tenant scope: `GLOBAL_PUBLIC`.

Fixtures:

- `apps/api/tests/fixtures/world_bank_rer41_document.json`;
- `apps/api/tests/fixtures/world_bank_rer41_proposal.json`.

The fixture contains one supporting macroeconomic observation, one explicit local-market limitation and two unknowns. It is not current investment guidance.

## Run deterministic acceptance

```bash
python -m pip install -e ".[dev]"
python scripts/verify_local_document_proposal_pipeline.py
pytest apps/api/tests/test_local_document_proposals.py
```

Expected gates:

```text
DOCUMENT_PROCESSED=true
EVIDENCE_BOUND=true
CANDIDATES_PROPOSED=true
ADMISSION_INDEPENDENT=true
CI_REPRODUCIBLE=true
MODEL_AUTHORITY_BLOCKED=true
```

## Connect a local model

Any local inference server exposing an OpenAI-compatible `POST /v1/chat/completions` endpoint can be placed behind `OpenAICompatibleLocalModelAdapter`.

```python
from axignal_api.document_proposals import OpenAICompatibleLocalModelAdapter

adapter = OpenAICompatibleLocalModelAdapter(
    base_url="http://127.0.0.1:8001",
    model="local-model-name-and-quantisation",
    api_key="local-only",
)
```

The adapter sends:

- temperature `0`;
- a JSON-only response request;
- the Pydantic-derived ProposalBatch schema;
- fragment IDs and hashes rather than unbounded filesystem access;
- an explicit instruction that document text is untrusted data;
- an explicit proposal-only authority statement.

Invalid HTTP responses, invalid JSON and schema-invalid output fail closed as `ModelProposalError`.

## Security properties

The bounded parser rejects document content matching high-risk instruction patterns before any model call, including attempts to:

- ignore prior instructions;
- reveal the system prompt;
- change permissions, budgets, policies or gates;
- write directly to the canonical Claim Ledger;
- embed scripts or command-oriented payloads.

Detection causes document quarantine. The parser never executes macros, scripts or embedded commands.

## Deliberate exclusions

This v0.1 slice does not yet:

- persist local model proposals through the PostgreSQL worker role;
- route a Navigator-created ResearchRun to a document source;
- run OCR;
- browse the live web;
- process tenant-private documents;
- schedule continuous monitoring;
- select among multiple local models;
- admit any model-produced claim.

The next integration gate is a dedicated proposal-writer database role and migration. That role may append raw objects, Evidence Objects, Candidate Claims, dossiers and admission handoff packages, but must have no `INSERT`, `UPDATE` or `DELETE` privilege on the canonical Claim Ledger.

## Rollback

Remove the document proposal route or disable its worker consumer. Preserve frozen source objects and proposal artifacts for audit. Canonical claims remain unchanged because this slice has no canonical write path.
