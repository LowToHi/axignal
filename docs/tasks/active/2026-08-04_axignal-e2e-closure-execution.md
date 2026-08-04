# AX-GE2E-P08-T03 — Subscriber Shell closure under the AXIGNAL global E2E programme

Goal ID: `AXIGNAL-GOAL-001`
Governing authority: Contract `31`, ADR-016 and `AX-GE2E-CLOSURE-CONTRACT-001`
Execution branch: `codex/axignal-e2e-contract-execution`
Starting head: `50eda82e263f80dac8274f59bebbad4a8eade5bc`
State: `IN_PROGRESS / CANONICAL_ACCEPTANCE_BLOCKED / NO_PUBLIC_LAUNCH`

## Objective

Close the authenticated subscriber Shell and Bid Workspace as the first bounded execution slice of the complete AXIGNAL closure programme, without reducing the contracted product, substituting fixtures for production authority, or treating partial engineering evidence as canonical acceptance.

The superior execution chain remains:

```text
C0 canonical reconciliation
→ C1 subscriber shell closure
→ C2 identity/tenant/trial renewal
→ C3 persistent authority plane
→ C4 research spine and AXENT
→ C5 evidence/admission
→ C6 foundational libraries F01–F07
→ C7 O01 procurement and Bid Workspace
→ C8 O02–O09 opportunity libraries
→ C9 cross-library/scenarios/outcomes
→ C10 enterprise/API/private data
→ C11 Stripe/billing/entitlements
→ C12 Founder Operations
→ C13 production trust
→ C14 UX/accessibility/multilingual/performance
→ C15 reproducible distribution and global matrix
→ C16 buyer/paid-value/support evidence
→ C17 P27 exact-head final acceptance
```

## Current execution slice

Active slice: `C0–C1`, represented as typed task `AX-GE2E-P08-T03` because the active typed-task schema governs P00–P24 task identifiers.

Implemented on this branch:

- a governed tender-section override layer that keeps unsupported mutations visibly unavailable;
- `Continue review` is explicitly non-mutating and cannot be mapped to `pursue`;
- a decision requires explicit `pursue` or `do_not_pursue` plus a rationale;
- `document.create`, `approval.record` and `export.create` no longer appear as operationally available actions;
- the BFF rejects requirement completion without linked verified evidence;
- the BFF rejects submission preparation with blockers, pending amendments or missing commercial approval;
- the BFF rejects submission approval without a ready preflight;
- the BFF projects legacy fixture mutations into precise clarification, commercial and submission audit event types;
- subscriber Navigator requests are bound to a server-validated opportunity and require the persistent ResearchRun API;
- subscriber Navigator requests fail closed instead of falling back to synthetic execution;
- accepted ResearchRuns redirect to `/research-runs/{runId}` and expose canonical worker, source, evidence, Candidate Claim, admitted-claim and dossier state;
- the ResearchRun route repeats the authentication boundary and is explicitly non-indexable;
- AXENT visibly discloses deterministic fallback mode and emits a response-mode header;
- AXENT local history is versioned, scoped by tenant and identity, bounded to 30 days, capped in volume and never represented as server-synchronised;
- malformed, expired and tenant-only legacy AXENT history is purged fail closed;
- the account avatar is a real menu and logout purges only AXENT local-history namespaces before redirecting;
- reduced-motion users receive a static cartographic equivalent and the WebGL frame loop is not mounted, while the accessible Globe table and controls remain available;
- the complete Shell chrome has one typed catalogue for English, Spanish, French, German, Portuguese and Italian;
- global navigation, contextual workspace navigation, command palette, notification, account, logout and accessibility labels change locale while retaining identical routes and capabilities;
- language preference persists through a full navigation and updates the document language;
- AXENT, Investigations and Bid Workspace expose one and only one main-content landmark from the product Shell;
- critical AXENT, Investigations and Bid Workspace routes reject duplicate IDs, positive tabindex and visible interactive controls without accessible names;
- those critical routes reflow without page-level horizontal overflow at 320 CSS pixels;
- critical AXENT controls remain available under 200 percent text scaling;
- forced-colors mode preserves interactive borders, current/pressed states and a visible two-pixel focus outline;
- synthetic Intelligence projections are withheld in real-adapter mode instead of being presented as live data;
- Playwright launches the subscriber candidate with explicit non-production fixture authority;
- critical browser tests use zero retries;
- web and landing security-boundary implementations are identical again;
- browser tests cover authority, degraded mode, server preconditions, precise audit projection, the Navigator-to-ResearchRun route transition, AXENT local-retention/logout boundaries, reduced-motion equivalence, six-locale Shell semantics and the automated accessibility boundary.

## Exact-head evidence boundary

The immediately preceding exact head
`b74c1b0728a065be6331d02455569670e5a48c9e` passed the complete triggered
matrix, including Contract Validation, Frontend Unit Contracts, G5, G6,
Executable Spine, E2E Technical Audit, P21-T02, P25-T01 and P26-T01.

That evidence is immutable evidence for that predecessor only. This documentary
reconciliation changes the head and therefore requires a fresh complete matrix
before it can contribute to C0–C1 acceptance.

## C1 blockers and disposition

```text
AX-SW-BLK-001 exact-head CI matrix                      OPEN
AX-SW-BLK-002 unsupported enabled actions               FIXED_BY_FAIL_CLOSED_UI
AX-SW-BLK-003 continue_review mapped to pursue           FIXED
AX-SW-BLK-004 synthetic operational data                 PARTIAL_FIX
AX-SW-BLK-005 Navigator persistent ResearchRun           PARTIAL_FIX_AT_BFF_AND_UI
AX-SW-BLK-006 evidence sufficiency enforcement           PARTIAL_FIX_AT_BFF
AX-SW-BLK-007 submission readiness enforcement           PARTIAL_FIX_AT_BFF
AX-SW-BLK-008 precise audit events                       PARTIAL_FIX_AT_BFF
AX-SW-BLK-009 deadlines_next_30_days calculation         PARTIAL_FIX_AT_BFF
AX-SW-BLK-010 AXENT retention/persistence contract       PARTIAL_FIX_AT_CLIENT
AX-SW-BLK-011 assistant degraded-mode provenance         FIXED_FOR_CURRENT_BFF
AX-SW-BLK-012 six-locale functional parity               PARTIAL_FIX_AT_SHELL_CHROME
AX-SW-BLK-013 formal accessibility acceptance            PARTIAL_FIX_AUTOMATED_ACCESSIBILITY
AX-SW-BLK-014 global desktop/tablet/mobile evidence      OPEN
AX-SW-BLK-015 real adapter and real-data journey         OPEN
```

`PARTIAL_FIX_AT_BFF`, `PARTIAL_FIX_AT_BFF_AND_UI`,
`PARTIAL_FIX_AT_CLIENT`, `PARTIAL_FIX_AT_SHELL_CHROME` and
`PARTIAL_FIX_AUTOMATED_ACCESSIBILITY` do not close the persistent,
product-wide or human-authority contracts. Equivalent enforcement, native event
typing, audit, reconciliation, retention, export, deletion, semantic parity and
accessibility acceptance must exist across every contracted surface.

For `AX-SW-BLK-005`, the subscriber Shell now creates only persistent
ResearchRuns, validates the selected opportunity against the server-resolved
tenant bootstrap, rejects synthetic fallback, redirects to the canonical run
route and polls the persistent BFF. The browser contract uses controlled API
responses to prove routing and rendering. C4 must still prove the same journey
against a disposable integrated topology with the real API, queue, worker,
admission runtime and dossier persistence before this blocker can be closed.

For `AX-SW-BLK-008`, the BFF exposes one precise canonical event vocabulary for
action responses and the append-only event endpoint, while the engineering
fixture store retains its legacy generic records. C3 must migrate authoritative
persistence to write the precise types natively before this blocker can be
closed.

For `AX-SW-BLK-010`, browser-local AXENT history is now explicitly temporary,
identity-scoped and purged on logout. It is not an AXIGNAL system of record and
is not synchronised across devices. C3/C4 must define the authoritative
conversation schema, tenant isolation, encryption, retention classes, legal
hold, export, user deletion, audit and backup/restore behaviour before this
blocker can be closed.

For `AX-SW-BLK-012`, the Shell chrome now has typed and browser-tested semantic
parity for `en`, `es`, `fr`, `de`, `pt` and `it`, including accessible names and
route-preserving navigation. The blocker remains partial because AXENT copy,
global destination bodies, Bid Workspace content, dynamic status vocabulary,
server errors and source-derived multilingual presentation are not yet complete
across all six locales. C14 must demonstrate the same meaning, authority,
uncertainty and action availability on every contracted surface.

For `AX-SW-BLK-013`, the automated boundary now verifies a single main landmark,
unique IDs, non-positive tabindex, accessible names for visible controls, reflow
at 320 CSS pixels, critical controls under 200 percent text scaling, reduced
motion and forced-colors keyboard focus across AXENT, Investigations and Bid
Workspace. The blocker remains partial: C14 still requires a reproducibly locked
axe/pa11y rule set, broader route and state coverage, real screen-reader and
keyboard sessions, zoom and reflow review for every contracted surface,
platform/browser assistive-technology coverage and explicit human accessibility
authority.

## Non-negotiable execution rules

- No autonomous submission, communication, signature, source admission or launch.
- No silent fixture fallback.
- No browser-authoritative tenant, role, entitlement, approval or source state.
- No dead CTA may appear operationally available.
- No CI retry may convert a flaky critical journey into acceptance.
- No phase is closed by code presence alone.
- Every material action requires contract, authority, persistence, audit, recovery and exact-head evidence.
- Any head change invalidates evidence bound to the prior head.

## Required evidence for C0–C1 closure

```text
canonical-head reconciliation
complete changed-file inventory
server/UI action parity report
zero unsupported enabled controls
qualification semantic regression test
all subscriber unit tests PASS
all subscriber browser tests PASS first run
G5 security boundary PASS
Executable Spine PASS
E2E Technical Audit PASS
rollback rehearsal PASS
exact-head evidence bundle
```

## Current disposition

```text
P08-T03 / C0-C1  IN_PROGRESS
C2               BLOCKED_BY_C0_C1
C3               BLOCKED_BY_C0_C2
C4               BLOCKED_BY_C2_C3
C5               BLOCKED_BY_C3_C4
C6               BLOCKED_BY_RIGHTS_AND_FOUNDATIONS
C7               BLOCKED_BY_C3_C5_C6
C8               BLOCKED_BY_SHARED_CONTRACTS_AND_LIBRARY_GATES
C9               BLOCKED_BY_C8
C10              BLOCKED_BY_C9
C11              BLOCKED_BY_C10
C12              BLOCKED_BY_C11_AND_P26_DEPENDENCIES
C13              BLOCKED_BY_INTEGRATED_HEAD
C14              BLOCKED_BY_FUNCTIONAL_COMPLETENESS
C15              BLOCKED_BY_C13_C14
C16              BLOCKED_BY_FINISHED_PRIVATE_ACCEPTANCE_PRODUCT
C17 / P27        NOT_STARTED
PUBLIC_LAUNCH    NO_GO
```

## Allowed markers

During this task, only evidence-backed partial markers may be emitted:

```text
AX_C0_CANONICAL_BASELINE_PASS
AX_C1_SUBSCRIBER_SHELL_FULL_E2E_PASS
...
AX_C17_P27_FINAL_MANIFEST_READY
```

The following markers remain prohibited until P27 and human digest approval:

```text
AXIGNAL_GLOBAL_E2E_100_PERCENT_COMPLETE
AXIGNAL_ACCEPTED_FOR_PUBLIC_LAUNCH
```
