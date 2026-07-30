# AX-F0-T04 — AXIGNAL GSAP UI/UX Skill

Status: `EVIDENCE_READY`
Date: `2026-07-28`
Goal ID: `AXIGNAL-GOAL-001`
Phase: `F0`

## Objective

Create a repository-local Agent Skill that gives AXIGNAL UI and UX work broad, current GSAP capability without weakening product truth, accessibility, performance, lifecycle safety, dependency discipline, or independent gate authority.

## Context

The repository had a dynamic Skill registry and typed Skill schema, but no executable `SKILL.md` capability for motion implementation. The user selected the official GreenSock `greensock/gsap-skills` repository as upstream.

Upstream snapshot:

- repository: `https://github.com/greensock/gsap-skills`;
- commit: `aed9cfd3277740755f6bfc1155c7aa645403b760`;
- license: MIT;
- modules reviewed: core, timeline, ScrollTrigger, plugins, utilities, React, frameworks, and performance.

## Affected systems

- `skills/axignal-gsap-ui-ux/` — executable Skill, typed contract, references, attribution, and deterministic auditor;
- `skills/registry.yaml` — conditional Skill routing;
- `docs/roadmap/04-dynamic-skill-map.md` — normative candidate Skill map;
- UI, UX, marketing, Globe, Graph, Timeline, Navigator, and evidence surfaces when the Skill is activated in future tasks.

No application runtime, package manifest, lockfile, deployment, source data, user data, or production dependency changed.

## Contracts and decisions

Governing authority:

- `docs/roadmap/00-goal-lock.md`;
- `AGENTS.md`;
- Contracts `05`, `08`, `12`, `13`, `16`, `18`, `20`, and `21`;
- ADR `006` for provisional layered visual-system values.

Decision:

- consolidate the official upstream modules into one AXIGNAL-specific conditional Skill;
- retain high creative freedom for choreography and implementation;
- fail closed at epistemic, accessibility, lifecycle, performance, identity, and gate-authority boundaries;
- keep the Skill at lifecycle state `CONTRACTED`;
- do not install GSAP or `@gsap/react` until an authorised implementation task needs them and updates the repository lockfile.

No new ADR is required because this task introduces no runtime provider or package and freezes no product architecture. A material runtime adoption remains subject to the applicable task, dependency evidence, and ADR rules.

## Skills activated

Always-on:

- `goal-keeper` `0.1.0`;
- `contract-router` `0.1.0`;
- `task-orchestrator` `0.1.0`;
- `gate-evaluator` `0.1.0`;
- `naming-guardian` `0.1.0`;
- `security-reviewer` `0.1.0`;
- `privacy-reviewer` `0.1.0`;
- `observability-engineer` `0.1.0`.

Conditional:

- `interaction-architect` `0.1.0`;
- `visualisation-designer` `0.1.0`;
- `accessibility-auditor` `0.1.0`;
- `multilingual-localiser` `0.1.0`;
- `frontend-architect` `0.1.0`;
- `performance-engineer` `0.1.0`;
- `test-engineer` `0.1.0`;
- Codex `skill-creator`, used to initialise and structurally validate the executable Skill.

## Implementation

1. Initialised `skills/axignal-gsap-ui-ux/` through the Codex Skill creator.
2. Adapted the official GreenSock Skill modules into a capability and framework selection reference.
3. Added AXIGNAL-specific motion hierarchy, surface semantics, creative directions, prohibited behavior, and evidence matrix.
4. Added a typed Skill contract conforming to `schemas/skill.schema.json`.
5. Added a dependency-free Node auditor with a built-in positive/negative self-test.
6. Preserved the upstream commit, project URL, copyright, and MIT license.
7. Registered the Skill as conditional and `CONTRACTED`.

## Risks and controls

| Risk                                          | Control                                                                                           |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Spectacle overrides comprehension             | Every effect requires a semantic owner and stable fallback                                        |
| Motion implies financial certainty or urgency | Explicit prohibited actions and AXIGNAL semantic contract                                         |
| Accessibility regression                      | Reduced motion, focus, keyboard, non-drag and non-visual equivalents are mandatory                |
| React lifecycle leaks                         | `useGSAP`, scoped selectors, context cleanup, and auditor checks                                  |
| Scroll or rendering jank                      | Transform-first patterns, low-end evidence, cancellation, and performance traces                  |
| Upstream drift                                | Pinned upstream commit and documented update protocol                                             |
| License loss                                  | Repository URL, snapshot, copyright, and MIT notice retained                                      |
| Dependency drift or secret leakage            | Public packages only; dependency addition deferred to an authorised locked task                   |
| Self-approval                                 | Lifecycle remains `CONTRACTED`; material direction and phase gates require independent evaluation |

## Validation checklist

- [x] Skill initialised with the required creator script.
- [x] `SKILL.md` frontmatter and directory structure validate.
- [x] Auditor positive and negative fixtures pass.
- [x] Canonical naming passes for the Skill.
- [x] Typed Skill contract validates against the repository JSON Schema.
- [x] Registry YAML parses and contains unique Skill IDs.
- [x] Repository-wide canonical naming passes.
- [x] New executable artifacts are formatted and diff integrity passes.

Evidence:

```text
Skill is valid!
AXIGNAL GSAP motion auditor self-test PASS (6 unsafe patterns rejected)
PASS skill contract; PASS registry: 54 unique skills; PASS openai.yaml
Canonical naming validation PASS
All matched files use Prettier code style!
git diff --check: PASS
```

## Observability

The Skill contract requires recording activation, version, outputs, and failures in future task evidence. Runtime metrics, logs, traces, and alerts are not applicable because this task adds no runtime code.

## Rollback

Remove the `axignal-gsap-ui-ux` Skill directory and revert its entries in the registry and Skill map. The rollback is documentation-only because this task installs no runtime dependency and changes no application behavior.

The Skill can be disabled without repository deletion by changing its registry state to `REVOKED` before the next task routing cycle.

## Known limitations

- Structural and deterministic checks do not substitute for browser, assistive-technology, comprehension, or device-performance evidence on a real UI.
- The Skill is not `ACTIVE` and has not independently passed a production motion gate.
- Exact motion tokens and visual direction remain provisional under Contract `20` and ADR `006`.

## Authorised next priority

Use the Skill on a bounded F1 prototype task, collect reduced-motion, keyboard, lifecycle, multilingual, and performance evidence, then request an independent lifecycle/gate decision.
