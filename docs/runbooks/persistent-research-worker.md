# Authenticated persistent ResearchRun runbook

Status: `IMPLEMENTATION CANDIDATE / PRODUCTION DISABLED`
Goal ID: `AXIGNAL-GOAL-001`

## Architecture

```text
browser credentials
→ Next.js verifies scrypt password
→ HttpOnly signed session (subject + email; no tenant)
→ server resolves subject → tenant UUID
→ short-lived HMAC identity assertion
→ FastAPI verifies identity assertion
→ POST /v1/research-runs
→ tenant-private ResearchRun + transactional outbox
→ Valkey queue
→ Research Worker
→ admitted institutional connector
→ immutable Source Object + Evidence Object
→ Candidate Claim
→ deterministic admission runtime
→ Canonical Claim Ledger or rejection
→ tenant-private dossier
→ polling returns dossier, evidence and claims
→ InvestigationContext integrates persistent results
```

The browser cannot send or select a tenant UUID. The legacy `X-AXIGNAL-Tenant-ID` header has no authority and is rejected when no valid identity assertion is present.

The API does not retrieve sources inside the request transaction. A queue outage leaves the outbox event pending and does not lose the ResearchRun.

## Required services

- PostgreSQL with PostGIS, pgvector and pgcrypto;
- Valkey;
- FastAPI assembled as `axignal_api.application:app`;
- one or more `axignal_api.worker` processes;
- Next.js as the authenticated same-origin gateway.

## Environment

```bash
export AXIGNAL_API_URL='http://127.0.0.1:8000'
export AXIGNAL_DATABASE_URL='postgresql://axignal:axignal@127.0.0.1:5432/axignal'
export AXIGNAL_VALKEY_URL='redis://127.0.0.1:6379/0'
export AXIGNAL_PERSISTENT_RESEARCH_ENABLED='true'
export AXIGNAL_PERSISTENT_RESEARCH_UI_ENABLED='true'
export AXIGNAL_RESEARCH_QUEUE_KEY='axignal:research:queue:v1'

export AXIGNAL_AUTH_REQUIRED='true'
export AXIGNAL_AUTH_EMAIL='operator@example.com'
export AXIGNAL_AUTH_SUBJECT='usr_operator'
export AXIGNAL_AUTH_TENANT_ID='11111111-1111-4111-8111-111111111111'
export AXIGNAL_SESSION_SECRET='<at-least-32-random-bytes>'
export AXIGNAL_IDENTITY_ASSERTION_SECRET='<different-at-least-32-random-bytes>'
```

Generate the password verifier locally:

```bash
node scripts/generate_auth_password.mjs 'a-long-local-password'
export AXIGNAL_AUTH_PASSWORD_SCRYPT='scrypt$<salt-hex>$<derived-key-hex>'
```

The session cookie contains only the authenticated subject and email. `AXIGNAL_AUTH_TENANT_ID` is read on the server after session verification. The API receives a signed assertion with a maximum lifetime of five minutes; the Next.js gateway currently emits assertions with a 60-second lifetime.

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
pnpm --filter @axignal/web dev
```

Open `http://127.0.0.1:3000`, authenticate, select the opportunity and use **Investigar oportunidad**. The same-origin route creates the persistent ResearchRun, polls its state and returns the worker output to the existing `InvestigationContext`.

## Fixture-to-persistent switchover

- `AXIGNAL_PERSISTENT_RESEARCH_UI_ENABLED=false`: the bounded PR #14 synthetic ResearchRun remains active;
- `AXIGNAL_PERSISTENT_RESEARCH_UI_ENABLED=true`: authentication becomes mandatory and the UI uses only the persistent API path;
- a persistent failure is shown as a failure and never silently replaced with the fixture;
- the base opportunity shell remains synthetic while real evidence, admitted claims and dossiers are integrated incrementally.

This is the deliberate gradual replacement boundary. It avoids presenting mixed synthetic and persistent data as a fully production-backed product.

## One-shot acceptance

```bash
python scripts/verify_persistent_research_spine.py
```

The acceptance proves:

- the legacy tenant header no longer authenticates a caller;
- a signed identity creates a ResearchRun in its resolved tenant;
- tenant A cannot read tenant B;
- RLS and FORCE RLS remain active;
- the outbox reaches Valkey and the worker is idempotent;
- no language-model call is used for the structured indicator;
- evidence, Candidate Claim, canonical claim and dossier are persisted;
- deterministic admission and append-only ledger gates remain intact;
- attribution is present;
- Intent Intelligence remains separate and cannot create claims.

## Operational states

```text
QUEUED
→ RETRIEVING
→ PROPOSING
→ ADMISSION_PENDING
→ COMPLETED | FAILED
```

The browser polling adapter maps worker states into Navigator states and integrates each retrieved view into the selected ResearchRun. A failed run retains `error_code` and `error_detail`. Workers must not substitute a source, increase budgets or remove attribution in response to a failure.

## Local model boundary

The Research Worker is the execution process; it is not synonymous with a language model.

For structured World Bank data, the worker uses a deterministic parser. The next permitted extension is a local proposal model for unstructured, already admitted documents. Its output must:

- validate against the Candidate Claim schema;
- declare producer type `LOCAL_MODEL`;
- remain proposal-only;
- never write to `canonical_claims`;
- never auto-admit an observed fact;
- never use tenant-private content for a global proposal;
- pass through the deterministic admission runtime, which retains sole authority.

## Remaining production gates

- replace the single configured identity mapping with an external OIDC provider and durable membership registry;
- rotate and store secrets in a managed secret store;
- add rate limiting, session revocation and security-event audit;
- supervise workers and outbox publisher as deployed services;
- expose queue, latency, completion, failure, RLS denial and assertion rejection metrics;
- rehearse migration and rollback in a non-production environment;
- obtain explicit human merge and deployment authorisation.

## Rollback

1. Set `AXIGNAL_PERSISTENT_RESEARCH_UI_ENABLED=false` to return the UI to the bounded fixture.
2. Set `AXIGNAL_PERSISTENT_RESEARCH_ENABLED=false` to stop new persistent creation.
3. Stop the worker.
4. Preserve pending outbox, ResearchRun, Source Object, Evidence Object, admission decision and ledger rows for audit.
5. Enable the source kill switch if source behaviour or rights are implicated.
6. Do not re-enable `X-AXIGNAL-Tenant-ID` as an authentication boundary.
