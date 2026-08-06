# P19 — Scenarios, Calibration & Outcomes

Task: `AX-GE2E-P19-T01`

Engineering foundation for versioned scenarios, as-of baselines, temporal holdouts, immutable forecast records, outcome reconciliation, calibration and model-status governance.

## Boundaries

- Scenario is distinct from forecast, target and observation.
- Baseline is distinct from counterfactual truth.
- Random split is distinct from temporal holdout.
- Backtest evidence is distinct from prospective performance.
- Post-cutoff revisions are excluded from as-of inputs.
- Confidence, accuracy and calibration remain separate.
- Partial, censored, pending and unavailable outcomes remain separate.
- Evaluation output is not a canonical claim.

## Architecture

Eight modules materialise 32 record types, 48 invariants, 12 lifecycle states, 11 stages, 12 readiness gates, 40 conformance fixtures and 72 adversarial cases.

## Temporal integrity

Each evaluation pins the cutoff, publication time, retrieval time, vintage and revision lineage. Holdouts cannot be reused for tuning, and forecasts remain append-only after emission.

## Outcomes and governance

Outcome evidence preserves pending, partial, censored, contested, revised and unobservable states. Integrity violations or repeated material calibration breaches lower model status. Restoration requires typed human approval, a new frozen holdout and passing evidence.

## Canonical state

P19 is engineering evidence only. P18 and transitive dependencies remain canonically blocked; merge to `main` and product activation are not authorised.
