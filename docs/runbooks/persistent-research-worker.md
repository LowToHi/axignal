# Persistent Research Worker runbook

Status: `IMPLEMENTATION CANDIDATE / PRODUCTION DISABLED`
Goal ID: `AXIGNAL-GOAL-001`

## Architecture

```text
POST /v1/research-runs
→ tenant-private ResearchRun + transactional outbox
→ outbox publisher
→ Valkey queue
→ Research Worker
→ admitted institutional connector
→ immutable Source Object
→ Evidence Object
→ Candidate Claim
→ deterministic admission runtime
→ Canonical Claim Ledger or rejection
→ tenant-private dossier
→ ResearchRun completion event
```

The API does not perform source retrieval inside the request transaction. A queue outage leaves the outbox event pending and does not lose the ResearchRun.

## Required services

- PostgreSQL with PostGIS, pgvector and pgcrypto;
- Valkey;
- FastAPI application assembled as `axignal_api.application:app`;
- one or more `axignal_api.worker` processes.

## Environment

```bash
export AXIGNAL_DATABASE_URL='postgresql://axignal:axignal@127.0.0.1:5432/axignal'
export AXIGNAL_VALKEY_URL='redis://127.0.0.1:6379/0'
export AXIGNAL_PERSISTENT_RESEARCH_ENABLED='true'
export AXIGNAL_RESEARCH_QUEUE_KEY='axignal:research:queue:v1'
```

For deterministic local and CI verification:

```bash
export AXIGNAL_LIVE_SOURCES_ENABLED='false'
export AXIGNAL_WORLD_BANK_FIXTURE_PATH='apps/api/tests/fixtures/world_bank_rus_inflation.json'
```

For an authorised live smoke run only:

```bash
export AXIGNAL_LIVE_SOURCES_ENABLED='true'
unset AXIGNAL_WORLD_BANK_FIXTURE_PATH
```

Live mode does not broaden the source contract. It still permits only the exact World Bank host, path, indicator, country, response type and resource budget.

## Start locally

```bash
docker compose up --build --detach --wait
python -m uvicorn axignal_api.application:app --app-dir apps/api/src --reload --port 8000
python -m axignal_api.worker --poll-seconds 2
```

Create a ResearchRun using a temporary development tenant identifier:

```bash
curl -sS -X POST 'http://127.0.0.1:8000/v1/research-runs' \
  -H 'content-type: application/json' \
  -H 'X-AXIGNAL-Tenant-ID: 11111111-1111-4111-8111-111111111111' \
  -d '{
    "context_id": "ctx_moscow_real_estate_v01",
    "opportunity_id": "opp_moscow_ramenki",
    "question": "Actualiza el contexto de inflación de la oportunidad.",
    "include_private_knowledge": false
  }'
```

The tenant header is a development boundary only. Production exposure remains prohibited until authenticated identity maps server-side to a tenant and the client cannot choose an arbitrary tenant UUID.

## One-shot acceptance

```bash
python scripts/verify_persistent_research_spine.py
```

The acceptance script proves:

- three PostgreSQL schemas exist;
- World Bank is admitted and Bank of Russia is quarantined;
- RLS and FORCE RLS are active;
- tenant A cannot be read by tenant B;
- the outbox reaches Valkey;
- the worker is idempotent;
- no language-model call is used for the structured indicator;
- one Evidence Object and one Candidate Claim are persisted;
- deterministic gates admit the exact observed fact;
- the Claim Ledger rejects in-place mutation;
- attribution is present in the dossier;
- Intent Intelligence remains separate and does not create claims.

## Operational states

```text
QUEUED
→ RETRIEVING
→ PROPOSING
→ ADMISSION_PENDING
→ COMPLETED | FAILED
```

A failed run retains `error_code` and `error_detail`. Workers must not substitute a source, increase budgets or remove attribution in response to a failure.

## Local model boundary

The Research Worker is the execution process; it is not synonymous with a language model.

For structured World Bank data, the worker uses a deterministic parser. A future local model adapter may propose Candidate Claims from unstructured admitted evidence, but:

- its output must validate against the Candidate Claim schema;
- its producer type must be `LOCAL_MODEL`;
- it cannot auto-admit an observed fact;
- it cannot write to `canonical_claims`;
- it cannot use tenant-private content for a global proposal;
- the deterministic runtime retains sole admission authority.

## Metrics and alerts

Required metrics before production:

- queued ResearchRuns;
- oldest pending outbox age;
- queue depth;
- worker completion and failure count;
- source latency and response size;
- source kill-switch state;
- candidate admission/rejection counts;
- duplicate deliveries;
- RLS denial count;
- canonical claim mutation attempts;
- attribution omissions.

Alert immediately when:

- a source kill switch changes;
- outbox age exceeds five minutes;
- the queue is unavailable;
- a source leaves its allowlist;
- response size exceeds the contract;
- a generative producer reaches automatic admission;
- a cross-tenant query returns data;
- an immutable ledger mutation is attempted.

## Rollback

1. Set `AXIGNAL_PERSISTENT_RESEARCH_ENABLED=false`.
2. Stop the worker.
3. Leave pending outbox and ResearchRun rows intact for audit.
4. Set the source kill switch to `true` if source behaviour or rights are involved.
5. Revert the API route and worker code if needed.
6. Do not delete Source Objects, Evidence Objects, admission decisions or canonical ledger rows.
7. The synthetic PR #14 ResearchRun remains the UI fallback until the persistent client path is accepted.
