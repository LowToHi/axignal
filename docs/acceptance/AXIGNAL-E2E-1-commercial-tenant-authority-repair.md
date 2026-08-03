# E2E-1 — Commercial passwordless tenant and ledger authority repair

## Scope

This receipt records the final diagnostic and bounded repair for the Commercial Shell post-browser SQL audit inside `E2E-1`.

It does not change the product runtime, payment lifecycle, tenant model, Stripe boundary, public launch state, library coverage, claims or programme scope.

## Observed evidence

On the consolidated candidate:

- the isolated PostgreSQL/API/web topology reached healthy state;
- legacy password login remained disabled;
- email verification and resident WebAuthn registration completed;
- the browser completed Professional selection, deterministic payment, Team upgrade, cancellation, final cancellation, rollback and persisted reload;
- the independent SQL auditor initially queried a historical tenant UUID and later applied a single human actor to every ledger event.

## Root cause 1 — tenant authority drift

The auditor retained the historical constant tenant `11111111-1111-4111-8111-111111111111`.

The current passwordless signup authority does not accept a browser- or environment-supplied tenant identifier. `identity_private.consume_signup_challenge` creates or reuses the authoritative organisation and returns its database-issued `tenant_id`. Consequently, the billing selection was correctly persisted under the passwordless session tenant, while the auditor queried an unrelated historical UUID.

## Root cause 2 — ledger actor taxonomy

The append-only payment ledger intentionally records different bounded authorities:

- explicit user requests use the authenticated subject;
- verified provider transitions use `stripe-signed-webhook`;
- the deterministic test cleanup uses `deterministic-test-rollback`.

Requiring every ledger row to carry the human subject would erase the provider-signature and rollback authority boundaries. The correct invariant is an exact actor taxonomy by ledger event type.

## Repair

The SQL auditor now:

1. requires the server-side authenticated subject from `AXIGNAL_AUTH_SUBJECT`;
2. resolves exactly one billing selection by `selected_by`;
3. derives the authoritative tenant from that persisted selection;
4. verifies selection, entitlement, ledger, receipts and rollback residue under that tenant;
5. executes the RLS isolation proof with a deterministic distinct tenant;
6. accepts only receipt dispositions defined by the current database schema: `APPLIED`, `STALE` or `IGNORED`;
7. verifies an exact ledger-event set and binds every event class to its proper actor;
8. requires provider event IDs and 64-character payload digests for signed provider transitions;
9. requires user and rollback events to remain free of provider identifiers and payload digests.

## Invariants preserved

```text
browser tenant input          != tenant authority
environment tenant fixture    != passwordless tenant authority
explicit commercial request   = authenticated subject
provider lifecycle mutation   = verified signed webhook
rollback mutation             = deterministic test authority
checkout completion           != entitlement
provider event required       = true
legacy password login         = disabled
external Stripe calls         = 0
cross-tenant visibility       = 0
active entitlement residue    = 0
pending selection residue     = 0
public launch                 = NO_GO
```

## Required revalidation

The repaired exact head must pass:

- `Commercial Shell E2E`;
- `E2E Single Candidate`;
- the bounded canonical E2E-1 matrix.

Only then may the phase emit:

```text
AX_E2E_SINGLE_CANDIDATE_PASS
```
