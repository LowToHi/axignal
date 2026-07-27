# 27 — AXIGNAL Local Research Worker and Candidate Claim Pipeline Contract

Version: `0.1.0`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

AXIGNAL MAY operate local or self-hosted research workers continuously to monitor authorised sources, extract evidence, detect changes and propose Candidate Claims. A model has proposal authority only. It MUST NOT admit claims, publish opportunities or write canonical truth directly.

The canonical pipeline is:

```text
authorised source
→ immutable raw object or reproducible reference
→ deterministic parsing and normalisation
→ model-assisted extraction or research
→ Evidence Objects
→ Candidate Claims
→ quarantine and validation
→ deterministic admission gates
→ Claim Ledger
→ opportunity projection
```

## 2. Authority boundary

The worker MAY:

- schedule and execute admitted connectors;
- detect source changes;
- extract structured facts from unstructured material;
- propose entities, aliases and graph relations;
- generate embeddings;
- deduplicate documents and candidate assertions;
- identify supporting, contradictory and missing evidence;
- propose Candidate Claims;
- create research dossiers;
- queue claims for admission review;
- request human or higher-capability model review.

The worker MUST NOT:

- set a claim to `ADMISSIBLE`, `CORROBORATED` or `ACTIONABLE`;
- infer source rights or override a rights decision;
- treat model confidence as truth probability;
- publish an opportunity directly;
- access private tenant data without a scoped ResearchRun;
- merge tenant-private knowledge into global knowledge;
- bypass structural, temporal, quantitative, source, rights or epistemic gates;
- continue beyond budget silently;
- execute deployment or infrastructure administration.

## 3. Source-first architecture

Structured, authoritative APIs MUST be processed primarily through deterministic code. AI SHOULD be introduced only where it adds measurable value.

Examples:

| Input | Preferred processing |
|---|---|
| official statistical time series | schema validation, normalisation, calculations and anomaly detection in code |
| market feed | licensed connector, deterministic aggregation and timestamp controls |
| company filing or regulatory document | parser plus model-assisted extraction |
| property data | authorised API or licensed dataset, deterministic normalisation |
| news or public document | event detection, browser retrieval and model-assisted extraction |
| scanned PDF | native extraction, then OCR if required, then structured extraction |

A large structured dataset MUST NOT create one model call per row when deterministic aggregation can identify material changes first.

## 4. Worker classes

The platform MAY use specialised workers:

- `SOURCE_SCHEDULER`;
- `CONNECTOR_WORKER`;
- `DOCUMENT_PARSER`;
- `OCR_WORKER`;
- `ENTITY_RESOLUTION_WORKER`;
- `EMBEDDING_WORKER`;
- `CHANGE_DETECTION_WORKER`;
- `RESEARCH_PLANNER`;
- `EVIDENCE_EXTRACTION_WORKER`;
- `CONTRADICTION_DISCOVERY_WORKER`;
- `CANDIDATE_CLAIM_WORKER`;
- `DOSSIER_WORKER`;
- `ADMISSION_HANDOFF_WORKER`.

Each worker MUST have a bounded tool set, input schema, output schema, model policy, retry policy, budget and kill switch.

## 5. Model routing

AXIGNAL MUST use a provider-independent model gateway.

Routing MAY include:

- local embeddings and classifiers;
- local language models for high-volume extraction;
- external low-cost models for routine research;
- higher-capability APIs for ambiguous, legal, multilingual or multistep cases;
- deterministic code for validation and admission.

The selected route MUST be based on:

- data sensitivity;
- task complexity;
- rights and jurisdiction;
- model quality evidence;
- latency;
- cost;
- availability;
- required context length;
- structured-output reliability.

Provider or local model changes MUST be versioned and evaluated against frozen fixtures.

## 6. Candidate Claim requirements

Every Candidate Claim MUST include:

- immutable candidate ID;
- subject, predicate and object or value;
- proposed claim type;
- proposed scope, geography and validity interval;
- Evidence Object references;
- source references and lineage groups;
- producer type and model identity;
- prompt or extraction-method version;
- extraction confidence;
- supporting and adverse evidence references;
- contradiction candidates;
- assumptions and unknowns;
- rights status inherited from source records;
- tenant scope;
- created time;
- lifecycle state;
- budget and ResearchRun references;
- deterministic gate results when evaluated.

A Candidate Claim MUST remain structurally distinct from an admitted canonical claim.

## 7. Candidate lifecycle

```text
PROPOSED
→ PARSED
→ EVIDENCE_BOUND
→ DUPLICATE_CHECKED
→ SOURCE_CHECKED
→ RIGHTS_CHECKED
→ STRUCTURALLY_VALIDATED
→ TEMPORALLY_VALIDATED
→ QUANTITATIVELY_VALIDATED
→ EPISTEMICALLY_REVIEWED
→ ADMISSION_QUEUED
```

Terminal or exceptional states:

- `DUPLICATE`;
- `INSUFFICIENT_EVIDENCE`;
- `RIGHTS_BLOCKED`;
- `SOURCE_BLOCKED`;
- `CONTESTED`;
- `QUARANTINED`;
- `REJECTED`;
- `EXPIRED`;
- `MODEL_FAILURE`;
- `BUDGET_EXHAUSTED`.

Only the canonical admission runtime may create or version a Claim Ledger record.

## 8. Evidence production

Model output alone is not evidence. An Evidence Object MUST point to an addressable source object, dataset slice, filing, page, document section, API response or reproducible calculation.

Every Evidence Object created by the worker MUST record:

- source and source-admission state;
- raw-object reference or reproducible request identity;
- retrieval, publication, observation and event time where available;
- hash;
- language;
- extract boundaries;
- parser, OCR and model versions;
- transformation lineage;
- extraction confidence;
- rights classification;
- retention rule;
- tenant scope.

## 9. Contradiction search

Workers MUST actively seek adverse evidence rather than only confirming the research question.

Contradiction discovery SHOULD include:

- direct semantic opposition;
- temporal conflict;
- scope mismatch;
- methodological disagreement;
- value disagreement;
- source correction;
- scenario incompatibility;
- missing denominator or unit conflict;
- source-lineage duplication.

A contradiction candidate MUST preserve both sides and MUST NOT automatically cancel either claim.

## 10. Idempotency and deduplication

Every source fetch, raw object, Evidence Object and Candidate Claim MUST have stable identities or idempotency keys.

The pipeline MUST detect:

- duplicate documents;
- mirrors and syndication;
- repeated API pages;
- equivalent multilingual assertions;
- previously rejected candidate claims;
- claims superseded by newer evidence;
- repeated model output from the same evidence.

Retries MUST not create duplicate canonical artifacts.

## 11. Scheduling and 24/7 operation

Continuous operation MAY be driven by:

- source publication cadence;
- checkpoint and cursor state;
- stale-claim refresh schedules;
- saved monitoring requests;
- material source changes;
- contradiction pressure;
- coverage gaps;
- Research Candidate Queue priority;
- Knowledge Tides after privacy gates.

Scheduling MUST respect source rate limits, cost budgets, maintenance windows and kill switches.

## 12. Budget control

Every job and ResearchRun MUST record estimated and actual:

- source/API charges;
- browser searches;
- input, cached-input and output tokens;
- local CPU/GPU time;
- OCR pages;
- storage and network;
- retries;
- human review;
- legal or rights review.

The worker MUST support:

- per-job limits;
- per-source daily limits;
- per-tenant limits;
- model-routing limits;
- concurrency limits;
- circuit breakers;
- explicit escalation approval;
- graceful degradation to deterministic processing or queueing.

## 13. Local execution security

A local worker MUST run under a dedicated identity with:

- no deployment credentials;
- no unrestricted database superuser role;
- append-only or queue-only proposal permissions;
- source credentials limited to admitted connectors;
- network egress allow-lists where feasible;
- encrypted secrets;
- bounded filesystem access;
- sandboxed document parsing;
- resource limits;
- auditable model and tool versions.

Compromise of a worker MUST not permit canonical admission or cross-tenant access.

## 14. Prompt-injection resistance

Source documents, web pages and retrieved text are untrusted data.

Workers MUST:

- separate instructions from source content;
- use typed tool calls;
- ignore source requests to reveal secrets, change tools or contact third parties;
- prevent retrieved text from modifying Goal Lock, source policy, budgets or admission rules;
- never execute embedded code or macros;
- quarantine suspicious documents;
- record injection detections.

## 15. Human and model escalation

Escalation MAY occur when:

- entity resolution is ambiguous;
- legal or regulatory interpretation is material;
- source rights are unclear;
- evidence conflicts materially;
- the claim is causal, predictive or high impact;
- extraction confidence is below policy;
- a model disagrees with deterministic calculations;
- publication would create substantial user or regulatory risk.

Escalation MUST preserve the original worker output and decision history.

## 16. Admission handoff

The handoff package MUST contain:

- Candidate Claim;
- all Evidence Object references;
- source and rights records;
- model and method metadata;
- independent-source grouping;
- contradiction set;
- unknown set;
- deterministic validation results;
- ResearchRun and cost references;
- human-review state.

The admission runtime MUST independently validate the package. Trust in the producing model or worker MUST NOT replace a gate.

## 17. Observability

Required metrics:

- source fetch success and latency;
- raw objects processed;
- parse and OCR failure rates;
- model calls, tokens and cost;
- local compute utilisation;
- candidate claims per source and model;
- duplicate rate;
- contradiction-discovery rate;
- evidence-to-candidate conversion;
- candidate-to-admitted conversion;
- rejection reason distribution;
- rights-block rate;
- source-lineage collapse rate;
- queue age;
- retries and dead letters;
- worker compromise or injection detections.

## 18. Failure and recovery

The system MUST support:

- checkpointed source cursors;
- replay from immutable raw objects;
- dead-letter queues;
- per-source pause and kill switch;
- model-provider failover;
- deterministic retry classification;
- quarantine of partial outputs;
- worker revocation;
- rebuilding derived indexes from canonical records.

A failed worker MUST not partially mutate the Claim Ledger.

## 19. Acceptance criteria

The capability is accepted when:

1. structured APIs can be processed without unnecessary model calls;
2. a local or external model can create schema-valid Candidate Claims;
3. no worker credential can admit a canonical claim;
4. source and rights failures stop the pipeline;
5. every Candidate Claim is traceable to Evidence Objects and raw references;
6. duplicate retries remain idempotent;
7. adverse evidence and unknowns are represented;
8. prompt-injection fixtures cannot change tools, budgets, tenant scope or admission state;
9. local and external model routes produce auditable method metadata;
10. budgets, costs and queue state are observable;
11. admission independently revalidates every handoff;
12. disabling a worker or source leaves canonical state consistent.
