# 22 — Packaging, Pricing and Entitlements Contract

Version: `0.3.0`
Status: `NORMATIVE CANDIDATE / PUBLIC PRICING AND BILLING BLOCKED`
Goal ID: `AXIGNAL-GOAL-001`
Governing programme: `Contract 31 / ADR-016`
Commercial runtime: `P21`
Identity and trial runtime: `P25`
Final gate: `P27`

## 1. Purpose

This contract governs how AXIGNAL packages B2G capabilities, presents candidate prices, enforces flat-tier seats and other entitlements, controls the seven-day trial and validates willingness to pay without misrepresenting product, source or commercial maturity.

Pricing reflects delivered professional value. Tokens and provider costs remain internal economic controls unless explicitly sold under a future approved contract.

## 2. State hierarchy

A label, provider object or UI selection does not grant a capability.

```text
package definition
≠ candidate price
≠ verified provider state
≠ commercial entitlement
≠ membership
≠ operational authority
≠ public availability
```

Every effective capability is versioned and enforced server-side.

## 3. Current candidate packages

| Package | Candidate amount | Billing | Seat capacity | Status |
|---|---:|---|---:|---|
| `CONTROLLED_TRIAL_7D` | `0 EUR` | No Stripe invocation | 2 | `CANDIDATE_ONLY` |
| `PROFESSIONAL_MONTHLY` | `149 EUR/month` | Flat-tier recurring package | 3 | `CANDIDATE_ONLY` |
| `TEAM_MONTHLY` | `399 EUR/month` | Flat-tier recurring package | 15 | `CANDIDATE_ONLY` |
| `ENTERPRISE_CONTRACT` | Quote only | Contract | Negotiated | `CANDIDATE_ONLY` |

These values are the current technical candidate price book. They are not validated public prices.

Prior bands such as Professional `349–499 EUR/month` and Team `899–1,499 EUR/month` remain historical hypotheses and have no current runtime authority.

## 4. Candidate price states

Every price or offer must declare one of:

- `HYPOTHESIS`;
- `CANDIDATE_ONLY`;
- `DESIGN_PARTNER`;
- `PRIVATE_ACCEPTANCE`;
- `PUBLIC_CURRENT`;
- `GRANDFATHERED`;
- `RETIRED`.

No price becomes `PUBLIC_CURRENT` before P27.

## 5. Flat-tier seat governance

Professional and Team use flat-tier packages, not per-seat Stripe quantity.

```text
Stripe subscription item quantity = 1
AXIGNAL seat capacity              = server-side entitlement
```

The authority chain is:

```text
verified trial or subscription
→ plan-to-capacity reconciliation
→ tenant seat entitlement
→ RESERVED or ACTIVE allocation
→ explicit membership
→ typed role binding
→ server-resolved access
→ forced RLS
→ append-only audit
```

Rules:

- trial capacity is 2;
- Professional capacity is 3;
- Team capacity is 15;
- a Team tenant may have fewer than four users;
- a fourth Professional seat is denied;
- a sixteenth Team seat is denied;
- invitations reserve capacity;
- acceptance activates the same allocation;
- expiry or revocation releases capacity;
- downgrade is denied while occupancy exceeds target capacity;
- the final owner cannot be revoked or demoted.

Stripe cannot create memberships, roles or tenant authority.

## 6. Role and capability boundary

Candidate organisation roles:

- Organisation Owner;
- Organisation Admin;
- B2G Manager;
- Research Operator;
- Bid Reviewer;
- Viewer;
- Billing Admin;
- Auditor.

Effective permission is:

```text
verified identity
∩ active session
∩ server-resolved tenant
∩ active membership
∩ role binding
∩ workspace scope
∩ seat-entitlement state
∩ package capability
∩ source rights
∩ security policy
∩ RLS
```

A seat is capacity, not unrestricted authority.

## 7. Controlled seven-day trial

### 7.1 Trial ownership

The trial belongs to a tenant or resolved economic identity, not a browser account.

```text
one tenant
→ one trial grant
→ one seven-day clock
→ one token and cost budget
→ two seats
```

Changing account, device, owner or email alias does not produce a new trial.

### 7.2 Trial start

The clock begins on the first admitted AI operation.

```text
verified email
→ passkey registered
→ trial READY
→ first admitted AI request
→ trial ACTIVE
→ expires_at = started_at + 7 days
```

Signup, login, alert confirmation and workspace opening do not start the clock.

### 7.3 Candidate limits

- seven consecutive 24-hour periods;
- two seats;
- 1,000,000-token ceiling;
- internal estimated-cost ceiling;
- one concurrent ResearchRun;
- restricted private connectors;
- restricted bulk export;
- no public API unless separately admitted;
- admitted source and rights scope only.

Token and cost reservations must be transactional.

### 7.4 Abuse controls

Strong subject claims may reuse or block a second trial. Weak signals may restrict or require step-up but cannot independently prove abuse.

Risk decisions:

- `ALLOW`;
- `ALLOW_RESTRICTED`;
- `REUSE_EXISTING_TRIAL`;
- `STEP_UP_REQUIRED`;
- `MANUAL_REVIEW`;
- `BLOCK_ABUSE`.

```text
shared IP ≠ abuse
risk score ≠ proof
new account ≠ new trial
email verified ≠ trial granted
```

### 7.5 Payment and conversion

The candidate trial uses no card and no Stripe checkout.

The trial must not:

- convert silently;
- create a paid entitlement without explicit package selection;
- reset through deletion or cancellation;
- hide expiry or limits;
- use fabricated urgency.

### 7.6 Expiry and retention

At expiry:

- new ResearchRuns and expensive operations stop;
- the workspace follows declared read-only rules;
- upgrade, export and deletion choices remain visible;
- tenant-private data follows the accepted retention schedule;
- source-derived global evidence remains governed independently;
- no research is silently deleted before its declared schedule.

## 8. Professional candidate package

Candidate audience: a small B2G team or active professional.

Candidate capabilities may include:

- up to three seats;
- admitted procurement libraries and jurisdictions;
- Navigator and ResearchRuns;
- InvestigationContexts, Opportunities and watchlists;
- evidence-linked dossiers;
- buyer, award, supplier and ownership context;
- Tender Alerts;
- Bid Workspace capabilities actually released;
- bounded export within rights;
- standard support.

Usage, source, history, document and workspace capacities remain to be validated.

## 9. Team candidate package

Candidate audience: bid, capture, tender, consulting and public-sector sales teams.

Candidate capabilities may include:

- up to fifteen seats;
- all admitted Professional capabilities;
- shared Pursuits;
- requirements, assignments, tasks and milestones;
- documents, comments and approvals;
- reporting and audit;
- larger admitted operational capacity;
- deeper comparison and history;
- admitted integrations;
- priority support.

## 10. Enterprise candidate package

Enterprise is quote-only and may include only delivered and contracted capabilities:

- negotiated organisations and seats;
- multiple admitted libraries or jurisdiction packs;
- SSO and SCIM after production acceptance;
- API and webhooks;
- tenant-private libraries and connectors;
- private data and claims;
- data residency or deployment controls when available;
- security, audit, support and SLA;
- onboarding and professional services.

Software, variable usage, third-party data and services must be separated when material.

## 11. Entitlement model

A capability grant should contain:

```text
subject
organisation
package
commercial state
capability
library, source or jurisdiction scope
limit
period
rights constraints
start and end time
origin
policy version
security state
```

The frontend may explain entitlements but is never the enforcement boundary.

## 12. Source-right interaction

A paid plan cannot override:

- licence;
- source-admission state;
- export restrictions;
- attribution;
- retention;
- jurisdiction;
- privacy;
- product maturity.

An unavailable capability must identify whether the cause is package, limit, rights, source, jurisdiction, security, trial state or suspension.

## 13. Usage and overages

Every usage dimension must be:

- defined;
- inspectable;
- timely;
- reproducible;
- consistent across UI, API, entitlement and invoice;
- separated from internal provider token accounting unless tokens are explicitly sold.

Before a paid overage, AXIGNAL must use an approved mechanism:

- hard stop;
- explicit user purchase;
- organisation-admin budget;
- explicit automatic-overage setting;
- package upgrade.

Silent overages are prohibited.

## 14. Price presentation

Any pricing surface must disclose:

- currency and interval;
- exact price state;
- total annual amount if annual billing exists;
- tax treatment;
- included seats;
- admitted library and jurisdiction scope;
- limits;
- hard-stop, upgrade or overage behaviour;
- cancellation and effective date;
- refund treatment;
- retention and deletion;
- source-dependent limitations;
- one unambiguous CTA per package.

## 15. Upgrades and downgrades

The customer must be told:

- when changes take effect;
- proration if applicable;
- capacity changes;
- what becomes read-only;
- which operations pause;
- export availability;
- downgrade conflicts;
- reversal path.

Downgrade must never silently delete customer work.

## 16. Cancellation

Self-service packages require a reasonable cancellation path after public activation.

The product must state:

- effective date;
- remaining access;
- renewal status;
- export opportunity;
- retention and deletion schedule;
- treatment of organisation-owned content.

Cancellation does not reset trial eligibility.

## 17. Commercial administration

Founder Operations P26-T02 must administer customers, trials and billing through typed server operations.

It must not:

- fabricate provider events;
- change verified Stripe state;
- grant arbitrary entitlement;
- extend trials silently;
- issue unaudited refunds;
- allow browser-selected billing authority.

## 18. Economic gate

A package or trial cannot become public-current unless evidence supports:

- qualified buyer understanding;
- willingness to pay;
- completed product value;
- retention or annual commitment;
- renewal;
- contribution margin;
- source, infrastructure, model and support costs;
- acceptable abuse, refund and dispute burden;
- acquisition payback;
- understandable package distinctions;
- reproducible entitlement and billing state;
- cancellation and downgrade operation.

## 19. Reinvestment

Profits may be reinvested in validated acquisition, source coverage, product, infrastructure, security and customer success only under measured return, margin, risk limits and reserves.

Page volume, source count or advertising spend must not be scaled without evidence.

## 20. Acceptance gate

Packaging, pricing, trial and seats advance only when:

1. every marketed row maps to server authority;
2. identity, abuse and seats pass in production acceptance;
3. complete external Stripe sandbox evidence exists;
4. paid and retention evidence exists;
5. pricing and package comprehension pass;
6. taxes, invoice, refund and dispute rules pass;
7. source-right constraints pass;
8. upgrade, downgrade, cancellation, expiry and deletion pass;
9. no dark pattern or silent conversion exists;
10. P26-T02 founder administration passes;
11. P27 binds the final exact head;
12. human Commercial, Finance/Tax, Security and Product authorities approve.

## 21. Current authority

```text
CANDIDATE PRICE BOOK        0 / 149 / 399 / QUOTE
SEATS                       2 / 3 / 15
PRICE STATUS                CANDIDATE_ONLY
SEAT GOVERNANCE E2E         PASS
TRIAL GOVERNANCE E2E        PASS
PUBLIC TRIAL                BLOCKED
PUBLIC PRICING              NOT VALIDATED
P26-T02 BILLING ADMIN       NOT STARTED
STRIPE LIVE                 BLOCKED
PUBLIC LAUNCH               NO_GO
```
