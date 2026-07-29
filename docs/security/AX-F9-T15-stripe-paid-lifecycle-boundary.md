# AX-F9-T15 — Stripe Paid Lifecycle Boundary

Goal ID: `AXIGNAL-GOAL-001`

State: `IMPLEMENTED_CANDIDATE`

## Scope

This cut implements the disabled-by-default technical boundary for:

```text
explicit paid plan selection
→ Stripe-hosted subscription Checkout
→ raw-body webhook signature verification
→ idempotent provider event receipt
→ paid entitlement activation
→ no monthly AI token quota or token overage billing
→ explicit upgrade
→ cancellation at period end or immediately
→ append-only payment ledger
→ terminal rollback
```

It does not activate public billing, validate prices, create production resources, or accept `AX-F9-T15`.

## Canonical Stripe account

AXIGNAL billing is pinned to:

```text
acct_1TybkH8feyjV8Pem
```

The runtime verifies `/v1/account` before provider mutations. A secret associated with another Stripe account fails closed.

The implementation is sandbox-only by default. Live secret keys and live webhook events are rejected while `AXIGNAL_STRIPE_SANDBOX_ONLY=true`.

## Kill switches

All default to disabled except sandbox-only mode:

```text
AXIGNAL_BILLING_RUNTIME_ENABLED=false
AXIGNAL_STRIPE_CHECKOUT_ENABLED=false
AXIGNAL_STRIPE_WEBHOOKS_ENABLED=false
AXIGNAL_STRIPE_LIFECYCLE_ENABLED=false
AXIGNAL_STRIPE_SANDBOX_ONLY=true
```

The switches are independent. Disabling Checkout does not disable signed webhook reconciliation. Disabling lifecycle changes blocks upgrade and cancellation without weakening webhook verification.

## Explicit selection and no automatic trial conversion

A trial activation or expiry has no Stripe dependency and emits no provider command.

Checkout requires an authenticated tenant and a body containing:

```text
operation_id
plan_code
confirm_paid_selection=true
```

The request body rejects `tenant_id`, provider price IDs, success URLs and cancel URLs. Tenant identity is resolved from the signed server assertion. Price IDs and redirect URLs are server configuration.

Checkout Sessions use `mode=subscription` and contain no Stripe trial parameter. The controlled AXIGNAL trial is not a Stripe subscription trial and never collects a payment method or schedules an automatic charge.

## Entitlement authority

The application role can request a selection and record the Checkout Session returned by Stripe. It cannot directly:

- insert or activate a paid entitlement;
- mutate payment ledger entries;
- create webhook receipts;
- apply provider lifecycle events;
- execute terminal rollback.

Only `axignal_billing_worker` can invoke the typed provider-event function. The worker has no direct table-read or table-write grant over product data.

A paid entitlement is created or changed only after a verified Stripe event reaches `tenant_private.apply_stripe_billing_event`.

Paid entitlement semantics remain:

```text
entitlement_kind = PAID_MONTHLY
unlimited_ai_tokens = true
token_budget_total = NULL
no token overage invoice path
```

ResearchRun, source-right, concurrency, document, export and safety limits remain independent of AI-token semantics.

## Webhook verification and idempotency

The endpoint reads the unmodified request bytes and verifies the `Stripe-Signature` HMAC over:

```text
timestamp + "." + raw_body
```

The default tolerance is 300 seconds and is bounded to 30–900 seconds.

For supported events, the runtime stores only:

- provider event ID;
- event type and creation time;
- mapped tenant and selection IDs;
- sandbox/live flag;
- configured provider account ID;
- SHA-256 payload digest;
- disposition.

Raw Stripe payloads, card data and payment-method details are not persisted.

Duplicate delivery with the same event ID and digest returns `DUPLICATE` without repeating transitions. Reuse of an event ID with a different digest fails with conflict. Older events are recorded as `STALE` and cannot reactivate a cancelled or rolled-back subscription.

## Supported provider events

```text
checkout.session.completed
checkout.session.expired
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
invoice.paid
invoice.payment_failed
```

Unsupported signed events return success with `IGNORED_UNSUPPORTED` and do not mutate tenant state.

A Stripe subscription status of `trialing` is rejected. AXIGNAL does not permit a provider-side auto-converting trial in this cut.

## Upgrade semantics

The only self-serve upgrade in v0.1 is:

```text
PROFESSIONAL_MONTHLY → TEAM_MONTHLY
```

It requires explicit confirmation. The provider command uses `proration_behavior=none`, so this candidate does not issue an immediate prorated charge. The new plan becomes the subscription price for the next invoice, while the entitlement transition follows the signed subscription update.

This is a conservative pilot policy, not a validated commercial decision. Alternative proration behaviour requires an explicit versioned contract and new tests.

## Cancellation

The user must explicitly choose one of two modes:

- `cancel_at_period_end=true`: access remains active until Stripe reports the terminal cancellation;
- `cancel_at_period_end=false`: the provider subscription is deleted immediately and the signed deletion event cancels the paid entitlement.

Cancellation releases all open AI reservations linked to the paid entitlement. A cancelled entitlement cannot authorize new operations.

## Payment ledger

`tenant_private.payment_ledger_entries` is append-only and tenant-isolated. It records user selections, upgrade/cancellation requests, provider events and rollback without storing raw payment credentials.

The ledger contains amount and currency only when present in a supported invoice event. It is not an accounting ledger and does not replace legally required invoicing, tax or financial records.

## Rollback

Rollback is an isolated billing-worker operation and must follow a successful provider cancellation command.

It:

1. releases all open reservations;
2. cancels the paid entitlement;
3. clears pending plan state;
4. marks the selection `ROLLED_BACK`;
5. appends an immutable rollback entry.

After rollback:

```text
future provider subscription charge capability = absent
active AXIGNAL paid entitlement = absent
reserved AI capability = zero
```

The cut does not automatically refund already settled invoices. Refunds require explicit financial authority, provider evidence and a separate audited operation.

## Known limitations

- The connected Stripe MCP account currently resolves to a different live account, so no remote AXIGNAL Stripe resources were created or mutated by this cut.
- The always-on CI test uses a local Stripe sandbox contract server and real PostgreSQL. It proves request shape, signatures, retries, event ordering, authority and lifecycle state, but not an external Stripe network round trip.
- A separate external sandbox smoke must verify the AXIGNAL test key, account ID, Price IDs, endpoint secret and Checkout creation before this evidence can satisfy the remaining payment acceptance gate.
- Enterprise contracts, invoices, tax, refunds, disputes, dunning and bank-transfer reconciliation remain outside this cut.

## Evidence

```text
.github/workflows/stripe-paid-lifecycle.yml
scripts/verify_stripe_billing_contract.py
scripts/verify_stripe_paid_lifecycle_e2e.py
scripts/verify_stripe_billing_authority_e2e.py
```

The implementing skill cannot self-approve the phase gate. `AX-F9-T15` remains `IN_PROGRESS` until external sandbox evidence, paid-event evidence, user research and the remaining security, privacy and commercial gates pass.
