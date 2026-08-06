# AXIGNAL Skill Registries

Goal ID: `AXIGNAL-GOAL-001`

The canonical skill set is the union of:

- `skills/registry.yaml` — foundation product, platform, epistemic, risk and operations skills;
- `skills/commercial-extension.registry.yaml` — marketing, pricing, acquisition and commercial validation skills;
- `skills/research-retrieval.registry.yaml` — Navigator Research Mode, authorised retrieval, tenant memory, local model operation and Candidate Claim pipeline skills;
- `skills/subscriber-workspace-ux.registry.yaml` — subscriber product shell, procurement workflow, navigation, design system, accessibility and UX validation skills.

## Registry rules

Every registry MUST declare:

- `goal_id: AXIGNAL-GOAL-001`;
- `canonical_brand: AXIGNAL`;
- `canonical_domain: axignal.com`;
- a version;
- a status;
- unique `skill_id` values.

GitHub Contract Validation loads every `skills/*.registry.yaml` file plus `skills/registry.yaml` and fails when:

- canonical identity differs;
- an ID is duplicated inside or across registries;
- YAML cannot be parsed;
- a registry does not expose a `skills` collection.

A modular registry does not create independent authority. Every skill remains subordinate to Goal Lock, `AGENTS.md`, contract 18, contract precedence and the active task.

## Research and retrieval activation

The following skills are mandatory for their respective scopes:

| Scope | Required skills |
|---|---|
| ResearchRun | `research-run-orchestrator`, `conversational-navigator`, `observability-engineer`, `finance-operator` |
| hybrid retrieval | `retrieval-policy-engineer`, `search-engineer`, `source-admission` |
| Browser | `authorised-browser-researcher`, `source-admission`, `security-reviewer`, `evidence-provenance-engineer` |
| private knowledge | `tenant-memory-engineer`, `privacy-reviewer`, `security-reviewer`, `data-architect` |
| local model worker | `local-model-operator`, `security-reviewer`, `test-engineer`, `finance-operator` |
| Candidate Claims | `candidate-claim-pipeline-engineer`, `epistemic-admission`, `evidence-provenance-engineer`, `source-admission` |
| subscriber workspace UX/UI | every skill declared in `skills/subscriber-workspace-ux.registry.yaml` |

Missing a required skill fails closed.
