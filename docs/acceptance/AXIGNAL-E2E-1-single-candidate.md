# AXIGNAL E2E-1 — Single Candidate Consolidation

Task: `AX-E2E-1`  
Target output: `AX_E2E_SINGLE_CANDIDATE_PASS`  
Active branch: `release/axignal-e2e-final`

## Frozen objective

Consolidate the required E2E engineering capabilities into one release branch, exact head, Git tree, configuration, CI matrix and artifact set.

This transition does not add a library, execute a coverage campaign, broaden a public claim, rewrite the programme, create a new pre-production phase or validate the business.

## Dominant line

The dominant engineering line is:

```text
ca17c4756e4bbbfee72b4547d281df0379e91cfa
```

It already contains the P21/P25/P26 chain, identity, seats, entitlements, Stripe contracts, security hardening, reproducibility, exact-head provenance, O01/TED source admission and the latest bounded Gate 7/F01 work.

## Integrated divergent line

The only material divergent product line is:

```text
d3e2dbd2cc6e44374cb4442c7083db7bffe8c153
```

It contributes Subscriber Workspace, its route-addressable product shell, bounded server contract, explicit fixture boundary, web security delta, tests, design tokens and frozen dependency graph.

## Structural merge

The two histories are preserved through:

```text
merge commit  8c57286b67258d016ba2f23bc4daf68b194dc41f
merge tree    83ad858454e972c7084d7449e697c61b3e6f8e72
parent 1      ca17c4756e4bbbfee72b4547d281df0379e91cfa
parent 2      d3e2dbd2cc6e44374cb4442c7083db7bffe8c153
```

The tree is based on the dominant engineering tree. Exactly the verified Subscriber Workspace paths are replaced or added using their Git blob identities. Shared files were accepted only after proving that the dominant line had not changed them since the common ancestor.

## Required coexistence

The exact candidate must contain simultaneously:

```text
passwordless identity and tenant authority
seat governance
Stripe pricing and entitlement contract
product-admitted TED source
Subscriber Workspace entry and server
same-origin mutation security
frozen JavaScript dependencies
```

## Activation boundary

Subscriber Workspace remains behind `AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED`.

The legacy shell remains the default fallback. Fixture mode is admitted only when `AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE=explicit`; no silent fixture fallback is authorised.

The real happy-path adapter and fixture removal remain E2E-2 work. E2E-1 must not claim them complete.

## Authority retirement

After the exact-head matrix succeeds, the following become lineage-only rather than active candidate authorities:

- Subscriber Workspace architecture and implementation PRs `#128` and `#130`;
- F01 candidate and rights PRs `#158` and `#159`;
- the temporary integration PR `#162`;
- the historical Gate 7 stacked PRs recorded in the machine-readable manifest.

Their commits and evidence remain immutable history. Only `release/axignal-e2e-final@EXACT_HEAD` may represent the active E2E candidate.

## Closure conditions

The dedicated workflow must prove on one exact head:

- required ancestry and merge-parent order;
- exact consolidation merge tree;
- exact capability and Subscriber Workspace blobs;
- Professional `149 EUR/month` and Team `399 EUR/month` contracts;
- TED `PRODUCT_ADMITTED` source state with public launch still `NO_GO`;
- safe feature flag and explicit fixture boundaries;
- Subscriber Workspace contract validation;
- P21 commercial and seat contract validation;
- Gate 7 consolidated contract validation;
- frozen dependency installation;
- web unit tests, typecheck and production build;
- retained exact-head and inventory artifacts.

Only a successful exact-head run may emit:

```text
AX_E2E_SINGLE_CANDIDATE_PASS
```

## Next transition

```text
E2E-2 — Happy path without fixtures
```
