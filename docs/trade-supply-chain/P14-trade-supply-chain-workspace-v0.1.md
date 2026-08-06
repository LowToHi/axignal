# P14 — Trade & Supply Chain Library + Supply Opportunity Workspace

Status: `ENGINEERING FOUNDATION / CANONICAL ACTIVATION BLOCKED`

Task: `AX-GE2E-P14-T01`  
Frozen engineering base: `0089864b1a3f3d88a0980ecaf4e6dd129299e021`

P14 binds `AX-LIB-O07` — Trade, Supply Chain and Market Flows — to the
Supply Opportunity Workspace.

## Truth boundaries

The contract keeps the following concepts distinct:

- aggregate trade flow versus shipment-level evidence;
- missing, suppressed and zero observations;
- origin, transit, re-export and economic provenance;
- destination and final use;
- value, quantity, net weight, gross weight, unit value and indices;
- source-native classification and versioned crosswalks;
- tariff schedule and duty actually owed;
- sanctions or controls evidence and legal applicability advice;
- disruption, delay, capacity constraint and confirmed closure;
- observed events, forecasts, scenarios and recommendations.

## Materialised evidence

- 8 bounded domain modules;
- 32 record types;
- 48 invariants;
- 12 lifecycle states;
- 11 operating-pipeline stages;
- 12 readiness gates;
- 40 conformance fixtures;
- 72 adversarial cases;
- deterministic reference functions;
- byte-exact rollback to the frozen P13 head.

## Authority

Models remain proposal-only and workers remain bounded. No model or worker can
contact suppliers, request quotations, place orders, book transport capacity,
submit customs or trade filings, give personalised sanctions advice, commit
capital or represent the organisation.

All four trade catalogue sources remain research-only, unreviewed and not
product-admitted. Public or global coverage is not authorised.
