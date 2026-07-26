# 05 — AXIGNAL Dependency and Gate Graph

Version: `0.3.1`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Authorisation graph

```text
F0 Goal + contracts ───────────────┐
                                  ├→ F2 Repository spine → F3 Epistemic kernel ─┐
F1 UX architecture + validation ──┘                                             │
                                                                                ├→ F4 Navigator
F1 ──────────────────────────────────────────────────────────────────────────────┘
F3 ──────────────────────────────────────────────────────────────────────────────┘

F4 → F5 Globe/Graph/Timeline parity
F3 + F4 + F5 → F6 Multilingual semantics
F4 + F6 + privacy controls → F7 Intent Intelligence
F2–F7 → F8 First lawful universe
F8 → F9 Paid design partners
F8 + F9 + sufficient history → F10 Scenarios and outcomes
F8–F10 → F11 Enterprise and API
F9–F11 + retention + operations → F12 General availability
```

## 2. Gate authority

A phase transition requires:

- task evidence;
- contract compliance;
- skill evidence;
- Goal Lock answers;
- unresolved-risk register;
- rollback or kill-switch evidence;
- explicit gate disposition.

The implementing agent MUST NOT approve its own phase gate without an independent `gate-evaluator` run.

## 3. Gate disposition

- `PASS` — all required evidence meets thresholds;
- `CONDITIONAL_PASS` — only explicitly permitted non-material conditions remain;
- `FAIL_CLOSED` — missing, conflicting or failed evidence;
- `PAUSE` — external dependency or strategic decision required;
- `SUPERSEDE` — the phase or task has been replaced by an approved version.

Unverifiable critical evidence results in `FAIL_CLOSED`, not assumed success.

## 4. Universal pre-gate checks

Every gate MUST verify:

1. `AXIGNAL-GOAL-001` still matches the implementation;
2. canonical naming has zero active defects;
3. claims, user intent and generated explanations remain separated;
4. security and privacy reviews are complete;
5. source and redistribution rights are explicit;
6. multilingual impact is addressed;
7. observability and ownership exist;
8. rollback or disabling is tested;
9. no hidden manual process is represented as automated;
10. known limitations are user-visible where material.

## 5. Naming gate

The following active strings MUST be absent:

```text
ASIGNAL
asignal.com
ASIGNAL-GOAL-001
```

The following are canonical:

```text
AXIGNAL
axignal.com
AXIGNAL-GOAL-001
LowToHi/axignal
```

Historical superseded documents MAY preserve prior mistakes only when clearly archived and excluded from active indexes. Active contracts, prototypes, schemas, API specifications and customer surfaces MUST contain only canonical naming.

## 6. F0 gate evidence

Required:

- complete goal-to-phase-to-task-to-contract-to-skill traceability;
- machine-readable task and skill schemas;
- complete active contract index;
- accepted or candidate ADR for every material decision;
- no material requirement existing only in chat;
- naming sweep report;
- roadmap gap report.

## 7. F1 gate evidence

Required:

- three differentiated design directions;
- prototype with Navigator, Globe, Graph, Timeline, rail and multilingual architecture;
- comparative control;
- moderated-test recordings or notes;
- task-level success metrics;
- comprehension of claims, contradiction, coverage and uncertainty;
- context-retention measurements;
- accessibility review;
- selected design decision and rejected alternatives.

## 8. F2 gate evidence

Required:

- clean-clone build;
- dependency lockfiles;
- container digest records;
- schema and OpenAPI validation;
- unit, integration and end-to-end tests;
- local synthetic run;
- telemetry traces;
- backup and restore demonstration.

## 9. F3 gate evidence

Required:

- admitted claim fixture;
- rejected claim fixture;
- contradiction fixture;
- expired and corrected claim fixtures;
- deterministic replay;
- source-rights failure;
- model-bypass attempt blocked;
- audit-event integrity;
- downstream invalidation proof.

## 10. F4 gate evidence

Required:

- typed command plans;
- equivalent commands in six languages;
- visible interpretation;
- undo and context restoration;
- entitlement-denial behaviour;
- grounded explanation with citations;
- no direct model write;
- investigation-trail save and reopen.

## 11. F5 gate evidence

Required:

- Globe and Graph task-parity matrix;
- AUTO routing test corpus;
- explicit override behaviour;
- Dual mode for qualified professional workflow;
- time and selection preserved across views;
- accessible non-visual equivalents;
- measured rendering and query budgets;
- no decorative-only lens.

## 12. F6 gate evidence

Required:

- original-language evidence retained;
- translation provenance;
- terminology glossary;
- entity aliases and transliteration;
- multilingual query equivalence;
- locale formats;
- regression corpus;
- human review of critical financial, legal and epistemic terms.

## 13. F7 gate evidence

Required:

- typed intent-event records;
- purpose-specific controls;
- user inspection and deletion;
- eligible-cohort denominator;
- unique-user and organisation diversity;
- temporal persistence and decay;
- minimum privacy cohort;
- manipulation simulations;
- no cross-tenant leakage;
- tides create research candidates only;
- 60%-interest example computed reproducibly from unique eligible users.

## 14. F8 gate evidence

Required:

- universe scorecard;
- source-admission records;
- coverage and freshness report;
- buyer-workflow evidence;
- historical reconstruction;
- rights and regulatory review;
- data and model cost estimate;
- multilingual layer terminology;
- complete Globe/Graph/claim/evidence path.

## 15. F9 gate evidence

Required:

- at least 10 independent paying partners;
- billing and entitlement tests;
- support and incident ownership;
- privacy and legal surfaces;
- data/AI cost per paid account;
- repeated consultation evidence;
- first retention measurement.

## 16. F10 gate evidence

Required:

- frozen temporal holdout;
- declared baseline;
- calibration report;
- preserved original forecasts;
- outcome reconciliation;
- subgroup performance;
- drift monitoring;
- demotion test.

## 17. F11 gate evidence

Required:

- tenant-isolation tests;
- private-source rights;
- API authentication and quotas;
- export enforcement;
- enterprise audit log;
- SSO/SCIM evidence when included;
- contractual support and recovery targets.

## 18. F12 gate evidence

Required:

- validated retention;
- sustainable gross margin;
- repeatable acquisition;
- production SLO record;
- disaster-recovery test;
- security programme;
- jurisdiction-selective availability;
- no unresolved material Goal Lock violation.

## 19. Dependency exception

A task MAY begin early for research or prototyping only when:

- it writes no production truth;
- it uses synthetic or explicitly sandboxed data;
- it is labelled non-authoritative;
- it cannot be mistaken for a passed phase;
- it does not create irreversible provider or architecture lock-in.

## 20. Gate ledger

Every gate decision MUST record:

- gate ID and phase;
- date;
- evaluated commit;
- contract versions;
- skill versions;
- evidence links;
- threshold results;
- unresolved conditions;
- disposition;
- next authorised phase or task.
