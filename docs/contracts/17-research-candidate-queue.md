# 17 — AXIGNAL Research Candidate Queue Contract

Version: `0.3.1`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

The Research Candidate Queue converts validated coverage gaps, Knowledge Tides, contradictions, external events and strategic hypotheses into governed research work.

It MUST ensure that attention changes what AXIGNAL investigates without allowing popularity to determine truth.

## 2. Candidate sources

A research candidate MAY originate from:

- aggregate Knowledge Tide;
- repeated high-value failed search;
- coverage gap;
- contradiction requiring adjudication;
- source correction or revocation;
- regulatory event;
- new market or universe hypothesis;
- user-submitted research request;
- enterprise-private request;
- model or analyst anomaly detection;
- scheduled universe refresh.

The origin MUST be explicit.

## 3. Candidate schema

Required fields:

- candidate ID;
- canonical research question;
- origin type and references;
- geographies, entities and universes;
- created time;
- privacy and tenant scope;
- external-evidence gap;
- current coverage;
- user-attention dimensions where applicable;
- strategic relevance;
- expected buyer value;
- source availability and rights status;
- estimated data, model and human cost;
- regulatory risk;
- manipulation risk;
- proposed research method;
- priority dimensions;
- lifecycle state;
- owner;
- expiry or review time.

## 4. Candidate states

```text
PROPOSED
→ ELIGIBILITY_REVIEW
→ PRIORITISED
→ RESEARCHING
→ EVIDENCE_COLLECTED
→ CLAIMS_PROPOSED
→ ADMISSION_REVIEW
→ COMPLETED
```

Exceptional states:

- `PRIVACY_SUPPRESSED`
- `RIGHTS_BLOCKED`
- `REGULATORY_BLOCKED`
- `DUPLICATE`
- `MANIPULATION_SUSPECTED`
- `INSUFFICIENT_VALUE`
- `EXPIRED`
- `REJECTED`
- `PAUSED`

## 5. Priority dimensions

The queue MUST remain multidimensional:

- qualified user-attention share;
- velocity and persistence;
- organisation diversity;
- language and user-geography diversity;
- coverage gap;
- external-evidence gap;
- contradiction pressure;
- buyer and strategic value;
- novelty;
- source availability;
- source rights confidence;
- research feasibility;
- estimated cost;
- regulatory complexity;
- manipulation risk;
- expected learning value.

A composite priority MAY order the queue only if weights and dimensions remain visible and versioned.

## 6. Sixty-percent example

When 60% of eligible active users independently investigate a canonical topic during a defined period, the queue SHOULD create or materially elevate a candidate when:

- the cohort exceeds the minimum privacy threshold;
- unique users, not prompts, define the numerator;
- organisation concentration is acceptable;
- bot, internal and campaign-driven traffic are excluded or labelled;
- the question is not already sufficiently covered;
- legal and source feasibility permit investigation.

This evidence supports research priority, not economic opportunity admission.

## 7. Candidate deduplication

The queue MUST detect equivalent questions across:

- languages;
- synonyms;
- transliterations;
- entity aliases;
- overlapping geographies;
- differently worded causal hypotheses.

Merged candidates MUST preserve their original origins, cohorts and timestamps.

## 8. Research plan

Before state `RESEARCHING`, a candidate MUST define:

- question and scope;
- falsification conditions;
- required claim types;
- supporting and contradictory evidence sought;
- candidate sources;
- source-rights checks;
- time horizon;
- cost budget;
- human-review need;
- stopping rule;
- expected product output.

## 9. Research execution

Research agents MAY:

- locate sources;
- retrieve authorised data;
- extract evidence;
- propose entities and claims;
- identify contradictions;
- create a research dossier.

They MUST NOT:

- admit claims directly;
- infer source rights;
- expose private prompts;
- fabricate missing evidence;
- continue beyond the approved budget silently;
- publish a user-facing opportunity before admission.

## 10. Output

A completed candidate MAY produce:

- admitted claims;
- contested claims;
- explicit unknowns;
- a coverage update;
- an opportunity subgraph;
- an evidence-based rejection;
- a new source-admission proposal;
- a user-visible research note;
- a decision not to cover the topic.

A useful negative result is a valid outcome.

## 11. Feedback to users

Users who saved or requested the investigation MAY receive status such as:

- queued;
- researching;
- blocked by insufficient lawful data;
- evidence found;
- contested;
- completed;
- no admissible conclusion.

The system MUST not promise completion dates or positive results without operational support.

## 12. Private and enterprise candidates

Private candidates MUST remain tenant-scoped unless explicit authority permits broader use.

A private research request MUST not influence global Knowledge Tides or public queue state by default.

## 13. Cost control

Every candidate MUST have an estimated and actual cost ledger covering:

- data access;
- model usage;
- compute;
- human review;
- legal or rights review;
- opportunity cost.

High-cost candidates require an explicit budget gate.

## 14. Metrics

Required metrics:

- candidate creation by origin;
- duplicate and suppression rate;
- queue age;
- research start and completion time;
- rights-block rate;
- candidate-to-evidence conversion;
- candidate-to-admitted-claim conversion;
- negative-result rate;
- cost by completed candidate;
- user revisit and satisfaction;
- tide-to-research conversion;
- manipulation false-positive and false-negative audits.

## 15. Queue governance

- Priority changes MUST be auditable.
- Sponsored or conflicted requests MUST be labelled and isolated from canonical ranking.
- Administrators MAY override priority only with a reason.
- Old candidates MUST decay or expire.
- Research completion MUST not imply opportunity maturity.

## 16. Acceptance criteria

The queue is accepted when:

- a Knowledge Tide creates a typed candidate rather than an economic claim;
- equivalent multilingual questions deduplicate correctly;
- private candidates stay isolated;
- source-rights blocks fail closed;
- research budgets are enforced;
- supporting, contradicting and negative evidence are collected;
- candidate history and priority changes are auditable;
- completed research passes through claim admission;
- a 60%-interest candidate can be reproduced from its cohort data.
