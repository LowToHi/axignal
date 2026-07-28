# Deterministic Admission Runtime v0.1

## Purpose

This runtime consumes durable admission handoffs produced by the proposal-only document worker. It is the only process in this vertical slice allowed to create a canonical Claim Ledger record from a model-located document fragment.

The runtime never calls a model. It independently reloads the source registry, immutable raw document, deterministic fragments, Evidence Objects and Candidate Claims from PostgreSQL, validates the package hash and rederives the admissible fact from source text.

## Supported profile

Policy: `document-observed-fact@0.1.0`.

The first profile accepts only an explicit observed numeric fact with:

- source `world-bank-rer41`;
- subject `geo_country_rus`;
- predicate `real_gdp_growth_annual_pct`;
- unit `percent_annual`;
- an explicit numeric value and year in one immutable fragment;
- current admitted source and rights state;
- exact equality between proposed and independently rederived value, unit and period.

`LIMITATION`, `FORECAST`, `PREDICTION`, `INFERENCE`, causal or local-market claims are not auto-admissible. They remain proposal records and are marked `HUMAN_REVIEW_REQUIRED` or `CONTESTED`.

## Authority separation

The runtime process receives only:

```dotenv
AXIGNAL_ADMISSION_DATABASE_URL=postgresql://axignal_admission_runtime_login:.../axignal
AXIGNAL_VALKEY_URL=redis://...
AXIGNAL_ADMISSION_QUEUE_KEY=axignal:admission:queue:v1
```

It must not receive `AXIGNAL_DATABASE_URL`, `AXIGNAL_PROPOSAL_DATABASE_URL`, model credentials, source credentials or deployment credentials.

The admission credential may:

- read source, raw-object, fragment, evidence, candidate and handoff records;
- create admission batches, decisions, canonical claims and immutable claim-state events;
- update only candidate admission state, handoff disposition, ResearchRun result fields and dossier status.

It may not insert, update or delete sources, raw objects, fragments or Evidence Objects.

## Flow

```text
admission_handoff INSERT
→ security-definer outbox trigger
→ admission.handoff.requested
→ trusted outbox publisher
→ axignal:admission:queue:v1
→ deterministic admission runtime
→ package/hash/source/rights/integrity gates
→ deterministic value-unit-period rederivation
→ one PostgreSQL transaction
→ decision + canonical claim or escalation
```

## Atomic transaction

A successful transaction performs:

1. lock the pending handoff and tenant ResearchRun;
2. create one pending admission batch;
3. create one durable decision per Candidate Claim;
4. insert a canonical claim only for a rederived admissible fact;
5. append a claim-state event for a newly created canonical claim;
6. link the original model proposal to the canonical claim without changing its producer metadata;
7. mark unsupported candidates for human review;
8. decide the batch and consume the handoff;
9. update ResearchRun canonical IDs and dossier status;
10. commit.

Any exception rolls back the whole transaction. The acceptance verifier introduces a failpoint after canonical insertion and requires zero surviving partial artifacts.

## Fail-closed outcomes

- package or immutable-record mismatch: `QUARANTINED`;
- source, rights or kill-switch policy failure: `REJECTED` / failed ResearchRun;
- unsupported epistemic class: `HUMAN_REVIEW_REQUIRED`;
- adverse evidence against the same semantics: `CONTESTED`;
- value, unit or period mismatch: `REJECTED`;
- equivalent existing canonical fingerprint: `DUPLICATE` and link to the existing claim;
- repeated delivery of a consumed handoff: idempotent replay.

## Start commands

One job:

```bash
python -m axignal_api.admission_runtime --once
```

Persistent worker:

```bash
python -m axignal_api.admission_runtime --poll-seconds 2
```

## Required acceptance evidence

```bash
python scripts/verify_deterministic_admission_runtime.py
```

The verifier proves:

- dedicated admission credential and denied Evidence Object mutation;
- transactional rollback with no partial ledger state;
- one rederived observed fact admitted;
- one limitation escalated to human review;
- model producer metadata preserved;
- zero model calls in admission;
- cross-tenant read denied;
- replay idempotent;
- tampered package quarantined;
- canonical claim admitted only by `DETERMINISTIC_RUNTIME`.

## Kill and rollback

1. stop the admission runtime process;
2. stop the admission outbox publisher;
3. purge or retain the Valkey admission queue according to incident policy;
4. preserve handoffs, decisions, batches, failures and ledger events for audit;
5. do not delete or rewrite admitted Claim Ledger rows;
6. disable the source kill switch only after a source review, never as an incident shortcut.

## Explicit exclusions

- no inference, prediction, causal or investment recommendation admission;
- no model-assisted admission;
- no OCR;
- no multiple-document synthesis;
- no human-review UI or reviewer identity workflow;
- no continuous scheduling or production deployment.
