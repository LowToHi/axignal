# 06 — AXIGNAL Current Execution State

Version: `0.6.0`
Status: `CONSOLIDATED BASELINE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`
Baseline branch: `agent/consolidated-baseline-v0.1`

## Reading rule

This document records the evidence-backed implementation state. A phase is not `PASSED` merely because code exists: its contractual gate, external validation and operational dependencies must also pass.

## Current phase state

| Phase | State | Evidence-backed interpretation |
|---|---|---|
| F0 — Goal and contracts | `GATE_REVIEW` | Goal Lock, contracts `00–27`, ADRs, schemas, task/skill registries and fail-closed validation exist. Final consolidated review remains. |
| F1 — UX architecture and validation | `GATE_REVIEW` | Investigation Shell v0.2, Navigator, lens switch, Timeline and Claim/Evidence Rail are executable. Qualified-user thresholds and multilingual equivalence remain unproven. |
| F2 — Reproducible repository spine | `EVIDENCE_READY` | Next.js, FastAPI, PostgreSQL/PostGIS/pgvector, Valkey, migrations, clean-clone CI, tests, builds and Playwright are implemented. Consolidated-baseline CI and migration/restore rehearsal are the acceptance gate. |
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
→ Valkey worker queue
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

## Consolidation debt resolution

The previous work was distributed across stacked draft PRs. The consolidation baseline now requires:

1. current `main` to be an ancestor of the integration branch;
2. one cumulative PR targeting `main`;
3. canonical naming validation;
4. contract, schema and OpenAPI validation;
5. full API, TypeScript, build and browser acceptance;
6. PostgreSQL/Valkey end-to-end acceptance;
7. cumulative migration replay over seeded prior-state data;
8. verified restoration of the pre-migration snapshot;
9. closure of superseded stacked PRs only after the cumulative gate is green;
10. no production deployment or secret provisioning as part of consolidation.

## Active gaps before phase acceptance

### F0

- final cross-contract inconsistency review;
- freeze the current execution-state authority and map precedence;
- close or explicitly retain any obsolete issue/PR descriptions.

### F1

- qualified-user testing against declared thresholds;
- comparison with a control direction;
- multilingual and accessibility acceptance;
- final visual-system gate.

### F2

- merge the green consolidated baseline into `main`;
- retain a reproducible migration/restore artifact;
- decide the production deployment topology separately.

### F3–F5

- bounded human-review workflow;
- additional deterministic claim profiles and contradiction lifecycle;
- source/entity expansion only through independent gates;
- complete Globe/Graph/Timeline parity and user validation.

## Only authorised next priority

> Close the consolidated-baseline gate before adding new product scope. After integration, implement the bounded human-review path for `HUMAN_REVIEW_REQUIRED` and `CONTESTED`, then return to the F1 qualified-user gate.

OCR, unrestricted browsing, broad source expansion, continuous production workers, billing and production deployment remain unauthorised until their dependencies pass.
