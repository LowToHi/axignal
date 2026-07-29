# 02 — AXIGNAL Task Catalogue

Version: `0.5.0`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

Every task MUST be instantiated from `schemas/task.schema.json` and MUST reference the Goal ID, phase, contracts, activated skills, dependencies, evidence, observability and rollback.

## Task ID format

```text
AX-F<phase>-T<number>
```

## Mandatory task fields

- stable task ID;
- `goal_id: AXIGNAL-GOAL-001`;
- phase;
- objective and measurable outcome;
- affected contracts;
- activated skills;
- dependencies;
- allowed modules;
- explicit exclusions;
- acceptance evidence;
- observability;
- security, privacy and rights impact;
- rollback or kill switch;
- Goal Lock answers.

A discovered task that changes scope MUST be registered before execution.

---

## F0 — Goal and contracts

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F0-T01` | Maintain the Goal Lock and anti-goals | Goal Lock, 00, 18 | goal-keeper, contract-router |
| `AX-F0-T02` | Maintain complete contract and ADR indexes | all | contract-router, gate-evaluator |
| `AX-F0-T03` | Convert material chat iterations into repository artifacts | 11, 18 | goal-keeper, hypothesis-curator |
| `AX-F0-T04` | Maintain typed task and skill schemas | 18 | task-orchestrator, skill-lifecycle-manager |
| `AX-F0-T05` | Enforce canonical `AXIGNAL / axignal.com` naming | Goal Lock, ADR-001 | naming-guardian, gate-evaluator |
| `AX-F0-T06` | Audit roadmap completeness before freeze | all | goal-keeper, gate-evaluator |
| `AX-F0-T07` | Integrate Contracts 21–24 and ADR-007 into indexes, gates and agent routing | 18, 21–24, ADR-007 | goal-keeper, contract-router, gate-evaluator |

## F1 — UX architecture and validation

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F1-T01` | Extend competitive benchmark for command, map and graph research | 05, 12–14 | ux-researcher |
| `AX-F1-T02` | Define buyer jobs, contexts and failure costs | 00, 01, 05 | ux-researcher, hypothesis-curator |
| `AX-F1-T03` | Design three materially different investigation shells | 05, 12–14, 20 | interaction-architect, visualisation-designer |
| `AX-F1-T04` | Prototype multilingual Navigator command interpretation | 14, 16 | conversational-navigator, multilingual-localiser |
| `AX-F1-T05` | Prototype `AUTO / GLOBE / GRAPH / DUAL` routing | 12–14 | lens-router-engineer, interaction-architect |
| `AX-F1-T06` | Prototype Globe–Graph parity and transitions | 12, 13, 20 | globe-engineer, graph-engineer, visualisation-designer |
| `AX-F1-T07` | Prototype persistent Timeline and Claim/Evidence Rail | 05, 12, 13 | timeline-engineer, interaction-architect |
| `AX-F1-T08` | Prototype intent-memory and Knowledge Tide transparency | 15, 17 | intent-intelligence-designer, privacy-reviewer |
| `AX-F1-T09` | Create six-language UX fixtures | 16 | multilingual-localiser |
| `AX-F1-T10` | Run moderated comparative usability tests | 05, 12–16, 20 | ux-researcher, gate-evaluator |
| `AX-F1-T11` | Iterate after every two participants | 12–16, 20 | interaction-architect, ux-researcher |
| `AX-F1-T12` | Accept, revise or reject the selected UX architecture | ADR-005–ADR-007 | goal-keeper, gate-evaluator |
| `AX-F1-T13` | Reproduce selected dark Investigation Shell reference faithfully | 05, 12–14, 20, ADR-007 | frontend-architect, interaction-architect, accessibility-auditor |
| `AX-F1-T14` | Reproduce selected light Investigation Shell reference faithfully | 05, 20, ADR-007 | frontend-architect, accessibility-auditor, multilingual-localiser |
| `AX-F1-T15` | Create faithful Graph and Dual states using the same component tree and fixtures | 12–14, 20, ADR-007 | graph-engineer, frontend-architect, test-engineer |
| `AX-F1-T16` | Design the complete conversion landing architecture and page flow | 21, 24 | ux-researcher, interaction-architect, hypothesis-curator |
| `AX-F1-T17` | Prototype hero and canonical Ask → Track product demonstration | 14, 20, 21, ADR-007 | interaction-architect, frontend-architect, conversational-navigator |
| `AX-F1-T18` | Prototype Pricing, plan comparison, FAQ and Trust Center entry points | 21, 22, 24 | ux-researcher, hypothesis-curator, legal-doc-coordinator |
| `AX-F1-T19` | Compare landing comprehension, trust and CTA clarity across variants | 21, 23, 24 | ux-researcher, product-analyst, gate-evaluator |
| `AX-F1-T20` | Store versioned UI reference assets and visual-regression fixtures | 08, 10, 20, ADR-007 | test-engineer, operations-writer |

## F2 — Reproducible repository spine

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F2-T01` | Scaffold monorepo and bounded modules | 04, 09, 18 | repository-architect |
| `AX-F2-T02` | Pin runtimes, dependencies and containers | 04, 08 | repository-architect, security-reviewer |
| `AX-F2-T03` | Configure PostgreSQL, PostGIS and pgvector | 04 | data-architect |
| `AX-F2-T04` | Configure API, workers, scheduler and object-store interfaces | 04, 07 | backend-architect |
| `AX-F2-T05` | Add migrations, fixtures and deterministic seeds | 04, 09 | data-architect, test-engineer |
| `AX-F2-T06` | Add CI for lint, types, tests, schemas and OpenAPI | 08, 09 | test-engineer, gate-evaluator |
| `AX-F2-T07` | Add OpenTelemetry and correlation IDs | 08, 10 | observability-engineer |
| `AX-F2-T08` | Document startup, backup and restore | 10 | operations-writer |
| `AX-F2-T09` | Prove clean-clone reproducibility | 08, 09 | gate-evaluator |
| `AX-F2-T10` | Scaffold marketing routes or application with shared design-system packages | 04, 20, 21 | repository-architect, frontend-architect |
| `AX-F2-T11` | Implement typed consent-aware acquisition event adapter | 06, 08, 23 | analytics-engineer, privacy-reviewer, test-engineer |
| `AX-F2-T12` | Add landing performance, accessibility, SEO and visual-regression CI | 08, 20, 21, 23 | performance-engineer, accessibility-auditor, test-engineer |
| `AX-F2-T13` | Add CRM, scheduling and lead-routing interfaces without claim authority | 04, 06, 18, 23 | backend-architect, privacy-reviewer, security-reviewer |
| `AX-F2-T16` | Add isolated shared-Traefik pilot edge and host-only credential lifecycle | 06, 08–10, 18, 19, ADR-011 | repository-architect, security-reviewer, test-engineer, operations-engineer, operations-writer |
| `AX-F2-T17` | Release the public landing through incumbent Traefik with private consent-aware intake | 06, 08–10, 18, 19 | repository-architect, privacy-reviewer, security-reviewer, test-engineer, operations-engineer, operations-writer |

## F3 — Epistemic kernel

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F3-T01` | Implement Source Registry | 03, 06 | source-admission, data-architect |
| `AX-F3-T02` | Implement immutable raw evidence references | 02, 03 | evidence-provenance-engineer |
| `AX-F3-T03` | Implement reversible entity resolution | 02, 03 | entity-resolution-engineer |
| `AX-F3-T04` | Implement candidate claim schema and versions | 02 | epistemic-admission |
| `AX-F3-T05` | Implement structural and temporal gates | 02 | epistemic-admission, test-engineer |
| `AX-F3-T06` | Implement rights and export gates | 03, 06 | source-admission, privacy-reviewer |
| `AX-F3-T07` | Implement quantitative reproducibility | 02 | epistemic-admission, data-quality-auditor |
| `AX-F3-T08` | Implement contradiction and source-lineage groups | 02 | epistemic-admission |
| `AX-F3-T09` | Implement immutable transitions and audit events | 02, 08 | epistemic-admission, observability-engineer |
| `AX-F3-T10` | Implement opportunity subgraph assembly | 02 | opportunity-modeler |
| `AX-F3-T11` | Implement correction, expiry and retraction propagation | 02, 10 | epistemic-admission, test-engineer |
| `AX-F3-T12` | Prove deterministic lifecycle replay | 08, 09 | gate-evaluator |

## F4 — Navigator and InvestigationContext

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F4-T01` | Define command ontology and typed command plans | 14, 16 | conversational-navigator, ontology-engineer |
| `AX-F4-T02` | Implement multilingual command parsing | 14, 16 | conversational-navigator, multilingual-localiser |
| `AX-F4-T03` | Show visible interpretation before material actions | 14 | interaction-architect, consent-ux-reviewer |
| `AX-F4-T04` | Implement `InvestigationContext` state machine | 12, 14 | interaction-architect, frontend-architect |
| `AX-F4-T05` | Implement execution, undo and command history | 12, 14 | conversational-navigator, frontend-architect |
| `AX-F4-T06` | Implement clarification thresholds | 14 | conversational-navigator, ux-researcher |
| `AX-F4-T07` | Implement claim-grounded explanation | 02, 14 | conversational-navigator, epistemic-admission |
| `AX-F4-T08` | Synchronise chat and direct manipulation | 12, 14 | interaction-architect |
| `AX-F4-T09` | Implement saved investigation trails | 12, 14 | frontend-architect, data-architect |
| `AX-F4-T10` | Prove no model can write canonical state directly | 02, 14 | security-reviewer, test-engineer |

## F5 — Globe, Graph and Timeline parity

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F5-T01` | Implement geographic layer contract | 12, 13 | globe-engineer, visualisation-designer |
| `AX-F5-T02` | Implement semantic zoom and coverage states | 13 | globe-engineer, accessibility-auditor |
| `AX-F5-T03` | Implement typed graph renderer | 12, 13 | graph-engineer, visualisation-designer |
| `AX-F5-T04` | Implement bounded expansion and path explanation | 07, 13 | graph-engineer, epistemic-admission |
| `AX-F5-T05` | Implement Timeline and `as_of` reconstruction | 02, 12, 13 | timeline-engineer |
| `AX-F5-T06` | Implement AUTO lens router | 12, 14 | lens-router-engineer, conversational-navigator |
| `AX-F5-T07` | Implement explicit Globe/Graph override | 12, 14 | frontend-architect |
| `AX-F5-T08` | Implement Dual professional mode | 12, 13 | globe-engineer, graph-engineer |
| `AX-F5-T09` | Preserve context across all lens changes | 12 | interaction-architect, test-engineer |
| `AX-F5-T10` | Add textual and tabular equivalents | 05, 13 | accessibility-auditor |
| `AX-F5-T11` | Validate performance budgets | 04, 08, 13 | performance-engineer, gate-evaluator |

## F6 — Multilingual semantic system

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F6-T01` | Define locale and terminology registry | 16 | multilingual-localiser, ontology-engineer |
| `AX-F6-T02` | Preserve original-language evidence | 02, 16 | evidence-provenance-engineer |
| `AX-F6-T03` | Implement translated claim renderings and provenance | 16 | multilingual-localiser, epistemic-admission |
| `AX-F6-T04` | Implement aliases and transliteration | 16 | entity-resolution-engineer |
| `AX-F6-T05` | Implement multilingual lexical and semantic search | 07, 16 | search-engineer, multilingual-localiser |
| `AX-F6-T06` | Implement locale-aware formats | 16 | frontend-architect |
| `AX-F6-T07` | Create parity and regression corpus | 08, 16 | multilingual-localiser, test-engineer |
| `AX-F6-T08` | Human-QA critical terminology | 16 | multilingual-localiser, gate-evaluator |
| `AX-F6-T09` | Localise landing, pricing, FAQ, methodology and structured metadata | 16, 21–24 | multilingual-localiser, frontend-architect |
| `AX-F6-T10` | Validate six-language commercial, methodological and legal terminology | 06, 16, 21–24 | multilingual-localiser, legal-doc-coordinator, gate-evaluator |

## F7 — Intent Intelligence and Knowledge Tides

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F7-T01` | Implement typed `USER_INTENT_EVENT` | 15 | intent-intelligence-engineer, data-architect |
| `AX-F7-T02` | Separate observed, inferred and confirmed preferences | 15 | intent-intelligence-engineer, privacy-reviewer |
| `AX-F7-T03` | Implement purpose-specific controls | 06, 15 | privacy-reviewer, consent-ux-reviewer |
| `AX-F7-T04` | Implement eligible-cohort and unique-user metrics | 15 | analytics-engineer, data-quality-auditor |
| `AX-F7-T05` | Implement Knowledge Tide dimensions | 15 | intent-intelligence-engineer, analytics-engineer |
| `AX-F7-T06` | Implement temporal decay and persistence | 15 | analytics-engineer |
| `AX-F7-T07` | Implement organisation diversity and anti-manipulation | 15 | fraud-risk-engineer, security-reviewer |
| `AX-F7-T08` | Implement privacy thresholds and aggregation | 06, 15 | privacy-reviewer, analytics-engineer |
| `AX-F7-T09` | Implement coverage-gap detection | 15, 17 | intent-intelligence-engineer |
| `AX-F7-T10` | Implement research candidate queue | 17 | research-queue-orchestrator |
| `AX-F7-T11` | Implement review, correction, deletion and opt-out | 06, 15 | privacy-reviewer, test-engineer |
| `AX-F7-T12` | Prove tides cannot create economic claims | 02, 15, 17 | epistemic-admission, gate-evaluator |

## F8 — First lawful universe

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F8-T01` | Score candidate universes | 01, 03, 11, 17 | universe-selector, hypothesis-curator |
| `AX-F8-T02` | Select wedge through explicit gate | 00, 01, 03 | goal-keeper, gate-evaluator |
| `AX-F8-T03` | Define universe ontology | 02, 03 | ontology-engineer, opportunity-modeler |
| `AX-F8-T04` | Admit minimum lawful source set | 03, 06 | source-admission |
| `AX-F8-T05` | Implement connectors and quality monitoring | 03, 08 | connector-engineer, data-quality-auditor |
| `AX-F8-T06` | Implement universe claim policies | 02 | epistemic-admission |
| `AX-F8-T07` | Build Globe and Graph layers | 12, 13 | globe-engineer, graph-engineer |
| `AX-F8-T08` | Add multilingual terminology | 16 | multilingual-localiser |
| `AX-F8-T09` | Reconstruct historical opportunities | 02, 08 | opportunity-modeler, timeline-engineer |
| `AX-F8-T10` | Validate buyer workflow, cost and margin | 01, 08, 11 | ux-researcher, product-analyst |
| `AX-F8-T11` | Parse one complete TED eForms XML profile and rederive deterministic non-personal Candidate Claims | 02–04, 06, 08–10, 18, 19, 27, ADR-010, ADR-012 | connector-engineer, ontology-engineer, epistemic-admission, privacy-reviewer, security-reviewer, test-engineer, gate-evaluator |

## F9 — Paid design partners

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F9-T01` | Implement identity, organisations and roles | 04, 06 | identity-engineer, security-reviewer |
| `AX-F9-T02` | Implement Stripe products and entitlements | 01, 07, 22 | billing-engineer |
| `AX-F9-T03` | Implement onboarding and privacy controls | 01, 06, 15, 21 | interaction-architect, privacy-reviewer |
| `AX-F9-T04` | Implement analytics and cost ledger | 01, 08, 23 | analytics-engineer, finance-operator |
| `AX-F9-T05` | Publish terms, privacy and methodology | 06, 10, 24 | legal-doc-coordinator, operations-writer |
| `AX-F9-T06` | Recruit 10 independent paid design partners | 01, 11, 21–23 | design-partner-operator |
| `AX-F9-T07` | Measure retention and decision impact | 01, 08, 11, 23 | product-analyst, hypothesis-curator |
| `AX-F9-T08` | Validate package names and customer-facing value metrics | 01, 11, 22 | hypothesis-curator, product-analyst, finance-operator |
| `AX-F9-T09` | Implement pricing, detailed comparison and entitlement catalogue | 07, 21, 22 | billing-engineer, frontend-architect, test-engineer |
| `AX-F9-T10` | Implement trial, sandbox or design-partner access flow | 06, 21–23 | interaction-architect, privacy-reviewer, design-partner-operator |
| `AX-F9-T11` | Implement self-service upgrade, downgrade and cancellation where applicable | 07, 22 | billing-engineer, test-engineer |
| `AX-F9-T12` | Publish first validated FAQ and Trust Center | 21, 24 | legal-doc-coordinator, operations-writer, accessibility-auditor |
| `AX-F9-T13` | Instrument acquisition-to-first-investigation funnel | 08, 21, 23 | analytics-engineer, product-analyst, privacy-reviewer |
| `AX-F9-T14` | Execute willingness-to-pay and conversion tests | 11, 22, 23 | hypothesis-curator, product-analyst, finance-operator |

## F10 — Scenarios and outcomes

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F10-T01` | Define scenario registry | 02, 08 | scenario-calibration-engineer |
| `AX-F10-T02` | Freeze temporal evaluation data | 02, 08 | data-quality-auditor |
| `AX-F10-T03` | Establish baselines | 08 | scenario-calibration-engineer |
| `AX-F10-T04` | Preserve forecasts immutably | 02 | timeline-engineer |
| `AX-F10-T05` | Implement outcome claims | 02 | opportunity-modeler |
| `AX-F10-T06` | Generate calibration and drift reports | 08 | scenario-calibration-engineer |
| `AX-F10-T07` | Implement model demotion and retirement | 08 | gate-evaluator, operations-engineer |

## F11 — Enterprise and API

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F11-T01` | Implement enterprise organisation controls | 06, 07 | identity-engineer |
| `AX-F11-T02` | Implement API keys, OAuth scopes and quotas | 07 | api-engineer, security-reviewer |
| `AX-F11-T03` | Implement private source connectors | 03, 06 | connector-engineer, source-admission |
| `AX-F11-T04` | Isolate private claims and trails | 02, 06 | data-architect, security-reviewer |
| `AX-F11-T05` | Implement export-right controls | 03, 07 | api-engineer, source-admission |
| `AX-F11-T06` | Implement SSO/SCIM when contracted | 06 | identity-engineer |
| `AX-F11-T07` | Produce enterprise audit package | 06, 10, 24 | security-reviewer, operations-writer |
| `AX-F11-T08` | Publish enterprise Trust Center package and controlled evidence room | 06, 10, 21, 24 | security-reviewer, legal-doc-coordinator, operations-writer |
| `AX-F11-T09` | Expose API, private-source and security maturity accurately on public surfaces | 03, 06, 07, 21, 24 | api-engineer, source-admission, security-reviewer |

## F12 — General availability

| Task | Outcome | Governing contracts | Skills |
|---|---|---|---|
| `AX-F12-T01` | Validate production SLOs and recovery | 08, 10 | operations-engineer, gate-evaluator |
| `AX-F12-T02` | Validate retention and gross margin | 01, 08, 11, 22, 23 | product-analyst, finance-operator |
| `AX-F12-T03` | Establish repeatable acquisition channel | 01, 21, 23 | growth-analyst, hypothesis-curator |
| `AX-F12-T04` | Admit every new universe independently | 03, 09 | universe-selector, gate-evaluator |
| `AX-F12-T05` | Maintain jurisdiction-specific availability | 06 | regulatory-scope-reviewer |
| `AX-F12-T06` | Run recurring Goal Lock audit | Goal Lock, 18 | goal-keeper, gate-evaluator |
| `AX-F12-T07` | Validate repeatable acquisition against activation, retention and margin | 21–23 | growth-analyst, product-analyst, finance-operator |
| `AX-F12-T08` | Operate experiment registry and evidence-gated reinvestment policy | 22, 23 | growth-analyst, analytics-engineer, gate-evaluator |
| `AX-F12-T09` | Maintain public pricing, methodology, FAQ and Trust Center change control | 10, 21, 22, 24 | operations-writer, legal-doc-coordinator, contract-router |

## Task closure rule

A task is not complete because code exists. It reaches `ACCEPTED` only when:

1. all required contracts are satisfied;
2. required skills produced their outputs;
3. automated and human evidence exists;
4. Goal Lock tests pass;
5. rollback or disabling is demonstrated;
6. no unresolved security, privacy, rights, commercial-truth or naming defect remains.
