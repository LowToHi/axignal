# 02 — AXIGNAL Active Task Catalogue

Version: `1.5.0`
Status: `NORMATIVE CANDIDATE / HUMAN APPROVAL REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`
Governing contract: `31`
Decision: `ADR-016`

## Task-state rule

```text
engineering state
≠ canonical state
```

P00–P24 task definitions remain preserved in the v1.4 shards. Their current canonical and engineering disposition is recorded in `data/programmes/global-e2e-canonical-state.v1.5.json`.

P25–P27 use the dual-state schema at `schemas/global-e2e-v1.5-task.schema.json`.

## Canonical and historical task sources

- `data/programmes/global-e2e-task-registry.v1.5.json`
- `data/programmes/global-e2e-canonical-state.v1.5.json`
- `data/programmes/global-e2e-tasks-p00-p04.v1.4.json`
- `data/programmes/global-e2e-tasks-p05-p09.v1.4.json`
- `data/programmes/global-e2e-tasks-p10-p14.v1.4.json`
- `data/programmes/global-e2e-tasks-p15-p19.v1.4.json`
- `data/programmes/global-e2e-tasks-p20-p24.v1.4.json`
- `data/programmes/global-e2e-tasks-p25-p27.v1.5.json`

## P00–P24 summary

| Task range | Engineering state | Canonical state | Current authority |
|---|---|---|---|
| `AX-GE2E-P00-T01` | `PASS` | `ACCEPTED` | Governance accepted |
| `AX-GE2E-P01-T01` | `IN_PROGRESS` | `IN_PROGRESS` | Buyer/workflow evidence only |
| `AX-GE2E-P02-T01`–`AX-GE2E-P16-T01` | Evidence present in stacked engineering PRs | `CANONICAL_ACCEPTANCE_BLOCKED` | No source/library commercial authority |
| `AX-GE2E-P17-T01`–`AX-GE2E-P23-T01` | Evidence present in stacked engineering PRs | `CANONICAL_ACCEPTANCE_BLOCKED` | No public or commercial activation |
| `AX-GE2E-P24-T01` | Acceptance framework implemented | `CANONICAL_ACCEPTANCE_BLOCKED` | `NO_GO`; no longer final launch authority |

Historical procurement task `AX-GE2E-P08-T01` remains present only in `data/programmes/global-e2e-tasks-p05-p09.v1.4.json`; it is immutable implementation evidence and is not an active v1.5 task.

## P25–P27 tasks

| Task | Outcome | Engineering state | Canonical state |
|---|---|---|---|
| `AX-GE2E-P25-T01` | Persistent passwordless identity, revocable sessions, recovery and tenant-level trial-abuse governance | `ENGINEERING_E2E_PASS` | `CANONICAL_ACCEPTANCE_BLOCKED` |
| `AX-GE2E-P26-T01` | IndexabilityGate, public snapshots, Tender Alerts, CRM, AI citations and Founder Admin foundation | `ENGINEERING_E2E_PASS` | `CANONICAL_ACCEPTANCE_BLOCKED` |
| `AX-GE2E-P26-T02` | Customers, trials, billing, invoices, disputes, refunds and entitlement administration | `NOT_STARTED` | `CANONICAL_NOT_STARTED` |
| `AX-GE2E-P26-T03` | Risk, abuse, sources, rights, coverage, connector and MCP administration | `NOT_STARTED` | `CANONICAL_NOT_STARTED` |
| `AX-GE2E-P26-T04` | Operations, workers, SLO, incidents, DR, settings, kill switches and audit | `NOT_STARTED` | `CANONICAL_NOT_STARTED` |
| `AX-GE2E-P27-T01` | Final exact-head re-acceptance and the only public-launch disposition | `NOT_STARTED` | `CANONICAL_NOT_STARTED` |

## Key task boundaries

### P25-T01

```text
implemented identity != public signup enabled
account != trial
risk score != proof of abuse
CI pass != production provider acceptance
```

### P26-T01

```text
dataset != indexable page
page generated != page published
alert subscriber != account
CRM contact != entitlement
Founder sidebar != complete Founder Operations
```

### P26-T02

Must not fabricate Stripe or subscription state. Every customer, trial, invoice, refund, dispute and entitlement operation must be typed, provider-reconciled and audited.

### P26-T03

Must not admit sources or MCPs from browser or model decisions. Weak abuse signals cannot independently block. Search Console DNS verification does not admit API or MCP access.

### P26-T04

Must not show secrets, simulate kill switches, claim backup recovery without restore evidence or allow unaudited break-glass operations.

### P27-T01

May return only:

```text
ACCEPTED_FOR_PUBLIC_LAUNCH
IN_PROGRESS
REJECTED
```

P27 approval is invalidated by any final-head change.

## Legacy task history

`AX-F0`–`AX-F12` and v1.4 P00–P24 task instances remain immutable audit and implementation evidence. They are not deleted or rewritten to appear v1.5-native.

## Legacy implementation task additions

| Task | Purpose | Governing scope | Required skills |
|---|---|---|---|
| `AX-F2-T18` | Rebuild the public landing for the B2G procurement wedge with six-locale parity, evidence-state truth and controlled B2G trial intake | 01–06, 08, 12–13, 16, 18, 20–21, 23, 28, ADR-013, ADR-014 | frontend-architect, axignal-gsap-ui-ux, axignal-cinematic-webgl-scroll, globe-engineer, multilingual-localiser, analytics-engineer, accessibility-auditor, performance-engineer, test-engineer |

This row preserves the immutable F2 implementation authority without representing it as a v1.5-native P25–P27 task or as canonical acceptance.

## Closure rule

A task reaches canonical acceptance only when:

- governing contracts pass;
- required skills are present;
- exact-head tests pass;
- required real-environment evidence exists;
- Goal Lock checks pass;
- rights, privacy and security dispositions are current;
- rollback or kill switch is accepted;
- human authority approves where required;
- dependencies are canonically accepted.

Code existence and green CI are insufficient.
