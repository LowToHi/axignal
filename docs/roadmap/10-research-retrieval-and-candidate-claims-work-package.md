# 10 — AXIGNAL Research, Retrieval and Candidate Claims Work Package

Version: `0.1.0`
Status: `AUTHORISED CONTRACTUAL DESIGN / IMPLEMENTATION GATED`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Objective

Implement the governed product flow:

```text
user requests investigation of an opportunity
→ Navigator creates ResearchRun
→ official API and authorised Browser retrieval
→ Evidence Objects
→ Candidate Claims
→ contradictions and unknowns
→ traceable dossier
→ admission queue
→ InvestigationContext update
```

This work package extends AXIGNAL's command-oriented Navigator into a research interface without changing the authority model: sources provide evidence, models propose and the deterministic runtime admits.

## 2. Governing contracts and decisions

- Goal Lock `AXIGNAL-GOAL-001`;
- contracts `02`, `03`, `04`, `06–10`, `12`, `14–19`, `25–27`;
- ADR-009;
- ADR-010.

## 3. Activated skills

Always-on:

- `goal-keeper`;
- `contract-router`;
- `task-orchestrator`;
- `gate-evaluator`;
- `naming-guardian`;
- `security-reviewer`;
- `privacy-reviewer`;
- `observability-engineer`.

Specialist:

- `research-run-orchestrator`;
- `retrieval-policy-engineer`;
- `authorised-browser-researcher`;
- `tenant-memory-engineer`;
- `local-model-operator`;
- `candidate-claim-pipeline-engineer`;
- `conversational-navigator`;
- `source-admission`;
- `evidence-provenance-engineer`;
- `epistemic-admission`;
- `data-architect`;
- `backend-architect`;
- `frontend-architect`;
- `test-engineer`;
- `finance-operator`.

## 4. Tasks

### `AX-F0-T08` — Freeze research and retrieval authority boundaries

Outcome:

- Contracts 25–27 and ADR-009–010 indexed and validated;
- schemas for ResearchRun, Candidate Claim and Tenant Knowledge Item validated;
- roadmap, registry and CI propagation complete.

Acceptance:

- contract validation passes;
- no model route receives canonical claim-write authority;
- no cross-domain vector query is permitted by specification.

### `AX-F2-T14` — Scaffold research service boundaries

Outcome:

- bounded service/package interfaces for ResearchRun orchestration, retrieval, worker queues and admission handoff;
- correlation IDs and cost ledger interface;
- no production sources or model provider required.

Dependencies:

- `AX-F0-T08`;
- `AX-F2-T04`;
- `AX-F2-T07`.

Acceptance:

- strict types and schemas;
- no service imports canonical-write credentials into research workers;
- clean-clone CI passes.

### `AX-F3-T13` — Implement Candidate Claim quarantine boundary

Outcome:

- Candidate Claim storage and lifecycle distinct from Claim Ledger;
- Evidence Object references required;
- deterministic gate-result records;
- immutable proposal history.

Dependencies:

- `AX-F3-T02`;
- `AX-F3-T04`;
- `AX-F3-T09`;
- `AX-F2-T14`.

Acceptance:

- direct model-to-Claim-Ledger tests fail closed;
- retries are idempotent;
- rejected proposals remain auditable.

### `AX-F4-T11` — Implement ResearchRun state machine

Outcome:

- create, read, cancel and inspect a ResearchRun;
- visible plan, source classes, budgets, stopping rule and status;
- typed progress events;
- no external retrieval in the first fixture.

Dependencies:

- `AX-F4-T04`;
- `AX-F4-T05`;
- `AX-F2-T14`.

Acceptance:

- every transition is evented;
- cancellation is idempotent;
- budget exhaustion is explicit;
- state persists in InvestigationContext.

### `AX-F4-T12` — Implement governed hybrid retrieval

Outcome:

- retrieval from synthetic `axignal_global`, `tenant_private` and external-authorised fixtures;
- structured, lexical, vector and graph result interfaces;
- source precedence and domain labels;
- no unrestricted corpus mixing.

Dependencies:

- `AX-F4-T11`;
- `AX-F6-T05`;
- ADR-009.

Acceptance:

- tenant isolation tests;
- domain and tenant scope mandatory;
- vector similarity never changes admission state;
- official API fixture outranks Browser secondary source where both exist.

### `AX-F4-T13` — Implement authorised Browser fixture

Outcome:

- Browser adapter over a frozen local fixture set;
- URL, retrieval time, hash, language, parser and rights metadata;
- prompt-injection and malicious-document tests;
- network disabled in the initial acceptance fixture.

Dependencies:

- `AX-F4-T12`;
- source-admission test fixtures.

Acceptance:

- retrieved instructions cannot alter tools, permissions, budgets or Goal Lock;
- unsupported rights state blocks Evidence Object creation;
- primary-source preference is reproducible.

### `AX-F4-T14` — Produce traceable Evidence, Candidate Claims and dossier

Outcome:

- source material becomes Evidence Objects;
- model or deterministic parser produces Candidate Claims;
- supporting, adverse and unknown sets are visible;
- dossier links every statement to evidence or provisional status.

Dependencies:

- `AX-F3-T13`;
- `AX-F4-T12`;
- `AX-F4-T13`.

Acceptance:

- no unsupported assertion in dossier;
- adverse evidence actively retrieved;
- Candidate Claims remain visually and structurally provisional;
- negative result is accepted as valid output.

### `AX-F4-T15` — Synchronise ResearchRun with InvestigationContext

Outcome:

- Navigator shows plan and progress;
- Globe, Graph, Timeline and Rail preserve context;
- selected run, provisional evidence, Candidate Claims and dossier are addressable;
- completion queues admission without claiming admission success.

Dependencies:

- `AX-F4-T11`;
- `AX-F4-T14`.

Acceptance:

- reload preserves research state;
- lens changes preserve active run;
- failures preserve prior canonical context;
- provisional and canonical claims cannot be visually confused.

### `AX-F7-T13` — Implement tenant-private knowledge controls

Outcome:

- tenant schema and Row-Level Security;
- purpose permissions;
- private retrieval;
- memory inspection, correction and deletion;
- embedding deletion propagation.

Dependencies:

- identity test principal;
- ADR-009;
- contract 26.

Acceptance:

- cross-tenant retrieval always denied;
- deletion removes search and vector availability;
- private material never reaches global Claim Ledger by default.

### `AX-F8-T11` — Implement source-first continuous Research Worker

Outcome:

- scheduled official-API fixture;
- deterministic change detection before model use;
- model-assisted extraction only for unstructured fixture;
- cost, token and compute ledger;
- kill switch and replay.

Dependencies:

- `AX-F3-T13`;
- `AX-F4-T14`;
- ADR-010.

Acceptance:

- structured rows are not sent individually to a model;
- worker can only write proposal/quarantine state;
- source or rights kill switch stops downstream proposals;
- raw fixture replay reproduces Candidate Claims.

### `AX-F8-T12` — Prove admission handoff independence

Outcome:

- Candidate Claim handoff package;
- deterministic admission runtime revalidates every field;
- model identity and quality do not waive gates.

Dependencies:

- `AX-F8-T11`;
- epistemic kernel gates.

Acceptance:

- malicious or high-confidence unsupported proposal is rejected;
- valid proposal passes only after independent gates;
- private scope cannot be promoted accidentally.

## 5. First vertical slice

The first implementation slice is deliberately synthetic and bounded:

```text
selected Moscow real-estate opportunity
→ user asks for regulatory and socioeconomic investigation
→ ResearchRun plan displayed
→ one frozen official-API fixture
→ one frozen authorised-Browser document fixture
→ one tenant-private note fixture with explicit permission
→ Evidence Objects
→ one supporting Candidate Claim
→ one contradiction Candidate Claim
→ one explicit unknown
→ dossier
→ admission queued
→ InvestigationContext updated
```

No real web browsing, customer data, source licence dependency or canonical admission is required to prove the architecture.

## 6. Explicit exclusions

- unrestricted live web crawling;
- scraping property portals without rights;
- a second physical vector database;
- model training on tenant content;
- automatic global contribution of private data;
- personalised investment recommendation;
- direct model writes to Claim Ledger;
- autonomous spending beyond run budgets;
- production 24/7 worker before fixture replay and kill-switch gates pass.

## 7. Observability

Every task MUST expose:

- correlation and ResearchRun IDs;
- state-transition count and latency;
- source and rights disposition;
- retrieval counts by domain;
- model route, tokens and cost;
- Evidence and Candidate Claim counts;
- contradiction and unknown counts;
- rejection reasons;
- queue age;
- cancellation and budget-exhaustion behaviour;
- tenant-boundary denials.

## 8. Rollback

- disable Research Mode behind a feature flag;
- retain command-mode Navigator and persistent InvestigationContext;
- cancel queued fixture runs;
- quarantine proposal artifacts;
- remove derived fixture indexes;
- leave canonical claims unchanged;
- rerun Contract Validation and Executable Spine.

## 9. Work-package gate

The block passes only when:

1. contracts and schemas are valid;
2. specialist skills resolve deterministically;
3. the synthetic vertical slice passes API and browser tests;
4. models cannot admit claims;
5. private and global knowledge remain isolated;
6. Browser prompt injection fails closed;
7. costs and budgets are observable;
8. rollback preserves the existing product shell and canonical state.
