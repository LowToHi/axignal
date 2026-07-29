# 06 — AXIGNAL Current Execution State

Version: `0.8.3`
Status: `PUBLIC LANDING DEPLOYED / AX-F8-T14 ACCEPTED / BOUNDED TED PRIVATE-PILOT RUNTIME`
Goal ID: `AXIGNAL-GOAL-001`
Canonical candidate: `PR #50 / agent/ax-f8-t14-ted-persistent-runtime`

## Reading rule

This document records the evidence-backed implementation state. A phase is not
`PASSED` merely because code exists: its complete contractual gate, external
validation and operational dependencies must also be accepted.

A deployed public landing is not evidence that the authenticated product,
private pilot, source universe, billing or general availability has passed.
Likewise, acceptance of one bounded source profile does not admit arbitrary TED
queries, full eForms semantics, another jurisdiction or worldwide coverage.

## Current phase state

| Phase | State | Evidence-backed interpretation |
|---|---|---|
| F0 — Goal and contracts | `GATE_REVIEW` | Goal Lock, contracts, ADRs, schemas and registries are integrated. Final cross-contract review and map freeze remain. |
| F1 — UX architecture and validation | `GATE_REVIEW` | Investigation Shell, Navigator, lens switch, Timeline and Claim/Evidence Rail are executable; the public Globe landing is deployed. Qualified-user controlled sessions, multilingual equivalence and accessibility acceptance remain separate gates. |
| F2 — Reproducible repository spine | `GATE_REVIEW` | Runtime spine, CI, migration replay, restore evidence and the reproducible public landing release are integrated. Formal phase acceptance, restricted deploy identity, product SLOs and private-pilot operational acceptance remain. |
| F3 — Epistemic kernel | `IN_PROGRESS` | A bounded macro profile and the accepted TED Search projection reach the append-only Claim Ledger through deterministic admission. The full XML procurement policy remains disabled. |
| F4 — Navigator and InvestigationContext | `IN_PROGRESS` | Authenticated ResearchRuns return evidence, proposals, admitted claims, human-review context and dossiers. The bounded TED Search profile is wired to Navigator; broader procurement commands remain outside the admitted profile. |
| F5 — Globe, Graph and Timeline parity | `IN_PROGRESS` | Product shell and canonical browser workflow exist; full procurement data layers, accessibility alternatives, performance budgets and user validation remain. |
| F6 — Multilingual semantic system | `LOCKED` | eForms source-language values are preserved by the parser, but AXIGNAL's canonical multilingual data and QA system is not implemented. |
| F7 — Intent Intelligence and Knowledge Tides | `LOCKED` | Privacy-thresholded operational aggregation is not implemented. |
| F8 — First lawful opportunity universe | `IN_PROGRESS` | `AX-F8-T14` is `ACCEPTED`: the non-personal TED Search profile is product-admitted and enabled only for authenticated private-pilot organisations. Complete XML semantics, correction/award lineage and broader universe coverage remain unaccepted. |
| F9 — Paid design-partner product | `PROPOSED` | B2G buyer research, willingness to pay, paid evidence, trial entitlements, billing and public commercial activation remain in `AX-F9-T15`; none is implied by F8 acceptance. |
| F10 — Scenarios, calibration and outcomes | `LOCKED` | Requires admitted historical universe data and commercial usage. |
| F11 — Enterprise, API and private data | `LOCKED` | Tenant RLS is foundational evidence, not an accepted enterprise product. |
| F12 — General availability | `LOCKED` | The public landing is live, but product SLO, disaster recovery, retention, private-pilot acceptance and operating-economics gates have not passed. |

## Implemented governed vertical slice

```text
bounded authenticated identity
→ server-resolved tenant
→ Navigator
→ persistent ResearchRun
→ PostgreSQL FORCE RLS + transactional outbox
→ Valkey worker queue
→ admitted source or immutable document
→ sanitised Source Object
→ Evidence Objects
→ Candidate Claims
→ deterministic admission
→ atomic Claim Ledger write
→ attributed dossier
→ polling back into InvestigationContext
```

The supporting runtime spine includes:

```text
persistent scheduler
→ lease-bound jobs
→ deduplicated outbox delivery
→ retry / dead-letter / lease recovery
→ content-addressed object storage
→ trace-context propagation and telemetry redaction
→ machine-readable deployment topology
```

The public surface additionally includes:

```text
main exact SHA
→ immutable landing image
→ incumbent Traefik
→ TLS and external health verification
→ private append-only consent-aware intake
→ deployment evidence and rollback
```

## Accepted bounded TED runtime

`AX-F8-T14` is accepted for the following exact profile:

```text
ted-search-non-personal-projection@0.1.0
```

```text
signed short-lived identity assertion
→ tenant resolved only in server code
→ fixed TED HTTPS endpoint
→ fixed query: place-of-performance IN (LUX)
→ one page / maximum three notices
→ publication number, title, buyer name and notice type only
→ no contact or natural-person fields
→ no arbitrary query
→ no tenant-private knowledge
→ no model calls
→ deterministic admission
→ attributed dossier
```

Runtime state:

```json
{
  "task_id": "AX-F8-T14",
  "task_state": "ACCEPTED",
  "source_state": "PRODUCT_ADMITTED",
  "profile_state": "PRODUCT_ADMITTED_BOUNDED_PROFILE",
  "runtime_default": "DISABLED",
  "activation_state": "PRIVATE_PILOT_ENABLED",
  "activation_scope": "AUTHENTICATED_VERIFIED_ORGANISATIONS",
  "workflow_flag": "AXIGNAL_TED_PROCUREMENT_ENABLED",
  "live_source_flag": "AXIGNAL_TED_LIVE_SOURCES_ENABLED",
  "ui_flag": "AXIGNAL_TED_PROCUREMENT_UI_ENABLED",
  "global_live_sources_enabled": false,
  "model_calls": 0,
  "api_redistribution": false,
  "public_general_availability": false,
  "billing_enabled": false
}
```

The default remains disabled. The private-pilot Compose profile explicitly
enables only the admitted TED source path. The global live-source flag remains
false, so activation cannot silently open World Bank or another institutional
connector.

## Historical first-universe evidence

The original selection decision remains immutable audit history:

```text
seven candidates scored
→ European Public Procurement Intelligence selected
→ selection did not itself admit a source
→ fixed non-personal Search API technical probe passed
→ eForms SDK 1.14 ContractNotice subtype 16 parser became evidence-ready
→ later AX-F8-T14 source-specific admission and runtime acceptance
```

Search API technical-probe evidence from GitHub Actions run `30442505574`:

```json
{
  "returned_notice_count": 3,
  "total_notice_count": 2023,
  "missing_requested_field_counts": 0,
  "personal_contact_fields_requested": false,
  "raw_payload_persisted": false,
  "notice_values_persisted": false,
  "source_state": "TECHNICAL_PROBE",
  "product_admitted": false,
  "runtime_enabled": false
}
```

That record describes the historical probe, not the later bounded product
admission.

Pinned official eForms SDK example evidence from run `30444435253`:

```json
{
  "source_release": "1.14.2",
  "customization_id": "eforms-sdk-1.14",
  "ubl_version": "2.3",
  "document_type": "ContractNotice",
  "notice_type": "cn-standard",
  "notice_subtype": "16",
  "organisation_count": 2,
  "buyer_reference_count": 1,
  "lot_count": 1,
  "candidate_claim_count": 17,
  "unique_candidate_fingerprint_count": 17,
  "personal_field_elements_observed": 3,
  "personal_values_emitted": false,
  "raw_content_persisted": false,
  "raw_values_persisted": false,
  "model_calls": 0,
  "canonical_claim_writes": 0,
  "source_product_admitted": false,
  "runtime_enabled": false,
  "universe_supported": false
}
```

The XML parser remains evidence-ready and does not inherit the Search profile's
runtime admission.

## Demonstrated invariants

- missing, forged and expired identity assertions fail closed;
- client-supplied tenant identifiers are rejected;
- tenant identity is resolved in server code and enforced with FORCE RLS;
- models and human reviewers cannot write canonical state directly;
- proposal, admission, reviewer and scheduler processes use separate PostgreSQL credentials;
- source, rights, hash, scope, value, unit and period gates fail closed;
- queue and scheduling replay are idempotent;
- canonical, review and scheduler histories are append-only;
- failpoints roll back related mutations atomically;
- object-store tampering is rejected;
- prohibited telemetry fields are redacted;
- the TED Search connector accepts only its fixed HTTPS host, path, query and field allowlist;
- contact and personal fields are prohibited from the admitted projection;
- API redistribution, bulk redistribution and model training are prohibited;
- the workflow, live-source and database source kill switches operate independently;
- kill-switch rollback creates zero evidence, candidate, canonical or dossier residue;
- TED live activation does not enable global live sources;
- the bounded profile performs zero model calls.

## Integrated baselines

| Unit | PR | Canonical squash commit |
|---|---:|---|
| Consolidated executable baseline | #21 | `cf83781766f12ebc55eeb9829d68d41e77500aa7` |
| Governance closure | #22 | `cb2c966d36207e908a19dd5381f9179d3c6fa406` |
| Bounded human review | #23 | `76ca919fea0d5740e80729aa7f9332f6aa6c5857` |
| F2 reproducible runtime closure | #24 | `15a232249736658dbe05a67d1f2541384848f5b3` |
| Public Globe landing implementation | #34 | `4e03c5fdef40c4d269fd5daf1005a29afb90a853` |
| Public landing release system | #35 | `fbb421ba9e817c11576d87b36bd6b9b01fd2e2be` |
| Release observability and hotfixes | #36–#39 | `2c51c340cd2a7a0e0dc1db0017452e723136d77b` |
| First lawful universe selection and TED Search probe | #40 | `ecba05dd18f62be0d5aaf558e994df0d28aea454` |
| Bounded AXIGNAL AI and token policy | #49 | `a7e42db131c2e7515538ee3cbae6e48102b8cdc6` |
| Bounded TED private-pilot runtime | #50 | `CANDIDATE_PENDING_MERGE` |

All subsequent development must branch from current `main`. Superseded branches
are audit history, not execution bases.

## Active gaps before phase acceptance

### F0–F2

- final cross-contract inconsistency review;
- formal F0/F1/F2 gate decisions;
- restricted `axignal-deploy` identity instead of root SSH;
- private-pilot operational deployment and independent acceptance;
- product SLO, recovery and incident ownership.

### F1

- execute qualified-user controlled sessions;
- authority-layer and evidence-traceability comprehension;
- multilingual and accessibility acceptance;
- final visual-system gate.

### F3–F5

- complete the XML-derived deterministic procurement policy;
- implement notice correction, cancellation, award and expiry propagation;
- complete Globe/Graph/Timeline parity after real-user evidence.

### F8

- define XSD and applicable Schematron validation strategy;
- validate a live TED notice XML retrieval path without persisting raw or personal values in CI;
- measure XML field completeness by notice subtype, country and period;
- prove notice correction, cancellation and award lineage;
- keep arbitrary TED queries and non-admitted profiles blocked;
- preserve the Search profile as an independently revocable bounded capability.

### F9

- recruit and execute qualified B2G design-partner sessions;
- validate category comprehension and willingness to pay;
- obtain independent paid evidence;
- implement trial, plan, token-entitlement and billing gates;
- keep public commercial activation blocked until `AX-F9-T15` is accepted.

## Only authorised next priority

> Merge and deploy the accepted bounded TED Search runtime to the authenticated
> private pilot, then execute `AX-F9-T15` buyer and paid-design-partner validation
> without broadening source, AI or canonical authority.

OCR, unrestricted browsing, national-portal scraping, simultaneous universe
expansion, billing, new model authority and public procurement-support claims
remain unauthorised until their own dependencies pass.
