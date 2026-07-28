# AXIGNAL Prototype Validation Plan

Version: `0.1.0`
Status: `RESEARCH PLAN`
Prototype: `docs/prototypes/globe-opportunity-claims-v0.1.html`

## 1. Research question

Does a map-first investigation shell help qualified multi-asset users discover and audit an opportunity more effectively than a search-first or list-first interface while preserving evidence, contradiction and temporal context?

## 2. Prototype scope

The prototype tests only:

```text
Globe
→ opportunity
→ claims
→ evidence
```

Included:

- synthetic world heat layer;
- semantic country and opportunity selection;
- persistent evidence rail;
- Opportunity, Evidence, Contradiction, Transmission and History lenses;
- timeline and historical state;
- context breadcrumbs;
- bounded AI explanation mock;
- saved investigation trail mock;
- keyboard shortcuts;
- textual country and opportunity alternatives.

Excluded:

- real market data;
- real source rights;
- production visual identity;
- authentication and billing;
- complete mobile design;
- actual generative-model calls;
- investment recommendations;
- performance at production scale.

## 3. Participant profile

Minimum: 5 qualified participants.
Preferred: 7.

Required mix:

- entrepreneurs with investible liquidity;
- sophisticated independent multi-asset users;
- advisers, analysts or research professionals;
- at least one family-office, holding or comparable team participant.

Participants must currently use at least two research, market, business-intelligence or opportunity platforms.

## 4. Method

Moderated remote or in-person usability sessions.

Duration: 45–60 minutes.

Structure:

1. background and current workflow;
2. unassisted first impression;
3. task sequence;
4. comprehension checks;
5. comparison with current tools;
6. willingness-to-pay and recurring-use discussion;
7. debrief.

The facilitator must avoid teaching the interface before the first three tasks.

## 5. Task script

### Task 1 — Discover

“Without using search, find a country where opportunity evidence appears to be strengthening and explain what the heat represents.”

Observe:

- first interaction;
- legend use;
- distinction between coverage and low value;
- time to select a country.

### Task 2 — Select an opportunity

“Choose one opportunity that appears worth investigating. Explain why it is visible.”

Observe:

- marker comprehension;
- use of opportunity summary and dimensions;
- whether the user misreads evidence strength as expected return.

### Task 3 — Inspect support and contradiction

“Find one claim supporting the opportunity and one claim that could weaken it.”

Observe:

- lens use;
- claim-type comprehension;
- ability to find contradiction without prompting.

### Task 4 — Audit evidence

“Open the evidence for one claim and tell us what was observed, when, and what remains an inference.”

Observe:

- source path;
- evidence metadata comprehension;
- confusion between publication, retrieval and event time.

### Task 5 — Preserve context

“Return to the exact opportunity and map state you came from.”

Observe:

- use of breadcrumbs, Escape and browser navigation;
- lost position or filter state;
- confidence that context was restored.

### Task 6 — Trace transmission

“Explore how the underlying event might transmit into the opportunity. Identify which relation is observed and which is inferred.”

Observe:

- graph literacy;
- edge-style comprehension;
- node expansion expectations;
- return to map.

### Task 7 — Historical replay

“Show what the system knew in April and identify what appeared later.”

Observe:

- timeline use;
- future-evidence leakage perception;
- distinction between historical and current interpretation.

### Task 8 — Save

“Save this investigation so that another person could reopen the same reasoning path.”

Observe:

- expectation of what is saved;
- difference between watchlist and investigation trail;
- sharing and collaboration expectations.

## 6. Comprehension questions

Participants must answer in their own words:

1. What does the map heat represent?
2. Does an uncovered country have low opportunity?
3. Is evidence strength a forecast of financial return?
4. Which statement is directly observed?
5. Which statement is inferred or predicted?
6. What contradicts the selected thesis?
7. What date does the current view represent?
8. What would invalidate the opportunity?

## 7. Metrics

### Critical task metrics

- task success;
- time to first selected opportunity;
- time from opportunity to original evidence metadata;
- number of dead ends;
- number of context-loss incidents;
- map-to-graph-to-map restoration success;
- historical reconstruction success;
- claim-type comprehension score;
- heatmap and coverage comprehension score.

### Behavioural signals

- search used before exploration;
- Evidence or Contradiction lens voluntarily opened;
- AI explanation invoked before evidence inspection;
- graph ignored or treated as decoration;
- saved trail understood;
- preference for list/table alternative.

### Attitudinal signals

- perceived authority;
- perceived overload;
- confidence in source traceability;
- perceived differentiation from existing tools;
- likelihood of weekly use;
- price reaction at €99, €299 and €799 tiers.

## 8. Success thresholds

The candidate may progress when:

- at least 80% complete the full opportunity-to-evidence path;
- median opportunity-to-evidence time is under 4 minutes without prior training;
- at least 80% correctly explain the heat metric and missing coverage;
- at least 80% distinguish observation from inference and prediction;
- at least 70% locate contradiction without facilitator instruction;
- no more than one participant loses context irrecoverably;
- most participants judge the map useful rather than decorative;
- no repeated interpretation of evidence strength as expected financial return.

These thresholds are provisional and must be compared with a simpler list-first control.

## 9. Falsification and redesign triggers

Redesign is mandatory when:

- search is consistently required to reach first value;
- participants cannot understand one primary heat layer;
- evidence rail feels secondary or hidden;
- graph relations are misread as causal facts;
- the timeline creates future-evidence confusion;
- users prefer a list-first home for the initial universe;
- information density prevents source auditing;
- users assume AXIGNAL is recommending an investment.

## 10. Iteration protocol

After every two sessions:

1. classify findings by severity and recurrence;
2. fix critical comprehension or context failures;
3. preserve the original prototype version;
4. record the change and hypothesis;
5. retest altered behaviour with a later participant.

Do not redesign visual styling merely from individual taste comments unless they reveal a comprehension, accessibility or trust problem.

## 11. Required outputs

- anonymised session notes;
- task metrics;
- issue log;
- prototype change log;
- video or timestamped evidence where consent permits;
- findings report;
- decision: accept, revise or reject map-first model;
- updated `12-interaction-model.md` and `13-visualisation-grammar.md`;
- new ADR if the interaction architecture changes materially.
