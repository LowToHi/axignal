# 09 — Commercial and Conversion Dynamic Skill Map

Version: `0.1.0-candidate`
Status: `PROPOSED EXTENSION / FAIL CLOSED UNTIL REGISTRY MERGE`
Goal ID: `AXIGNAL-GOAL-001`
Registry extension: `skills/commercial-extension.registry.yaml`

## 1. Purpose

This map extends the canonical dynamic skill system for the selected product-UI fidelity target and the public marketing, pricing, acquisition and Trust Center system.

The skills are proposed capabilities, not autonomous authorities. They operate under the Goal Lock, Contract 18, Contracts 20–24 and the active task.

## 2. Activation rule

A task MUST fail closed when it references a skill that has not been:

1. defined in the candidate extension;
2. reviewed against its governing contracts;
3. merged into `skills/registry.yaml`;
4. validated against `schemas/skill.schema.json`;
5. tested;
6. activated by an authorised gate.

Documentation of a skill does not authorise execution.

## 3. Skill map

| Skill | Trigger | Required output | Governing contracts |
|---|---|---|---|
| `visual-fidelity-auditor` | implementation or review of selected UI | comparison against ADR-007, drift report, accessibility-safe disposition | 05, 08, 12, 13, 20, 21 |
| `conversion-copy-strategist` | hero, CTA, FAQ, value proposition or landing copy | truthful copy hypotheses, variants and comprehension evidence | 00, 06, 16, 21, 24 |
| `pricing-and-packaging-analyst` | plans, prices, limits or value metric | packaging hypothesis, WTP protocol, margin and rejection conditions | 01, 08, 11, 22, 23 |
| `entitlement-architect` | capability, quota, usage or plan enforcement | typed entitlement map, source-right intersection and migration | 04, 06, 07, 22 |
| `experimentation-engineer` | A/B, multivariate or sequential experiment | preregistration, assignment, metrics, guardrails, rollback and result | 06, 08, 11, 21–23 |
| `seo-architect` | metadata, content architecture or organic acquisition | crawlability, locale alternates, structured data and quality gate | 16, 21, 23, 24 |
| `crm-automation-engineer` | form, lead routing, scheduling or follow-up | purpose-limited lifecycle automation with audit and stop controls | 04, 06, 18, 23 |
| `trust-center-editor` | methodology, privacy, security, status or correction page | evidence-linked public statement with owner and review trigger | 02, 03, 06, 10, 15, 16, 24 |
| `acquisition-funnel-analyst` | funnel, channel, activation, retention or payback | denominator-safe analysis linking acquisition to product value | 01, 06, 08, 21, 23 |

## 4. Task routing

### Product UI fidelity

Tasks `AX-F1-T13` through `AX-F1-T15` and `AX-F1-T20` SHOULD activate:

- visual-fidelity-auditor;
- interaction-architect;
- frontend-architect;
- accessibility-auditor;
- test-engineer;
- performance-engineer where applicable.

### Landing and product proof

Tasks `AX-F1-T16` through `AX-F1-T19` SHOULD activate:

- conversion-copy-strategist;
- interaction-architect;
- ux-researcher;
- visual-fidelity-auditor;
- accessibility-auditor;
- multilingual-localiser;
- trust-center-editor when methodology is present.

### Pricing and entitlements

Tasks `AX-F9-T08` through `AX-F9-T11` SHOULD activate:

- pricing-and-packaging-analyst;
- entitlement-architect;
- billing-engineer;
- finance-operator;
- product-analyst;
- privacy-reviewer;
- gate-evaluator.

### Trust and FAQ

Tasks `AX-F9-T12`, `AX-F11-T08`, `AX-F11-T09` and `AX-F12-T09` SHOULD activate:

- trust-center-editor;
- legal-doc-coordinator;
- security-reviewer;
- privacy-reviewer;
- source-admission;
- multilingual-localiser;
- accessibility-auditor.

### Acquisition and experimentation

Tasks `AX-F2-T11` through `AX-F2-T13`, `AX-F9-T13`, `AX-F9-T14`, `AX-F12-T07` and `AX-F12-T08` SHOULD activate:

- experimentation-engineer;
- acquisition-funnel-analyst;
- analytics-engineer;
- crm-automation-engineer where applicable;
- privacy-reviewer;
- security-reviewer;
- finance-operator;
- gate-evaluator.

### Organic acquisition

Landing, resource and locale tasks SHOULD activate:

- seo-architect;
- multilingual-localiser;
- conversion-copy-strategist;
- performance-engineer;
- accessibility-auditor;
- epistemic-admission when public economic assertions are present.

## 5. Conflict rules

- Conversion copy cannot override canonical product capability.
- Pricing cannot override source rights or jurisdiction availability.
- SEO cannot override epistemic admission, accessibility or performance.
- Experimentation cannot weaken privacy, security, non-advice or disclosure requirements.
- CRM automation cannot write canonical claims, opportunities or Knowledge Tides.
- Visual fidelity cannot justify inaccessible or misleading semantics.
- Growth analysis cannot authorise reinvestment without activation, retention, margin and payback evidence.

## 6. Evidence ledger additions

Commercial and conversion task evidence MUST record:

- copy, design, pricing or experiment version;
- audience and eligibility;
- locale;
- entitlement state;
- analytics schema version;
- source and consent state;
- primary and guardrail metrics;
- product activation outcome;
- economic interpretation;
- rollback;
- skill versions and gate decision.

## 7. Acceptance gate

The extension can merge into the canonical registry only when:

- every skill validates against the skill schema;
- each has at least one positive and negative test;
- task routing is deterministic;
- conflict rules are tested;
- missing skills fail closed;
- no commercial skill can modify canonical epistemic state;
- no implementing skill can approve its own output;
- prior registry versions remain recoverable.