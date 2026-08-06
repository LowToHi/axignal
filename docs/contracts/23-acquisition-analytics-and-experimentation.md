# 23 — Acquisition Analytics and Experimentation Contract

Version: `0.2.0`
Status: `NORMATIVE CANDIDATE / PRODUCTION DATA AND P27 VALIDATION REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`
Governing programme: `Contract 31 / ADR-016`
Primary phases: `P23`, `P26`, `P27`

## 1. Purpose

This contract governs how AXIGNAL measures acquisition, consent, identity, trial activation, completed B2G value, paid conversion, retention and expansion, and how it runs experiments without sacrificing truthfulness, privacy, accessibility, source rights or product authority.

Optimising impressions, clicks, citations, alerts or signups while users fail to complete useful B2G work is not success.

## 2. Canonical acquisition funnel

```text
search impression, AI citation, referral or outreach
→ qualified public page or landing visit
→ source and methodology engagement
→ Tender Alert, sample investigation or trial CTA
→ consent or passwordless signup
→ tenant and trial-risk decision
→ trial READY
→ first admitted AI request starts trial
→ qualified opportunity shortlist
→ evidence and source inspection
→ bid/no-bid or pursuit workflow materially advanced
→ explicit paid package
→ repeated use
→ retention or renewal
→ expansion or referral
```

Every stage requires an explicit event, denominator and authority source.

## 3. Truth boundaries

```text
impression ≠ visit
visit ≠ qualified buyer
click ≠ consent
Tender Alert ≠ account
account ≠ trial
trial READY ≠ trial started
trial started ≠ customer value
subscription event ≠ settled payment
paid invoice ≠ completed value
AI citation ≠ endorsement
Search Console position ≠ causal acquisition
CRM stage ≠ entitlement
```

## 4. Primary metrics

Candidate primary metrics:

- admitted-page impression and click rate;
- qualified landing-visit rate;
- opportunity or methodology engagement;
- Tender Alert request and confirmed-opt-in rate;
- passwordless signup completion;
- risk-decision distribution and false-positive rate;
- trial READY rate;
- first admitted AI-use rate;
- time to first relevant shortlist;
- first evidence/source inspection;
- first completed dossier;
- first bid/no-bid or pursuit advancement;
- trial-to-paid conversion;
- paid weekly active organisations;
- retention and renewal;
- expansion by seats, package, library or jurisdiction;
- contribution margin;
- acquisition payback;
- support burden.

Traffic, page count, indexed URLs, token volume and AI citations are not primary success metrics.

## 5. Event taxonomy

Events are versioned and typed. Candidate families:

### Organic discovery

- `organic.page_candidate_evaluated`;
- `organic.snapshot_published`;
- `organic.snapshot_expired`;
- `organic.page_viewed`;
- `organic.source_opened`;
- `organic.methodology_opened`;
- `organic.ai_citation_observed`;
- `organic.search_console_imported`.

### Tender Alerts and CRM

- `alert.requested`;
- `alert.delivery_succeeded`;
- `alert.delivery_failed`;
- `alert.confirmed`;
- `alert.unsubscribed`;
- `crm.contact_created`;
- `crm.lifecycle_changed`;
- `crm.consent_changed`.

### Identity and trial

- `identity.signup_started`;
- `identity.email_verified`;
- `identity.passkey_bound`;
- `identity.session_started`;
- `trial.risk_evaluated`;
- `trial.ready`;
- `trial.activated`;
- `trial.step_up_required`;
- `trial.reused`;
- `trial.budget_exhausted`;
- `trial.expired`.

### Product value

- `product.research_run_started`;
- `product.research_run_completed`;
- `product.opportunity_shortlisted`;
- `product.claim_inspected`;
- `product.source_inspected`;
- `product.dossier_completed`;
- `product.bid_decision_recorded`;
- `product.pursuit_created`;
- `product.requirement_completed`;
- `product.outcome_recorded`.

### Billing and retention

- `billing.checkout_started`;
- `billing.provider_event_verified`;
- `billing.invoice_settled`;
- `billing.entitlement_reconciled`;
- `billing.subscription_changed`;
- `billing.subscription_cancelled`;
- `billing.refund_recorded`;
- `billing.dispute_recorded`;
- `retention.renewed`;
- `expansion.seat_or_package_added`.

Events must not fabricate provider, identity, trial, publication or product authority.

## 6. Identity and stitching

The system distinguishes:

- anonymous browser session;
- consented Tender Alert contact;
- CRM contact;
- verified identity;
- organisation member;
- trial tenant;
- billing customer;
- aggregate reporting cohort.

Identity stitching must not use undisclosed invasive fingerprinting or combine unrelated data merely to improve attribution.

HMAC or pseudonymous identifiers remain personal-data risk and require purpose, access and retention controls.

## 7. Search Console evidence

Google Search Console may contribute observed search-performance evidence after official API admission.

Candidate dimensions:

- query;
- page;
- country;
- device;
- date;
- search appearance where available.

Candidate metrics:

- clicks;
- impressions;
- CTR;
- average position.

Requirements:

- least-privilege API identity;
- secret reference only;
- bounded date range and row limits;
- import timestamp and property identity;
- data-quality state;
- rate-limit handling;
- audit;
- retention;
- revocation and kill switch.

The provided DNS TXT token is verification evidence only. It is not a Search Analytics import.

Search Console data cannot:

- set a page to `INDEXABLE`;
- publish or unpublish a page;
- prove buyer quality;
- grant a trial;
- establish revenue causality;
- authorise launch.

## 8. MCP analytics boundary

Any Search Console MCP is an external connector and tool authority.

Before use, it must pass:

- exact implementation and release identity;
- maintainer and licence review;
- dependency and supply-chain review;
- credential and Google-scope review;
- read/write/destructive tool classification;
- deny-by-default allowlist;
- prompt-injection and output-trust review;
- audit, revocation and kill switch.

MCP output is external evidence. It is not analytics authority, canonical truth or permission to mutate Search Console.

## 9. Attribution

AXIGNAL may record:

- referrer;
- UTM values;
- landing or public snapshot version;
- content asset;
- query/page performance from admitted Search Console imports;
- partner or referral code;
- first- and last-touch estimates;
- self-reported source;
- observed AI citation.

Attribution is an estimate. No report may present it as causal truth without controlled evidence.

## 10. Organic SEO measurement

Organic reporting must separate:

```text
page candidate
indexability decision
published snapshot
sitemap inclusion
crawl observation
index observation
impression
click
qualified visit
conversion
completed value
revenue
```

A page-volume increase is not a positive result unless quality, qualified activation and economics remain healthy.

Guardrails:

- thin-page rate;
- duplicate or cannibalising pages;
- stale snapshots;
- crawl waste;
- source-right incidents;
- misleading structured data;
- low-quality or unqualified traffic;
- conversion and product-value degradation.

## 11. AI citation measurement

Citation events preserve:

- provider;
- answer surface;
- cited URL;
- protected query evidence;
- observation source;
- observation time;
- snapshot version;
- actor or import process.

Reports must distinguish:

- citation observed;
- click or referral observed;
- signup attributed;
- trial activated;
- value completed;
- payment settled.

Citation count alone does not justify investment.

## 12. Tender Alert measurement

Tender Alert metrics include:

- request rate;
- delivery success;
- confirmation rate;
- unsubscribe and complaint rate;
- alert open and click under applicable consent;
- return to admitted opportunity pages;
- later identity creation;
- later trial and paid conversion.

The system must preserve:

```text
alert consent
≠ marketing consent
≠ account identity
≠ trial eligibility
```

## 13. CRM boundary

The CRM may record:

- source;
- consent state;
- declared company and role;
- target market or sector;
- lifecycle stage;
- lead score;
- owner;
- next action;
- commercial outcome;
- retention or deletion state.

CRM automation cannot overwrite:

- identity;
- risk decision;
- trial grant;
- paid entitlement;
- source or claim state;
- provider billing state.

## 14. Experiment registry

Every experiment is registered before exposure with:

- stable ID;
- hypothesis;
- owner;
- affected funnel stage;
- target population;
- eligibility and exclusions;
- exact copy, price, package, public-page or onboarding version;
- primary metric;
- guardrails;
- stopping rule;
- assignment method;
- privacy, accessibility, rights and security review;
- rollback;
- decision.

Post-hoc metric selection is prohibited.

## 15. Permitted experiment domains

Candidate experiments may test:

- B2G value-proposition wording;
- hero hierarchy;
- faithful product proof;
- CTA commitment level;
- Tender Alert framing;
- public-page layout and content depth;
- pricing presentation without changing provider authority;
- annual versus monthly explanation;
- FAQ and methodology placement;
- form length;
- onboarding order;
- sample investigation;
- qualified acquisition channels.

## 16. Prohibited experiments

Experiments must not:

- fabricate urgency, scarcity, proof or citations;
- hide prices, limits, cancellation or source coverage;
- weaken evidence or uncertainty disclosure;
- discriminate using sensitive characteristics;
- intentionally reduce accessibility;
- change contractual terms without authority;
- generate thin SEO pages;
- expose users to an unadmitted source;
- alter trial eligibility or abuse policy from the browser;
- change IndexabilityGate thresholds without typed authority;
- enable public indexing, signup or billing;
- install or widen an MCP.

## 17. Guardrail metrics

Relevant guardrails include:

- comprehension of B2G purpose;
- confusion with guarantee, legal advice or autonomous bidding;
- privacy and consent understanding;
- accessibility failures;
- performance;
- form and passkey errors;
- unqualified lead rate;
- abuse false positives;
- refund and dispute rate;
- first-value completion;
- support burden;
- trust feedback;
- source-right or coverage incidents;
- thin-page and crawl-waste rates.

A conversion gain with material guardrail degradation is rejected.

## 18. Segmentation and privacy

Permitted segments may include:

- locale;
- country;
- acquisition source;
- public page class;
- sector;
- B2G role;
- organisation type;
- device;
- trial and product state;
- candidate package.

Small or re-identifiable groups are suppressed or aggregated. Search queries and company scope may reveal sensitive intent and require minimisation and access control.

## 19. Data quality

Pipelines must detect:

- duplicate events;
- bots and internal traffic;
- impossible event order;
- missing or stale snapshot versions;
- consent mismatch;
- clock drift;
- schema mismatch;
- delayed imports;
- Search Console partial rows or sampling limitations;
- experiment contamination;
- CRM/provider/identity state mismatch.

Reports display current data-quality limitations.

## 20. Statistical and qualitative discipline

Experiment decisions consider sample size, exposure balance, novelty, repeated measurement, multiple comparisons, seasonality, channel mix, practical effect size, uncertainty and guardrails.

Quantitative evidence is complemented by:

- buyer interviews;
- comprehension tests;
- onboarding observation;
- sales objections;
- lost-deal reasons;
- support themes;
- private-acceptance interviews.

Individual comments are not population truth.

## 21. Channel reinvestment

A channel is eligible for scaled reinvestment only when evidence supports:

- qualified traffic;
- completed consent or signup;
- trial activation;
- completed B2G value;
- paid conversion or credible pipeline;
- acceptable CAC, payback and contribution margin;
- low fraud, complaint and refund risk;
- support capacity.

Search impressions, rankings, citations or alert subscribers alone do not justify scaling.

## 22. Decision states

Every experiment ends with:

- `SHIP`;
- `ITERATE`;
- `REJECT`;
- `INCONCLUSIVE`;
- `STOPPED_FOR_GUARDRAIL`;
- `INVALID_DATA`.

Results and rejected variants remain auditable.

## 23. Acceptance gate

This contract advances only when:

1. events connect acquisition to completed product value;
2. identity, CRM, trial, billing and product authority remain distinct;
3. consent and deletion pass;
4. Search Console API evidence is admitted or explicitly excluded;
5. every connected MCP passes admission;
6. organic page lifecycle is measured without page-volume incentives;
7. AI citations are measured as observations only;
8. experiment assignment is reproducible;
9. guardrails prevent harmful optimisation;
10. data quality is visible;
11. reinvestment follows measured economics;
12. P27 accepts the exact final head.

## 24. Current authority

```text
P26 ORGANIC EVENT FOUNDATION      ENGINEERING PASS
TENDER ALERT CONSENT FOUNDATION   ENGINEERING PASS
CRM FOUNDATION                    ENGINEERING PASS
AI CITATION LEDGER                ENGINEERING PASS
SEARCH CONSOLE DNS                USER-ATTESTED EVIDENCE
SEARCH CONSOLE API IMPORT         NOT PROVEN
GSC MCP                           NOT ADMITTED
PUBLIC ANALYTICS ACTIVATION       BLOCKED
CHANNEL SCALE                     NOT AUTHORISED
PUBLIC LAUNCH                     NO_GO
```
