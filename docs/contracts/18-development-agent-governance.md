# 18 — AXIGNAL Development Agent Governance Contract

Version: `0.3.1`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

This contract governs every autonomous or assisted development agent working on AXIGNAL. Its purpose is to make end-to-end development possible without allowing the product goal, epistemic boundaries or validated decisions to disappear inside local implementation tasks.

## 2. Mandatory execution order

Before changing the repository, an agent MUST resolve:

```text
Goal Lock
→ active phase
→ task specification
→ governing contracts
→ mandatory skills
→ dependencies and permissions
→ acceptance evidence
→ rollback and kill switch
```

The agent MUST refuse to execute an underspecified material task.

## 3. Source of authority

Precedence:

1. explicit current user decision;
2. `docs/roadmap/00-goal-lock.md`;
3. `AGENTS.md`;
4. this contract;
5. product constitution;
6. security/privacy/regulatory contract;
7. epistemic contract;
8. capability-specific contracts;
9. accepted ADRs;
10. typed task;
11. implementation details.

A current explicit user correction such as canonical naming MUST be propagated rather than left as chat-only context.

## 4. Goal lock

Every material task MUST reference `AXIGNAL-GOAL-001`.

Before closure, the agent MUST answer every Goal Lock test and attach the answers to the task or PR.

A failed or unknown answer blocks acceptance unless an applicable contract explicitly permits it.

## 5. Canonical naming

The only active product identity is:

- brand: **AXIGNAL**;
- domain: **axignal.com**;
- repository: `LowToHi/axignal`;
- Goal ID: `AXIGNAL-GOAL-001`.

The legacy strings `ASIGNAL`, `asignal.com` and `ASIGNAL-GOAL-001` are active-document defects.

CI MUST scan active repository content for forbidden naming.

## 6. Phase authority

An agent MUST determine the current phase state before work:

- `LOCKED` — implementation prohibited except synthetic research explicitly permitted;
- `AUTHORISED` — tasks may enter `READY`;
- `IN_PROGRESS` — only registered tasks may execute;
- `GATE_REVIEW` — implementation pauses except evidence repair;
- `PASSED` — dependent phases may be authorised;
- `FAILED` — new implementation pauses pending repair or supersession;
- `PAUSED` — external decision or dependency required.

The agent MUST NOT present a locked or explored phase as completed.

## 7. Task contract

Every task MUST validate against `schemas/task.schema.json` and include:

- task and Goal IDs;
- phase;
- objective;
- measurable outcome;
- governing contracts;
- activated skills and versions;
- dependencies;
- allowed scope;
- prohibited scope;
- acceptance evidence;
- security, privacy, rights and multilingual impact;
- observability;
- rollback or kill switch;
- owner and reviewer.

## 8. Dynamic skill activation

The task orchestrator MUST load:

- always-on governance skills;
- task-type skills;
- risk-triggered skills;
- language and accessibility skills for user-facing work;
- source, rights and data-quality skills for ingestion work;
- epistemic skills for claims, opportunities and scenarios.

A missing mandatory skill results in `BLOCKED`.

## 9. Contract-first changes

A material behavioural change MUST update its contract before or with implementation.

Material changes include:

- product purpose or boundary;
- claim semantics;
- user-intent use;
- source rights;
- API meaning;
- pricing entitlement;
- personalisation;
- multilingual semantics;
- security model;
- architecture authority;
- phase or gate thresholds.

## 10. Epistemic separation

An agent MUST preserve these bounded contexts:

```text
user message and intent
≠ private preference
≠ aggregate Knowledge Tide
≠ research candidate
≠ evidence
≠ admitted claim
≠ opportunity
≠ scenario
≠ outcome
```

The agent MUST reject any shortcut that treats popularity, model confidence or visual prominence as truth.

## 11. UX continuity

User-facing implementation MUST preserve one shared `InvestigationContext` across:

- Navigator;
- Globe;
- Graph;
- Timeline;
- Claim and Evidence Rail;
- investigation trails.

A feature that exists only in Globe or only in Graph requires an explicit parity decision and must not silently weaken the other lens.

## 12. Multilingual requirement

Any material user-facing task MUST evaluate all six launch languages by architecture, even when implementation is initially fixture-based.

Canonical semantics remain language-neutral and original evidence remains recoverable.

## 13. Data and source safety

An agent MUST NOT:

- scrape because content is public;
- infer commercial-use rights;
- store restricted raw data without permission;
- train models on data without explicit authority;
- expose tenant-private data;
- bypass attribution;
- continue after source revocation.

Every connector requires source admission and a kill switch.

## 14. Security and privacy

Security and privacy are acceptance requirements.

Any task touching user messages, preferences, profiling, organisation data, exports, authentication or model providers MUST activate the relevant reviewers.

Raw user prompts MUST not become global analytics by default.

## 15. Evidence discipline

An agent MUST distinguish:

- test output;
- benchmark result;
- screenshot or recording;
- human-research evidence;
- source-rights record;
- hypothesis;
- inference;
- unsupported assertion.

A task cannot close on a narrative statement alone.

## 16. Self-review prohibition

The implementing agent MAY prepare gate evidence but MUST NOT grant final `PASS` to its own phase without an independent gate-evaluator role or explicit user decision.

## 17. Fail-closed conditions

The task MUST fail closed when:

- Goal Lock is missing or contradicted;
- required contract or skill is missing;
- source rights are unknown;
- privacy cohort is insufficient;
- test results are unavailable;
- canonical state cannot be replayed;
- rollback is impossible for a material change;
- naming guard fails;
- AI output can bypass admission;
- a locked dependency is treated as passed.

## 18. Scope discovery

When implementation discovers new work:

- non-material repair MAY remain within the task;
- material work MUST create a new typed task;
- architectural or product change MUST create an ADR and contract update;
- the current task MUST pause if the new dependency invalidates its assumptions.

## 19. PR requirements

Every material PR MUST state:

- Goal ID;
- phase and tasks;
- contracts affected;
- skills activated;
- decisions made;
- tests and evidence;
- migrations;
- security/privacy/rights impact;
- multilingual impact;
- observability;
- rollback;
- known limitations;
- next authorised priority.

## 20. Development completion

End-to-end completion does not mean all imagined features exist.

AXIGNAL reaches a phase-complete state only when the relevant gate passes. General availability requires F12 evidence and no unresolved material Goal Lock violation.

## 21. Acceptance criteria

Agent governance is accepted when:

- every registered task resolves phase, contracts and skills deterministically;
- forbidden out-of-phase tasks fail closed;
- CI blocks naming defects;
- source and privacy risk activate mandatory reviewers;
- Goal Lock answers appear in PR evidence;
- new material scope creates tasks and ADRs rather than hidden work;
- implementing agents cannot self-approve gates;
- a simulated generic-chatbot shortcut is rejected;
- a simulated high-interest-to-economic-claim shortcut is rejected;
- the roadmap can generate an unambiguous next authorised task.
