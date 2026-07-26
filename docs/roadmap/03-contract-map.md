# 03 — AXIGNAL Contract Map

Version: `0.3.1`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

This map prevents an implementation agent from reading one contract in isolation and losing the complete product goal.

## Contract registry

| ID | Contract | Governs | Primary phases |
|---:|---|---|---|
| `00` | Product Constitution | product identity, users, value, invariants and anti-goals | F0–F12 |
| `01` | Business Model and Pricing | buyer, plans, revenue hypotheses and commercial gates | F0, F8–F12 |
| `02` | Epistemic Claims System | claims, evidence, contradiction, provenance, scenarios and outcomes | F3–F12 |
| `03` | Data Sources and APIs | source admission, rights, ingestion and quality | F3, F8, F11–F12 |
| `04` | System Architecture | stack, modules, storage, eventing and deployment | F2–F12 |
| `05` | UI and UX Exploration | experience principles and core surfaces | F1, F4–F6, F8–F9 |
| `06` | Security, Privacy and Regulatory Boundary | privacy, security, advice boundary and controls | all phases |
| `07` | Product API | API resources, auth, entitlements and errors | F2, F4–F5, F8–F11 |
| `08` | Quality, Observability and Gates | SLOs, data quality, model quality and release evidence | all phases |
| `09` | Delivery and Acceptance | phase sequencing, evidence and definition of done | all phases |
| `10` | Documentation and Operations | ADRs, runbooks, incidents and change control | all phases |
| `11` | Product Hypothesis Register | falsifiable buyer, pricing, wedge and defence assumptions | F0, F1, F8–F12 |
| `12` | Interaction Model | InvestigationContext, lenses, navigation continuity and trails | F1, F4–F5 |
| `13` | Visualisation Grammar | Globe, Graph, Timeline and epistemic visual semantics | F1, F5, F8 |
| `14` | Conversational Navigation | Navigator commands, explanation and UI control | F1, F4–F5 |
| `15` | Intent Intelligence | personal memory, Knowledge Tides and privacy-preserving aggregation | F1, F7, F9 |
| `16` | Multilingual Semantic System | six-language UX, evidence preservation and semantic parity | F1, F4, F6, F8–F12 |
| `17` | Research Candidate Queue | coverage gaps, research prioritisation and investigation lifecycle | F7–F8 |
| `18` | Development Agent Governance | Goal Lock, task routing, skill activation and gate discipline | all phases |

## Capability-to-contract matrix

| Capability | Required contracts |
|---|---|
| Navigator | `02`, `06`, `12`, `14`, `16`, `18` |
| InvestigationContext | `05`, `12`, `14`, `18` |
| Globe | `05`, `07`, `12`, `13`, `16` |
| Graph | `02`, `05`, `07`, `12`, `13`, `16` |
| Timeline | `02`, `05`, `12`, `13` |
| Claim and Evidence Rail | `02`, `03`, `05`, `06`, `12`, `13`, `16` |
| AUTO lens routing | `12`, `14`, `16` |
| Dual mode | `12`, `13` |
| Investigation trails | `06`, `12`, `14`, `15` |
| Personal Interest Memory | `06`, `15` |
| Knowledge Tides | `06`, `08`, `15`, `17` |
| Research Candidate Queue | `02`, `03`, `08`, `15`, `17` |
| Claim Ledger | `02`, `03`, `04`, `06`, `08` |
| Opportunity Engine | `02`, `03`, `08`, `11` |
| Multilingual search | `02`, `07`, `16` |
| Billing and entitlements | `01`, `04`, `06`, `07`, `08` |
| Enterprise private data | `02`, `03`, `06`, `07`, `10`, `16` |

## Phase-to-contract matrix

| Phase | Mandatory contracts |
|---|---|
| F0 | Goal Lock, `00–11`, `18` |
| F1 | `00`, `05`, `06`, `08`, `11–16`, `18` |
| F2 | `04`, `06–10`, `18` |
| F3 | `02–04`, `06`, `08–10`, `18` |
| F4 | `02`, `05–08`, `12`, `14`, `16`, `18` |
| F5 | `02`, `04–08`, `12–14`, `16`, `18` |
| F6 | `02–08`, `12`, `14`, `16`, `18` |
| F7 | `02`, `04`, `06`, `08`, `10`, `12`, `14–18` |
| F8 | `00–13`, `16–18` |
| F9 | `00–12`, `14–18` |
| F10 | `02`, `04`, `06`, `08–12`, `16`, `18` |
| F11 | `01–10`, `12`, `14–16`, `18` |
| F12 | all applicable contracts |

## Contract precedence

When contracts appear to conflict, precedence is:

1. Goal Lock;
2. `AGENTS.md`;
3. contract `18`;
4. product constitution `00`;
5. security, privacy and regulatory contract `06`;
6. epistemic contract `02`;
7. capability-specific contract;
8. accepted ADR;
9. task specification;
10. implementation detail.

A lower layer MUST NOT silently weaken a higher layer.

## Required change propagation

A material contract change MUST update:

- this map;
- affected phase entries;
- affected tasks;
- skill activation rules;
- machine-readable schemas;
- ADRs;
- acceptance tests;
- migration and rollback documentation.

## Contract completeness gate

F0 cannot pass while any capability exists in the Goal Lock without:

- at least one governing contract;
- at least one task;
- at least one responsible skill;
- at least one evidence gate;
- an explicit security, privacy and rights classification.
