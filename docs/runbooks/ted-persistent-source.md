# TED persistent source runbook

## Runtime topology

```text
authenticated POST /v1/research-runs/procurement
→ PostgreSQL ResearchRun + retrieval outbox
→ Valkey retrieval queue
→ axignal_ted_worker
→ official direct XML notices
→ double parse + non-personal projection
→ Source Objects without raw XML
→ notice versions + Evidence Objects + Candidate Claims
→ durable admission handoff
→ procurement admission outbox
→ Valkey admission queue
→ axignal_ted_admission_runtime
→ independent redownload + rederivation
→ admission decisions + canonical Claim Ledger + dossier
→ existing GET /v1/research-runs/{id}
```

## Required configuration

```text
AXIGNAL_TED_RESEARCH_ENABLED=true
AXIGNAL_TED_DATABASE_URL=<axignal_ted_worker DSN>
AXIGNAL_TED_ADMISSION_DATABASE_URL=<axignal_ted_admission_runtime DSN>
AXIGNAL_VALKEY_URL=<private Valkey DSN>
AXIGNAL_TED_RETRIEVAL_QUEUE_KEY=axignal:ted:retrieval:queue:v1
AXIGNAL_TED_ADMISSION_QUEUE_KEY=axignal:ted:admission:queue:v1
```

Production credentials must be rotated from the deterministic development values created by migration `070`; neither process receives the application owner DSN or the other process's credential.

For CI or a frozen demonstration:

```text
AXIGNAL_TED_LIVE_SOURCES_ENABLED=false
AXIGNAL_TED_FIXTURE_MANIFEST_PATH=apps/api/tests/fixtures/ted_persistent_fixture_manifest.json
```

For a controlled live ResearchRun:

```text
AXIGNAL_TED_LIVE_SOURCES_ENABLED=true
```

## Processes

Retrieval worker:

```bash
python -m axignal_api.procurement_retrieval_runtime
```

Admission runtime:

```bash
python -m axignal_api.procurement_admission_runtime
```

Both support `--once` for acceptance tests.

## Operational gates

Before enabling the feature flag:

1. apply migration `070` twice and prove idempotence;
2. rotate both login passwords;
3. prove the retrieval worker cannot insert canonical claims;
4. prove the admission runtime cannot update Evidence Objects or source policy;
5. verify the fixture end-to-end path and forced rollback failpoints;
6. verify official SDK 1.14.2 correction and result examples;
7. verify the TED legal/privacy record and attribution text are current;
8. keep public marketing and bulk scheduling disabled.

## Data invariants

- `source_objects.raw_payload` contains a sanitised descriptor, never XML;
- `procurement_notice_versions.raw_xml_persisted=false` is a database check;
- Evidence payloads contain only admitted predicates and structurally validated values;
- excluded identity predicates never become Candidate Claims;
- the admission runtime must redownload every XML and match raw hashes;
- duplicate queue delivery converges without duplicate canonical claims;
- every ResearchRun is tenant-scoped and read through existing RLS.

## Kill switch

Immediate containment:

```sql
UPDATE axignal_global.sources
SET kill_switch = true, updated_at = now()
WHERE source_id = 'src_ted_search_api_v3';
```

Then disable `AXIGNAL_TED_RESEARCH_ENABLED`, stop both processes and quarantine pending TED handoffs. Do not delete Source Objects, Evidence Objects, decisions or ledger history.

## Rollback

Application rollback removes the procurement route and stops both processes. Schema rollback requires a verified pre-070 snapshot because migration `070` introduces roles, tables, grants and the admission-handoff router. The CI rehearsal creates and restores that snapshot and proves forced failures leave no partial Evidence or canonical state.

## Authority ceiling

The maximum runtime result is deterministic admission of the explicit non-personal observed predicate allowlist. Models and human reviewers retain zero canonical authority. Public universe support, billing and bid execution remain separate gates.
