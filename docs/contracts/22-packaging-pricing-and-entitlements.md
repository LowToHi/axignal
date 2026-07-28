# 22 — Packaging, Pricing and Entitlements Contract

Version: `0.1.0-candidate`
Status: `NORMATIVE CANDIDATE / WILLINGNESS-TO-PAY VALIDATION REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

This contract governs how AXIGNAL packages capabilities, presents prices, enforces entitlements and validates willingness to pay without misrepresenting product maturity or creating arbitrary commercial friction.

Pricing MUST reflect delivered professional value rather than reducing AXIGNAL to a count of AI messages.

## 2. Candidate packages

The initial candidate packaging architecture is:

### Research

For an individual professional conducting traceable investigations.

Candidate scope:

- Navigator;
- Globe, Graph and Timeline;
- Claim and Evidence Rail;
- saved investigations and watchlists within declared limits;
- included universes;
- basic alerts;
- basic exports;
- standard support.

### Professional

For analysts and small teams requiring deeper workflows and collaboration.

Candidate scope:

- all Research capabilities;
- expanded historical depth;
- advanced comparisons;
- larger investigation, alert and export allowances;
- collaboration and shared Trails;
- professional reporting;
- additional universes;
- priority support;
- optional API access when commercially and technically admitted.

### Enterprise

For organisations requiring governance, private data and contractual controls.

Candidate scope:

- organisations, roles and administrative controls;
- SSO and SCIM when contracted;
- private sources and private claims;
- API access, quotas and auditability;
- source and export-right controls;
- security and compliance package;
- service levels and support;
- data residency or deployment requirements only when available and contracted.

Plan names and composition remain hypotheses. A stronger packaging architecture MAY supersede them through commercial evidence and an ADR.

## 3. Candidate value metrics

Pricing MAY depend on one or more declared dimensions:

- seats;
- admitted universes;
- saved investigations or active Trails;
- research execution volume;
- historical depth;
- alerts and monitored conditions;
- exports and report generation;
- API requests or data volume;
- private-source connectors;
- private storage and retention;
- enterprise security, audit and support obligations.

The commercial model MUST minimise unpredictable bills. Every metered dimension MUST be observable by the customer before charges occur.

## 4. Prohibited primary metrics

AXIGNAL SHOULD NOT use the following as the sole value metric:

- chatbot messages;
- prompt tokens;
- clicks;
- number of claims viewed;
- arbitrary feature unlock counts unrelated to customer value.

Provider costs MAY influence internal economics, but public pricing SHOULD reflect the customer's research capacity and outcome, not internal implementation trivia.

## 5. Price status

Every public or sales-facing price MUST have a declared status:

- `HYPOTHESIS`;
- `DESIGN_PARTNER`;
- `PRIVATE_BETA`;
- `PUBLIC_CURRENT`;
- `GRANDFATHERED`;
- `RETIRED`.

Unvalidated figures MUST NOT be presented as established market prices.

## 6. Price presentation

Where public prices exist, the pricing surface MUST show:

- billing currency;
- billing interval;
- monthly equivalent when annual billing is offered;
- actual annual saving without fabricated reference pricing;
- tax treatment appropriate to locale;
- included limits;
- overage or upgrade treatment;
- cancellation and effective-date rules;
- refund policy where applicable;
- plan-specific CTA.

Currency and tax presentation MUST use locale-aware formatting. The default Spanish locale uses euros when a generic example is necessary, but actual product currency is a commercial decision.

## 7. Annual billing

Annual billing MAY offer a real discount or additional committed capacity. It MUST NOT use:

- false urgency;
- permanently expiring discounts;
- misleading crossed-out prices;
- hidden non-refundable terms.

The user MUST understand total payable amount and renewal timing before purchase.

## 8. Early access and design partners

Before pricing is validated, the permitted public states include:

- Request access;
- Request pricing;
- Book a demo;
- Join private beta;
- Become a design partner.

Design-partner agreements SHOULD exchange preferential commercial terms for explicit access, feedback, case-study or workflow-validation commitments. Any such obligations MUST be documented.

## 9. Entitlement model

Entitlements MUST be explicit, versioned and enforced server-side.

A capability grant SHOULD include:

```text
subject
organisation
plan
capability
scope
limit
period
source-right constraints
start time
end time
origin
version
```

The frontend MAY explain entitlements but MUST NOT be the enforcement boundary.

## 10. Capability catalogue

The entitlement catalogue SHOULD cover:

- universes and geographies;
- historical depth;
- Navigator operations;
- saved Trails and watchlists;
- alert count and cadence;
- collaboration;
- report and media exports;
- API access and quotas;
- private sources;
- private claims and workspaces;
- organisation administration;
- security and audit features;
- support tier.

Every marketed plan row MUST map to a real entitlement or contractual service obligation.

## 11. Source-right interaction

A paid plan cannot override source licences, export restrictions or jurisdictional limits.

The effective permission is:

```text
commercial entitlement
∩ source rights
∩ organisation policy
∩ jurisdiction availability
∩ current security state
```

An unavailable capability MUST explain whether the cause is plan, rights, region, source, security or product maturity.

## 12. Usage and overages

Usage meters MUST be:

- defined;
- inspectable;
- timely;
- reproducible;
- consistent between UI, API and invoice;
- separated from provider token accounting unless tokens are explicitly sold.

Before a paid overage, AXIGNAL MUST provide an approved mechanism such as:

- hard stop;
- user-approved purchase;
- admin-approved budget;
- explicit automatic overage setting;
- plan upgrade.

Silent overages are prohibited.

## 13. Free, trial and sandbox access

A free trial, sandbox or public sample investigation MAY be used to reduce adoption friction.

It MUST declare:

- included capabilities;
- data freshness and synthetic-data status;
- duration or usage limit;
- export restrictions;
- whether payment details are required;
- what happens at expiry;
- data retention and deletion behaviour.

A trial MUST NOT silently convert into a paid subscription without clear prior disclosure and affirmative agreement.

## 14. Plan comparison

The detailed comparison MUST prioritise decision-relevant differences, including:

- intended user and team size;
- included universes;
- research and history capacity;
- collaboration;
- alerts;
- exports;
- API;
- private data;
- security and administration;
- support and SLA.

Rows MUST NOT be multiplied solely to make a plan appear larger.

## 15. Upgrades and downgrades

The customer MUST be told:

- when changes take effect;
- how prorating works;
- what happens to data beyond a lower plan's limits;
- which alerts or automations pause;
- what remains exportable;
- how to reverse an accidental change.

Downgrading MUST NOT silently delete research. Data retention and read-only states MUST be explicit.

## 16. Cancellation

Cancellation MUST be available through a reasonable self-service path for self-service plans.

The product MUST state:

- effective date;
- remaining access;
- renewal cancellation status;
- export opportunity;
- retention and deletion schedule;
- treatment of organisation-owned content.

Enterprise termination follows the governing agreement but MUST still have an operational offboarding plan.

## 17. Enterprise pricing

Enterprise quotes MAY incorporate:

- seats;
- private-source complexity;
- data and API volume;
- security obligations;
- deployment or residency needs;
- SLA and support;
- onboarding and integration services;
- source licensing costs.

The quote MUST separate recurring software, variable usage, third-party data and professional services when material.

## 18. Commercial experiments

Pricing experiments MUST comply with Contract 23.

They MUST NOT:

- discriminate using sensitive or protected characteristics;
- change contracted prices without authority;
- show inconsistent totals during the same purchase journey;
- use fabricated scarcity;
- hide plan limits;
- undermine accessibility or privacy.

## 19. Economic gate

A plan cannot be promoted to public scale unless evidence supports:

- willingness to pay;
- activation and retention;
- gross-margin viability;
- source and infrastructure cost coverage;
- support burden;
- refund and chargeback tolerance;
- understandable value metric;
- acceptable expansion and downgrade behaviour.

Channels and spend MUST NOT be scaled before conversion and unit economics are validated.

## 20. Reinvestment policy

Profits MAY be reinvested in:

- validated acquisition channels;
- data coverage;
- automation;
- infrastructure;
- product improvement;
- positioning and content;
- customer success.

Reinvestment MUST be conditioned on measured return, margin, risk limits, reserves and channel validation. AXIGNAL MUST NOT scale unvalidated paid acquisition merely because budget is available.

## 21. Acceptance gate

Packaging and pricing advance from candidate when:

1. target buyers understand the plan distinctions;
2. each marketed capability maps to an entitlement;
3. willingness-to-pay evidence exists;
4. gross-margin and support assumptions are measured;
5. pricing pages disclose limits, taxes and renewal terms;
6. usage and overage accounting is reproducible;
7. source-right constraints remain enforced;
8. upgrade, downgrade and cancellation flows are tested;
9. no dark pattern or fabricated discount exists;
10. public price status and version are auditable.

Exact plan names, public prices, limits and discounts remain unfrozen until this gate passes.