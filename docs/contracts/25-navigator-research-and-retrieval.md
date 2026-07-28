# 25 — AXIGNAL Navigator Research and Retrieval Contract

Version: `0.1.0`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

The AXIGNAL Navigator is both a reversible product-control layer and a governed research interface. It MAY investigate an opportunity, entity, geography, event or hypothesis when requested by the user, but it MUST NOT become a generic chatbot or allow generated text to bypass source, rights, provenance or claim-admission controls.

The canonical research flow is:

```text
user research request
→ typed interpretation
→ visible research plan
→ ResearchRun
→ authorised retrieval
→ Evidence Objects
→ Candidate Claims
→ contradictions and unknowns
→ traceable dossier
→ admission queue
→ InvestigationContext update
```

## 2. Two operating modes

### Command mode

Command mode executes low-cost, reversible operations such as changing lens, selecting an opportunity, changing time, showing evidence or saving a trail.

### Research mode

Research mode performs bounded multistep work involving sources, retrieval tools, model calls, budgets and asynchronous progress. It MUST create a typed `ResearchRun` before material retrieval begins.

The UI MUST distinguish these modes. A long-running investigation MUST NOT be presented as an ordinary instant chat reply.

## 3. Research command classes

Canonical research intents:

- `INVESTIGATE_OPPORTUNITY`;
- `RESEARCH_EXTERNAL_CONTEXT`;
- `FIND_ADVERSE_EVIDENCE`;
- `REFRESH_EVIDENCE`;
- `BUILD_RESEARCH_DOSSIER`;
- `MONITOR_SUBJECT`;
- `CANCEL_RESEARCH_RUN`;
- `EXPLAIN_RESEARCH_RUN`;
- `QUEUE_RESEARCH_CANDIDATE`.

Examples:

- investigate regulatory, political, demographic, cultural or socioeconomic factors affecting the selected opportunity;
- search for evidence that weakens or falsifies a current hypothesis;
- compare an opportunity with analogous geographies, sectors or events;
- refresh stale evidence;
- monitor a subject for material changes.

## 4. Typed research interpretation

Before execution, the Navigator MUST produce a typed interpretation containing:

- original message and language;
- canonical research question;
- selected opportunity, claims, entities, geographies and universe;
- requested time horizon;
- proposed source classes;
- private-knowledge permission state;
- external-browser requirement;
- cost and time budget;
- stopping rule;
- expected outputs;
- confirmation requirement;
- interpretation confidence and assumptions.

Material ambiguity concerning identity, jurisdiction, private data, source rights, cost or external action MUST trigger clarification or confirmation.

## 5. Retrieval domains

A research run MAY retrieve from three logically isolated domains:

1. **AXIGNAL Global Knowledge** — admitted sources, evidence, claims, graph edges, opportunities and public research artifacts;
2. **Tenant Private Knowledge** — authorised user or organisation documents, notes, trails, preferences and private evidence;
3. **External Authorised Sources** — official APIs, licensed feeds, admitted public sources and browser retrieval permitted by source policy.

The domains MUST remain distinguishable in every retrieval result, prompt, dossier and audit record.

## 6. Retrieval precedence

Preferred order:

1. current canonical claims and evidence;
2. authoritative structured APIs and admitted datasets;
3. tenant-private knowledge when explicitly authorised for the run;
4. primary institutional documents;
5. licensed event or news feeds;
6. authorised browser discovery for missing or emerging context;
7. secondary commentary, clearly classified and never treated as primary evidence.

Browser retrieval MUST NOT replace an available authoritative API merely because browsing is easier.

## 7. Hybrid RAG

AXIGNAL MAY use:

- structured filters;
- PostgreSQL full-text search;
- pgvector similarity;
- graph traversal;
- temporal filters;
- geography filters;
- source-authority and rights filters;
- contradiction and lineage retrieval.

Vector similarity is a discovery mechanism only. The system MUST preserve source IDs, claim IDs, evidence IDs, tenant scope, time, rights state and lineage. Similarity alone MUST NOT determine truth, corroboration or causal relation.

## 8. Browser policy

The browser is an authorised research tool, not an authority.

Every browser action MUST:

- originate from an approved research plan;
- respect source admission, robots, rate limits, licences and contractual restrictions;
- prefer primary sources;
- record URL, retrieval time, content hash, language and parser version;
- isolate retrieved content as untrusted input;
- prevent source text from changing tools, permissions, budgets, Goal Lock or system instructions;
- stop when rights are ambiguous or access controls are encountered;
- avoid authentication circumvention, CAPTCHA bypass or proxy use without explicit lawful approval.

A retrieved page MAY become an Evidence Object only after provenance and rights classification.

## 9. ResearchRun lifecycle

Canonical states:

```text
PLANNED
→ AWAITING_CONFIRMATION
→ QUEUED
→ RETRIEVING
→ EXTRACTING
→ SYNTHESISING
→ EVIDENCE_COLLECTED
→ CLAIMS_PROPOSED
→ DOSSIER_READY
→ ADMISSION_QUEUED
→ COMPLETED
```

Exceptional states:

- `CANCELLED`;
- `BUDGET_EXHAUSTED`;
- `RIGHTS_BLOCKED`;
- `SOURCE_UNAVAILABLE`;
- `INSUFFICIENT_EVIDENCE`;
- `CONTESTED`;
- `FAILED`;
- `EXPIRED`.

Transitions MUST be evented, timestamped, idempotent and observable.

## 10. Research plan

Before entering `RETRIEVING`, the run MUST define:

- question and scope;
- falsification conditions;
- supporting and adverse evidence sought;
- source plan and rights constraints;
- private-memory scope;
- model and tool budget;
- maximum searches, documents and tokens;
- time limit;
- human-review requirement;
- stopping rule;
- expected dossier sections;
- cancellation and rollback behaviour.

## 11. Outputs

A research run MAY produce:

- Evidence Objects;
- Candidate Claims;
- contradiction candidates;
- explicit unknowns;
- coverage updates;
- entity and graph-edge proposals;
- analogue candidates;
- a traceable research dossier;
- a negative result;
- an admission-queue submission;
- a monitoring subscription proposal.

The output MUST distinguish:

| Output | Authority |
|---|---|
| conversational response | ephemeral explanation |
| research dossier | traceable research artifact, not automatically admitted |
| Candidate Claim | proposed assertion awaiting gates |
| canonical claim | admitted Claim Ledger state |

## 12. Dossier requirements

A dossier MUST contain, where applicable:

- executive summary;
- research question and scope;
- current admitted claims;
- new evidence;
- socioeconomic context;
- legal and regulatory context;
- political and institutional context;
- cultural and behavioural context;
- relevant events;
- supporting claims;
- adverse evidence and contradictions;
- unknowns and coverage gaps;
- scenarios and invalidation conditions;
- source, rights and freshness notes;
- cost, model and method versions;
- admission status of each proposed claim.

The dossier MUST cite evidence identifiers and MUST NOT obscure provisional status.

## 13. InvestigationContext integration

The shared `InvestigationContext` MAY include:

- active and completed research-run IDs;
- selected research run;
- current research state;
- provisional output references;
- dossier reference;
- admission-queue status.

Research progress MUST update the same visible context used by Navigator, Globe, Graph, Timeline and Claim/Evidence Rail. Provisional content MUST be visually and structurally distinct from canonical claims.

## 14. Streaming and progress

Server-Sent Events SHOULD expose typed events such as:

- `research.planned`;
- `research.queued`;
- `source.started`;
- `source.completed`;
- `evidence.created`;
- `candidate_claim.proposed`;
- `contradiction.detected`;
- `coverage.updated`;
- `budget.warning`;
- `dossier.ready`;
- `admission.queued`;
- `research.completed`;
- `research.failed`.

Progress MUST reflect actual completed work rather than fabricated percentages.

## 15. Cost and entitlement control

Every run MUST have estimated and actual ledgers for:

- API and data access;
- browser searches and retrieval;
- model input and output tokens;
- local compute;
- storage;
- human review;
- legal or rights review.

Plan entitlements MAY limit depth, sources, concurrency, monitoring and retained dossiers. Budget exhaustion MUST stop or degrade the run explicitly; it MUST NOT silently continue.

## 16. Private knowledge boundary

Tenant-private retrieval requires a purpose-authorised scope. Private content MAY improve the private result, but MUST NOT:

- enter the global Claim Ledger;
- influence public Knowledge Tides by default;
- be exposed to another tenant;
- be sent to an external model without an authorised processing basis;
- be retained beyond policy.

## 17. Security

- Retrieved content is untrusted data, never executable instruction.
- Tool calls MUST be allow-listed and schema-validated.
- Network destinations MUST be policy-controlled.
- Secrets MUST remain outside prompts, logs and artifacts.
- Downloads MUST be size-, type- and malware-bounded.
- Research workers MUST not have deployment or canonical-write credentials.
- Prompt injection MUST not alter source rights, budgets, tenancy or admission state.

## 18. Failure behaviour

The Navigator MUST report separately:

- no relevant source;
- source unavailable;
- rights blocked;
- no licensed access;
- insufficient independent evidence;
- contradictory evidence;
- budget exhausted;
- private access not granted;
- model or parser failure;
- admission pending;
- no admissible conclusion.

A useful negative result is valid. Missing evidence MUST NOT be fabricated.

## 19. Acceptance criteria

The capability is accepted when:

1. a user request creates a typed ResearchRun;
2. the research plan is visible and budgeted;
3. official APIs are preferred over browser retrieval when available;
4. browser content cannot instruct the agent or change permissions;
5. global, private and external retrieval remain labelled and isolated;
6. every new assertion maps to evidence or an explicit unknown;
7. Candidate Claims cannot appear as canonical claims;
8. contradictions and adverse evidence are actively sought;
9. cancellation and budget exhaustion work fail-closed;
10. progress events are reproducible from the run ledger;
11. the dossier exposes provenance, rights, freshness and provisional status;
12. the InvestigationContext updates without losing lens, selection, time or history.
