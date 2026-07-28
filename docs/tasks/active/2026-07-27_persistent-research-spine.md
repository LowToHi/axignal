# AXIGNAL persistent ResearchRun spine

Goal ID: `AXIGNAL-GOAL-001`
Status: `EVIDENCE_READY / FAIL-CLOSED / NOT MERGED`
Base: `agent/research-run-vertical-slice-v0.1`
Head: `agent/persistent-research-spine-v0.1`
Accepted implementation head: `6d5754dff66780c837bdb27233dd9893017f146e`

## Objective

Replace the bounded ResearchRun fixture with an operational persistence and worker spine while preserving the synthetic shell as rollback.

```text
ResearchRun
+ Source Object
+ Evidence Object
+ Candidate Claim
+ dossier
+ admission batch
→ PostgreSQL

transactional outbox
→ Valkey
→ Research Worker
→ deterministic admission runtime
→ immutable Claim Ledger
```

## Knowledge domains

- `axignal_global`: admitted sources, raw Source Objects, public evidence, global Candidate Claims, admission batches and canonical claims;
- `tenant_private`: ResearchRuns, dossiers, evidence links and private knowledge protected by RLS and FORCE RLS;
- `intent_intelligence`: tenant-scoped intent events and privacy-thresholded Knowledge Tides that can only create research candidates.

## First admitted source

`world-bank-wdi`:

- World Bank Indicators API v2;
- Russian Federation;
- `FP.CPI.TOTL.ZG`;
- CC BY 4.0;
- commercial reuse and redistribution with attribution;
- exact host/path allowlist;
- one request per run;
- no secret;
- deterministic parser;
- national annual context only.

`bank-of-russia-statistics` remains `QUARANTINED / RIGHTS_PENDING / KILL_SWITCH_ON`.

## Acceptance

- [x] PostgreSQL schemas and source registry created;
- [x] tenant RLS and FORCE RLS declared;
- [x] immutable Claim Ledger declared;
- [x] transactional outbox declared;
- [x] Valkey publisher and queue implemented;
- [x] queued worker implemented;
- [x] World Bank connector implemented with live-disabled default;
- [x] deterministic observed-fact admission implemented;
- [x] persistent ResearchRun API implemented;
- [x] frozen source fixture implemented;
- [x] controlled live source smoke workflow implemented;
- [x] Ruff and API tests green at final head;
- [x] disposable PostgreSQL/Valkey acceptance green;
- [x] live World Bank source smoke green;
- [x] PR evidence comment recorded.

## Immutable evidence

- Contract Validation run `30303748966`: PASS;
- Executable Spine run `30303748961`: PASS;
- World Bank Live Source Smoke run `30303748957`: PASS;
- sanitised live-source artifact `8667595122`, digest `sha256:015f16d72a22735f93686e5a0fb21dc2162fcf24b32ce2aeec9aa57ad0654807`;
- temporary formatter workflows removed before final acceptance.

## Explicit exclusions

- no production authentication;
- no arbitrary Browser;
- no portal scraping;
- no Bank of Russia production retrieval;
- no local or external model call for the first structured source;
- no model-based automatic admission;
- no Knowledge Tide claim generation;
- no production deployment;
- no deletion of prior synthetic fixtures;
- no merge without explicit human authorisation.

## Rollback

Disable `AXIGNAL_PERSISTENT_RESEARCH_ENABLED`, stop the worker and retain all database rows for audit. The PR #14 synthetic ResearchRun remains the UI fallback. Canonical claims and claim-state events are append-only and must not be deleted during rollback.
