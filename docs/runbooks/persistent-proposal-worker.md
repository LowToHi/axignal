# Persistent proposal worker boundary

Status: `IMPLEMENTED / FEATURE-GATED / PROPOSAL-ONLY`

## Purpose

This boundary connects an authenticated tenant-scoped `ResearchRun` to the local document proposal pipeline without giving the model-facing process any capability to write canonical claims. The worker connects with a dedicated PostgreSQL login, not the application or migration credential.

```text
Navigator
→ POST /v1/research-runs/document-proposals
→ PostgreSQL ResearchRun + proposal outbox
→ dedicated Valkey proposal queue
→ axignal_proposal_worker
→ immutable document object and fragments
→ provisional Evidence Objects
→ Candidate Claims
→ traceable dossier
→ durable admission handoff
→ separate axignal_admission_runtime
```

## Database identities

### `axignal_proposal_worker`

Permitted:

- read admitted source records;
- insert immutable source objects and fragments;
- insert provisional Evidence Objects;
- insert Candidate Claims;
- insert dossiers and tenant-scoped evidence links;
- insert a durable admission-handoff package;
- update only the operational fields of the active ResearchRun;
- append audit and failure records.

Explicitly denied:

- every privilege on `axignal_global.canonical_claims`;
- every privilege on `axignal_global.claim_state_events`;
- every privilege on `axignal_global.admission_batches`;
- deployment, migration and source-policy administration.

### `axignal_admission_runtime`

This role is defined but is not invoked by this slice. It can read handoff inputs and owns the narrowly scoped future path for deterministic admission. A local or external model never receives this identity.

The existing structured deterministic worker remains unchanged until its admission path is migrated separately. The model-facing document worker never uses that legacy role.

## Job contract

```json
{
  "schema_version": 2,
  "job_kind": "DOCUMENT_PROPOSAL",
  "tenant_id": "uuid",
  "research_run_id": "uuid",
  "source_id": "world-bank-rer41",
  "document_id": "doc_world_bank_rer41",
  "pipeline_version": "local-document-proposal-pipeline@0.1.0",
  "budget": {
    "max_documents": 1,
    "max_model_calls": 1,
    "max_input_tokens": 12000,
    "max_output_tokens": 2500
  }
}
```

Structured-source jobs, document-proposal jobs and future admission-review jobs are distinct contracts and queues.

## Persistent states

```text
QUEUED
→ RETRIEVING
→ DOCUMENT_PARSING
→ SECURITY_SCANNING
→ PROPOSING
→ EVIDENCE_BINDING
→ HANDOFF_PENDING
→ COMPLETED_PROVISIONAL
```

Exceptional terminal states:

- `QUARANTINED` for document security detections;
- `FAILED` for schema, dependency, rights, routing or persistence failures.

`COMPLETED_PROVISIONAL` never means admitted truth. It means the dossier and handoff are durable and await a different authority.

## Idempotency

Stable identities are used for:

- source object: source ID plus immutable document hash;
- fragment: deterministic parser fragment ID;
- Evidence Object: deterministic evidence key;
- Candidate Claim: deterministic fingerprint;
- handoff: canonical package hash;
- dossier: one dossier per ResearchRun.

A duplicate queue delivery must preserve the same artifact counts and create no canonical claim.

## Configuration

Required for the frozen worker:

```dotenv
AXIGNAL_PERSISTENT_RESEARCH_ENABLED=true
AXIGNAL_DATABASE_URL=postgresql://axignal:...@localhost:5432/axignal
AXIGNAL_PROPOSAL_DATABASE_URL=postgresql://axignal_proposal_worker:...@localhost:5432/axignal
AXIGNAL_VALKEY_URL=redis://...
AXIGNAL_PROPOSAL_QUEUE_KEY=axignal:proposal:queue:v1
AXIGNAL_DOCUMENT_FIXTURE_PATH=apps/api/tests/fixtures/world_bank_rer41_document.json
AXIGNAL_DOCUMENT_PROPOSAL_FIXTURE_PATH=apps/api/tests/fixtures/world_bank_rer41_proposal.json
```

Optional local endpoint:

```dotenv
AXIGNAL_LOCAL_MODEL_BASE_URL=http://127.0.0.1:8001
AXIGNAL_LOCAL_MODEL_NAME=qwen-local
AXIGNAL_LOCAL_MODEL_API_KEY=local-only
```

When a local endpoint is configured, the frozen proposal fixture is not used. The authority boundary remains identical.

To route Navigator through the document path:

```dotenv
AXIGNAL_DOCUMENT_PROPOSAL_UI_ENABLED=true
```

The feature remains off by default.

## Processes

API:

```bash
uvicorn axignal_api.application:app --host 0.0.0.0 --port 8000
```

Outbox publisher, isolated from model execution:

```bash
python -m axignal_api.proposal_publisher
```

Proposal worker, configured only with the proposal DSN and Valkey:

```bash
python -m axignal_api.proposal_worker
```

Single acceptance iteration:

```bash
python -m axignal_api.proposal_worker --once
```

## Acceptance

```bash
python scripts/verify_persistent_proposal_worker.py
```

The verifier proves:

- authenticated creation and queue delivery;
- tenant RLS isolation;
- durable raw document and two fragments;
- two Evidence Objects and two Candidate Claims;
- one provisional dossier and one pending handoff;
- zero canonical claims;
- direct canonical insertion under `axignal_proposal_worker` fails with insufficient privilege;
- duplicate delivery is idempotent.

## Rollback

1. Disable `AXIGNAL_DOCUMENT_PROPOSAL_UI_ENABLED`.
2. Stop the proposal publisher and proposal worker.
3. Pause or purge only the proposal queue.
4. Mark pending proposal outbox records failed or retain them for replay.
5. Preserve raw documents, fragments, Candidate Claims, dossiers and handoffs for audit.
6. Leave the canonical Claim Ledger unchanged.

## Credential boundary

The API and outbox publisher use `AXIGNAL_DATABASE_URL`. The model-facing worker must not receive that variable in production; it uses only `AXIGNAL_PROPOSAL_DATABASE_URL`. The local Docker migration installs a development password for repeatable CI. Production provisioning must rotate it before enabling the feature.
