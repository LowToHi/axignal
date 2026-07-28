# 12 — F2 Deliverable-Gap Closure

Version: `0.2.0`
Status: `GATE_REVIEW`
Goal ID: `AXIGNAL-GOAL-001`
Canonical integration: `main@15a232249736658dbe05a67d1f2541384848f5b3`

## Decision

PR #24 was squash-merged into `main` as `15a232249736658dbe05a67d1f2541384848f5b3` after all relevant workflows passed on the exact PR head `9e58e002f9448a0d7272411cfeddcaecd8bee9cf`.

F2 now has executable evidence for:

1. scheduler persistence, idempotency, lease recovery and dead-letter behavior;
2. content-addressed object storage, immutable addressing and hash rejection;
3. OpenTelemetry trace propagation with prohibited-field redaction;
4. explicit runtime credentials, health, readiness, restart and concurrency contracts;
5. clean-clone CI, migration replay and pre-050 snapshot restore.

## Acceptance evidence

```text
Contract Validation       SUCCESS
Human Review Acceptance   SUCCESS
Executable Spine          SUCCESS
F2 Runtime Closure        SUCCESS
```

The authoritative acceptance commands are:

```text
scripts/verify_f2_runtime_closure.py
scripts/verify_f2_migration_rehearsal.sh
scripts/verify_runtime_topology.py
```

Demonstrated results include:

- duplicate scheduled jobs: `0`;
- expired lease recovery: `PASS`;
- dead-letter transition: `PASS`;
- scheduler canonical writes: `DENIED`;
- scheduler Evidence Object mutation: `DENIED`;
- object-store tamper detection: `PASS`;
- telemetry secrets: `0`;
- migration replay: `PASS`;
- snapshot restore: `PASS`;
- scheduler container healthcheck: `PASS`;
- production deployment: `false`.

## Gate interpretation

This integration resolves the previously identified scheduler, object-storage-interface, OpenTelemetry and reproducible-topology deliverable gaps. F2 advances from `EVIDENCE_READY` to `GATE_REVIEW`.

A formal `PASSED` decision remains separate from implementation evidence and requires the roadmap authority to accept the complete normative F2 gate. Production deployment topology, production secrets, SLOs and disaster recovery are explicitly outside this decision.

## Next authorised work

Return to the F1 qualified-user gate. Build and run a controlled AXIGNAL-versus-control validation harness before broadening sources, OCR, browsing, models, billing or production deployment.
