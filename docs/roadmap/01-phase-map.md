# 01 — AXIGNAL Active Phase Map

Version: `1.5.0`
Status: `NORMATIVE CANDIDATE / HUMAN APPROVAL REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`
Governing contract: `31`
Decision: `ADR-016`
Canonical baseline: `main@b9a08a2a07d04d635164e161d1b27a7a53df8575`
Engineering-stack candidate: `e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073`

## State semantics

Engineering and canonical states are independent.

```text
engineering code or CI
≠ canonical acceptance
≠ product admission
≠ commercial availability
≠ public launch
```

## Active sequence

| Phase | Engineering state | Canonical state | Objective | Exit gate |
|---|---|---|---|---|
| `P00` | `ENGINEERING_E2E_PASS` | `CANONICALLY_ACCEPTED` | Integrate governance and synchronise canonical authority | Human authority, automated gates and rollback rehearsal passed |
| `P01` | `ENGINEERING_IN_PROGRESS` | `IN_PROGRESS` | Validate global buyers, jobs, budgets and workflows | Qualified primary evidence by library and workflow |
| `P02` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Freeze global ontology and library contracts | New library can be added without rewriting the core |
| `P03` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Security, identity and rights by design | Tenant, role, source-right and data-class boundaries pass |
| `P04` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Source Admission Factory and Connector SDK | Repeatable source promotion and revocation circuit |
| `P05` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Implement seven foundational libraries | Versioned global foundations pass |
| `P06` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Multilingual and Document Intelligence | Six-language and document evidence parity |
| `P07` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Opportunity Operations Core | Opportunity-to-outcome E2E with audit and export |
| `P08` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Global Procurement and Bid Workspace | Multijurisdiction Procurement E2E and source admission |
| `P09` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Grants and Application Workspace | Multinational grant E2E and source admission |
| `P10` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Regulatory and Market Entry Workspace | Regulation-to-action E2E without legal advice |
| `P11` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Infrastructure and Project Pursuit Workspace | Project pipeline-to-outcome E2E |
| `P12` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Corporate and Account Opportunity Workspace | Filing/entity-to-account E2E |
| `P13` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Sovereign/Macro and Strategy Workspace | Vintage-aware market-strategy E2E |
| `P14` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Trade/Supply and Supply Workspace | Flow/dependency-to-pursuit E2E |
| `P15` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Energy/Climate and Transition Workspace | Transition-opportunity E2E |
| `P16` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Innovation/IP and Innovation Workspace | Patent/research-to-pursuit E2E |
| `P17` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Cross-library intelligence | Multi-library query preserves authority and provenance |
| `P18` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Intent Intelligence and Knowledge Tides | Privacy-safe candidates, never claims |
| `P19` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Scenarios, calibration and outcomes | Baselines, holdouts and calibrated uncertainty |
| `P20` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Enterprise, API, private data and integrations | Enterprise tenant and API acceptance |
| `P21` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Commercial runtime, pricing, Stripe and seat governance | External sandbox, pricing, paid evidence, margin and seat governance |
| `P22` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Production, SLO, DR, security, privacy and legal framework | Independent restore and zero critical findings on accepted head |
| `P23` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Product UX, B2G landing, copy and market shell | Comprehension, accessibility and conversion evidence |
| `P24` | `ENGINEERING_EVIDENCE_READY` | `CANONICAL_ACCEPTANCE_BLOCKED` | Acceptance framework and evidence manifest | Reusable exact-head evidence engine; no final launch authority |
| `P25` | `ENGINEERING_E2E_PASS` | `CANONICAL_ACCEPTANCE_BLOCKED` | Passwordless identity and trial-abuse governance | Production identity, recovery, provider and abuse acceptance |
| `P26` | `ENGINEERING_IN_PROGRESS` | `CANONICAL_ACCEPTANCE_BLOCKED` | Organic discovery, AI citations and Founder Operations | T01–T04 accepted; public and admin surfaces fully governed |
| `P27` | `NOT_STARTED` | `CANONICAL_NOT_STARTED` | Final exact-head re-acceptance and public-launch gate | All critical evidence and typed human approvals pass |

## P26 task state

| Task | Engineering state | Canonical state |
|---|---|---|
| `AX-GE2E-P26-T01` Organic Discovery and Founder Admin Foundation | `ENGINEERING_E2E_PASS` | `CANONICAL_ACCEPTANCE_BLOCKED` |
| `AX-GE2E-P26-T02` Customers, Trials and Billing Administration | `NOT_STARTED` | `CANONICAL_NOT_STARTED` |
| `AX-GE2E-P26-T03` Risk, Abuse, Sources and Coverage Administration | `NOT_STARTED` | `CANONICAL_NOT_STARTED` |
| `AX-GE2E-P26-T04` Operations, SLO, Incidents, DR, Settings and Audit | `NOT_STARTED` | `CANONICAL_NOT_STARTED` |

## Parallelisation

P08–P16 engineering may proceed in parallel when their shared contracts exist. P17 depends canonically on all nine library phases. Research and technical probes may start early only when non-authoritative, rights-safe, reversible and incapable of changing product or public state.

## Final launch rule

P24 is an acceptance framework. P27 is the only final launch gate.

P27 may return only:

```text
ACCEPTED_FOR_PUBLIC_LAUNCH
IN_PROGRESS
REJECTED
```

There is no partial or bounded public launch.

## Historical phases

- F0–F12 remain auditable history.
- P00–P24 v1.4 remain auditable history.
- Contract 30 and ADR-015 remain preserved.
- Their active ordering and final-gate authority are superseded by Contract 31 and ADR-016 after approval.
