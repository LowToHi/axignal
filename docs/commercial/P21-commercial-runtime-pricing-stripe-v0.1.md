# P21 — Commercial Runtime, Pricing and Stripe

**Task:** `AX-GE2E-P21-T01`  
**Engineering baseline:** `87b30a1035b557040dd33c5f0acedc62d0ebfa93`  
**State:** `BLOCKED`  
**Evidence status:** `ENGINEERING_EVIDENCE_READY`  
**Canonical activation:** `false`  
**Commercial activation:** `false`  
**Live Stripe payments:** `false`

## Objective

Validate packaging, entitlements, Stripe, pricing, payments, cancellation, margin and operating economics without turning provider state, commercial assumptions or engineering evidence into launch authority.

## Frozen inputs

P21 composes five exact P20-era contracts:

1. P20 Enterprise/API/private-data runtime.
2. F9 entitlement token ledger.
3. F9 entitlement hardening.
4. F9 trial and retention lifecycle.
5. F9 Stripe paid lifecycle.

Each binding is engineering evidence only. None is independently canonical or commercially active.

## Architecture

| Module | Boundary |
|---|---|
| `PACKAGE_CATALOG` | Versioned products, packages, capabilities, seats and support tiers |
| `PRICE_BOOK_AND_LOCALIZATION` | Server-side prices, currencies, discounts and candidate localization |
| `ENTITLEMENT_POLICY` | Derives bounded access from ledger, policy, rights and tenant state |
| `STRIPE_CUSTOMER_CHECKOUT` | Sandbox Checkout Sessions with server-owned price mappings |
| `SUBSCRIPTION_AND_PAYMENT_LEDGER` | Verified, append-only, idempotent provider-event projection |
| `CANCELLATION_REFUND_DUNNING` | Period-end cancellation, bounded refund and failed-payment transitions |
| `TAX_INVOICE_RECONCILIATION` | Registration-gated tax calculation and invoice/credit-note evidence |
| `UNIT_ECONOMICS_AND_MARGIN` | Assumption-bound contribution-margin and stress scenarios |

## Truth boundaries

```text
package definition        != product availability
candidate price           != approved public price
Stripe Product or Price   != entitlement
checkout created          != payment
checkout completed        != settled funds
invoice paid event        != rights or product authority
subscription active       != canonical or launch authority
technical quota           != commercial entitlement or billing
cancellation requested    != immediate deletion
refund                    != entitlement restoration
automatic tax enabled     != tax registration
provider invoice          != audited revenue recognition
margin scenario           != audited operating economics
unlimited label           != unbounded compute
```

## Candidate packaging and pricing

The price book is explicitly `CANDIDATE_ONLY`, tax-exclusive and server-resolved:

| Plan | Candidate amount | Boundary |
|---|---:|---|
| `CONTROLLED_TRIAL_7D` | €0 | Seven days, 1,000,000-token budget, no Stripe invocation |
| `PROFESSIONAL_MONTHLY` | €149/month | 1–3 seats, bounded fair use and P20 technical quotas |
| `TEAM_MONTHLY` | €399/month | 4–15 seats, bounded fair use and P20 technical quotas |
| `ENTERPRISE_CONTRACT` | Quote only | Human contract, no self-activation |

Amounts are not public price authority or market-validation claims. Stripe price identifiers remain environment bindings and cannot be selected by the client.

## Stripe contract

- API version: `2026-06-24.dahlia`.
- Checkout Sessions and Billing for recurring payments.
- Restricted API-key references; no production key material.
- Dynamic payment methods; no hardcoded `payment_method_types`.
- `integration_identifier` required for checkout correlation.
- Webhook signature, event-ID idempotency, provider-account and livemode checks.
- Sandbox only; `livemode=false`.
- Automatic tax blocked unless an active registration decision exists.

## Entitlement derivation

A paid entitlement is derived only when all conditions pass:

```text
verified provider event
∩ reconciled append-only ledger
∩ tenant match
∩ current policy
∩ current rights
∩ bounded commercial approval
```

A UI, Checkout Session, Stripe customer ID, subscription ID or invoice cannot directly grant access.

`PAST_DUE` and `DISPUTED` suspend new paid work. Cancellation at period end preserves bounded access until the verified period boundary, then transitions to read-only retention. Refunds do not silently reactivate or expand entitlement.

## Unit economics

P21 models contribution margin with integer minor-unit arithmetic:

```text
contribution margin
= net revenue excluding collected tax
- model costs
- retrieval and compute
- storage and observability
- payment processing
- variable support
- webhooks and connectors
```

Candidate thresholds:

- Gross-margin floor: 65%.
- Contribution-margin floor: 55%.
- Variable-cost ceiling: 45%.
- Human approval required.

Reference scenarios:

| Scenario | Net revenue | Variable cost | Contribution margin | Gate |
|---|---:|---:|---:|---|
| Professional reference | €149 | €50 | 66.44% | Candidate pass |
| Team reference | €399 | €163 | 59.15% | Candidate pass |
| Professional stress | €149 | €114 | 23.48% | Block |

These are disclosed assumptions, not audited accounts, forecasts or market proof. CAC, capital expenditure, tax collected, revenue recognition and founder compensation remain separate.

## Readiness gates

1. Tenant and provider account resolved.
2. Package version pinned.
3. Server price mapping current.
4. Currency and tax policy current.
5. Stripe keys restricted and rotatable.
6. Checkout idempotency passed.
7. Webhook signature, replay and ordering passed.
8. Payment ledger reconciled.
9. Entitlement derivation fail-closed.
10. Cancellation, refund and dunning tested.
11. Margin scenario within approved floor.
12. Human commercial review current.

All gates must pass. The resulting state is `READY_ENGINEERING_ONLY`, never launch authority.

## Evidence

- 5 frozen bindings.
- 8 modules.
- 32 record types.
- 48 invariants.
- 12 lifecycle states.
- 11 pipeline stages.
- 12 readiness gates.
- 40 conformance fixtures.
- 72 adversarial cases.
- 0 live Stripe calls.
- 0 production credentials.
- 0 canonical writes.
- 0 commercial activations.
- 0 launch actions.

## Adversarial coverage

The suite blocks:

- Client price-ID tampering.
- Treating Checkout completion as payment.
- Forged, replayed or out-of-order provider events.
- Cross-tenant customer or subscription reuse.
- Past-due subscriptions treated as active.
- Cancellation and refund races.
- Tax-registration and invoice misrepresentation.
- Unlimited-usage and quota bypass.
- Margin assumptions presented as audited economics.

Every adversarial case requires zero canonical, external-action, live-payment, revenue-recognition and entitlement-escalation deltas.

## Rollback

P21 changes exactly 13 paths:

- 12 P21-only artifacts are deleted.
- `scripts/verify_p20_rollback.py` is restored byte-exactly from `87b30a1035b557040dd33c5f0acedc62d0ebfa93`.
- Seven P20 authority artifacts are checked for drift.
- The final tree equals frozen P20 for every changed path.

## Authority boundary

Models, workers, browser clients, API clients and Stripe events cannot:

- choose effective prices;
- approve discounts or refunds;
- grant paid entitlements directly;
- bypass tax, rights, quota or tenant gates;
- recognise revenue;
- publish a price;
- launch paid availability;
- create canonical source or claim authority.

Commercial activation requires independent typed human authority after P20 and all transitive dependencies are admitted or explicitly superseded.
