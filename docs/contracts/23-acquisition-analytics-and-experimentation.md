# 23 — Acquisition Analytics and Experimentation Contract

Version: `0.1.0-candidate`
Status: `NORMATIVE CANDIDATE / VALIDATION REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

This contract governs how AXIGNAL measures acquisition, conversion, activation, retention and expansion, and how it runs experiments without sacrificing truthfulness, privacy, accessibility or the product goal.

Analytics MUST connect marketing activity to delivered product value. Optimising clicks while users fail to complete a useful investigation is not success.

## 2. Canonical funnel

AXIGNAL MUST measure the following funnel where applicable:

```text
impression or referral
→ qualified landing visit
→ product proof interaction
→ pricing or use-case engagement
→ request access / signup / demo
→ qualification
→ attended meeting or trial start
→ first completed investigation
→ first inspected claim and source
→ repeat investigation
→ paid conversion
→ retention
→ expansion or referral
```

Each stage MUST have an explicit event definition and denominator.

## 3. Primary metrics

Candidate primary metrics include:

- qualified-visit rate;
- hero CTA rate;
- product-demo engagement rate;
- pricing-view rate;
- request-access or signup completion;
- qualified-meeting rate;
- show rate;
- trial activation rate;
- first-investigation completion rate;
- time to first inspected claim and source;
- opportunity-to-evidence completion;
- repeat-investigation rate;
- paid conversion;
- retention by cohort;
- expansion by seats, universes or usage;
- gross margin and acquisition payback.

Traffic volume alone MUST NOT be treated as validated demand.

## 4. Event taxonomy

Events MUST be versioned and typed. Candidate event families:

- `acquisition.page_viewed`;
- `acquisition.cta_clicked`;
- `acquisition.product_demo_started`;
- `acquisition.product_demo_completed`;
- `acquisition.pricing_viewed`;
- `acquisition.plan_compared`;
- `acquisition.faq_opened`;
- `acquisition.trust_content_viewed`;
- `lead.form_started`;
- `lead.form_submitted`;
- `lead.qualified`;
- `sales.meeting_booked`;
- `sales.meeting_attended`;
- `product.investigation_started`;
- `product.investigation_completed`;
- `product.claim_inspected`;
- `product.source_inspected`;
- `billing.checkout_started`;
- `billing.subscription_started`;
- `billing.subscription_changed`;
- `billing.subscription_cancelled`.

Every event SHOULD include only fields required for analysis and operations.

## 5. Identity and stitching

Anonymous, authenticated user and organisation identifiers MUST remain purpose-limited.

Identity stitching MUST NOT use undisclosed fingerprinting or combine unrelated data sources merely to increase attribution accuracy.

The system MUST distinguish:

- anonymous session;
- consented marketing identity;
- product user;
- organisation member;
- billing customer;
- aggregate reporting cohort.

## 6. Attribution

AXIGNAL MAY record:

- referrer;
- campaign and UTM values;
- landing variant;
- content or research asset;
- partner or referral code;
- first-touch and last-touch candidate attribution;
- self-reported discovery source.

Attribution models are estimates. Reports MUST NOT present them as causal truth without controlled evidence.

## 7. Experiment registry

Every experiment MUST be registered before exposure with:

- stable ID;
- hypothesis;
- owner;
- affected funnel stage;
- target population;
- eligibility and exclusions;
- primary metric;
- guardrail metrics;
- sample or stopping rule;
- start and end conditions;
- variant assignment method;
- privacy and accessibility review;
- rollback;
- decision outcome.

Post-hoc metric selection is prohibited.

## 8. Permitted experiment domains

Candidate experiments MAY test:

- value-proposition language;
- hero hierarchy;
- faithful product-demo framing;
- CTA wording and commitment level;
- use-case routing;
- pricing presentation;
- annual versus monthly explanation;
- FAQ ordering;
- methodology and Trust Center placement;
- form length;
- onboarding sequence;
- sample-investigation selection;
- content and acquisition channels.

## 9. Prohibited experiments

Experiments MUST NOT:

- fabricate urgency, scarcity or social proof;
- hide prices, limits or cancellation;
- weaken disclosure of inference, prediction or uncertainty;
- conceal Knowledge Tides or privacy controls;
- discriminate using sensitive characteristics;
- intentionally reduce accessibility;
- expose users to materially different contractual terms without authority;
- misrepresent unavailable functionality;
- use dark patterns to increase conversion;
- optimise investment-action urgency.

## 10. Guardrail metrics

Each conversion experiment MUST monitor relevant guardrails such as:

- comprehension of AXIGNAL's purpose;
- confusion with personalised advice or trading;
- privacy-control discovery;
- accessibility failures;
- page performance;
- form errors;
- unqualified lead rate;
- cancellation or refund rate;
- first-investigation completion;
- support burden;
- customer trust feedback.

A conversion gain with material guardrail degradation MUST be rejected.

## 11. Segmentation

Permitted analytical segments MAY include:

- locale;
- acquisition source;
- use case;
- organisation type;
- plan;
- device class;
- new versus returning;
- product activation state.

Segments MUST have sufficient population and privacy protection. Small or re-identifiable groups MUST be suppressed or aggregated.

## 12. Knowledge Tides separation

Marketing analytics, product usage analytics and Knowledge Tides MUST remain separate datasets and purposes.

A marketing conversion event MUST NOT become an economic claim. A product query MAY contribute to a privacy-protected aggregate Knowledge Tide only under Contract 15 and applicable controls.

## 13. CRM and lead operations

Lead routing MAY integrate with a CRM and scheduling system.

The system MUST record:

- source and consent state;
- requested use case;
- organisation where voluntarily supplied;
- lifecycle stage;
- owner or queue;
- next action;
- commercial outcome;
- lawful retention or deletion state.

CRM automation MUST NOT overwrite canonical product claims or research state.

## 14. Automation

Permitted automation MAY include:

- form confirmation;
- meeting routing;
- lead scoring based on declared business-fit criteria;
- reminder and follow-up sequences;
- trial onboarding;
- inactivity or activation nudges;
- sales and customer-success handoff.

Automation MUST be frequency-limited, auditable, stoppable and compliant with communication preferences.

## 15. Statistical discipline

Experiment decisions MUST consider:

- sample size;
- exposure balance;
- novelty effects;
- repeated measurement;
- multiple comparisons;
- seasonality and channel mix;
- practical effect size;
- confidence or uncertainty;
- guardrail outcomes.

AXIGNAL SHOULD prefer sequential or Bayesian methods only when the method, stopping criteria and interpretation are documented. Statistical significance alone is insufficient for rollout.

## 16. Qualitative evidence

Quantitative analytics MUST be complemented by:

- moderated usability sessions;
- sales-call objection coding;
- onboarding observation;
- lost-deal reasons;
- support themes;
- design-partner interviews.

Qualitative evidence MUST be recorded without treating individual comments as population-level truth.

## 17. Data quality

Analytics pipelines MUST detect:

- duplicate events;
- missing identifiers;
- impossible orderings;
- bot and internal traffic;
- clock drift;
- schema-version mismatch;
- delayed delivery;
- experiment-assignment contamination;
- consent-state inconsistency.

Reports MUST display known data-quality limitations.

## 18. Privacy and consent

Analytics collection MUST comply with Contract 06.

Requirements include:

- purpose limitation;
- minimisation;
- consent or other valid basis where applicable;
- locale-aware cookie and tracking controls;
- deletion and access handling;
- processor inventory;
- retention limits;
- no advertising disclosure that contradicts actual data use.

## 19. Performance

Analytics and experimentation code MUST NOT materially degrade:

- Core Web Vitals;
- interaction responsiveness;
- accessibility;
- product-demo loading;
- checkout reliability.

Non-essential analytics SHOULD load after critical content and respect consent state.

## 20. Channel validation and reinvestment

A channel is eligible for scaled reinvestment only when evidence supports:

- qualified traffic;
- conversion beyond the landing page;
- first-investigation activation;
- paid conversion or credible pipeline;
- acceptable acquisition cost;
- acceptable payback and margin;
- low fraud and low refund risk.

Budget MUST NOT be scaled solely because top-of-funnel metrics are strong.

## 21. Decision states

Each experiment MUST end with one state:

- `SHIP`;
- `ITERATE`;
- `REJECT`;
- `INCONCLUSIVE`;
- `STOPPED_FOR_GUARDRAIL`;
- `INVALID_DATA`.

Results and rejected variants MUST remain auditable.

## 22. Acceptance gate

This contract advances when:

1. the funnel and event taxonomy are implemented and documented;
2. acquisition is connected to first-investigation value;
3. experiment assignment and exposure are reproducible;
4. privacy and consent behaviour pass review;
5. guardrail metrics prevent harmful optimisation;
6. CRM and automations are auditable and stoppable;
7. attribution limitations are explicit;
8. data quality is monitored;
9. channel reinvestment follows measured economics;
10. no experiment can silently weaken product truth or accessibility.