# AXIGNAL C2 — Identity, Session, Tenant, Seats and Trial

```text
Contract                 AX-GE2E-CLOSURE-EXECUTION-002
Gate                     C2
Task authority           AX-GE2E-P25-T01 renewal
State                    IN_PROGRESS
Required marker          AX_C2_IDENTITY_TENANT_TRIAL_PASS
Previous canonical gate  C1 CLOSED / PASS
Next gate                C3 BLOCKED_BY_C2
Merge                    NOT_AUTHORIZED
Public launch            NO_GO
```

## Scope decision

```text
Passwordless recovery evidence       MUST_CLOSE / EVIDENCE_ONLY
P25 exact-head renewal                MUST_CLOSE
Organisation and membership evidence REUSE_EXISTING_AUTHORITY
Seat governance                      REUSE_EXISTING_AUTHORITY
Entitlement runtime                  REUSE_EXISTING_AUTHORITY
Trial retention                      REUSE_EXISTING_AUTHORITY
Second identity implementation       REJECTED_OVERENGINEERING
C3 persistence changes               DEFERRED_CONTRACTED
C4 research changes                  DEFERRED_CONTRACTED
```

C2 composes the existing canonical identity, organisation, seat, entitlement and retention authorities. It does not create another account service, tenant resolver, membership model, entitlement engine or trial ledger.

## Required journey

```text
signup
→ verify email
→ register passkey
→ create identity and tenant
→ resolve organisation relationship
→ issue opaque session
→ logout and revoke
→ authenticate and rotate session
→ step-up when required
→ recover from a sessionless browser
→ revoke every active pre-recovery session
→ revoke every previous authenticator
→ reject recovery-code replay
→ register replacement passkey
→ issue replacement AAL2 session
→ preserve tenant and trial
→ enforce protected routes
```

Trial authority:

```text
READY
→ first admitted AI use
→ ACTIVE
→ token and cost reservations
→ concurrency and seat limits
→ expiry
→ server-enforced read-only retention or governed paid conversion
```

## Material gap identified

The integrated head already demonstrated signup, WebAuthn registration, AAL2 authentication, logout, session rotation, tenant-owned trial, alias reuse, step-up, budgets, concurrency, memberships, seats, entitlement and retention.

The missing C2 evidence was the complete recovery boundary. The existing UI, API and PostgreSQL functions were present, but the exact-head browser journey did not execute:

- recovery from another browser while a session remained active;
- immediate invalidation of that session;
- revocation of the previous authenticator;
- one-time recovery-code replay denial;
- replacement passkey registration;
- replacement recovery-code issuance;
- continuity of the same tenant and trial.

## Bounded implementation

The existing `tests/e2e/identity-passwordless.spec.ts` now uses two independent browser contexts and two virtual CTAP2 authenticators:

```text
browser A
→ register original passkey
→ logout
→ authenticate
→ hold active rotated session

browser B without session
→ consume one recovery code
→ register replacement passkey
→ receive eight replacement codes
→ receive new AAL2 session

browser A
→ active session rejected after recovery
→ old credential still present locally
→ server rejects old credential
→ consumed recovery code rejected on replay

browser B
→ logout replacement session
→ replacement passkey authenticates
→ new rotated session issued
```

The journey emits the non-sensitive marker:

```text
artifacts/c2-identity-recovery-browser.json
```

The P25 workflow fails closed unless that marker proves:

- session rotation;
- one-time recovery code;
- revocation of prior sessions;
- revocation of prior authenticators;
- replacement passkey;
- eight replacement codes;
- AAL2 replacement session;
- tenant continuity;
- preserved trial state;
- zero external identity-provider and model calls;
- public signup remains unauthorized.

## Existing authorities to renew on the final head

```text
P25 identity/passwordless/trial abuse
P21-T02 organisation/membership/seat governance
Entitlement Runtime
Trial Retention Lifecycle
G5 and protected-route boundaries
Full Migration Matrix
Core, Runtime and Domain canonical gates
```

## Acceptance status

```text
Passwordless signup and rotation        PENDING_FINAL_HEAD
Recovery and authenticator replacement  PENDING_FINAL_HEAD
Organisation and membership             PENDING_FINAL_HEAD
Seat governance                         PENDING_FINAL_HEAD
Trial READY → ACTIVE                     PENDING_FINAL_HEAD
Token/cost/concurrency limits            PENDING_FINAL_HEAD
Expiry → read-only retention             PENDING_FINAL_HEAD
Deletion/purge/restore                   PENDING_FINAL_HEAD
Protected routes                         PENDING_FINAL_HEAD
Complete exact-head matrix               PENDING_FINAL_HEAD
```

The marker remains prohibited:

```text
AX_C2_IDENTITY_TENANT_TRIAL_PASS = NOT_EMITTED
```

C3 remains blocked until every required item is terminal success on one exact SHA and this record is updated to `CLOSED / PASS` without changing that authority silently.
