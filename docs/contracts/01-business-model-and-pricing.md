# 01 — Business Model and Pricing Contract

Version: `0.3.0`
Status: `NORMATIVE / B2G CANDIDATE-PRICING / VALIDATION REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`
Governing programme: `Contract 31 / ADR-016`
Commercial runtime: `P21`
Final pricing gate: `P27`

## 1. Commercial model

AXIGNAL MUST be sold as a premium recurring Business-to-Government opportunity-intelligence and operations product, not as a low-cost tender newsletter, generic AI assistant, public-data resale or transaction-commission business.

The first commercial shell serves organisations and professionals that sell to government. The parent architecture supports the nine Contract 31 opportunity libraries through independent product, source and commercial gates.

The commercial stack MAY include:

1. public methodology and admitted source-linked intelligence pages;
2. Tender Alerts and limited public discovery;
3. private Design Partner or acceptance access;
4. Professional and Team recurring subscriptions;
5. Enterprise contracts;
6. additional admitted library, source or jurisdiction entitlements;
7. API and data entitlements where rights permit;
8. tenant-private connectors and data;
9. professional onboarding or services declared separately.

Bid submission, supplier representation, legal certification, unrelated transaction execution, custody and performance fees remain outside the current authority.

## 2. Canonical commercial narrative

Commercial category:

> **Business-to-Government (B2G) Opportunity Intelligence**

Initial market:

> **Public contracts and global tenders**

Outcome statement:

> **Find the public contracts your business is built to pursue, qualify them with traceable evidence and coordinate the pursuit inside one governed workspace.**

The narrative MUST communicate:

- public-contract discovery and qualification;
- contracting-authority, award, supplier and ownership context;
- requirements, amendments, deadlines and lifecycle;
- evidence, contradictions and unknowns;
- human bid/no-bid and operational authority;
- admitted source and coverage limitations;
- persistent team workflow and learning.

The narrative MUST NOT imply:

- guaranteed eligibility, profitability, award or legal compliance;
- worldwide coverage based on catalogue listings;
- autonomous bid decisions;
- public availability before P27;
- that TED or another portal is AXIGNAL's product identity.

## 3. Value unit

The paid value is not raw notice count, messages, tokens, generated text or interface panels.

The paid value is:

- earlier and more relevant opportunity discovery;
- faster and better-supported qualification;
- reduced cost of unsuitable pursuits;
- traceability from opportunity to source and document version;
- visible supporting, contradicting and unresolved evidence;
- buyer, supplier, award, ownership and historical context;
- persistent investigations and dossiers;
- requirements, tasks, documents and approvals;
- collaboration and audit;
- outcome and reusable learning;
- governed multi-jurisdiction research capacity.

Public pricing SHOULD reflect professional opportunity capacity and workflow value, not provider token cost.

## 4. Priority buyer

The priority buyer has a recurring B2G workflow and satisfies at least two of:

- reviews public opportunities repeatedly;
- spends material staff or advisory time qualifying tenders;
- sells or advises across multiple buyers, categories or geographies;
- has suffered a missed, late or costly pursue/decline decision;
- values source auditability and document evidence;
- coordinates a team or approval workflow;
- can convert one relevant finding or avoided pursuit into value exceeding the subscription;
- needs context, monitoring, API or governance beyond commodity alerts.

Priority segments:

1. B2G business-development leaders;
2. bid, tender and capture teams;
3. public-sector sales organisations;
4. tender and market-entry consultancies;
5. technology, engineering, defence, energy, health and infrastructure suppliers;
6. multi-region organisations requiring governed procurement intelligence.

## 5. Current candidate price book

The versioned server-side P21 commercial runtime is the current technical source for candidate package definitions.

| Package | Candidate price | Flat-tier seats | Status |
|---|---:|---:|---|
| `CONTROLLED_TRIAL_7D` | `0 EUR` | 2 | `CANDIDATE_ONLY` |
| `PROFESSIONAL_MONTHLY` | `149 EUR/month` | 3 | `CANDIDATE_ONLY` |
| `TEAM_MONTHLY` | `399 EUR/month` | 15 | `CANDIDATE_ONLY` |
| `ENTERPRISE_CONTRACT` | Quote only | Contracted | `CANDIDATE_ONLY` |

These values are not:

- validated public prices;
- willingness-to-pay evidence;
- market-standard claims;
- revenue forecasts;
- authority to activate billing.

Historical candidate ranges such as:

```text
Professional 349–499 EUR/month
Team         899–1,499 EUR/month
```

remain preserved hypothesis history. They do not override the active candidate price book.

No price becomes `PUBLIC_CURRENT` before P01, P21 and P27 accept buyer, paid, retention, margin and support evidence.

## 6. Flat-tier seat model

Professional and Team are candidate flat-tier packages.

```text
Stripe quantity = 1 package
AXIGNAL = internal seat-capacity authority
```

Candidate capacities:

- controlled trial: 2;
- Professional: 3;
- Team: 15.

A Team organisation may operate with fewer than four users. Professional cannot allocate a fourth seat. Team cannot allocate a sixteenth seat.

Effective access is:

```text
verified trial or paid entitlement
∩ tenant seat entitlement
∩ active membership
∩ role binding
∩ workspace scope
∩ source rights
∩ security state
∩ RLS
```

A Stripe customer, subscription label or browser value cannot grant membership or capacity.

## 7. Controlled seven-day trial

The trial is a candidate acquisition mechanism, implemented in engineering but not publicly activated.

### 7.1 Ownership

A trial belongs to a tenant or resolved economic identity, not to an account, email alias, device, cookie or IP address.

```text
one tenant
→ one trial grant
→ one seven-day clock
→ one shared token and cost budget
→ two seats
```

### 7.2 Start

The clock starts on the first admitted AI operation:

```text
verified email
→ passkey
→ trial READY
→ first admitted AI request
→ trial ACTIVE
→ seven consecutive 24-hour periods
```

Signup, login, Tender Alert subscription or opening the workspace does not start the trial.

### 7.3 Candidate limits

- two seats;
- 1,000,000-token ceiling;
- internal estimated-cost ceiling;
- one concurrent ResearchRun;
- restricted bulk export;
- restricted private connectors;
- no public API unless separately admitted;
- source and rights limits;
- no silent paid conversion.

### 7.4 Abuse governance

Strong claims may reuse or deny another trial. Weak signals may restrict, require step-up or manual review but cannot independently prove abuse.

```text
account created ≠ trial granted
shared IP ≠ abuse
risk score ≠ proof of fraud
new email alias ≠ new economic identity
```

### 7.5 Expiry

At expiry:

- new expensive operations stop;
- existing work follows declared read-only, export, retention and deletion rules;
- no paid entitlement starts without explicit plan selection;
- deletion does not reset trial eligibility.

## 8. Professional candidate package

Candidate purpose: a small B2G team or active professional requiring governed discovery, qualification and pursuit context.

Candidate package:

- up to three seats;
- admitted procurement scope only;
- persistent investigations, opportunities and watchlists;
- evidence-linked dossiers;
- buyer, award, supplier and ownership context where admitted;
- standard monitoring and Tender Alerts;
- Bid Workspace capabilities actually released;
- bounded exports within rights;
- standard support.

Exact usage, source and workspace limits remain unfrozen.

## 9. Team candidate package

Candidate purpose: bid, tender, capture, consulting or public-sector sales teams.

Candidate package:

- up to fifteen seats;
- all admitted Professional capabilities;
- shared Pursuits, requirements, tasks, documents and approvals;
- larger operational capacity;
- deeper history and comparisons;
- reporting and audit;
- admitted integrations;
- priority support.

Exact usage, source and workspace limits remain unfrozen.

## 10. Enterprise candidate package

Enterprise remains quote-only.

Candidate scope MAY include:

- contracted seats and organisations;
- multiple admitted libraries or jurisdiction packs;
- SSO and SCIM after production acceptance;
- API and webhooks;
- tenant-private libraries and connectors;
- private data and claims;
- security, audit and contractual support;
- data residency or deployment requirements when actually available;
- onboarding and professional services.

Quotes MUST separate recurring software, variable usage, third-party data and professional services when material.

## 11. Price status

Every sales-facing price MUST declare one state:

- `HYPOTHESIS`;
- `CANDIDATE_ONLY`;
- `DESIGN_PARTNER`;
- `PRIVATE_ACCEPTANCE`;
- `PUBLIC_CURRENT`;
- `GRANDFATHERED`;
- `RETIRED`.

The current 0/149/399/quote catalogue is `CANDIDATE_ONLY`.

## 12. Price presentation

Any pricing surface MUST show:

- currency;
- interval;
- tax treatment;
- flat-tier seat capacity;
- source, library and jurisdiction scope;
- operational limits;
- upgrade and downgrade behaviour;
- cancellation effective date;
- retention and deletion;
- source-dependent limitations;
- exact price status;
- plan-specific CTA.

Candidate pricing MUST NOT be described as market validated.

## 13. Annual billing

Annual billing may be introduced only after evidence and must disclose:

- total annual amount;
- monthly equivalent where shown;
- actual saving;
- tax treatment;
- renewal date;
- cancellation and refund rules.

False urgency, fabricated discounts and hidden non-refundable terms are prohibited.

## 14. Acquisition model

Priority acquisition system:

```text
admitted procurement data
→ governed transactional pages and Market Intelligence
→ Google, Bing and eligible answer engines
→ Tender Alert or sample investigation
→ passwordless signup
→ governed trial
→ completed B2G value workflow
→ explicit paid plan
→ retention and expansion
```

Supporting channels:

- founder-led B2G intelligence and methodology;
- LinkedIn distribution;
- targeted outbound;
- partnerships and associations;
- webinars and demonstrations;
- paid acquisition only after evidence.

Search traffic, Tender Alerts and CRM leads do not grant trials or establish buyer quality.

Google Search Console data may support diagnostics after API admission. DNS verification alone does not prove API integration.

## 15. Design Partners and private acceptance

Private paid acceptance may be used to validate complete workflows before public launch.

Requirements:

- explicitly admitted organisation;
- controlled terms and declared maturity;
- no open signup;
- no public-launch representation;
- auditable access and billing;
- feedback and evidence obligations where agreed;
- source and coverage disclosure;
- independent suspension and rollback.

A private-acceptance price is not a permanent discount from an invented list price.

## 16. Pricing experiments

A package or price change requires evidence such as:

- direct budget-authority interview;
- independent paid acceptance;
- signed annual proposal;
- completed value workflow;
- renewal or retention;
- usage and support evidence;
- enterprise proposal outcome;
- upgrade, downgrade or cancellation behaviour.

Every experiment records:

- audience and eligibility;
- exact offer version;
- source and entitlement scope;
- primary and guardrail metrics;
- denominator;
- variable and support cost;
- limitations;
- decision and rollback.

## 17. Commercial gates

### B0 — Problem and buyer evidence

Pass only with qualified direct evidence of recurring workflow pain, decision cost and budget responsibility.

### B1 — Independent paid acceptance

Pass only with unrelated organisations paying under explicit terms for a working AXIGNAL value loop.

### B2 — Completed value

Pass only when customers complete the declared opportunity-to-evidence-to-pursuit workflow without hidden unpriced consulting.

### B3 — Retention or annual commitment

Pass only with accepted repeated use, renewal or annual-commitment evidence.

### B4 — Expansion

Pass only with accepted seat, package, library or jurisdiction expansion evidence.

### B5 — Repeatable acquisition

Pass only when an attributable channel produces paying customers with acceptable contribution margin, support burden and payback.

## 18. Cost discipline

AXIGNAL MUST prioritise:

- official and reusable data;
- deterministic transforms;
- caching and incremental processing;
- content-addressed evidence reuse;
- local or low-cost models;
- sampled rather than universal enrichment;
- source-specific processing;
- transactional trial budgets;
- hard cost, concurrency and export controls.

Provider token usage is an internal cost metric, not the primary paid value unit.

## 19. Reinvestment

Profits may be reinvested in:

- validated acquisition channels;
- source and jurisdiction coverage;
- evidence and document automation;
- infrastructure and reliability;
- product and operational workspaces;
- positioning and methodology;
- customer success;
- security, privacy and compliance.

Reinvestment requires measured return, margin, risk limits, reserves and channel validation. Unvalidated advertising, SEO page volume or source breadth must not be scaled merely because budget exists.

## 20. Acceptance and launch

Final pricing requires P27 evidence for:

- buyer and budget validity;
- willingness to pay;
- complete Stripe sandbox evidence;
- authorised live-boundary evidence;
- completed customer value;
- retention and renewal;
- contribution margin;
- support burden;
- acquisition payback;
- package comprehension;
- cancellation, refund and dispute operation;
- source-right and entitlement enforcement.

Only P27 can authorise public pricing and launch.

## 21. Current authority

```text
B2G COMMERCIAL SHELL             SELECTED
CURRENT CANDIDATE PRICE BOOK     0 / 149 / 399 / QUOTE
PRICE STATUS                     CANDIDATE_ONLY
TRIAL ENGINEERING                E2E PASS
SEAT GOVERNANCE ENGINEERING      E2E PASS
PUBLIC TRIAL                     BLOCKED
PUBLIC PRICING                   NOT VALIDATED
STRIPE LIVE                      BLOCKED
INDEPENDENT PAID EVIDENCE        MISSING
RETENTION AND RENEWAL            MISSING
PUBLIC LAUNCH                    NO_GO
```
