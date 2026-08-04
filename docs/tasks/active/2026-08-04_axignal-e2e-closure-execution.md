# AX-GE2E-P08-T03 — Subscriber Shell closure under the AXIGNAL global E2E programme

Goal ID: `AXIGNAL-GOAL-001`  
Governing authority: Contract `31`, ADR-016 and `AX-GE2E-CLOSURE-EXECUTION-002`  
Execution branch: `agent/axignal-c0-canonical-reconciliation-v1`  
C0 authority head: `fb0b93c5cf47ea08d8e6ee38950033e7224727f3`  
C1 engineering evidence head: `30e21a6eabce9a2ff909e817bde94238db1560ae`  
State: `IN_PROGRESS / ENGINEERING_E2E_PASS / HUMAN_USABILITY_AUTHORITY_PENDING / NO_PUBLIC_LAUNCH`

## Objective

Close the authenticated Subscriber Shell and Bid Workspace as the first bounded execution slice after the canonical C0 baseline, without reducing product scope, substituting engineering fixtures for human acceptance, or advancing C2 before C1 has all required authorities.

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

This does not authorize merge, source admission, commercial activation or public launch.

## C1 exact-head engineering evidence

The bounded rollback change at `30e21a6eabce9a2ff909e817bde94238db1560ae` passed the complete pull-request workflow matrix:

```text
C1_ENGINEERING_HEAD     30e21a6eabce9a2ff909e817bde94238db1560ae
MATRIX                  53 / 53 COMPLETED / SUCCESS
FAILED                  0
CANCELLED               0
NON_TERMINAL            0
```

Load-bearing evidence:

```text
Frontend Unit Contracts          30928582204  PASS
Subscriber Viewport Matrix       30928582689  PASS
E2E Technical Audit              30928582771  PASS
G5 Web Security Boundaries       30928582229  PASS
G6 Reproducibility               30928582068  PASS
Executable Spine                 30928582751  PASS
P21-T02 Seat Governance          30928582043  PASS
Commercial Shell E2E             30928582235  PASS
Stripe Paid Lifecycle            30928582321  PASS
Entitlement Runtime              30928581902  PASS
P25 Trial Abuse Runtime          30928583497  PASS
Trial Retention Lifecycle        30928583461  PASS
Full PostgreSQL Migration Matrix 30928582498  PASS
Pilot Deployment Candidate       30928582870  PASS
```

Critical browser jobs use zero retries. The engineering matrix is exact-head evidence only; it is not qualified-user research.

## C1-owned blocker disposition

The ownership manifest assigns five blockers exclusively to C1. All five are technically closed and revalidated on the canonical exact head:

```text
AX-SW-BLK-001 exact-head CI matrix                 CLOSED / PASS
AX-SW-BLK-002 unsupported enabled actions          CLOSED / PASS
AX-SW-BLK-003 continue_review mapped to pursue     CLOSED / PASS
AX-SW-BLK-011 degraded-mode provenance             CLOSED / PASS
AX-SW-BLK-014 desktop/tablet/mobile evidence       CLOSED / PASS
```

The remaining ten blockers are not C1 co-ownership:

```text
C3  AX-SW-BLK-008 AX-SW-BLK-009 AX-SW-BLK-010 AX-SW-BLK-015
C4  AX-SW-BLK-004 AX-SW-BLK-005 AX-SW-BLK-006 AX-SW-BLK-007
C14 AX-SW-BLK-012 AX-SW-BLK-013
```

They remain downstream work for their exclusive contractual packages and are not grounds for misreporting C1 engineering failure.

## Rollback rehearsal

The kill switch is:

```text
AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED=false
```

The exact-head unit contract now proves:

1. a tenant workspace mutation is persisted;
2. the ledger is captured;
3. the feature is disabled;
4. the persisted ledger remains byte-identical;
5. the feature is re-enabled;
6. the same tenant revision, requirement state and audit event are restored.

Authority:

```text
test     apps/web/tests/subscriber-workspace-server.test.ts
run      30928582204
result   PASS
```

Rollback does not delete identity, workspace, claim, billing or audit ledgers.

## Human usability authority

C1 is not canonically closed because the required qualified-user evidence does not exist yet.

The governing research contract remains:

```text
minimum participants                  8
bid/proposal managers                 >= 3
business-development or B2G managers >= 2
subject-matter reviewer               >= 1
organisation administrator           >= 1
accessibility participant/specialist  >= 1
non-English primary-locale sessions   >= 2
```

The declared task-success, navigation, authority-comprehension and accessibility thresholds must also be met. The existing `F1 Qualified-User Validation` workflow is an engineering protocol/harness; it is not evidence that eight qualified humans completed the study.

Authoritative pending record:

```text
docs/research/2026-08-01-subscriber-workspace-tooling-ux-study.md
status: HUMAN_USABILITY_EVIDENCE_PENDING
```

## Current disposition

```text
C0                       CLOSED / PASS
C1_ENGINEERING           CLOSED / PASS
C1_HUMAN_AUTHORITY       BLOCKED / MISSING
C1_CANONICAL             IN_PROGRESS
C2                       BLOCKED_BY_C1_HUMAN_AUTHORITY
PR_169                   OPEN / DRAFT / UNMERGED
MERGE                    NOT_AUTHORIZED
PUBLIC_LAUNCH            NO_GO
COMMERCIAL_ACTIVATION    NOT_AUTHORIZED
SOURCE_ADMISSION         NOT_AUTHORIZED
```

## Marker authority

Allowed and already effective:

```text
AX_C0_CANONICAL_BASELINE_PASS
```

Prohibited until the qualified-user study satisfies its complete cohort and threshold contract:

```text
AX_C1_SUBSCRIBER_SHELL_FULL_E2E_PASS
```

Prohibited until P27 and human digest approval:

```text
AXIGNAL_GLOBAL_E2E_100_PERCENT_COMPLETE
AXIGNAL_ACCEPTED_FOR_PUBLIC_LAUNCH
```

## Exact-head rule for this reconciliation

This documentary reconciliation changes the branch head. Its statements become effective only if the complete pull-request workflow matrix for the commit containing this record is terminal `success`. Any head change invalidates evidence bound to the predecessor and requires a new exact-head matrix.
