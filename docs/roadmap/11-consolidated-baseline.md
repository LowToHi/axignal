# 11 — Consolidated Executable Baseline

Version: `0.1.1`
Status: `MERGED / GATE PASSED`
Goal ID: `AXIGNAL-GOAL-001`
Canonical baseline: `main@cf83781766f12ebc55eeb9829d68d41e77500aa7`
Cumulative PR: `#21`

## Result

The long-lived stacked draft-PR chain has been replaced by one reviewable, reproducible and reversible baseline on `main`.

This integration did not expand product scope, admit new source classes, deploy production services or declare unrelated roadmap phases passed.

## Source chain retained for audit

The baseline preserves the implementation and specialised evidence from:

- PR #5 — end-to-end roadmap, contracts and governance;
- PR #9 — executable spine;
- PR #11 — reproducible CI and runner hardening;
- PR #12 — persistent InvestigationContext;
- PR #13 — research/retrieval contracts;
- PR #14 — governed ResearchRun vertical slice;
- PR #15 — persistent research spine and first institutional source;
- PR #16 — authenticated Navigator integration;
- PR #17 — proposal-only local document pipeline;
- PR #18 — persistent proposal worker with credential separation;
- PR #19 — independent deterministic admission runtime.

All source PRs are closed as `SUPERSEDED_BY_CONSOLIDATED_BASELINE`. Their branches and conversations remain available for audit, but MUST NOT be used as the base for new development.

## History resolution

The cumulative technical history originally diverged from `main` by one canonical naming commit. A two-parent integration commit joined current `main` and the CI-green runtime head before PR #21 was reviewed. PR #21 was then squash-merged into `main` as:

```text
cf83781766f12ebc55eeb9829d68d41e77500aa7
Establish AXIGNAL consolidated executable baseline v0.1
```

## Preserved invariants

1. `AXIGNAL`, `axignal.com`, `LowToHi/axignal` and `AXIGNAL-GOAL-001` are canonical identity.
2. Models have proposal authority only.
3. The deterministic runtime is the sole automatic admission authority.
4. Application, proposal-worker and admission-runtime credentials are physically separated.
5. Tenant isolation is enforced through RLS and server-resolved identity.
6. Source/evidence lineage is immutable and canonical ledger events are append-only.
7. Contradiction, limitation and unknown information are preserved.
8. Rights, integrity, scope, temporal and quantitative gates fail closed.
9. Queues are idempotent and admission transactions are atomic.
10. Production capability remains behind explicit authorisation and feature gates.

## Gate evidence

All cumulative gates passed:

```text
CURRENT_MAIN_ANCESTOR                 PASS
CANONICAL_NAMING_GREEN                PASS
CONTRACTS_SCHEMAS_OPENAPI_GREEN       PASS
RUFF_GREEN                            PASS
API_TESTS_GREEN                       PASS
TYPESCRIPT_GREEN                      PASS
BUILDS_GREEN                          PASS
PLAYWRIGHT_GREEN                      PASS
POSTGRES_EXTENSIONS_GREEN             PASS
VALKEY_GREEN                          PASS
PERSISTENT_RESEARCH_GREEN             PASS
PROPOSAL_ISOLATION_GREEN              PASS
DETERMINISTIC_ADMISSION_GREEN         PASS
MIGRATION_REPLAY_GREEN                PASS
SNAPSHOT_RESTORE_GREEN                PASS
NO_PRODUCTION_DEPLOYMENT               PASS
```

CI evidence:

- Contract Validation `30340309234` — success;
- Executable Spine `30340309338` — success;
- World Bank Live Source Smoke `30340309404` — success.

## Migration and restore result

The rehearsal reconstructed the pre-proposal database boundary, inserted representative governed data, captured a snapshot, applied migrations `025`, `030` and `035`, and reapplied the same sequence.

```json
{
  "baseline_snapshot_created": true,
  "cumulative_migrations_applied": [25, 30, 35],
  "migration_replay_idempotent": true,
  "seeded_data_preserved": true,
  "proposal_worker_canonical_insert": false,
  "admission_runtime_evidence_update": false,
  "snapshot_restore_verified": true,
  "partial_state_detected": false
}
```

Snapshot restore reproduced the pre-migration schema and seeded data in a clean database. Production-specific down migrations remain a separate decision.

## Development rule after consolidation

```text
current main
→ new bounded branch
→ independent PR
→ relevant gates
→ merge or reject
```

The superseded PR chain must never be extended.

## Rollback

No production deployment or customer data migration occurred. Repository rollback is one revert of commit `cf83781766f12ebc55eeb9829d68d41e77500aa7`. The tested pre-migration snapshot restore is the database rollback evidence for this baseline.

## Post-baseline priority

```text
bounded human-review queue
→ reviewer identity and reason codes
→ append-only review history
→ no bypass of rights/integrity/scope gates
→ F1 qualified-user validation
```

New sources, OCR, unrestricted browsing, continuous operation, billing and production deployment remain outside this completed integration gate.
