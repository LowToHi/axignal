# 13 — F1 Qualified-User Validation Harness

Version: `0.1.0`
Status: `EVIDENCE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## Objective

Measure whether qualified users understand AXIGNAL's authority layers, trace evidence correctly, identify unknowns and complete bounded investigation tasks more reliably than with a linear control surface.

## Experiment contract

```text
pseudonymised participant
→ frozen task
→ deterministic AXIGNAL or CONTROL assignment
→ equivalent content
→ append-only interaction events
→ structured immutable response
→ reproducible metrics
```

The condition changes presentation only. Task statement, evidence, source state and declared unknowns are identical in both conditions.

## Primary metrics

- task completion rate;
- critical error rate;
- evidence traceability rate;
- authority-layer comprehension;
- unknowns identification rate.

## Guardrails

- participant PII columns: `0`;
- cross-tenant access: denied;
- model, participant and evaluator canonical writes: denied;
- answer keys never returned to the participant client;
- condition immutable after session start;
- events and responses append-only;
- production deployment: false.

## Technical acceptance

The unit must prove six frozen tasks, deterministic assignment with both conditions reachable, equivalent participant payloads, idempotent session replay, hidden answer keys, reproducible metrics, migration replay and pre-060 snapshot restore.

## External gate

This harness does not fabricate qualified-user results. F1 remains in `GATE_REVIEW` until real controlled sessions meet thresholds frozen before recruitment. Initial planning thresholds are at least six distinct qualified users, twelve valid sessions, at least 80% AXIGNAL completion, no more than 10% critical errors, at least 85% authority comprehension and zero privacy or isolation incidents.

## Non-goals

No production deployment, participant recruitment automation, recordings, email storage, OCR, new sources, billing, new model authority or commercial-universe expansion.
