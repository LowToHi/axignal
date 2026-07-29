# 22 — Packaging, Pricing and Entitlements Contract

Version: `0.2.0-candidate`
Status: `NORMATIVE CANDIDATE / B2G WILLINGNESS-TO-PAY VALIDATION REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`
Commercial programme: `Contract 28`

## 1. Purpose

This contract governs how AXIGNAL packages B2G procurement capabilities, presents prices, enforces entitlements and validates willingness to pay without misrepresenting product maturity, source availability or epistemic authority.

Pricing MUST reflect delivered professional value rather than reducing AXIGNAL to AI messages, tokens or raw notice counts.

## 2. Candidate commercial states

AXIGNAL MAY expose these commercial states:

- `PUBLIC_SAMPLE`;
- `TRIAL_PRIVATE`;
- `TRIAL_PUBLIC`;
- `DESIGN_PARTNER`;
- `PROFESSIONAL`;
- `TEAM_GROWTH`;
- `ENTERPRISE`;
- `GRANDFATHERED`;
- `READ_ONLY_EXPIRED`;
- `SUSPENDED`;
- `CANCELLED`.

A state name does not grant a capability. Every capability MUST be represented by a versioned server-side entitlement.

## 3. Candidate packages

Exact names and composition remain hypotheses until the acceptance gate passes.

### 3.1 Public Sample

Purpose: demonstrate AXIGNAL's method without reproducing the paid workflow.

Candidate scope:

- selected public or synthetic investigations;
- clearly labelled source freshness and coverage;
- source-linked Claim and Evidence examples;
- no tenant-private work;
- no unrestricted ResearchRun execution;
- no bulk export or API;
- no implication that every displayed jurisdiction is product-supported.

### 3.2 Design Partner

For an organisation participating in paid workflow validation.

Candidate price band:

- `€300–€600/month` per organisation;
- fixed three-to-six-month term.

Candidate scope:

- bounded users;
- admitted European procurement sources;
- bounded ResearchRuns, dossiers, watchlists and alerts;
- direct onboarding and declared support;
- explicit feedback and workflow-validation commitments;
- experimental capability labels;
- negotiated migration or exit treatment.

### 3.3 Professional

For one active procurement, business-development or advisory professional.

Candidate price band:

- `€349–€499/month`.

Candidate scope:

- one primary seat;
- admitted European procurement coverage;
- Navigator, Globe, Graph and Timeline where released;
- persistent InvestigationContexts and watchlists;
- bounded ResearchRuns and evidence-linked dossiers;
- Claim and Evidence Rail;
- standard-frequency change, cancellation and award monitoring;
- bounded professional exports within source rights;
- standard support.

### 3.4 Team / Growth

For bid teams, consultancies and public-sector sales teams.

Candidate price band:

- `€899–€1,499/month`.

Candidate scope:

- three-to-five included seats;
- all Professional capabilities;
- shared InvestigationContexts, Trails, annotations and assignments;
- larger ResearchRun, dossier, watchlist and alert allowances;
- deeper historical comparisons;
- admitted buyer, supplier and award-network analysis;
- priority support;
- admitted integrations.

### 3.5 Enterprise

For organisations requiring governance, private data, API or contractual controls.

Candidate price band:

- starting range `€18,000–€45,000/year`;
- annual contract by default.

Candidate scope MAY include:

- negotiated seats and organisations;
- jurisdiction packs;
- SSO and SCIM when delivered;
- private sources and tenant-private claims;
- API access, quotas and auditability;
- source and export-right controls;
- security and compliance package;
- service levels and support;
- data residency or deployment requirements only when available and contracted;
- onboarding and professional services.

Plan names, price bands and composition MAY be superseded only through commercial evidence and an ADR.

## 4. Candidate value metrics

Pricing MAY depend on one or more declared dimensions:

- seats and organisations;
- admitted jurisdiction or source packs;
- persistent InvestigationContexts and active Trails;
- ResearchRun execution volume;
- complete evidence-linked dossiers;
- monitored opportunities and alert cadence;
- document and page processing capacity;
- historical depth;
- collaboration;
- exports and report generation;
- API requests or data volume;
- private-source connectors;
- private storage and retention;
- enterprise security, audit, support and SLA obligations.

The commercial model MUST minimise unpredictable bills. Every metered dimension MUST be observable before charges occur.

## 5. Prohibited primary metrics

AXIGNAL SHOULD NOT use as the sole value metric:

- chatbot messages;
- prompt or completion tokens;
- clicks;
- number of claims viewed;
- raw notices indexed;
- arbitrary feature unlocks unrelated to customer value;
- uncalibrated prediction count.

Provider costs MAY influence internal economics, but public pricing SHOULD reflect the customer's research capacity and workflow outcome.

## 6. Price status

Every public or sales-facing price MUST declare one state:

- `HYPOTHESIS`;
- `DESIGN_PARTNER`;
- `PRIVATE_BETA`;
- `PUBLIC_CURRENT`;
- `GRANDFATHERED`;
- `RETIRED`.

The candidate bands in this contract are `HYPOTHESIS`. They MUST NOT be represented as validated, customary or guaranteed market prices.

## 7. Price presentation

A public pricing surface MUST show:

- billing currency;
- billing interval;
- total annual amount when annual billing is offered;
- monthly equivalent where used;
- actual annual saving without fabricated reference pricing;
- tax treatment appropriate to locale;
- included seats, sources, jurisdictions and limits;
- ResearchRun, dossier, document, page, monitoring, export and API allowances where relevant;
- hard stop, upgrade or overage treatment;
- cancellation and effective-date rules;
- refund policy;
- source-dependent limitations;
- plan-specific CTA.

Currency and tax presentation MUST use locale-aware formatting. Generic Spanish examples use euros, but actual product currency is a commercial decision.

## 8. Annual billing

Annual billing MAY offer a real discount, committed capacity, onboarding or support benefit.

It MUST NOT use:

- false urgency;
- permanently expiring discounts;
- misleading crossed-out prices;
- hidden non-refundable terms;
- an annual monthly-equivalent price without the total payable amount.

The customer MUST understand the total, renewal timing and cancellation treatment before purchase.

## 9. Early access and Design Partners

Before pricing is validated, permitted public states include:

- Request access;
- Request pricing;
- Book a B2G workflow demo;
- Join private beta;
- Become a paid Design Partner.

Design Partner agreements SHOULD exchange preferential commercial terms for explicit workflow access, feedback, evidence-quality reporting or case-study permissions. Every obligation MUST be documented.

A Design Partner price MUST NOT be displayed as a permanent discount from an invented list price.

## 10. Entitlement model

Entitlements MUST be explicit, versioned and enforced server-side.

A capability grant SHOULD contain:

```text
subject
organisation
commercial state
plan
capability
source or jurisdiction scope
limit
period
source-right constraints
start time
end time
origin
version
```

The frontend MAY explain entitlements but MUST NOT be the enforcement boundary.

Effective permission is:

```text
commercial entitlement
∩ source rights
∩ organisation policy
∩ jurisdiction availability
∩ epistemic authority
∩ current security state
```

## 11. Capability catalogue

The entitlement catalogue SHOULD cover:

- sources, jurisdictions and government levels;
- historical depth;
- Navigator and ResearchRun operations;
- saved InvestigationContexts, Trails and watchlists;
- dossier generation;
- document and page processing;
- alert count and cadence;
- collaboration;
- report and media exports;
- API access and quotas;
- private sources;
- private claims and workspaces;
- organisation administration;
- security and audit features;
- support and SLA.

Every marketed plan row MUST map to a real entitlement or contractual service obligation.

## 12. Source-right interaction

A paid plan or Enterprise agreement cannot override source licences, export restrictions, attribution, jurisdiction or product-admission state.

An unavailable capability MUST explain whether the cause is:

- plan;
- usage limit;
- rights;
- source;
- jurisdiction;
- security;
- product maturity;
- trial state;
- operator suspension.

No catalogue entry creates a commercial entitlement.

## 13. Usage and overages

Usage meters MUST be:

- defined;
- inspectable;
- timely;
- reproducible;
- consistent between UI, API and invoice;
- separated from provider token accounting unless tokens are explicitly sold.

Before a paid overage, AXIGNAL MUST use an approved mechanism:

- hard stop;
- user-approved purchase;
- organisation-admin-approved budget;
- explicit automatic overage setting;
- plan upgrade.

Silent overages are prohibited.

## 14. Seven-day controlled trial

A seven-day trial is a candidate acquisition mechanism governed by Contracts 01 and 28. It remains disabled until this section's implementation gate passes.

### 14.1 Trial identity and duration

- Seven consecutive 24-hour periods from activation.
- One verified organisation and server-resolved tenant.
- Initial maximum of two users.
- One trial per organisation or business domain within a declared cooling-off period.
- Business-email or equivalent organisation verification SHOULD be required.
- Disposable-email and automated-account abuse controls MUST exist.

### 14.2 Initial trial scope

The first candidate SHOULD include:

- admitted European TED coverage only;
- three ResearchRuns;
- two complete evidence-linked dossiers;
- declared hard document and page allowance;
- bounded saved opportunities and alerts;
- one trial-labelled export where source rights permit;
- standard-frequency updates.

Every limit MUST be configurable, visible and enforced before cost is incurred.

### 14.3 Trial exclusions

The trial MUST exclude:

- API access;
- bulk raw-data export or redistribution;
- private source connectors;
- SSO, SCIM and enterprise administration;
- unlimited document processing or AI;
- high-frequency automation;
- sources or jurisdictions not product-admitted for trial;
- predictive win, margin, eligibility or legal scores;
- bid submission or representation.

### 14.4 Payment and conversion

The initial private validation SHOULD prefer no payment card.

The trial MUST NOT:

- convert silently into paid;
- create a charge without affirmative plan selection;
- hide renewal or plan limits;
- use fabricated countdown urgency.

At expiry:

- new ResearchRuns and monitoring MUST stop;
- the workspace SHOULD move to `READ_ONLY_EXPIRED` for a declared period;
- the user MUST receive clear upgrade, export and deletion choices;
- no paid entitlement starts without explicit agreement.

### 14.5 Retention and deletion

The initial candidate SHOULD retain tenant-private trial state for no more than 30 days after expiry unless the user converts, requests earlier deletion or another lawful basis applies.

The product MUST declare:

- tenant-private content retained;
- source-derived global objects retained independently;
- deletion schedule;
- backup expiry;
- user deletion path;
- read-only behaviour;
- treatment of annotations, uploads and generated dossiers.

Downgrade or expiry MUST NOT silently delete research before the declared schedule.

### 14.6 Trial safety controls

Before any production trial activation, AXIGNAL MUST have:

- server-side entitlements and hard limits;
- source-right and attribution enforcement;
- per-trial cost ledger;
- ResearchRun, export and concurrency budgets;
- organisation and rate-limit controls;
- tenant-isolation tests;
- prompt, document-size and file-type controls;
- malware and unsafe-file controls for uploads;
- expiry and deletion jobs;
- anomaly detection for automated extraction or redistribution;
- separate trial suspension and kill switch;
- append-only audit events;
- no admission-authority bypass.

## 15. Trial promotion gates

### Private trial gate

Pass only when:

1. `AX-F8-T14` has accepted the European procurement E2E loop;
2. a qualified user completes the full trial value loop without operator data repair;
3. hard limits, expiry and read-only transition pass E2E tests;
4. source rights, export and attribution cannot be bypassed;
5. tenant isolation and deletion pass;
6. variable cost and support burden fit the approved acquisition model;
7. no copy overstates coverage, eligibility, prediction or authority.

### Public trial gate

Pass only when:

- private trial evidence is accepted;
- qualified activation and explicit paid intent are credible;
- abuse remains controllable;
- premium perception is not materially damaged;
- payment, upgrade, cancellation and refund paths are tested;
- trial and payment kill switches are independently tested.

## 16. Plan comparison

The comparison MUST prioritise decision-relevant differences:

- intended user and team size;
- admitted sources and jurisdictions;
- ResearchRun, dossier and history capacity;
- collaboration;
- monitoring and alerts;
- document processing;
- exports;
- API;
- private data;
- security and administration;
- support and SLA.

Rows MUST NOT be multiplied solely to make a plan appear larger.

## 17. Upgrades and downgrades

The customer MUST be told:

- when changes take effect;
- how proration works;
- what happens to data beyond a lower plan's limits;
- which ResearchRuns, alerts or automations pause;
- what becomes read-only;
- what remains exportable under source rights;
- how to reverse an accidental change.

Downgrading MUST NOT silently delete research.

## 18. Cancellation

Cancellation MUST be available through a reasonable self-service path for self-service plans.

The product MUST state:

- effective date;
- remaining access;
- renewal cancellation status;
- export opportunity;
- retention and deletion schedule;
- treatment of organisation-owned content.

Enterprise termination follows the governing agreement but MUST have an operational offboarding plan.

## 19. Enterprise pricing

Enterprise quotes MAY incorporate:

- seats and organisations;
- jurisdiction packs;
- private-source complexity;
- data and API volume;
- security obligations;
- deployment or residency needs;
- SLA and support;
- onboarding and integration services;
- source licensing costs.

The quote MUST separate recurring software, variable usage, third-party data and professional services when material.

## 20. Commercial experiments

Pricing and trial experiments MUST comply with Contract 23.

They MUST NOT:

- discriminate using sensitive or protected characteristics;
- change contracted prices without authority;
- show inconsistent totals during one purchase journey;
- use fabricated scarcity;
- hide limits;
- weaken accessibility, privacy, security or source rights;
- treat a catalogue source as a supported entitlement;
- claim predictive accuracy without accepted evidence.

## 21. Economic gate

A plan or trial cannot be promoted to public scale unless evidence supports:

- willingness to pay;
- activation and repeated use;
- retention or annual commitment;
- gross-margin viability;
- source, infrastructure, model and support cost coverage;
- acceptable trial and refund burden;
- understandable value metric;
- acceptable upgrade, downgrade and cancellation behaviour;
- server-side entitlement reproducibility;
- jurisdiction and source-right enforcement.

Channels and spend MUST NOT scale before conversion and unit economics are validated.

## 22. Reinvestment policy

Profits MAY be reinvested in:

- validated acquisition channels;
- admitted source and jurisdiction coverage;
- evidence and document automation;
- infrastructure and reliability;
- product improvement;
- positioning and methodology;
- customer success;
- security, privacy and compliance.

Reinvestment MUST be conditioned on measured return, margin, risk limits, reserves and channel validation. AXIGNAL MUST NOT scale unvalidated acquisition or source breadth merely because budget is available.

## 23. Acceptance gate

Packaging, pricing and trial advance from candidate when:

1. target B2G buyers understand plan distinctions and premium value;
2. each marketed capability maps to a server-side entitlement;
3. paid willingness-to-pay evidence exists;
4. gross-margin and support assumptions are measured;
5. pricing surfaces disclose limits, taxes, sources, jurisdictions and renewal terms;
6. usage, expiry and overage accounting is reproducible;
7. source-right constraints remain enforced;
8. upgrade, downgrade, cancellation, trial expiry and deletion flows are tested;
9. no dark pattern, fabricated discount or silent conversion exists;
10. public price status and version are auditable;
11. the trial passes its private and public promotion gates;
12. no plan grants unsupported global coverage or predictive authority.

Exact plan names, public prices, limits, discounts and trial allowances remain unfrozen until this gate passes.

## 24. Current authority state

```text
PACKAGES AND PRICE BANDS ARE HYPOTHESES
/ SERVER-SIDE ENTITLEMENTS REQUIRED
/ SEVEN-DAY TRIAL DESIGNED BUT DISABLED
/ NO SILENT CONVERSION
/ NO PUBLIC CURRENT PRICE
/ NO GLOBAL SOURCE ENTITLEMENT FROM CATALOGUE LISTING
```
