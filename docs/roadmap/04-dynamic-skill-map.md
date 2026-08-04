# 04 — AXIGNAL Dynamic Skill Map

Version: `0.5.0`
Status: `NORMATIVE CANDIDATE / CONTRACT 31 ALIGNMENT`
Goal ID: `AXIGNAL-GOAL-001`
Governing programme: `Contract 31 / ADR-016`

## 1. Purpose

Dynamic skills are bounded capability contracts loaded according to the active task. They ensure each task receives specialist rules, evidence requirements and prohibited shortcuts.

A skill is not autonomous product authority. It operates under the Goal Lock, `AGENTS.md`, Contract 18, Contract 31 and the typed task.

## 2. State boundary

Skills must distinguish:

```text
engineering output
≠ canonical acceptance
≠ product admission
≠ public launch
```

No skill may approve its own work, widen its task, admit a source, grant authority or return a P27 launch disposition.

## 3. Skill lifecycle

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

## 4. Activation algorithm

For every material task, the orchestrator must:

1. read `goal_id`, phase and engineering/canonical state;
2. load Goal Lock, AGENTS, Contract 18 and Contract 31;
3. resolve applicable capability contracts and ADRs;
4. load mandatory skills from the registries;
5. add conditional skills triggered by sources, privacy, security, identity, billing, SEO, MCP, language, UI, research or operational scope;
6. resolve conflicts by contract precedence;
7. record skill versions and evidence;
8. refuse execution when a required skill is unavailable or revoked.

## 5. Always-on governance skills

| Skill | Responsibility |
|---|---|
| `goal-keeper` | Detect goal drift and anti-goal violations |
| `contract-router` | Resolve contracts, supersession and precedence |
| `task-orchestrator` | Validate scope, dependencies and dual state |
| `gate-evaluator` | Evaluate evidence without self-acceptance |
| `naming-guardian` | Enforce AXIGNAL identifiers |
| `security-reviewer` | Require security controls and threat review |
| `privacy-reviewer` | Require personal-data, consent and retention controls |
| `observability-engineer` | Require metrics, logs, traces and alerts |

## 6. Product and epistemic skills

| Skill | Trigger | Required output |
|---|---|---|
| `epistemic-admission` | claims, evidence, opportunity, scenario or outcome | admission rules, state transitions and tests |
| `source-admission` | source, connector, licence or export | rights record, admission state and kill switch |
| `evidence-provenance-engineer` | evidence transformation | lineage, hashes, method and replay |
| `entity-resolution-engineer` | aliases, merge or identifiers | reversible resolution evidence |
| `opportunity-modeler` | Opportunity or Pursuit assembly | typed state and invalidation conditions |
| `scenario-calibration-engineer` | forecast or probability | baseline, holdout, calibration and demotion |
| `data-quality-auditor` | ingestion or derived metrics | quality profile and quarantine |
| `opportunity-operations-engineer` | workspace, task, approval or outcome | tenant-scoped operating model and audit |

## 7. Research and AI skills

| Skill | Trigger | Required output |
|---|---|---|
| `research-run-orchestrator` | ResearchRun or dossier | plan, lifecycle, budget and cancellation |
| `retrieval-policy-engineer` | lexical, vector, graph, API or browser retrieval | bounded retrieval and source precedence |
| `authorised-browser-researcher` | external web or documents | provenance, injection controls and stopping evidence |
| `tenant-memory-engineer` | private data or memory | RLS, purpose and deletion propagation |
| `local-model-operator` | local model or routing | sandbox, evaluation, resources and kill switch |
| `candidate-claim-pipeline-engineer` | extraction or Claim proposal | schema, lineage and no-canonical-write proof |
| `research-queue-orchestrator` | research gaps | prioritisation and evidence routing |
| `prompt-injection-reviewer` | documents, web, connectors or MCP output | isolation, tool and output-validation controls |

## 8. Identity, trial and abuse skills

| Skill | Trigger | Required output |
|---|---|---|
| `identity-engineer` | identity, roles, sessions, SSO or SCIM | server-authoritative identity model |
| `webauthn-engineer` | passkeys or recovery | RP/origin, challenge, credential and recovery evidence |
| `session-security-engineer` | cookies, sessions or assertions | revocation, rotation and timeout controls |
| `trial-governance-engineer` | free trial or onboarding | tenant-level grant, delayed clock and budgets |
| `fraud-risk-engineer` | abuse or multi-account risk | strong/weak signals, step-up and false-positive controls |
| `seat-governance-engineer` | membership, invitation or capacity | transactional allocation, role and downgrade evidence |
| `consent-ux-reviewer` | verification, consent or step-up | explicit, reversible and low-friction UX |

Mandatory P25 combination:

```text
identity-engineer
+ webauthn-engineer
+ session-security-engineer
+ trial-governance-engineer
+ fraud-risk-engineer
+ seat-governance-engineer
+ security-reviewer
+ privacy-reviewer
+ test-engineer
```

## 9. Experience and accessibility skills

| Skill | Trigger | Required output |
|---|---|---|
| `ux-researcher` | workflow or validation | evidence-backed findings |
| `interaction-architect` | navigation or direct manipulation | state and recovery model |
| `visualisation-designer` | chart, map, graph or timeline | semantic encodings and QA |
| `axignal-gsap-ui-ux` | GSAP, motion, animation or cinematic interaction | semantic choreography, implementation, reduced-motion fallback and validation evidence |
| `axignal-cinematic-webgl-scroll` | Globe texture, Canvas, GPU, LOD or sharpness work | capability tiers, regional blending, rights, fallback and measurable R3F quality gates |
| `globe-engineer` | geographic surfaces | projection, layer and semantic zoom contract |
| `graph-engineer` | relational surfaces | typed traversal and layout |
| `timeline-engineer` | historical state | as-of and revision integrity |
| `lens-router-engineer` | AUTO, Globe, Graph or Dual | routing and explanation |
| `conversational-navigator` | commands or explanations | typed intent and grounded response |
| `accessibility-auditor` | user-facing surface | WCAG and non-visual evidence |
| `consent-ux-reviewer` | permissions or communication | consent and authority UX |

## 10. Multilingual skills

| Skill | Trigger | Required output |
|---|---|---|
| `multilingual-localiser` | text, search or evidence rendering | locale, terminology and parity tests |
| `ontology-engineer` | predicates, libraries or concepts | canonical vocabulary and mappings |
| `search-engineer` | lexical, semantic or entity search | ranking, language parity and explanation |

## 11. Organic discovery and growth skills

| Skill | Trigger | Required output |
|---|---|---|
| `programmatic-seo-engineer` | generated public page or sitemap | IndexabilityGate, URL and lifecycle contract |
| `content-quality-gate` | indexability or publication | uniqueness, depth, source and freshness evidence |
| `structured-data-engineer` | JSON-LD or semantic publication | visible-content parity and validation |
| `crawler-policy-engineer` | robots, sitemap or agent access | crawler-specific allow/deny policy |
| `search-console-operator` | GSC property or analytics | official API, least privilege and read-only evidence |
| `ai-citation-analyst` | answer-engine citation | observation ledger and attribution limits |
| `tender-alert-operator` | alert capture and delivery | double opt-in, compensation and unsubscribe |
| `crm-governance-engineer` | contacts, lead score or lifecycle | CRM/identity/entitlement separation |
| `growth-analyst` | acquisition and attribution | funnel, payback and causal limitations |

Mandatory P26-T01 combination:

```text
programmatic-seo-engineer
+ content-quality-gate
+ structured-data-engineer
+ crawler-policy-engineer
+ tender-alert-operator
+ crm-governance-engineer
+ ai-citation-analyst
+ consent-ux-reviewer
+ accessibility-auditor
```

## 12. MCP and connector skills

| Skill | Trigger | Required output |
|---|---|---|
| `connector-engineer` | external API or data integration | idempotence, rights and kill switch |
| `mcp-security-reviewer` | MCP server or tool | exact implementation, scopes and threat review |
| `tool-permission-engineer` | tool allowlist or destructive action | deny-by-default permission matrix |
| `supply-chain-security-reviewer` | package, release or dependency | provenance, vulnerabilities and release identity |
| `secret-boundary-reviewer` | OAuth, service account or API credential | reference-only secret flow |
| `egress-policy-engineer` | connector network access | destination and method allowlist |

MCP activation requires all six skills plus `source-admission`, `security-reviewer`, `privacy-reviewer` and `test-engineer`.

Catalogue presence must never trigger installation.

## 13. Platform and Founder Operations skills

| Skill | Trigger | Required output |
|---|---|---|
| `repository-architect` | monorepo or CI | reproducible structure |
| `backend-architect` | API, jobs or services | typed failure contracts |
| `frontend-architect` | UI and state | rendering and authority boundaries |
| `data-architect` | schema, migration or retention | canonical schemas and migration plan |
| `api-engineer` | API or webhook | OpenAPI, auth, quotas and compatibility |
| `billing-engineer` | Stripe or entitlements | provider reconciliation and ledger evidence |
| `performance-engineer` | latency or rendering | measured budget and degradation plan |
| `test-engineer` | implementation | automated and adversarial evidence |
| `operations-engineer` | deployment or incidents | runbooks, rollback and recovery |
| `operations-writer` | operational documentation | executable runbooks |
| `founder-control-plane-engineer` | `/admin` or global mutations | founder authority and typed operations |
| `incident-commander` | incident workflows | severity, ownership and append-only timeline |
| `disaster-recovery-engineer` | backup or restore | isolated restore, RPO and RTO evidence |
| `feature-flag-governor` | flags or kill switches | server-side state and audit |
| `audit-ledger-engineer` | privileged events | immutable, scoped audit evidence |

## 14. Commercial and validation skills

| Skill | Trigger | Required output |
|---|---|---|
| `hypothesis-curator` | buyer, pricing or wedge | falsifiable hypothesis and state |
| `product-analyst` | usage, retention or outcomes | validated interpretation |
| `finance-operator` | cost, margin or revenue | unit economics and budget control |
| `universe-selector` | new opportunity universe | rights, value and cost scorecard |
| `design-partner-operator` | private paid acceptance | recruitment and evidence loop |
| `regulatory-scope-reviewer` | legal or regulated expansion | scope and blocked capabilities |
| `legal-doc-coordinator` | customer terms or notices | review checklist and package |
| `launch-manifest-auditor` | P27 | exact-head evidence and approval digest |

## 15. Task-specific mandatory combinations

### P26-T02

```text
founder-control-plane-engineer
+ billing-engineer
+ identity-engineer
+ seat-governance-engineer
+ finance-operator
+ audit-ledger-engineer
+ security-reviewer
```

### P26-T03

```text
fraud-risk-engineer
+ source-admission
+ connector-engineer
+ mcp-security-reviewer
+ tool-permission-engineer
+ supply-chain-security-reviewer
+ secret-boundary-reviewer
+ egress-policy-engineer
```

### P26-T04

```text
founder-control-plane-engineer
+ operations-engineer
+ incident-commander
+ disaster-recovery-engineer
+ feature-flag-governor
+ audit-ledger-engineer
+ secret-boundary-reviewer
```

### P27

```text
launch-manifest-auditor
+ gate-evaluator
+ security-reviewer
+ privacy-reviewer
+ accessibility-auditor
+ finance-operator
+ legal-doc-coordinator
+ disaster-recovery-engineer
+ data-quality-auditor
+ product-analyst
```

## 16. Skill creation contract

A new skill must define:

- stable ID and version;
- purpose and triggers;
- inputs;
- governing contracts;
- allowed outputs;
- prohibited actions;
- tests;
- telemetry;
- owner;
- deactivation and rollback;
- conflict rules.

It must be registered and validated before use.

## 17. Prohibited skill behaviour

A skill must not:

- override Goal Lock or Contract 31;
- treat generated text or tool output as accepted evidence;
- broaden source rights;
- create unregistered tasks;
- mark its own work accepted;
- hide uncertainty or failures;
- access unrelated tenant data;
- add a provider, connector or MCP silently;
- widen tool permissions;
- treat DNS verification as API access;
- treat Search Console metrics as publication authority;
- treat a sidebar as durable administration;
- authorise public launch;
- rename AXIGNAL or axignal.com.

## 18. Skill evidence ledger

Each task run records:

- task, engineering state and canonical state;
- skill IDs and versions;
- activation reason;
- inputs and hashes;
- outputs;
- warnings and conflicts;
- tests;
- disposition;
- reviewer or gate decision.

## 19. Skill gate

The system is accepted when:

- every task resolves mandatory skills deterministically;
- missing skills fail closed;
- revoked skills cannot execute;
- skill output cannot grant product authority;
- P25, P26 and P27 combinations are enforced;
- MCP and Search Console operations require the declared security skills;
- evidence remains reproducible and auditable.
