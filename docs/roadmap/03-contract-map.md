# 03 — AXIGNAL Contract Map

Version: `1.4.0`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## Precedence

1. Goal Lock;
2. `AGENTS.md`;
3. Contract `18`;
4. Contract `30`;
5. Product Constitution `00`;
6. Security and Privacy `06`;
7. Epistemic Claims `02`;
8. capability-specific contract;
9. accepted ADR;
10. typed task;
11. implementation detail.

Contract 30 governs programme scope, phase ordering and the no-partial-launch rule. Contracts 00–29 remain applicable capability contracts where they do not weaken Contract 30.

## Active contract

| ID | Contract | Governs | Active phases |
|---:|---|---|---|
| `30` | Global E2E Development Contract v1.4 | finished global product, libraries, Opportunity Operations, P00–P24 and launch gate | P00–P24 |

## Capability mapping

| Capability | Governing contracts |
|---|---|
| AXIGNAL Core and InvestigationContext | `02`, `04–08`, `12–14`, `18–20`, `25–27`, `30` |
| Foundational libraries F01–F07 | `02–04`, `06`, `08`, `10`, `16`, `18–19`, `30` |
| Opportunity libraries O01–O09 | `00–11`, `16`, `18–19`, `25–30` |
| Opportunity Operations | `02`, `04`, `06–10`, `12`, `18–20`, `22`, `25–27`, `30` |
| Global source admission | `03`, `06`, `08–10`, `18–19`, `28`, `30` |
| Multilingual and documents | `02–08`, `16`, `19`, `25–27`, `30` |
| Cross-library intelligence | `02–08`, `12–17`, `25–27`, `30` |
| Knowledge Tides | `06`, `08`, `15`, `17`, `24`, `26`, `30` |
| Scenarios and outcomes | `02`, `08`, `10`, `27`, `30` |
| Enterprise/API/private data | `03–10`, `22`, `24`, `26`, `30` |
| Billing and entitlements | `01`, `04`, `06–08`, `22`, `29`, `30` |
| Landing, copy and acquisition | `00–01`, `06`, `08`, `11`, `16`, `20–24`, `30` |
| Public launch | all applicable contracts, Contract `30`, ADR-015 |

## Phase mapping

| Phases | Mandatory contract emphasis |
|---|---|
| P00 | Goal Lock, `18`, `30`, ADR-015 |
| P01 | `00–01`, `05`, `11`, `21–23`, `30` |
| P02 | `02–04`, `07–10`, `12–19`, `25–27`, `30` |
| P03 | `03`, `04`, `06–10`, `18–19`, `26`, `30` |
| P04 | `03`, `06`, `08–10`, `18–19`, `27–28`, `30` |
| P05–P06 | `02–08`, `10`, `16`, `18–19`, `25–27`, `30` |
| P07 | `02`, `04–10`, `12`, `18–20`, `22`, `25–27`, `30` |
| P08–P16 | all applicable capability contracts plus `30` |
| P17–P19 | `02–08`, `10`, `12–17`, `24–27`, `30` |
| P20–P22 | `01–10`, `18–30` as applicable |
| P23 | `00–01`, `05–06`, `08`, `10–11`, `16`, `20–24`, `30` |
| P24 | all applicable contracts and ADRs |

## Required change propagation

Material changes must update this map, phase map, typed tasks, schemas, ADRs, gates, migration, rollback and user-facing truth.
