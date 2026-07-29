# AX-F9-T15 — Entitlement Runtime Security Boundary

Status: `CANDIDATE / DISABLED BY DEFAULT / COMMERCIAL VALIDATION NOT CLAIMED`

## Accepted implementation target

This cut implements only the server-side entitlement and trial token-ledger spine:

```text
authenticated identity
→ server-resolved tenant
→ explicit controlled-trial activation
→ transactional token reservation
→ deterministic AXIGNAL-only scope decision
→ short-lived typed capability token
→ reconciliation or release
→ exhaustion or expiry fail-closed
→ read-only preservation of prior work
```

## Independent kill switches

- `AXIGNAL_TRIAL_RUNTIME_ENABLED=false` blocks new trial activation.
- `AXIGNAL_END_USER_AI_ENABLED=false` blocks new AI authorisation.
- Reconciliation and release remain available after the AI kill switch so an in-flight reservation cannot become stranded.
- Stripe, billing and public trial activation are not wired in this cut.

## Tenant and authority boundary

- Tenant identity comes only from the signed server assertion.
- Request bodies reject unknown fields and never accept `tenant_id` or `organisation_id`.
- Entitlements, reservations and events use PostgreSQL `FORCE ROW LEVEL SECURITY`.
- Capability tokens bind tenant, reservation, operation and capability and expire within five minutes.
- The token ledger grants no model, source-admission, canonical-claim or external-action authority.

## Trial invariants

- exactly one controlled trial may ever be activated per tenant;
- duration is exactly seven days;
- cumulative organisation budget is exactly 1,000,000 tokens;
- no daily reset, overage or silent conversion exists;
- reservation occurs before execution under a row lock;
- reconciliation cannot exceed the reservation;
- expiry transitions the entitlement to `READ_ONLY` without deleting evidence or dossiers.

## Paid-plan invariant

`PAID_MONTHLY` entitlements have `unlimited_ai_tokens=true`, `token_budget_total=NULL` and no token-overage path. Safety, source-right, concurrency and abuse controls remain outside the token quota model.

## Evidence required before merge

- focused lint and unit tests;
- normative policy verification;
- two-connection concurrent overspend test;
- exact exhaustion and idempotent replay;
- cross-tenant RLS denial;
- expiry to read-only;
- release with zero reserved-token residue;
- paid no-quota reservation and reconciliation;
- append-only event mutation rejection.

## Explicit non-claims

This implementation does not validate pricing, willingness to pay, paid Design Partners, gross margin, public acquisition, Stripe configuration or customer-facing legal terms. Those remain acceptance gates for AX-F9-T15.
