# 03 — AXIGNAL Contract Map

Version: `1.5.0`
Status: `NORMATIVE CANDIDATE / HUMAN APPROVAL REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`

## Precedence

1. explicit current human decision;
2. Goal Lock;
3. `AGENTS.md`;
4. Contract `18`;
5. Contract `31`;
6. Product Constitution `00`;
7. Security and Privacy `06`;
8. Epistemic Claims `02`;
9. applicable capability-specific contract;
10. accepted ADR;
11. typed task;
12. implementation detail.

Contract 31 governs programme scope, dual engineering/canonical state, P00–P27 ordering, P24's acceptance-framework role, P25/P26 launch-critical scope and P27's exclusive final-launch authority.

Contracts 00–30 remain applicable capability contracts where they do not weaken or contradict Contract 31.

## Active and historical programme contracts

| ID | Contract | State | Governs |
|---:|---|---|---|
| `30` | Global E2E Development Contract v1.4 | Preserved history | Original P00–P24 programme and no-partial-launch decision |
| `31` | Global E2E Development Contract v1.5 | Normative candidate | P00–P27, dual state, P25/P26, Search Console/MCP governance and P27 final gate |

## Decision records

| ADR | State | Role |
|---|---|---|
| `ADR-015` | Preserved history | Finished global product before public launch; original P00–P24 sequence |
| `ADR-016` | Proposed | Extends the sequence through P27 and makes P27 the final gate |

## Capability mapping

| Capability | Governing contracts |
|---|---|
| AXIGNAL Core and InvestigationContext | `02`, `04–08`, `12–14`, `18–20`, `25–27`, `31` |
| Product identity and B2G shell | `00`, `01`, `21`, `23`, `31` |
| Foundational libraries F01–F07 | `02–04`, `06`, `08`, `10`, `16`, `18–19`, `31` |
| Opportunity libraries O01–O09 | `00–11`, `16`, `18–19`, `25–29`, `31` |
| Opportunity Operations | `02`, `04`, `06–10`, `12`, `18–20`, `22`, `25–27`, `31` |
| Global source admission | `03`, `06`, `08–10`, `18–19`, `28`, `31` |
| Multilingual and documents | `02–08`, `16`, `19`, `25–27`, `31` |
| Cross-library intelligence | `02–08`, `12–17`, `25–27`, `31` |
| Knowledge Tides | `06`, `08`, `15`, `17`, `24`, `26`, `31` |
| Scenarios and outcomes | `02`, `08`, `10`, `27`, `31` |
| Enterprise/API/private data | `03–10`, `22`, `24`, `26`, `31` |
| Passwordless identity and recovery | `03`, `06`, `18`, `20`, `22`, `31` |
| Trial abuse and trial economics | `01`, `06`, `22`, `29`, `31` |
| Billing, seats and entitlements | `01`, `04`, `06–08`, `22`, `29`, `31` |
| Landing and B2G copy | `00–01`, `06`, `08`, `11`, `16`, `20–24`, `31` |
| Programmatic SEO and public snapshots | `06`, `08`, `21`, `23`, `24`, `31` |
| Tender Alerts and consent | `06`, `21`, `23`, `31` |
| CRM acquisition foundation | `06`, `21`, `23`, `31` |
| AI citation evidence | `02`, `08`, `21`, `24`, `31` |
| Founder Operations | `03`, `06`, `08`, `10`, `18–24`, `29`, `31` |
| Google Search Console | `06`, `08`, `21`, `23`, `31` |
| MCP connectors | `03`, `04`, `06`, `08`, `18`, `20`, `31` |
| Private acceptance | all applicable contracts plus `31` and ADR-016 |
| Public launch | all applicable contracts plus `31`, ADR-016 and P27 |

## Phase mapping

| Phases | Mandatory contract emphasis |
|---|---|
| P00 | Goal Lock, `18`, `30`, ADR-015; preserved acceptance history |
| P01 | `00–01`, `05`, `11`, `21–23`, `31` |
| P02 | `02–04`, `07–10`, `12–19`, `25–27`, `31` |
| P03 | `03`, `04`, `06–10`, `18–19`, `26`, `31` |
| P04 | `03`, `06`, `08–10`, `18–19`, `27–28`, `31` |
| P05–P06 | `02–08`, `10`, `16`, `18–19`, `25–27`, `31` |
| P07 | `02`, `04–10`, `12`, `18–20`, `22`, `25–27`, `31` |
| P08–P16 | all applicable capability contracts plus `31` |
| P17–P19 | `02–08`, `10`, `12–17`, `24–27`, `31` |
| P20 | `03–10`, `18–20`, `22`, `24`, `26`, `31` |
| P21 | `01`, `04`, `06`, `08`, `22`, `29`, `31` |
| P22 | `03`, `06`, `08`, `10`, `19`, `31` |
| P23 | `00–01`, `05–06`, `08`, `10–11`, `16`, `20–24`, `31` |
| P24 | all applicable contracts; acceptance framework only after v1.5 |
| P25 | `03`, `06`, `18`, `20`, `22`, `29`, `31` |
| P26-T01 | `06`, `08`, `21`, `23`, `24`, `31` |
| P26-T02 | `01`, `06`, `21`, `22`, `29`, `31` |
| P26-T03 | `03`, `04`, `06`, `08`, `18`, `24`, `31` |
| P26-T04 | `06`, `08`, `10`, `18`, `19`, `22`, `31` |
| P27 | all applicable contracts and ADRs; exact final-head acceptance |

## Superseded interpretations

Contract 31 supersedes:

- P24 as a standalone final launch gate;
- `BOUNDED_PUBLIC_LAUNCH` as a permitted public disposition;
- European TED as the complete required pre-launch product;
- historical price bands as current candidate-price authority;
- a complete Founder Admin claim based only on P26-T01;
- Search Console DNS verification as proof of API integration;
- MCP catalogue presence as connector admission.

## Required change propagation

Material changes must update:

- this map;
- Contract 31 or a superseding contract;
- ADR;
- phase map;
- task catalogue and registry;
- canonical-state registry;
- schemas;
- gates;
- migration and rollback;
- security, privacy and rights records;
- user-facing truth.
