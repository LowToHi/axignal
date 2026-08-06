# P21-T02 — End-to-End Seat Governance

**Task:** `AX-GE2E-P21-T02`  
**Baseline:** P23-T03 exact head `1bc87c572a576895ad6037179509f24531b726e2`  
**State:** `ENGINEERING IMPLEMENTATION / COMMERCIAL ACTIVATION BLOCKED`

## Decision

Professional and Team are flat-tier packages:

```text
Professional  €149/month  → capacity 3
Team          €399/month  → capacity 15
```

Stripe bills one recurring package unit. It does not count people, resolve tenant
authority or grant memberships. AXIGNAL materialises the plan as a tenant seat
entitlement and governs every allocation internally.

The controlled seven-day trial receives capacity two, preserving the earlier
controlled-trial boundary.

## Authority chain

```text
verified billing or trial entitlement
→ plan-to-capacity reconciliation
→ tenant seat entitlement
→ seat reservation or active allocation
→ explicit membership
→ role binding
→ server-resolved access decision
→ RLS-protected product operation
→ append-only audit
```

No browser value, model output, worker payload, Stripe customer identifier or
subscription label can create a member or widen capacity.

## Persistent model

### `organisation_seat_entitlements`

One current materialised capacity record per tenant:

- source product entitlement;
- source billing selection;
- plan;
- flat-tier capacity;
- ACTIVE, READ_ONLY, SUSPENDED or CANCELLED state;
- policy version and validity.

A database trigger reconciles trial activation, paid activation, Professional →
Team upgrade, suspension, cancellation and expiry. A capacity reduction is
transactionally denied if occupied seats exceed the target plan.

### `organisation_memberships`

Explicit principal-to-tenant membership with:

- immutable tenant scope;
- opaque principal identifier;
- normalised email;
- lifecycle state;
- workspace scope;
- join, suspension and revocation evidence.

### `organisation_invitations`

Single-use, email-bound invitations with:

- idempotent operation identifier;
- requested role;
- token digest only;
- bounded expiry;
- delivery provider;
- accepted, expired, revoked and delivery-failed states.

### `organisation_seat_allocations`

The conserved seat resource:

```text
RESERVED invitation
→ ACTIVE membership
→ RELEASED
```

Acceptance converts the same row from reservation to active allocation. It does
not create a second seat.

### `membership_role_bindings`

Typed roles:

- Organisation Owner;
- Organisation Admin;
- B2G Manager;
- Research Operator;
- Bid Reviewer;
- Viewer;
- Billing Admin;
- Auditor.

The last active owner cannot be revoked or demoted.

### `membership_audit_events`

Append-only evidence for owner bootstrap, reservations, acceptance, expiry,
delivery failure, revocation and role changes.

## Capacity and concurrency

Every invitation locks the tenant seat entitlement before it counts active and
reserved allocations.

```text
lock tenant capacity
→ expire stale reservations
→ recount ACTIVE + RESERVED
→ deny when count >= capacity
→ insert invitation and reservation
→ commit
```

Two concurrent requests competing for the final seat cannot both succeed.

## Seat consumption

| State | Consumes capacity |
|---|---:|
| Active human membership | Yes |
| Pending unexpired invitation | Yes |
| Suspended membership | Yes |
| Revoked or expired membership | No |
| Expired, revoked or failed invitation | No |
| Service principal or internal worker | No |
| Time-bounded platform support access | No |

Suspended members retain their allocation so suspension cannot be used to
oversubscribe a package. Revocation releases it.

## Access enforcement

When `AXIGNAL_SEAT_GOVERNANCE_ENABLED=true`, authenticated API requests are
intersected with the membership and seat decision:

```text
signed identity assertion
∩ server-resolved tenant
∩ active membership
∩ active role bindings
∩ current seat entitlement
∩ request method
```

- ACTIVE permits bounded reads and writes.
- READ_ONLY permits GET/HEAD/OPTIONS and denies writes.
- SUSPENDED and CANCELLED deny product access.
- Billing, trial activation, owner bootstrap and invitation acceptance remain
  explicit pre-membership paths.
- Missing or unavailable governance state fails closed.

## Invitation delivery

Production delivery requires an approved SMTP configuration and a public
acceptance URL. Failure compensates the reservation:

```text
reserve seat
→ attempt delivery
→ delivery failure
→ mark DELIVERY_FAILED
→ release reserved seat
```

The deterministic test provider can expose the raw acceptance token only when
both `AXIGNAL_ENVIRONMENT=test` and `AXIGNAL_TEST_RUNTIME_ENABLED=true`.
Production persists only SHA-256 token digests.

## User interface

The authenticated product shell exposes:

- current plan and capacity;
- active, reserved and available counts;
- approved owner bootstrap;
- invitation form with role selection;
- active members and role changes;
- pending invitation revocation;
- member revocation;
- explicit capacity-exhaustion and upgrade signals.

The UI is not authoritative. Every operation repeats policy in PostgreSQL.

## Upgrade and downgrade

### Professional → Team

A verified billing event changes the product entitlement plan. The seat trigger
raises capacity from three to fifteen without replacing memberships.

### Team → Professional

The downgrade is denied while `ACTIVE + RESERVED > 3`. Administrators must
revoke invitations or memberships first. No silent eviction or arbitrary member
selection is permitted.

### Cancellation and dunning

- PAST_DUE or disputed billing suspends the seat entitlement.
- Pending invitations are revoked and reserved seats released.
- Terminal cancellation changes seat authority to CANCELLED.
- Existing records and audit evidence remain for bounded retention.
- No refund or provider event reactivates membership authority silently.

## Security controls

- PostgreSQL `ENABLE` and `FORCE ROW LEVEL SECURITY`;
- tenant context set transaction-locally by the server;
- application role cannot mutate governance tables directly;
- typed `SECURITY DEFINER` functions with fixed `search_path`;
- no client tenant, role or capacity input;
- idempotent invite operations;
- single-use invitation token digest;
- last-owner protection;
- cross-tenant non-disclosure;
- append-only audit;
- test-provider confinement;
- fail-closed delivery and authorization.

## Evidence boundary

```text
pricing metadata       != governed capacity
governed capacity      != commercial validation
invitation delivered   != user activation
membership active      != unrestricted authority
CI green               != public launch
```

The implementation may be engineering-ready while prices, public signup,
production SMTP, Stripe live and commercial activation remain independently
blocked.
