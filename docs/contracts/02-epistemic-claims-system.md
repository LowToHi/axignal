# 02 — Epistemic Claims System Contract

Version: `0.1.0`
Status: `NORMATIVE`

## 1. Purpose

The epistemic claims system is the authoritative core of ASIGNAL. It MUST distinguish extraction, belief, evidence, inference and forecast so that no generative output becomes product truth merely because it is plausible.

The core transformation is:

```text
raw signal
→ evidence object
→ candidate claim
→ structural validation
→ source and rights validation
→ epistemic admission
→ canonical claim ledger
→ graph relationships
→ market state and opportunity assembly
→ scenario model
```

## 2. Claim definition

A claim is an atomic, scoped and time-bounded assertion about an entity, event, measurement, relationship or scenario.

A valid claim MUST contain:

- immutable `claim_id`;
- canonical `subject` reference;
- typed `predicate`;
- typed `object` or value;
- `claim_type`;
- `epistemic_status`;
- observation timestamp;
- event or validity time where applicable;
- geography or jurisdiction where applicable;
- evidence references;
- source references;
- method version;
- producer identity;
- lineage and dependencies;
- rights classification;
- freshness and expiry rules;
- confidence dimensions;
- contradiction links;
- version and replacement information.

## 3. Claim types

Canonical initial types:

- `OBSERVED_QUALITATIVE`
- `OBSERVED_QUANTITATIVE`
- `CALCULATED`
- `RELATIONAL`
- `TREND`
- `CAUSAL_HYPOTHESIS`
- `PREDICTIVE`
- `COMMERCIAL_HYPOTHESIS`
- `EXPERIMENTAL_RESULT`
- `OUTCOME`
- `RISK`
- `LEGAL_OR_REGULATORY`

Each type MUST have independent admission requirements.

## 4. Epistemic states

Canonical lifecycle:

```text
PROPOSED
→ PARSED
→ SOURCE_BOUND
→ STRUCTURALLY_VALID
→ RIGHTS_VALID
→ ADMISSIBLE
→ CORROBORATED
→ ACTIONABLE
```

Terminal or exceptional states:

- `CONTESTED`
- `SUPERSEDED`
- `FALSIFIED`
- `EXPIRED`
- `RETRACTED`
- `REJECTED`
- `QUARANTINED`

State transitions MUST be evented and auditable. State MUST NOT be overwritten without preserving history.

## 5. Evidence

Evidence is not free text alone. Every evidence object MUST include:

- `evidence_id`;
- source location;
- retrieval timestamp;
- content hash;
- extract or structured payload;
- source publication time where available;
- parser or extractor version;
- immutable raw-object reference;
- legal-use classification;
- language;
- confidence in extraction;
- retention rule.

A web page, filing, API response, dataset row, document paragraph or verified experiment result MAY become evidence.

## 6. Provenance

ASIGNAL SHOULD model provenance compatibly with the concepts of entity, activity and agent used by W3C PROV.

At minimum, the system MUST answer:

- who or what produced the claim;
- from which evidence;
- using which transformation;
- at what time;
- under which software and model version;
- whether a human reviewed it;
- which prior claims it depends on.

Circular derivations MUST be rejected or explicitly quarantined.

## 7. Deterministic admission gates

### Structural gate

MUST verify schema, types, identifiers, units, dates, geography and required fields.

### Source gate

MUST verify that the source exists, is addressable or archived and is classified for reliability and independence.

### Rights gate

MUST verify that collection, storage, transformation, internal use, display and redistribution are permitted for the intended product surface.

### Temporal gate

MUST distinguish publication time, observation time, event time and validity interval.

### Quantitative gate

MUST verify units, currencies, denominators, transformations, missing data and reproducibility.

### Epistemic gate

MUST prevent:

- inference presented as observation;
- correlation presented as causation;
- duplicated syndication counted as independent corroboration;
- forecasts presented as facts;
- absence of evidence presented as evidence of absence;
- stale claims participating in current state without explicit historical use.

## 8. Corroboration and source independence

Corroboration MUST be based on independent source groups, not URL count.

The system MUST maintain `source_lineage_group_id` to detect:

- copied press releases;
- syndicated news;
- mirrors;
- aggregators repeating one primary source;
- datasets derived from the same upstream source.

A claim MAY be corroborated by one highly authoritative primary source when the claim is directly within that source’s competence. The reason MUST be encoded in policy.

## 9. Contradictions

Contradictions are first-class graph edges.

The system MUST support:

- direct contradiction;
- scope contradiction;
- temporal contradiction;
- methodological contradiction;
- value disagreement;
- source correction;
- scenario incompatibility.

Contradictory claims MUST NOT automatically cancel each other. The system MUST preserve both, compare scope and produce an explicit contested state when necessary.

## 10. Confidence model

ASIGNAL MUST NOT use a single opaque truth score.

Canonical dimensions:

- `evidence_strength`;
- `source_authority`;
- `source_independence`;
- `extraction_confidence`;
- `method_reproducibility`;
- `freshness`;
- `scope_completeness`;
- `contradiction_pressure`;
- `forecast_uncertainty`;
- `rights_confidence`.

A composite rank MAY be used for ordering only if all component scores remain visible and the weighting model is versioned.

## 11. Vector and graph roles

Embeddings MAY support:

- semantic similarity;
- multilingual matching;
- duplicate detection;
- contradiction candidate discovery;
- related-market exploration;
- clustering;
- analogue retrieval.

Embeddings MUST NOT:

- admit claims;
- determine truth;
- establish causal relationships;
- serve as the only persistence of claim semantics;
- count similar text as independent evidence.

Canonical rule:

> The vector discovers; the graph contextualises; the runtime admits.

## 12. Opportunity assembly

An opportunity is a versioned subgraph, not a generated paragraph.

A candidate opportunity MUST include typed roles such as:

- problem or anomaly claim;
- affected entity or payer claim;
- scale or frequency claim;
- market-access claim;
- competition claim;
- operational feasibility claim;
- legal and regulatory risk claim;
- AI-absorption risk claim;
- contradiction set;
- unknown set;
- invalidation conditions;
- optional experimental or outcome claims.

No opportunity may be classified as `ACTIONABLE` solely from trend claims.

## 13. Trend model

Trend analysis SHOULD compute, where relevant:

- claim velocity;
- evidence density;
- independent-source growth;
- geographic replication;
- persistence;
- commercial validation;
- contradiction pressure;
- novelty;
- opportunity maturation;
- scenario drift.

Every trend metric MUST identify its claim population, time window and method version.

## 14. Scenario model

A scenario MUST include:

- subject and scope;
- horizon;
- generation timestamp;
- model and feature versions;
- supporting claims;
- contradicting claims;
- assumptions;
- probability band or calibrated score;
- uncertainty;
- historical analogues;
- invalidation conditions.

The system MUST preserve old forecasts and compare them with outcomes. It MUST NOT rewrite forecasts after the event.

## 15. Calibration

Predictive components MUST be calibrated on frozen historical data with strict temporal separation.

Required measures depend on the forecast but SHOULD include:

- Brier score;
- calibration curve;
- log loss;
- interval coverage;
- precision and recall for event detection;
- baseline comparison;
- performance by market, geography and horizon;
- drift monitoring.

A scenario model MUST fail closed from public ranking if calibration evidence is unavailable or materially stale.

## 16. Human review

Human review MAY:

- approve source policies;
- resolve ontology ambiguity;
- adjudicate contested claims;
- correct entity resolution;
- approve high-impact publication;
- override automated state with a reason.

Every override MUST be signed, timestamped and reversible. Human review MUST NOT erase the machine decision history.

## 17. Retractions and corrections

Corrections MUST create a new version or replacement claim. The original MUST remain linked and visible in the audit history.

Retraction events MUST propagate to:

- opportunity subgraphs;
- trend aggregates;
- scenario inputs;
- cached API responses;
- user watchlists and alerts;
- exported reports where technically possible.

## 18. User-facing language

The UI MUST use disciplined language:

- “observed” for observations;
- “calculated” for reproducible calculations;
- “inferred” for model interpretation;
- “scenario” or “forecast” for future states;
- “contested” when material evidence conflicts;
- “insufficient evidence” when gates fail.

The UI MUST NOT use “verified investment”, “guaranteed opportunity”, “safe return” or equivalent language.

## 19. Acceptance criteria

The claims core is not accepted until it demonstrates:

1. immutable claim and evidence IDs;
2. versioned state transitions;
3. reproducible quantitative claims;
4. contradiction storage and display;
5. source-lineage grouping;
6. deterministic schema and rights gates;
7. expiry propagation;
8. preserved forecast history;
9. machine-readable export;
10. tests proving AI-generated text cannot bypass admission.
