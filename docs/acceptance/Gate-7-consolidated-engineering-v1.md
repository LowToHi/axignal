# Gate 7 — Canonical engineering consolidation v1

## Decision

This consolidation converts the stacked and parallel Gate 7 development branches
into one exact-head engineering authority. It does **not** admit a source, execute
the real evidence campaign, approve Legal or Privacy/Data Rights decisions, or
authorise public launch.

```text
STACK_CONSOLIDATED   = true
SINGLE_EXACT_HEAD    = true
CAMPAIGN_AUTHORITY   = false
PUBLIC_LAUNCH        = NO_GO
```

## Canonical lineage

The consolidated tree preserves the complete ordered lineage:

1. Gate 7 coverage, source and multilingual contract — PR #101.
2. O01 Global Public Procurement evidence baseline — PR #102.
3. O01 source inventory and rights boundary — PR #119.
4. O01 Legal and Privacy evidence package — PR #121.
5. O01 evidence campaign contract — PR #123.
6. O01 procurement domain contracts — PR #126.
7. Contextual contact policy and approval renewal — PR #127.

Two parallel lines are integrated without changing their historical meaning:

- PR #120 contributes the fifteen fail-closed dossiers
  `AX-LIB-F01–F07` and `AX-LIB-O02–O09`.
- PR #129 contributes the final performance/capacity harness and the concurrency
  fixes exposed by its retained failed campaigns.

PRs #128 and #130 are subscriber-workspace and UX work. They are intentionally
outside this Gate 7 consolidation.

## Current authority

The PR and branch heads listed in the contract are lineage evidence only. They are
not independent current authorities after consolidation.

The current technical authority is the exact Git head checked out by CI. Its
runtime attestation freezes:

```text
exact_head_sha
git_tree_sha
approval_manifest_digest
minimum referenced evidence expiry
Gate 7 artifact digest source
```

The GitHub Actions artifact digest is obtained from the uploaded consolidated
artifact after the workflow completes. It is not embedded into the artifact that
it hashes.

## Library dossier state

The consolidated tree contains exactly sixteen dossiers:

```text
AX-LIB-F01–F07
AX-LIB-O01–O09
```

All dossiers remain fail-closed:

```text
canonical_state = BLOCKED
claim_decision  = DENIED
active sources  = 0
product-admitted sources = 0
```

O01 contains a bounded TED candidate source and current engineering evidence, but
Legal, Privacy/Data Rights, quality, multilingual, lag, kill-switch and rollback
acceptance remain incomplete.

## Supersession rules

Historical files remain available for audit, but only one active contract is
selected for each scope:

- `AX-LIB-O01-legal-privacy-approval-request.v0.2.json` supersedes v0.1.
- `AX-LIB-O01-TED-contact-policy-reconciliation.v0.2.json` supersedes the
  professional-contact-person-data interpretation in the field-rights v0.1
  matrix; the remainder of that matrix stays active.
- `AX-G7-performance-capacity-contract.v0.2.json` supersedes v0.1.

A superseded file cannot become current merely because it still exists in Git
history or is referenced as historical evidence.

## Exact-head workflow

`.github/workflows/gate7-consolidated-engineering.yml` performs the integrated
verification on one checkout:

1. proves the exact Git head and tree;
2. installs the frozen dependency graph;
3. runs concurrency, contextual-policy, renewal and domain tests;
4. verifies source snapshots, rights, Legal/Privacy reconciliation, renewal,
   campaign and domain contracts;
5. materialises the exact-head approval manifest and renewal package;
6. materialises the sixteen-library Gate 7 report;
7. rejects conflict markers, duplicate libraries, active sources, stale authority
   heads and undeclared supersession;
8. uploads one content-addressable evidence package.

The expected output is:

```text
GATE7_CONSOLIDATED_ENGINEERING_PASS
```

## Remaining authority gates

Engineering consolidation is not campaign acceptance. The following remain
blocked until independently evidenced and signed:

```text
LEGAL decision                         MISSING
PRIVACY_DATA_RIGHTS decision           MISSING
real representative evidence campaign NOT EXECUTED
source admission                       false
campaign authority                     false
global coverage claim                  false
multilingual claim                     false
public launch                          NO_GO
```
