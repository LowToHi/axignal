# AX-GE2E-P08-T03 — Subscriber Shell closure under the AXIGNAL global E2E programme

Goal ID: `AXIGNAL-GOAL-001`  
Governing authority: Contract `31`, ADR-016 and `AX-GE2E-CLOSURE-EXECUTION-002`  
Execution branch: `agent/axignal-c0-canonical-reconciliation-v1`  
C0 authority head: `fb0b93c5cf47ea08d8e6ee38950033e7224727f3`  
C1 engineering and documentary evidence head: `a739b41f6e36b7e2eb9d8dd6a317101055d79523`  
State: `CLOSED / PASS / POST_LAUNCH_USABILITY_REQUIRED / NO_PUBLIC_LAUNCH_AUTHORITY_FROM_C1`

## Objective

Close the authenticated Subscriber Shell and Bid Workspace as the first bounded execution slice after the canonical C0 baseline, without reducing product scope or weakening authority boundaries.

Qualified-user usability validation remains mandatory, but it is moved behind launch because requiring external qualified users before the product is accessible creates a circular dependency. The study is now a post-launch validation gate and does not block C1, C2, P27 or launch.

The superior pre-launch execution chain remains:

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
→ launch authority
→ PL-UX-01 qualified-user Subscriber Workspace validation
```

## C0 authority

C0 is formally closed on the canonical branch:

```text
C0_HEAD                 fb0b93c5cf47ea08d8e6ee38950033e7224727f3
C0_MATRIX               53 / 53 COMPLETED / SUCCESS
C0_FAILED               0
C0_CANCELLED            0
C0_NON_TERMINAL         0
C0_MARKER               AX_C0_CANONICAL_BASELINE_PASS
```

## C1 exact-head authority

The final C1 predecessor head passed the complete pull-request workflow matrix:

```text
C1_EVIDENCE_HEAD        a739b41f6e36b7e2eb9d8dd6a317101055d79523
MATRIX                  53 / 53 COMPLETED / SUCCESS
FAILED                  0
CANCELLED               0
NON_TERMINAL            0
```

Load-bearing evidence:

```text
Contract Validation               30930376868  PASS
RC6 Exact Head Provenance         30930376635  PASS
Frontend Unit Contracts           30930380161  PASS
Subscriber Viewport Matrix        30930376877  PASS
E2E Technical Audit               30930380286  PASS
G5 Web Security Boundaries        30930380310  PASS
G6 Reproducibility                30930376777  PASS
Executable Spine                  30930380347  PASS
P21-T02 Seat Governance           30930376755  PASS
Commercial Shell E2E              30930376687  PASS
Stripe Paid Lifecycle             30930377050  PASS
Entitlement Runtime               30930376701  PASS
P25 Trial Abuse Runtime           30930376749  PASS
Trial Retention Lifecycle         30930376649  PASS
Full PostgreSQL Migration Matrix  30930376637  PASS
Pilot Deployment Candidate        30930383905  PASS
```

Critical browser jobs use zero retries.

## C1-owned blocker disposition

The ownership manifest assigns five blockers exclusively to C1. All five are closed:

```text
AX-SW-BLK-001 exact-head CI matrix                 CLOSED / PASS
AX-SW-BLK-002 unsupported enabled actions          CLOSED / PASS
AX-SW-BLK-003 continue_review mapped to pursue     CLOSED / PASS
AX-SW-BLK-011 degraded-mode provenance             CLOSED / PASS
AX-SW-BLK-014 desktop/tablet/mobile evidence       CLOSED / PASS
```

The remaining subscriber blockers retain their exclusive downstream ownership:

```text
C3  AX-SW-BLK-008 AX-SW-BLK-009 AX-SW-BLK-010 AX-SW-BLK-015
C4  AX-SW-BLK-004 AX-SW-BLK-005 AX-SW-BLK-006 AX-SW-BLK-007
C14 AX-SW-BLK-012 AX-SW-BLK-013
```

They do not reopen C1.

## Rollback rehearsal

The kill switch is:

```text
AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED=false
```

The exact-head contract proves:

1. a tenant workspace mutation is persisted;
2. the ledger is captured;
3. the feature is disabled;
4. the persisted ledger remains byte-identical;
5. the feature is re-enabled;
6. the same tenant revision, requirement state and audit event are restored.

Authority:

```text
test     apps/web/tests/subscriber-workspace-server.test.ts
run      30930380161
result   PASS
```

Rollback does not delete identity, workspace, claim, billing or audit ledgers.

## Post-launch qualified-user validation

The qualified-user study is retained without weakening its cohort, tasks or thresholds. Its sequencing changes only:

```text
previous position       pre-launch C1 blocker
corrected position      post-launch validation gate PL-UX-01
tracking authority      GitHub issue #170
pre-launch blocker      false
C1 blocker              false
C2 blocker              false
P27 blocker             false
mandatory after launch  true
```

The study activates after AXIGNAL is launched under the final P27 and human launch authority and real qualified users can use the normal subscriber journey.

Required cohort remains:

```text
minimum participants                  8
bid/proposal managers                 >= 3
business-development or B2G managers >= 2
subject-matter reviewer               >= 1
organisation administrator           >= 1
accessibility participant/specialist  >= 1
non-English primary-locale sessions   >= 2
```

The existing `F1 Qualified-User Validation` workflow remains an engineering protocol and analysis harness. It does not impersonate human evidence.

A critical post-launch safety, authority, privacy, accessibility or integrity finding must create corrective work and may invoke the relevant kill switch. Non-critical usability findings enter the governed product backlog and do not retroactively invalidate a correctly authorized launch.

## Current disposition

```text
C0                       CLOSED / PASS
C1_ENGINEERING           CLOSED / PASS
C1_ROLLBACK              CLOSED / PASS
C1_CANONICAL             CLOSED / PASS
C1_POST_LAUNCH_STUDY     OPEN / REQUIRED / NON_BLOCKING
C2                       AUTHORIZED_TO_BEGIN
PR_169                   DRAFT / UNMERGED
MERGE                    NOT_AUTHORIZED
PUBLIC_LAUNCH            NO_GO_PENDING_C2_C17_AND_P27
COMMERCIAL_ACTIVATION    NOT_AUTHORIZED
SOURCE_ADMISSION         NOT_AUTHORIZED
```

The human study is no longer the reason for `PUBLIC_LAUNCH=NO_GO`. Launch remains blocked only by the unfinished downstream closure packages and final P27 authority.

## Marker authority

Allowed after this documentary head itself passes the complete exact-head matrix:

```text
AX_C1_SUBSCRIBER_SHELL_FULL_E2E_PASS
```

The marker means C1's contracted pre-launch engineering slice is complete. It does not claim that the post-launch usability study has already occurred.

Still prohibited until C17/P27 and explicit human launch authority:

```text
AXIGNAL_GLOBAL_E2E_100_PERCENT_COMPLETE
AXIGNAL_ACCEPTED_FOR_PUBLIC_LAUNCH
```

## Exact-head rule

This sequencing correction changes the branch head. Its statements become effective only if the complete pull-request workflow matrix for the commit containing this record is terminal `success`. Any later head change invalidates evidence bound to this documentary head and requires a new exact-head matrix.
