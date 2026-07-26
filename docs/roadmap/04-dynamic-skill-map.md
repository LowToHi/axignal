# 04 — AXIGNAL Dynamic Skill Map

Version: `0.3.1`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

Dynamic skills are bounded capability contracts loaded by the development agent according to the active task. They reduce goal loss by ensuring each task receives the specialist rules, evidence requirements and prohibited shortcuts it needs.

A skill is not an autonomous product authority. It operates under the Goal Lock, `AGENTS.md`, contract `18` and the task specification.

## 2. Skill lifecycle

```text
DISCOVERED
→ PROPOSED
→ CONTRACTED
→ TESTED
→ ACTIVE
→ MONITORED
→ REVISED | DEPRECATED | REVOKED
```

No skill may be activated before its contract and tests exist.

## 3. Skill activation algorithm

For every task, the orchestrator MUST:

1. read `goal_id` and phase;
2. load the Goal Lock;
3. resolve governing contracts;
4. load mandatory skills from `skills/registry.yaml`;
5. add conditional skills triggered by data, privacy, security, language, UI or financial scope;
6. resolve conflicts by contract precedence;
7. record activated skill versions in task evidence;
8. refuse execution if a required skill is unavailable or revoked.

## 4. Always-on governance skills

| Skill | Responsibility |
|---|---|
| `goal-keeper` | Detect goal drift and anti-goal violations |
| `contract-router` | Resolve applicable contracts and precedence |
| `task-orchestrator` | Validate task completeness and dependencies |
| `gate-evaluator` | Evaluate evidence and authorise transitions |
| `naming-guardian` | Enforce AXIGNAL, axignal.com and canonical identifiers |
| `security-reviewer` | Detect security impact and required controls |
| `privacy-reviewer` | Detect personal-data, profiling and retention impact |
| `observability-engineer` | Require metrics, logs, traces and alerts |

These skills MUST run for every material task.

## 5. Product and epistemic skills

| Skill | Trigger | Output |
|---|---|---|
| `epistemic-admission` | claim, evidence, opportunity, scenario or outcome work | admission rules, tests and state-transition evidence |
| `source-admission` | new source, connector, licence or export | source rights record and admission decision |
| `evidence-provenance-engineer` | evidence extraction or transformation | lineage, hashes, method versions and replay path |
| `entity-resolution-engineer` | aliases, entity merge or identifiers | reversible resolution evidence |
| `opportunity-modeler` | opportunity assembly or maturity | typed subgraph and invalidation conditions |
| `scenario-calibration-engineer` | forecasts or probabilities | baseline, holdout, calibration and demotion rules |
| `data-quality-auditor` | ingestion or derived metrics | quality profile, threshold and quarantine behaviour |

## 6. Experience skills

| Skill | Trigger | Output |
|---|---|---|
| `ux-researcher` | workflow, onboarding or validation work | evidence-backed findings and test plan |
| `interaction-architect` | navigation, context or direct manipulation | interaction state model and recovery rules |
| `visualisation-designer` | charts, maps, graph or timeline | semantic encodings and perceptual QA |
| `globe-engineer` | geographic surfaces | layer, tile, projection and semantic zoom contract |
| `graph-engineer` | relational surfaces | typed graph, bounded traversal and layout contract |
| `timeline-engineer` | historical state | as-of reconstruction and temporal integrity |
| `lens-router-engineer` | AUTO, Globe, Graph or Dual selection | deterministic routing and explanation rules |
| `conversational-navigator` | chat commands or explanations | typed intent plan and grounded response |
| `accessibility-auditor` | any user-facing surface | WCAG evidence and non-visual equivalent |
| `consent-ux-reviewer` | permission, memory or data-use controls | explicit, reversible consent/authority UX |

## 7. Multilingual skills

| Skill | Trigger | Output |
|---|---|---|
| `multilingual-localiser` | text, search, command or evidence rendering | locale, terminology, translation provenance and parity tests |
| `ontology-engineer` | predicates, universes or multilingual concepts | canonical vocabulary and mappings |
| `search-engineer` | lexical, semantic or entity search | ranking contract, language parity and match explanation |

## 8. Intent Intelligence skills

| Skill | Trigger | Output |
|---|---|---|
| `intent-intelligence-designer` | prototype or UX of user-interest features | transparent user and aggregate interaction design |
| `intent-intelligence-engineer` | intent events, preferences or tides | typed pipeline and separation from economic truth |
| `analytics-engineer` | cohort, trend or conversion metrics | denominator, uniqueness and time-window definitions |
| `fraud-risk-engineer` | collective behaviour or rankings | coordination, manipulation and abuse controls |
| `research-queue-orchestrator` | coverage gaps and candidate studies | prioritisation, lifecycle and evidence routing |

## 9. Platform and operations skills

| Skill | Trigger | Output |
|---|---|---|
| `repository-architect` | monorepo, packages or CI | reproducible structure and boundaries |
| `backend-architect` | API, jobs or services | typed service and failure contracts |
| `frontend-architect` | application state and UI implementation | state, rendering and entitlement boundaries |
| `data-architect` | databases, migrations or retention | canonical schemas and migration plans |
| `connector-engineer` | source integration | idempotent connector and kill switch |
| `api-engineer` | public or enterprise API | OpenAPI, auth, quotas and compatibility |
| `identity-engineer` | users, roles or SSO | tenant-safe identity and access model |
| `billing-engineer` | pricing and Stripe | idempotent billing and entitlement evidence |
| `performance-engineer` | latency or rendering budgets | measured performance and degradation plan |
| `test-engineer` | any implementation | automated evidence and failure cases |
| `operations-engineer` | deployment or incidents | runbooks, rollback, recovery and ownership |
| `operations-writer` | operating documentation | executable runbooks and verification |

## 10. Commercial and validation skills

| Skill | Trigger | Output |
|---|---|---|
| `hypothesis-curator` | buyer, pricing, wedge or defence claims | falsifiable hypothesis and evidence state |
| `product-analyst` | usage, retention or decision impact | validated metric interpretation |
| `finance-operator` | costs, margin or revenue | unit economics and budget control |
| `universe-selector` | new opportunity universe | rights/value/cost/regulation scorecard |
| `design-partner-operator` | paid validation | recruitment, evidence and feedback loop |
| `growth-analyst` | acquisition channels | attribution, payback and repeatability evidence |
| `regulatory-scope-reviewer` | financial, crypto or jurisdiction expansion | scope decision and blocked capabilities |
| `legal-doc-coordinator` | customer terms or notices | legal-review checklist and publication package |

## 11. Skill creation contract

A new skill MUST define:

- stable ID;
- version;
- purpose;
- trigger conditions;
- required inputs;
- governing contracts;
- allowed outputs;
- prohibited actions;
- tests;
- telemetry;
- owner;
- deactivation and rollback;
- conflict rules.

It MUST be registered in `skills/registry.yaml` and validate against `schemas/skill.schema.json`.

## 12. Dynamic adaptation

Skills MAY evolve from observed failure, but they MUST NOT self-modify silently.

A revision requires:

1. recorded failure or improvement hypothesis;
2. updated skill contract;
3. version increment;
4. regression tests;
5. evidence comparison;
6. gate approval;
7. preserved prior version.

## 13. Prohibited skill behaviour

A skill MUST NOT:

- override the Goal Lock;
- treat generated text as accepted evidence;
- broaden source rights;
- create tasks outside the roadmap without registering them;
- mark its own work accepted;
- hide uncertainty or test failures;
- access unrelated tenant data;
- introduce a new provider or architecture silently;
- rename AXIGNAL or the domain;
- optimise engagement at the expense of epistemic integrity.

## 14. Skill evidence ledger

Each task run MUST record:

- skill IDs and versions;
- activation reason;
- inputs and relevant hashes;
- outputs;
- warnings and conflicts;
- tests run;
- disposition;
- reviewer or gate decision.

## 15. Skill gate

The dynamic skill system is accepted when:

- every task resolves mandatory skills deterministically;
- missing required skills fail closed;
- conflicting skills resolve by contract precedence;
- skill versions are visible in PR evidence;
- revoked skills cannot run;
- regression tests demonstrate that a specialist skill prevents at least one known failure mode.
