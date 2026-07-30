# AX-F9-T15 — Commercial Shell Deterministic Test Boundary

Status: `IN_PROGRESS / TEST-ONLY / EXTERNAL STRIPE MISSING`

## Purpose

Validate the authenticated AXIGNAL commercial product shell without depending on
an external Stripe account or representing synthetic provider events as payment
evidence.

## Authority chain

```text
authenticated identity
→ server-resolved tenant
→ explicit paid selection
→ deterministic hosted test checkout
→ signed raw-body provider event
→ existing billing worker
→ persistent paid entitlement
→ upgrade or cancellation
→ append-only ledger
→ rollback
```

The deterministic provider cannot create an entitlement directly. It may only
produce the same typed event envelope accepted by the existing signed webhook
boundary. The billing worker retains sole paid-lifecycle mutation authority.

## Activation gates

All three settings are mandatory:

```text
AXIGNAL_BILLING_PROVIDER=test
AXIGNAL_TEST_RUNTIME_ENABLED=true
AXIGNAL_ENVIRONMENT=test
```

The provider and its checkout page fail closed outside that conjunction. The
client cannot select the provider, tenant, event ID, provider payload, plan
mapping, subscription identifiers or event timestamp.

## Explicit exclusions

- no external Stripe request;
- no live Stripe resource;
- no card or payment method;
- no commercial payment evidence;
- no pricing validation;
- no trial conversion;
- no direct entitlement activation;
- no raw webhook payload persistence;
- no production activation.

## Evidence semantics

Every artifact must state:

```json
{
  "provider": "DETERMINISTIC_TEST_PROVIDER",
  "external_stripe_verified": false,
  "commercial_payment_evidence": false,
  "external_stripe_calls": 0
}
```

Passing this boundary does not complete `AX-F9-T15`, does not set global
`rollback.tested=true`, and does not authorise billing, public trial or live
charging.
