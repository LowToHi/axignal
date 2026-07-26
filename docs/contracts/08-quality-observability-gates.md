# 08 — Quality, Observability and Gates Contract

Version: `0.1.0`
Status: `NORMATIVE`

## 1. Objective

ASIGNAL MUST measure whether its data, claims, scenarios, user experience and commercial model are trustworthy enough to operate. “The pipeline ran” is not evidence of product correctness.

## 2. Observability dimensions

The platform MUST expose four connected observability layers:

1. infrastructure health;
2. source and data quality;
3. epistemic and model quality;
4. product and commercial outcomes.

A request, claim or opportunity SHOULD be traceable across these layers through correlation identifiers.

## 3. Infrastructure SLOs

Paid beta target objectives:

- monthly web/API availability: `99.5%` excluding published maintenance;
- authentication and entitlement p95: `<250 ms`;
- common API read p95: `<500 ms`;
- claim-detail p95: `<800 ms`;
- cached page server response p95: `<1.5 s`;
- background job success rate: `>99%` excluding source-origin failures;
- no unacknowledged critical incident beyond defined escalation window.

Targets MUST be revised from production evidence.

## 4. Source health

For every source:

- last successful retrieval;
- expected next update;
- request failure rate;
- schema drift;
- parse failure rate;
- raw-object duplication;
- latency against source publication;
- rights status;
- credential expiry;
- quota consumption;
- downstream claim count;
- affected product surfaces.

Source outages MUST be distinguished from internal failures.

## 5. Data quality gates

A batch MUST be quarantined when a material threshold fails.

Initial required checks:

- schema conformance;
- required-field completeness;
- identifier validity;
- duplicate detection;
- date plausibility;
- unit and currency validity;
- geographic validity;
- unexpected distribution shift;
- entity-resolution confidence;
- lineage completeness;
- rights metadata completeness.

Thresholds MUST be source-specific and versioned.

## 6. Epistemic quality

Required metrics:

- candidate-to-admitted claim rate;
- rejection reason distribution;
- claims lacking independent corroboration;
- contested claim rate;
- correction and retraction rate;
- expired-claim propagation latency;
- evidence-link integrity;
- quantitative reproducibility rate;
- source-lineage duplication rate;
- human override rate and reasons;
- claims admitted by policy version.

A sudden admission-rate change MUST trigger policy or source-drift review.

## 7. Entity quality

Track:

- automatic merge precision from audited samples;
- unresolved entity rate;
- low-confidence merge rate;
- split and correction rate;
- identifier coverage;
- alias growth;
- cross-jurisdiction ambiguity;
- downstream claims affected by corrections.

Low-confidence entity merges MUST NOT contribute to public high-confidence opportunity states.

## 8. Forecast and scenario quality

Every production scenario model MUST have:

- frozen evaluation datasets;
- temporal holdout;
- baseline comparison;
- calibration report;
- performance by geography, universe and horizon;
- drift thresholds;
- retraining or retirement policy;
- reproducible versioned features;
- outcome reconciliation.

Relevant metrics MAY include Brier score, log loss, interval coverage, precision, recall and calibration error.

A model MUST be demoted or removed when its calibration degrades beyond its approved threshold.

## 9. Opportunity quality

Track:

- opportunities by maturity state;
- supporting and contradicting claim counts;
- source diversity;
- time to first corroboration;
- time to invalidation;
- user inspection rate;
- evidence drill-down rate;
- watchlist addition rate;
- revisit rate;
- user correction or challenge rate;
- downstream commercial or real-world outcomes when known.

An opportunity MUST NOT be promoted because it maximises engagement alone.

## 10. Product analytics

Events MUST be defined in a versioned analytics contract.

Core events:

- globe layer viewed;
- market or geography opened;
- opportunity inspected;
- claim inspected;
- evidence source opened;
- contradiction inspected;
- graph path explored;
- historical replay used;
- watchlist item added;
- alert opened;
- report exported;
- plan upgrade started and completed.

Analytics MUST respect privacy and source rights.

## 11. Trust metrics

ASIGNAL SHOULD measure whether users understand the methodology:

- percentage who can distinguish observation from forecast;
- percentage who inspect sources;
- correction acknowledgement rate;
- perceived confidence calibration;
- methodology comprehension in user research;
- trust after a visible model error or retraction.

High visual engagement with low epistemic comprehension is a product failure.

## 12. Commercial metrics

Required:

- qualified visitor-to-demo;
- demo-to-paid;
- trial-to-paid where trials exist;
- MRR and ARR;
- gross margin by plan;
- data cost per paid account;
- AI cost per paid account;
- logo and revenue retention;
- net revenue retention;
- upgrades and additional seats;
- annual-plan share;
- acquisition payback;
- support load per account.

## 13. Release gates

### Gate R0 — Contract integrity

- affected contracts updated;
- ADR included when necessary;
- schema compatibility checked.

### Gate R1 — Engineering quality

- unit, integration and end-to-end tests pass;
- migrations tested;
- static analysis passes;
- dependencies scanned;
- accessibility checks pass.

### Gate R2 — Data and epistemic quality

- fixtures reproduce the full lineage;
- admission rules pass;
- correction and expiry propagation pass;
- no restricted data leaks.

### Gate R3 — Security and operations

- threat-model impact reviewed;
- logging and alerts added;
- rollback documented;
- backup implications reviewed.

### Gate R4 — Product acceptance

- acceptance criteria demonstrated;
- qualified-user testing completed for material UX changes;
- no misleading certainty introduced.

## 14. Universe admission gate

A universe MAY be marketed as supported only when:

- source rights are approved;
- coverage is measured;
- ontology is stable enough;
- claim admission policies are tested;
- freshness is accurately represented;
- at least one high-value workflow is validated;
- user demand is evidenced;
- cost and margin are acceptable;
- regulatory review is complete;
- outage and revocation are tested.

## 15. Severity model

- `SEV-0`: security breach, unauthorised transaction-like behaviour, audit-ledger corruption or widespread restricted-data exposure;
- `SEV-1`: material tenant isolation failure, false authoritative claim propagation, severe outage or corrupted source lineage;
- `SEV-2`: significant universe degradation, wrong entitlement, widespread stale state or failed scenario correction;
- `SEV-3`: limited degradation, delayed source or non-critical UX failure;
- `SEV-4`: cosmetic or low-impact issue.

## 16. Alerts

Alerts MUST be actionable and tied to an owner and runbook.

Avoid alerting on every individual source failure when aggregation and retry policy are more appropriate.

Required high-priority alerts:

- unauthorised access attempt patterns;
- audit-log write failure;
- claim-state propagation failure;
- source-rights status change;
- tenant-isolation test failure;
- backup failure;
- critical credential expiry;
- scenario calibration breach;
- severe entity merge anomaly;
- Stripe entitlement mismatch.

## 17. Dashboards

Minimum dashboards:

1. platform health;
2. source health and cost;
3. claim admission and corrections;
4. opportunity and scenario state;
5. security and entitlement;
6. product usage;
7. revenue and gross margin.

## 18. Audit samples

Automated quality MUST be supplemented with regular stratified human audits.

Samples SHOULD cover:

- high-impact opportunities;
- high-ranking claims;
- low-confidence entity merges;
- multilingual extraction;
- contested claims;
- model-generated causal hypotheses;
- source groups with unusual admission rates.

## 19. Definition of production-ready

A capability is production-ready only when:

- its contract exists;
- acceptance tests exist;
- telemetry exists;
- failure behaviour is known;
- rollback or disabling is possible;
- security and rights reviews pass;
- support and incident ownership are assigned;
- user-visible limitations are documented.
