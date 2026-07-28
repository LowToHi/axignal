# 11 — Consolidated Executable Baseline

Version: `0.1.0`
Status: `INTEGRATION GATE`
Goal ID: `AXIGNAL-GOAL-001`
Target: `main`
Integration branch: `agent/consolidated-baseline-v0.1`

## Purpose

Replace the long-lived stacked draft-PR chain with one reviewable, reproducible and reversible baseline against current `main` before any new capability is developed.

This is an integration operation. It does not expand product scope, admit new sources, deploy production services or declare roadmap phases passed.

## Source chain

The cumulative baseline preserves the accepted implementation and evidence from:

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

The integration branch also contains the canonical AXIGNAL naming correction already present on `main`. The two histories are joined by a two-parent merge commit before the cumulative PR is opened.

## Baseline invariants

The consolidation MUST preserve:

1. `AXIGNAL`, `axignal.com`, `LowToHi/axignal` and `AXIGNAL-GOAL-001` as canonical identity;
2. models with proposal authority only;
3. deterministic runtime as the sole automatic admission authority;
4. physically separated application, proposal-worker and admission-runtime credentials;
5. tenant isolation through RLS and server-resolved identity;
6. immutable source/evidence lineage and append-only canonical ledger events;
7. contradiction, limitation and unknown preservation;
8. fail-closed rights, integrity, scope, temporal and quantitative gates;
9. idempotent queues and atomic admission transactions;
10. explicit feature flags and synthetic fallback where production capability is not authorised.

## Integration gates

The baseline is mergeable only when all gates pass on the cumulative head:

```text
CURRENT_MAIN_ANCESTOR
CANONICAL_NAMING_GREEN
CONTRACTS_SCHEMAS_OPENAPI_GREEN
RUFF_GREEN
API_TESTS_GREEN
TYPESCRIPT_GREEN
BUILDS_GREEN
PLAYWRIGHT_GREEN
POSTGRES_EXTENSIONS_GREEN
VALKEY_GREEN
PERSISTENT_RESEARCH_GREEN
PROPOSAL_ISOLATION_GREEN
DETERMINISTIC_ADMISSION_GREEN
MIGRATION_REPLAY_GREEN
SNAPSHOT_RESTORE_GREEN
NO_PRODUCTION_DEPLOYMENT
```

## Migration and restore rehearsal

The cumulative rehearsal creates a database at the pre-proposal boundary, inserts representative governed data, snapshots it, applies migrations `025`, `030` and `035`, reapplies the same sequence, and verifies:

- existing Source Objects, Evidence Objects, Candidate Claims and ResearchRuns survive unchanged;
- new tables and columns exist;
- the proposal worker cannot insert canonical claims;
- the admission runtime cannot mutate Evidence Objects;
- the admission login remains available under its bounded role;
- replay does not duplicate or corrupt schema/data.

The snapshot is then restored into a clean database and must reproduce the pre-migration schema and seeded data. Snapshot restore is the authorised rollback proof for this baseline; production-specific down migrations remain a separate decision.

## Supersession procedure

After the cumulative PR is green and merged:

1. record the final merge SHA and CI runs here or in the PR body;
2. close PRs #5, #9 and #11–#19 as `SUPERSEDED_BY_CONSOLIDATED_BASELINE`;
3. add a comment to each source PR pointing to the cumulative baseline and preserving its specialised evidence;
4. do not delete source branches until audit retention is explicitly decided;
5. continue development from updated `main`, never from the old stacked heads.

## Merge strategy

Use a squash merge for the cumulative PR so `main` receives one clearly named baseline commit while the original commit and PR evidence remains available in GitHub history.

Recommended commit title:

```text
Establish AXIGNAL consolidated executable baseline v0.1
```

## Rollback

No production data or deployment is part of this integration. Repository rollback is one revert of the consolidated squash commit. Migration rollback evidence is the tested pre-migration snapshot restore.

## Post-baseline priority

Only after the baseline is merged:

```text
bounded human-review queue
→ reviewer identity and reason codes
→ append-only review history
→ no bypass of rights/integrity/scope gates
→ F1 qualified-user validation
```

New sources, OCR, unrestricted browsing, continuous operation, billing and production deployment remain outside this integration gate.
