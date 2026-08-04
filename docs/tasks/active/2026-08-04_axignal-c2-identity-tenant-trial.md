# AXIGNAL C2 — Identity, Session, Tenant, Seats and Trial

```text
Contract                 AX-GE2E-CLOSURE-EXECUTION-002
Gate                     C2
Task authority           AX-GE2E-P03-T02
Implementation renewal   P25-T01 identity/passwordless/trial abuse
State                    EVIDENCE_READY
Required marker          AX_C2_IDENTITY_TENANT_TRIAL_PASS
Validated predecessor    11d8c2435ff899d0276dd4f0d6c51da45775e0dc
Previous canonical gate  C1 CLOSED / PASS
Next gate                C3 AUTHORIZED_ONLY_AFTER_ATTESTATION_HEAD_PASS
Merge                    NOT_AUTHORIZED
Public launch            NO_GO
```

## Scope decision

```text
Passwordless recovery evidence       CLOSED / PASS
P25 exact-head renewal                CLOSED / PASS
Organisation and membership evidence REUSED / PASS
Seat governance                      REUSED / PASS
Entitlement runtime                  REUSED / PASS
Trial retention                      REUSED / PASS
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

## Material gap closed

The existing UI, API and PostgreSQL functions already implemented recovery, but the prior browser journey did not execute the complete boundary. The C2 change added exact-head evidence for:

- recovery from another browser while a session remained active;
- immediate invalidation of that session;
- revocation of the previous authenticator;
- one-time recovery-code replay denial;
- replacement passkey registration;
- replacement recovery-code issuance;
- continuity of the same tenant and trial.

No second identity, tenant, membership, entitlement or trial implementation was introduced.

## Recovery evidence

The existing `tests/e2e/identity-passwordless.spec.ts` uses two independent browser contexts and two virtual CTAP2 authenticators:

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

The exact-head P25 artifact is:

```text
artifact_id  8906279065
run_id       30943693350
head_sha     11d8c2435ff899d0276dd4f0d6c51da45775e0dc
digest       sha256:6a9a5e86dfd1ea4c18db7267a99596f22305d2e2aff72e346ab9dcf40aa54576
```

It contains the non-sensitive marker:

```text
artifacts/c2-identity-recovery-browser.json
```

## Validated predecessor matrix

```text
AXIGNAL PR Gate — Core       30943693385  SUCCESS
AXIGNAL PR Gate — Runtime    30943693350  SUCCESS
AXIGNAL PR Gate — Domain     30943693506  SUCCESS
Remote Pilot Operations      30943693253  SUCCESS
Procurement Admission        30943692976  SUCCESS
```

The validated predecessor proves:

```text
Passwordless signup and rotation        PASS
Recovery and authenticator replacement  PASS
Organisation and membership             PASS
Seat governance                         PASS
Trial READY → ACTIVE                     PASS
Token/cost/concurrency limits            PASS
Expiry → read-only retention             PASS
Deletion/purge/restore                   PASS
Protected routes                         PASS
Complete exact-head matrix               PASS
```

## Closure rule

The predecessor matrix proves the implementation, but does not make this documentary head authoritative by itself. The C2 marker is carried by a separate closure attestation and becomes effective only when the complete matrix for the commit containing that attestation is terminal success.

Until then:

```text
AX_C2_IDENTITY_TENANT_TRIAL_PASS = CANDIDATE_NOT_EFFECTIVE
C2                              = EVIDENCE_READY
C3                              = BLOCKED_BY_ATTESTATION_HEAD_MATRIX
```

The closure attestation preserves:

```text
PR_STATE               OPEN / DRAFT / UNMERGED
MERGE                   NOT_AUTHORIZED
PUBLIC_LAUNCH           NO_GO
COMMERCIAL_ACTIVATION   NOT_AUTHORIZED
SOURCE_ADMISSION        NOT_AUTHORIZED
```
