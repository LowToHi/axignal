# 06 — AXIGNAL Current Execution State

Version: `0.6.1`
Status: `CONSOLIDATED BASELINE MERGED`
Goal ID: `AXIGNAL-GOAL-001`
Canonical baseline: `main@cf83781766f12ebc55eeb9829d68d41e77500aa7`

## Reading rule

This document records the evidence-backed implementation state. A phase is not `PASSED` merely because code exists: its complete contractual gate, external validation and operational dependencies must also pass.

## Current phase state

| Phase | State | Evidence-backed interpretation |
|---|---|---|
| F0 — Goal and contracts | `GATE_REVIEW` | Goal Lock, contracts `00–27`, ADRs, schemas, task/skill registries and fail-closed validation are integrated into `main`. Final cross-contract review and map freeze remain. |
| F1 — UX architecture and validation | `GATE_REVIEW` | Investigation Shell v0.2, Navigator, lens switch, Timeline and Claim/Evidence Rail are executable. Qualified-user thresholds, control comparison and multilingual equivalence remain unproven. |
| F2 — Reproducible repository spine | `EVIDENCE_READY` | The cumulative baseline, clean-clone CI, PostgreSQL/Valkey integration, migrations, snapshot restore, API, builds and Playwright are merged. A final F2 deliverable-gap review remains before declaring the phase passed. |
| F3 — Epistemic kernel | `IN_PROGRESS` | One bounded end-to-end profile reaches an append-only Claim Ledger through independent deterministic admission. General entity, contradiction, correction, expiry and multi-profile coverage remain. |
| F4 — Navigator and InvestigationContext | `IN_PROGRESS` | Authenticated persistent ResearchRuns return evidence, proposals, admitted claims and dossiers to one InvestigationContext. Full multilingual command equivalence, previews, entitlements and general undo remain. |
| F5 — Globe, Graph and Timeline parity | `IN_PROGRESS` | Product shell and canonical browser workflow exist; complete functional parity, accessibility alternatives, performance budgets and user gate remain. |
| F6 — Multilingual semantic system | `LOCKED` | Contracts exist; the canonical multilingual data and QA system is not implemented. |
| F7 — Intent Intelligence and Knowledge Tides | `LOCKED` | Schemas and isolated knowledge-domain foundations exist; privacy-thresholded operational aggregation is not implemented. |
| F8 — First lawful opportunity universe | `LOCKED` | World Bank sources prove ingestion and rights gates but do not constitute a commercially admitted opportunity universe. |
| F9 — Paid design-partner product | `LOCKED` | Production organisations, entitlements, billing, onboarding and paying design partners are absent. |
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
→ admitted structured source or immutable document
→ Evidence Objects
→ Candidate Claims
→ proposal-only model worker
→ durable admission handoff
→ independent deterministic rederivation
→ atomic Claim Ledger write or bounded escalation
→ dossier and InvestigationContext
```

Demonstrated invariants:

- a model cannot write canonical state;
- proposal and admission processes use separate PostgreSQL credentials;
- source, rights, hash, scope, value, unit and period gates fail closed;
- tenant isolation is enforced by RLS;
- queue replay is idempotent;
- canonical writes and state events are append-only;
- a failpoint inside admission rolls back every related mutation;
- `HUMAN_REVIEW_REQUIRED` remains outside the canonical ledger.

## Consolidation debt — resolved

The previous implementation was distributed across stacked draft PRs. The debt was closed through PR #21 and canonical squash commit `cf83781766f12ebc55eeb9829d68d41e77500aa7`.

Completed gates:

1. current `main` lineage incorporated;
2. one cumulative PR reviewed against `main`;
3. canonical naming, contracts, schemas and OpenAPI validated;
4. API, TypeScript, builds and browser workflow passed;
5. PostgreSQL, Valkey and controlled live-source smoke passed;
6. cumulative migrations `025`, `030` and `035` applied and replayed over seeded prior-state data;
7. pre-migration snapshot restored into a clean database;
8. proposal/admission credential boundaries reverified;
9. PRs #5, #9 and #11–#19 closed as superseded while retaining branches and evidence;
10. no production deployment or secret provisioning performed.

All subsequent development MUST branch from current `main`. The superseded stack is audit history, not an execution base.

## Active gaps before phase acceptance

### F0

- final cross-contract inconsistency review;
- freeze current execution-state authority and map precedence;
- decide final retention policy for superseded branches.

### F1

- qualified-user testing against declared thresholds;
- comparison with a control direction;
- multilingual and accessibility acceptance;
- final visual-system gate.

### F2

- complete the final deliverable-gap review against the normative phase map;
- explicitly resolve any missing scheduler, object-storage-interface or OpenTelemetry baseline requirement;
- decide production deployment topology separately.

### F3–F5

- bounded human-review workflow;
- additional deterministic claim profiles and contradiction lifecycle;
- source/entity expansion only through independent gates;
- complete Globe/Graph/Timeline parity and user validation.

## Only authorised next priority

> Implement the bounded human-review path for `HUMAN_REVIEW_REQUIRED` and `CONTESTED`, preserving reviewer identity, reason codes, append-only history and non-bypassable integrity gates. Then return to the F1 qualified-user gate.

OCR, unrestricted browsing, broad source expansion, continuous production workers, billing and production deployment remain unauthorised until their dependencies pass.
