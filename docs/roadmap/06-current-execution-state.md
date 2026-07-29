# 06 — AXIGNAL Current Execution State

Version: `0.8.2`
Status: `PUBLIC LANDING DEPLOYED / F8 WEDGE SELECTED / TED XML PARSER EVIDENCE READY`
Goal ID: `AXIGNAL-GOAL-001`
Canonical baseline: `main@ecba05dd18f62be0d5aaf558e994df0d28aea454`

## Reading rule

This document records the evidence-backed implementation state. A phase is not `PASSED` merely because code exists: its complete contractual gate, external validation and operational dependencies must also be accepted.

A deployed public landing is not evidence that the authenticated product, private pilot, source universe, billing or general availability has passed.

## Current phase state

| Phase | State | Evidence-backed interpretation |
|---|---|---|
| F0 — Goal and contracts | `GATE_REVIEW` | Goal Lock, contracts, ADRs, schemas and registries are integrated. ADR-012 records the first-universe wedge and AX-F8-T11 records its first XML parser profile. Final cross-contract review and map freeze remain. |
| F1 — UX architecture and validation | `GATE_REVIEW` | Investigation Shell, Navigator, lens switch, Timeline and Claim/Evidence Rail are executable; the public Globe landing is deployed. Qualified-user thresholds, control comparison, multilingual equivalence and accessibility acceptance remain unproven. |
| F2 — Reproducible repository spine | `GATE_REVIEW` | Runtime spine, CI, migration replay, restore evidence and the reproducible public landing release are integrated. Formal phase acceptance, restricted deploy identity, product SLOs and private-pilot acceptance remain separate gates. |
| F3 — Epistemic kernel | `IN_PROGRESS` | A bounded macro profile reaches the append-only Claim Ledger through independent deterministic admission and bounded human review. Procurement XML now produces deterministic Candidate Claims, but the procurement admission policy remains disabled. |
| F4 — Navigator and InvestigationContext | `IN_PROGRESS` | Authenticated ResearchRuns return evidence, proposals, admitted claims, human-review context and dossiers. Procurement commands and live procurement ResearchRuns are not implemented. |
| F5 — Globe, Graph and Timeline parity | `IN_PROGRESS` | Product shell and canonical browser workflow exist; procurement data layers, full parity, accessibility alternatives, performance budgets and user validation remain. |
| F6 — Multilingual semantic system | `LOCKED` | eForms source-language values are preserved by the parser, but AXIGNAL's canonical multilingual data and QA system is not implemented. |
| F7 — Intent Intelligence and Knowledge Tides | `LOCKED` | Privacy-thresholded operational aggregation is not implemented. |
| F8 — First lawful opportunity universe | `IN_PROGRESS` | European Public Procurement Intelligence is selected at 96/100. The six-block ontology, bounded Search API connector and SDK 1.14 ContractNotice subtype 16 XML parser are evidence-ready. TED remains `TECHNICAL_PROBE`, `NOT_PRODUCT_ADMITTED`; policy, runtime and public support remain disabled. |
| F9 — Paid design-partner product | `LOCKED` | Production organisations, entitlements, billing, onboarding and paying procurement design partners are absent. |
| F10 — Scenarios, calibration and outcomes | `LOCKED` | Requires admitted historical universe data and commercial usage. |
| F11 — Enterprise, API and private data | `LOCKED` | Tenant RLS is foundational evidence, not an accepted enterprise product. |
| F12 — General availability | `LOCKED` | The public landing is live, but product SLO, disaster recovery, retention, private-pilot acceptance and operating-economics gates have not passed. |

## Implemented governed vertical slice

```text
bounded authenticated identity
→ Navigator
→ persistent ResearchRun
→ PostgreSQL RLS + transactional outbox
→ Valkey worker queues
→ admitted source or immutable document
→ Evidence Objects
→ Candidate Claims
→ proposal-only model worker
→ deterministic admission
→ atomic Claim Ledger write or bounded escalation
→ human review with append-only events and no canonical authority
→ dossier and InvestigationContext
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

## First-universe state

```text
seven candidates scored
→ European Public Procurement Intelligence selected
→ eForms six-block ontology defined
→ TED source registered as TECHNICAL_PROBE
→ fixed non-personal Search API connector implemented
→ official live Search API probe: PASS
→ eForms SDK 1.14 ContractNotice subtype 16 parser implemented
→ official pinned SDK XML example: PASS
→ deterministic non-personal Candidate Claims produced
→ procurement admission policy remains disabled
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

Current exact boundaries:

```json
{
  "selected_universe": "eu_public_procurement",
  "selection_state": "ACCEPTED",
  "ontology_state": "ACCEPTED",
  "source_state": "TECHNICAL_PROBE",
  "source_product_admitted": false,
  "search_connector_state": "EVIDENCE_READY",
  "xml_parser_profile": "ted-eforms-cn16@0.1.0",
  "xml_parser_state": "EVIDENCE_READY",
  "connector_runtime_enabled": false,
  "claim_policy_state": "DISABLED_PENDING_PRODUCT_ADMISSION_AND_XML_PARSER",
  "canonical_procurement_claims": 0,
  "universe_supported": false,
  "public_marketing_authorised": false
}
```

## Demonstrated invariants

- models and human reviewers cannot write canonical state directly;
- proposal, admission, reviewer and scheduler processes use separate PostgreSQL credentials;
- source, rights, hash, scope, value, unit and period gates fail closed;
- tenant isolation is enforced by RLS;
- queue and scheduling replay are idempotent;
- canonical, review and scheduler histories are append-only;
- failpoints roll back related mutations atomically;
- object-store tampering is rejected;
- prohibited telemetry fields are redacted;
- public landing deployment is exact-SHA, TLS-verified and rollback-protected;
- procurement selection does not imply source or universe admission;
- missing procurement fields remain unknown instead of becoming zero or negative evidence;
- the TED Search connector requests no personal contact fields and remains disabled by default;
- the XML parser rejects unknown SDK, UBL, document, notice type and subtype profiles;
- DTD, entity and oversized XML inputs fail closed;
- official personal contact elements are counted but their values are not emitted;
- Candidate Claim fingerprints are deterministic and unique;
- XML parsing performs zero model calls and zero canonical writes.

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

All subsequent development MUST branch from current `main`. Superseded branches are audit history, not execution bases.

## Active gaps before phase acceptance

### F0–F2

- final cross-contract inconsistency review;
- formal F0/F1/F2 gate decisions;
- restricted `axignal-deploy` identity instead of root SSH;
- private-pilot deployment and independent acceptance;
- product SLO, recovery and incident ownership.

### F1

- execute qualified-user controlled sessions;
- authority-layer and evidence-traceability comprehension;
- multilingual and accessibility acceptance;
- final visual-system gate.

### F3–F5

- run independent deterministic procurement admission over frozen parser outputs;
- prove rollback and idempotent replay with zero model or reviewer canonical authority;
- implement notice correction, cancellation, award and expiry propagation;
- complete Globe/Graph/Timeline parity after real-user evidence.

### F8

- define XSD and applicable Schematron validation strategy;
- validate a live TED notice XML retrieval path without persisting raw or personal values in CI;
- measure field completeness by notice subtype, country and period;
- prove notice correction, cancellation and award lineage;
- complete source-specific privacy and attribution review;
- keep `PRODUCT_ADMITTED` blocked until every source gate passes;
- implement a real procurement ResearchRun only after source and policy activation evidence;
- validate buyer workflow, willingness to pay and operating cost.

## Only authorised next priority

> Feed frozen, version-pinned XML parser outputs into the independent deterministic admission runtime. Prove policy decisions, idempotent replay, rollback after a forced post-insert failure, append-only lineage and zero model or reviewer canonical authority before any live procurement ResearchRun or UI integration.

OCR, unrestricted browsing, national-portal scraping, simultaneous universe expansion, billing, new model authority and public procurement-support claims remain unauthorised until their dependencies pass.
