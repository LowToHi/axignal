# P24 — Global Acceptance, Paid Evidence and Launch Gate

Task: `AX-GE2E-P24-T01`

Baseline: exact P23 head `dec5473ad590fdb5de941d6b383e2ab01136befe`.

## Purpose

P24 is the final decision layer for AXIGNAL. It does not repeat the individual phase contracts. It binds their exact evidence, executes representative integrated journeys, distinguishes technical payment verification from commercial evidence and produces a fail-closed launch decision.

The initial state is deliberately:

```text
BLOCKED_PENDING_REAL_EVIDENCE
```

The implementation of this contract is not itself global acceptance and cannot authorize launch.

## Truth boundary

```text
all phase contracts exist       != integrated product accepted
all CI checks pass              != real environment accepted
sandbox billing works           != Stripe live accepted
founder test payment settles    != independent paid demand
one paid invoice                != completed customer value
controlled pilot                != public launch
public launch                   != general availability
model recommendation            != launch authority
```

## Acceptance chain

```text
exact P17–P23 heads
→ transitive contract verification
→ integrated global journeys
→ complete Stripe sandbox round trip
→ production, security, DR and UX evidence
→ controlled Stripe live technical payment
→ independent paid customer evidence
→ finance reconciliation
→ typed human acceptance
→ controlled live pilot
→ bounded public cohort
→ general availability only after renewal and cohort stability
```

## Global journeys

P24 requires evidence for ten integrated journeys:

1. Public interest to controlled access.
2. Authenticated intent to persistent `InvestigationContext`.
3. Evidence to proposed claim to reviewed claim to human decision.
4. Library reuse with provenance and rights.
5. Team collaboration with tenant isolation.
6. Enterprise identity, API and private-data boundaries.
7. Paid subscription to reconciled entitlement.
8. Renewal, payment failure, recovery and cancellation.
9. Incident, isolated restore, failover and failback.
10. Keyboard, mobile and assistive-technology completion.

Fixtures and synthetic events may validate deterministic branches but cannot satisfy environment-specific gates.

## Paid evidence ladder

### Level 1 — Sandbox technical evidence

Required:

- Stripe-hosted Checkout;
- provider-delivered signed events;
- subscription and first settled invoice;
- Test Clock renewal;
- payment failure and dunning state;
- payment recovery;
- cancellation;
- append-only ledger reconciliation;
- entitlement projection.

This validates the integration. It does not permit live billing or launch.

### Level 2 — Controlled live technical evidence

Required before admitting any external paid tenant:

- restricted live credential;
- separately created live Product and Price objects;
- a small real charge;
- settlement and live invoice;
- signed live webhook delivery;
- reconciled AXIGNAL ledger;
- entitlement matching provider state;
- cancellation or refund path.

A founder or related-party payment may satisfy this technical level only. It does not count as customer evidence.

### Level 3 — Independent paid customer evidence

Required for bounded public launch:

- an unrelated external organization;
- explicit terms and privacy acceptance;
- settled provider invoice;
- signed provider events;
- reconciled ledger;
- tenant-matched entitlement;
- at least one completed AXIGNAL value workflow;
- at least fourteen observation days;
- no active dispute;
- no refund during the observation window.

The contract starts with one independent paid tenant as the minimum evidence for a bounded launch. This is a gate for controlled progression, not a claim of product-market fit.

A Test Clock renewal is valid sandbox lifecycle evidence but is not real renewal evidence for general availability.

## Launch modes

### `NO_GO`

No live tenant, public traffic or paid media.

### `CONTROLLED_LIVE_PILOT`

- Maximum five explicitly admitted tenants.
- Stripe live may be enabled only for those tenants.
- No open public signup.
- No paid media.
- Every admission is auditable and reversible.

### `BOUNDED_PUBLIC_LAUNCH`

- Maximum twenty-five tenants.
- Public traffic may be opened progressively.
- Independent paid customer evidence is mandatory.
- No paid media by default.
- Expansion requires healthy SLOs and no stop conditions.

### `GENERAL_AVAILABILITY`

Requires all bounded-launch gates plus:

- real later-period renewal evidence;
- stable bounded cohorts;
- support readiness;
- renewed exact-manifest approvals.

Paid media remains a separate budget authority even after general availability.

## Typed human authority

The acceptance manifest digest must be approved by:

- Product Acceptance Authority;
- Security Acceptance Authority;
- SRE Release Authority;
- Finance/Billing Authority;
- Legal/Privacy Authority.

Commercial Launch Authority selects the allowed launch mode after those domain approvals. A head change invalidates every approval because the manifest digest changes.

CI, models, workers, browser clients and provider events cannot grant this authority.

## Stop conditions

Any of the following freezes expansion and can trigger rollback:

- critical security finding;
- cross-tenant disclosure;
- billing reconciliation mismatch;
- excessive webhook signature failures;
- provider/entitlement mismatch;
- restore verification failure;
- fast error-budget burn;
- critical accessibility regression;
- revocation of evidence supporting a material public claim;
- an open payment dispute in the controlled cohort.

Stop conditions fail closed. Incident mitigation can continue, but cohort expansion cannot.

## Rollback

Launch rollback must:

- use a verified immutable artifact;
- preserve provider events, invoices, ledger records and audit history;
- preserve or revoke access according to verified provider state;
- stop new admissions and new spend;
- never delete customer financial evidence;
- produce an append-only rollback decision and reconciliation digest.

## Evidence manifest

`data/acceptance/p24-evidence-manifest-template.v0.1.json` is intentionally marked `TEMPLATE_NOT_EVIDENCE`.

Real execution must replace every `MISSING` field with sanitized digests and hashed external identifiers. Secrets, raw payment-method details, private customer documents and full research payloads must never be placed in the artifact.

## Current decision

```text
engineering contract: implemented
real integrated journeys: missing
complete sandbox round trip: missing
controlled live payment: missing
independent paid customer: missing
real security acceptance: missing
real restore evidence: missing
real UX/browser evidence: missing
human approvals: missing
launch decision: NO_GO
```

This status is correct. P24 is complete as an executable acceptance contract only after CI passes; AXIGNAL itself is launchable only after the real evidence manifest and typed approvals satisfy the gate.
