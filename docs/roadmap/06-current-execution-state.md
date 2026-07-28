# 06 — AXIGNAL Current Execution State

Version: `0.7.0`
Status: `F2 INTEGRATED / F1 VALIDATION AUTHORISED`
Goal ID: `AXIGNAL-GOAL-001`
Canonical baseline: `main@15a232249736658dbe05a67d1f2541384848f5b3`

## Reading rule

This document records the evidence-backed implementation state. A phase is not `PASSED` merely because code exists: its complete contractual gate, external validation and operational dependencies must also be accepted.

## Current phase state

| Phase | State | Evidence-backed interpretation |
|---|---|---|
| F0 — Goal and contracts | `GATE_REVIEW` | Goal Lock, contracts, ADRs, schemas and registries are integrated. Final cross-contract review and map freeze remain. |
| F1 — UX architecture and validation | `GATE_REVIEW` | Investigation Shell, Navigator, lens switch, Timeline and Claim/Evidence Rail are executable. Qualified-user thresholds, control comparison, multilingual equivalence and accessibility acceptance remain unproven. |
| F2 — Reproducible repository spine | `GATE_REVIEW` | Scheduler, content-addressed object storage, OpenTelemetry baseline, explicit runtime topology, migration replay, snapshot restore and clean-clone CI are integrated through PR #24. Formal phase acceptance remains a separate gate decision. |
| F3 — Epistemic kernel | `IN_PROGRESS` | A bounded profile reaches the append-only Claim Ledger through independent deterministic admission and bounded human review. General entity, contradiction, correction, expiry and multi-profile coverage remain. |
| F4 — Navigator and InvestigationContext | `IN_PROGRESS` | Authenticated ResearchRuns return evidence, proposals, admitted claims, human-review context and dossiers. Full multilingual command equivalence, previews, entitlements and general undo remain. |
| F5 — Globe, Graph and Timeline parity | `IN_PROGRESS` | Product shell and canonical browser workflow exist; full parity, accessibility alternatives, performance budgets and user validation remain. |
| F6 — Multilingual semantic system | `LOCKED` | Contracts exist; the canonical multilingual data and QA system is not implemented. |
| F7 — Intent Intelligence and Knowledge Tides | `LOCKED` | Privacy-thresholded operational aggregation is not implemented. |
| F8 — First lawful opportunity universe | `LOCKED` | Current institutional fixtures prove ingestion and rights gates but do not form a commercial universe. |
| F9 — Paid design-partner product | `LOCKED` | Production organisations, entitlements, billing, onboarding and paying partners are absent. |
| F10 — Scenarios, calibration and outcomes | `LOCKED` | Requires admitted historical universe data and commercial usage. |
| F11 — Enterprise, API and private data | `LOCKED` | Tenant RLS is foundational evidence, not an accepted enterprise product. |
| F12 — General availability | `LOCKED` | No production deployment, SLO, disaster recovery, retention or operating-economics gate has passed. |

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

The supporting runtime spine now includes:

```text
persistent scheduler
→ lease-bound jobs
→ deduplicated outbox delivery
→ retry / dead-letter / lease recovery
→ content-addressed object storage
→ trace-context propagation and telemetry redaction
→ machine-readable non-production topology
```

## Demonstrated invariants

- models and human reviewers cannot write canonical state directly;
- proposal, admission, reviewer and scheduler processes use separate PostgreSQL credentials;
- source, rights, hash, scope, value, unit and period gates fail closed;
- tenant isolation is enforced by RLS;
- queue and scheduling replay are idempotent;
- canonical, review and scheduler histories are append-only;
- failpoints roll back related mutations atomically;
- expired scheduler leases recover without duplicate logical jobs;
- object-store tampering is rejected;
- prohibited telemetry fields are redacted;
- production deployment remains disabled.

## Integrated baselines

| Unit | PR | Canonical squash commit |
|---|---:|---|
| Consolidated executable baseline | #21 | `cf83781766f12ebc55eeb9829d68d41e77500aa7` |
| Governance closure | #22 | `cb2c966d36207e908a19dd5381f9179d3c6fa406` |
| Bounded human review | #23 | `76ca919fea0d5740e80729aa7f9332f6aa6c5857` |
| F2 reproducible runtime closure | #24 | `15a232249736658dbe05a67d1f2541384848f5b3` |

All subsequent development MUST branch from current `main`. Superseded branches are audit history, not execution bases.

## Active gaps before phase acceptance

### F0

- final cross-contract inconsistency review;
- freeze execution-state authority and map precedence;
- decide retention policy for superseded branches.

### F1

- qualified-user testing against frozen thresholds;
- AXIGNAL-versus-control comparison using equivalent content;
- authority-layer and evidence-traceability comprehension;
- multilingual and accessibility acceptance;
- final visual-system gate.

### F2

- formal roadmap authority decision: `PASSED` or remain `GATE_REVIEW`;
- production topology, secrets, SLOs and disaster recovery remain explicitly separate and unauthorised.

### F3–F5

- additional deterministic claim profiles and contradiction lifecycle;
- source/entity expansion only through independent gates;
- complete Globe/Graph/Timeline parity after user evidence.

## Only authorised next priority

> Build the F1 qualified-user validation harness with pseudonymised sessions, frozen tasks, deterministic AXIGNAL/control assignment, append-only interaction events, reproducible metrics and zero canonical-state authority. Then execute controlled sessions with qualified users.

OCR, unrestricted browsing, broad source expansion, billing, new model authority and production deployment remain unauthorised until their dependencies pass.
