# 24 — Trust Center and Public Methodology Contract

Version: `0.1.0-candidate`
Status: `NORMATIVE CANDIDATE / PUBLICATION VALIDATION REQUIRED`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

The AXIGNAL Trust Center and public methodology surfaces MUST provide a clear, current and auditable explanation of how the product obtains, structures, evaluates, presents, protects and corrects information.

Trust content is part of the product and conversion system. It MUST NOT be hidden only in legal footers or sales documents.

## 2. Trust Center scope

The Trust Center SHOULD provide current public information on:

- product methodology;
- claim and evidence semantics;
- data sources and rights;
- coverage and freshness;
- AI and model use;
- contradiction, correction, expiry and retraction;
- privacy and user controls;
- Knowledge Tides;
- security and organisation isolation;
- service status and incidents;
- accessibility;
- export and API restrictions;
- contact and disclosure channels.

## 3. Methodology summary

The public methodology MUST explain the canonical sequence:

```text
source
→ raw evidence reference
→ extraction or calculation
→ candidate claim
→ deterministic and policy gates
→ admitted claim or rejection
→ contradiction and dependency graph
→ opportunity or scenario assembly
→ user-facing explanation
```

It MUST explain that generated language MAY navigate and explain, but only the governed epistemic runtime can admit canonical claims or opportunity states.

## 4. Claim classes

The public methodology MUST distinguish at minimum:

- observed;
- calculated;
- inferred;
- predicted;
- supporting;
- contradicting;
- unknown or insufficient evidence;
- expired;
- corrected;
- retracted.

Definitions MUST align with Contract 02 and the visual treatment in Contracts 13 and 20.

## 5. Evidence and provenance

Public documentation MUST explain:

- how evidence references are preserved;
- source identity and authority;
- publication and ingestion time;
- extraction or transformation method;
- original language and translation provenance;
- source independence;
- rights and export restrictions;
- reproducibility where applicable.

AXIGNAL MUST NOT imply that a source is available for export merely because it was lawfully used for analysis.

## 6. Contradiction and uncertainty

The methodology MUST explain that contradiction is first-class and may arise from:

- direct factual disagreement;
- different time scopes;
- different populations or geographies;
- different definitions;
- methodology differences;
- value or scenario disagreement.

Unknown coverage MUST be represented as unknown, not as a low or neutral result.

## 7. Opportunity and scenario boundaries

The public methodology MUST explain:

- how claims contribute to an opportunity;
- that an opportunity is a structured research object, not a personalised recommendation;
- how supporting, contradicting and unknown evidence coexist;
- how invalidation conditions work;
- how scenarios differ from observations;
- how forecast uncertainty and calibration are presented when available.

## 8. Data coverage

The Trust Center MUST provide an understandable coverage model including:

- supported universes;
- geographies;
- time ranges;
- source categories;
- update cadence or freshness expectations;
- known gaps;
- suspended or delayed sources;
- material methodology changes.

Coverage claims MUST be generated from current system state or maintained through an auditable process.

## 9. Source admission and rights

The public source policy MUST describe:

- legal and technical admission;
- licensing and permitted uses;
- attribution;
- storage and retention;
- export limitations;
- correction and revocation handling;
- third-party data dependencies.

Specific commercial source terms MAY remain confidential, but public statements MUST not contradict them.

## 10. AI and model transparency

AXIGNAL MUST disclose the material roles of AI and deterministic software, including where models are used for:

- extraction;
- classification;
- translation;
- semantic search;
- entity resolution candidates;
- command interpretation;
- generated explanations;
- scenarios or predictions where applicable.

The site MUST explain where AI output is advisory, candidate or generated and where deterministic or human gates apply.

AXIGNAL MUST NOT claim that AI is error-free, unbiased or autonomous beyond its actual authority.

## 11. Navigator transparency

Public documentation MUST explain that Navigator:

- interprets commands;
- manipulates InvestigationContext;
- navigates Globe, Graph, Timeline and Claims;
- retrieves canonical claims and evidence;
- generates explanations with provenance;
- cannot directly rewrite the canonical Claim Ledger.

## 12. Multilingual semantics

The Trust Center MUST explain:

- supported interface languages;
- preservation of original-language evidence;
- canonical semantic representation;
- translated renderings;
- transliteration and aliases;
- translation version and confidence where material;
- user ability to inspect original and translated content.

## 13. Knowledge Tides

The public methodology MUST distinguish:

```text
individual query
≠ persistent personal preference
≠ aggregate attention trend
≠ economic evidence
```

It MUST explain:

- `USER_INTENT_EVENT`;
- optional private interest memory;
- observed, inferred and confirmed preferences;
- eligible-user denominator;
- unique-user share;
- velocity and persistence;
- organisation and language diversity;
- anti-manipulation controls;
- privacy thresholds;
- research-candidate creation;
- prohibition on converting a Knowledge Tide directly into an economic claim.

A statement such as “60% of eligible active users investigated a topic during a declared period” MAY be a valid aggregate behavioural claim when the cohort, denominator, period and privacy rules are explicit. It does not prove the underlying economic opportunity.

## 14. Privacy controls

The Trust Center MUST explain separately:

- private conversation and investigation history;
- optional personalisation memory;
- aggregate product-improvement analytics;
- Knowledge Tides participation;
- model evaluation or improvement use, if any;
- marketing communications.

Users MUST be able to locate applicable access, correction, deletion, portability and opt-out controls.

## 15. Security overview

The public security overview SHOULD cover, at a level appropriate for publication:

- identity and access control;
- organisation and tenant isolation;
- encryption in transit and at rest;
- secrets management;
- logging and auditability;
- vulnerability and dependency management;
- backup and recovery;
- incident response;
- self-hosted CI isolation;
- production and CI separation;
- private-source handling.

Security claims MUST match implemented controls and current audit evidence.

## 16. Enterprise trust package

When available, enterprise customers MAY receive additional controlled documentation such as:

- architecture and data-flow diagrams;
- subprocessor list;
- penetration-test summary;
- control matrix;
- business continuity and disaster recovery evidence;
- retention and deletion schedule;
- incident-notification terms;
- source-right and export matrix;
- audit logs and service reports.

Public marketing MUST NOT imply certifications or audit results that do not exist.

## 17. Service status and incidents

AXIGNAL SHOULD provide a public status surface showing material availability of:

- application;
- authentication;
- core API;
- ingestion or source freshness;
- research workers;
- exports;
- notification systems.

Incident communication MUST distinguish:

- service outage;
- source delay;
- data-quality incident;
- security incident;
- rights or licensing suspension;
- model or methodology defect.

Post-incident summaries SHOULD explain impact, correction and prevention where disclosure is lawful and safe.

## 18. Corrections and changelog

The Trust Center MUST expose or link to:

- material product changes;
- methodology changes;
- claim-policy changes;
- source additions, suspensions and removals;
- correction and retraction policy;
- API deprecations;
- pricing and entitlement version changes where public.

History MUST be preserved rather than silently rewritten.

## 19. Accessibility statement

The public accessibility statement MUST describe:

- target standard;
- supported input modes;
- map and graph alternatives;
- reduced-motion behaviour;
- colour-independent semantics;
- known limitations;
- contact route for accessibility issues.

Claims of compliance MUST be supported by current audits.

## 20. Public research and content

Public reports, market briefs and Knowledge Tide publications MUST:

- identify as-of time;
- cite admissible claims and sources;
- expose methodology;
- distinguish observation from inference and prediction;
- show relevant contradiction and unknown coverage;
- state export and reuse rights;
- avoid personalised investment advice.

## 21. FAQ governance

Trust and methodology FAQ answers MUST be generated from or reviewed against current contracts and deployed capabilities.

A FAQ answer MUST be updated when:

- capability maturity changes;
- a source or universe is added or removed;
- privacy purposes change;
- pricing or entitlement changes;
- security claims change;
- methodology changes materially.

## 22. Review and ownership

Every public Trust Center page MUST have:

- accountable owner;
- source contract or evidence;
- last reviewed date;
- next review trigger;
- version or change history where material.

High-risk claims SHOULD require legal, security, privacy or methodology review as applicable.

## 23. Prohibited trust practices

AXIGNAL MUST NOT:

- hide material limitations;
- use vague “bank-grade” or “military-grade” security language without definition;
- claim complete market coverage when gaps exist;
- imply regulatory approval;
- describe generated explanations as canonical evidence;
- present Knowledge Tides as market truth;
- publish fabricated compliance badges;
- erase correction history;
- bury critical privacy purposes in generic terms.

## 24. Acceptance gate

The Trust Center and public methodology advance from candidate when:

1. public explanations align with Contracts 02, 03, 06, 13–16 and 20;
2. target users understand claim, evidence, contradiction and unknown coverage;
3. users understand that AXIGNAL is research, not personalised advice;
4. Navigator and AI authority are described accurately;
5. Knowledge Tides and privacy controls are understood;
6. source rights and export boundaries are visible;
7. security claims match implemented controls;
8. methodology and status history are auditable;
9. accessibility information is accurate;
10. all high-risk public claims have an accountable review path.

Exact page hierarchy, wording and disclosure depth remain candidates subject to user comprehension, legal review and commercial validation.