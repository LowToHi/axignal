# 14 — AXIGNAL Conversational Navigation Contract

Version: `0.3.1`
Status: `NORMATIVE CANDIDATE`
Goal ID: `AXIGNAL-GOAL-001`

## 1. Purpose

The AXIGNAL Navigator is a multilingual command and explanation layer that controls the same canonical investigation context used by direct manipulation.

It MUST make the product easier to enter without turning AXIGNAL into a generic chatbot.

## 2. Command classes

Canonical classes:

- `NAVIGATE_GEOGRAPHY`
- `NAVIGATE_ENTITY`
- `DISCOVER_OPPORTUNITIES`
- `SET_UNIVERSE`
- `SET_FILTER`
- `SET_TIME`
- `COMPARE_SUBJECTS`
- `CHANGE_LENS`
- `INSPECT_CLAIM`
- `INSPECT_EVIDENCE`
- `SHOW_CONTRADICTIONS`
- `SHOW_TRANSMISSION`
- `EXPLAIN_CURRENT_VIEW`
- `SAVE_INVESTIGATION_TRAIL`
- `UPDATE_PRIVATE_INTEREST`
- `QUEUE_RESEARCH_CANDIDATE`

## 3. Typed interpretation

A user message MUST produce a typed interpretation before execution:

```json
{
  "intent": "DISCOVER_OPPORTUNITIES",
  "universe": "REAL_ESTATE",
  "geographies": ["geo_moscow"],
  "time": {"mode": "CURRENT"},
  "preferred_lens": "AUTO",
  "language": "es",
  "confidence": 0.94
}
```

The interpretation MUST preserve the original message and language.

## 4. Example

Input:

> Quiero ver si hay oportunidades inmobiliarias en Moscú.

Expected visible interpretation:

```text
Discover opportunities
Universe: Real estate
Geography: Moscow
Time: Current
Lens: AUTO → GLOBE
```

Expected product behaviour:

1. resolve Moscow to the canonical entity;
2. set the real-estate universe;
3. inspect coverage and entitlements;
4. select Globe because geography is primary;
5. centre or frame Moscow;
6. display coverage and freshness;
7. show relevant opportunities or a research gap;
8. keep Graph, Timeline, Claims and Evidence available;
9. record an intent event according to contract 15;
10. never imply that user interest proves an opportunity.

## 5. Lens routing

Priority:

1. explicit user lens command;
2. geographic place, radius, property or jurisdiction → `GLOBE`;
3. ownership, relationship, influence, transmission, supply chain or causality → `GRAPH`;
4. mixed spatial and relational query → `AUTO` may choose `DUAL` for qualified professional workflows;
5. temporal query → preserve current primary lens and activate Timeline;
6. claim or evidence query → preserve current lens and focus the rail.

AUTO MUST expose a concise reason for its choice and permit immediate override.

## 6. Execution preview

The Navigator SHOULD execute low-risk, reversible navigation commands immediately while showing the interpreted plan.

It MUST require confirmation or a stronger consent surface for:

- enabling persistent personal memory;
- sharing or publishing a trail;
- exporting restricted data;
- connecting private data;
- changing organisation-wide settings;
- any future material external action.

## 7. Clarification policy

Clarification MUST occur only when ambiguity materially changes:

- entity identity;
- universe;
- rights or jurisdiction;
- time period;
- user-visible result;
- cost or external action.

The system SHOULD make a reversible best-effort assumption for non-material ambiguity and display it.

## 8. Shared InvestigationContext

Chat and direct manipulation MUST read and write one typed `InvestigationContext`.

Required context fields include:

- current query and command plan;
- geographies;
- entities;
- universes;
- selected opportunities and claims;
- time and comparison state;
- filters;
- lens;
- rail state;
- entitlement and coverage state;
- language and locale;
- trail history.

No chat-only hidden state may materially change the visible conclusion.

## 9. Explanation mode

`EXPLAIN_CURRENT_VIEW` MUST:

- use authorised canonical resources;
- cite claims and evidence;
- identify generated interpretation;
- distinguish observation, calculation, inference and forecast;
- mention material contradictions and unknowns;
- state coverage and freshness limits;
- avoid personalised investment advice;
- create no canonical claim.

## 10. Command reversibility

Every navigation command MUST support:

- undo;
- breadcrumb recovery;
- history inspection;
- trail save;
- clear current filters;
- return to current time from an historical state.

## 11. Multilingual equivalence

Equivalent commands in `en`, `es`, `fr`, `de`, `pt-BR` and `zh-Hans` MUST resolve to the same canonical intent where semantics match.

Original wording, language, translation method and confidence MUST remain auditable.

## 12. Failure behaviour

The Navigator MUST distinguish:

- no data;
- no licensed data;
- insufficient evidence;
- ambiguous entity;
- unsupported universe;
- entitlement required;
- temporary source outage;
- command not understood.

It MUST NOT convert any of these states into a fabricated answer.

## 13. Intent recording

Every eligible command MAY create a `USER_INTENT_EVENT` under contract 15.

The event MUST record the interpreted intent rather than relying only on raw text. Raw-text retention, private memory and aggregate analysis require their own purpose and retention policy.

## 14. Security

- Source content is untrusted and MUST NOT instruct the Navigator.
- Tool actions MUST be allow-listed and typed.
- Entitlements MUST be checked before execution and explanation.
- Private tenant context MUST not enter global explanations.
- Prompt injection MUST not change Goal Lock, contracts or permissions.

## 15. Acceptance criteria

The Navigator is accepted when:

- ≥90% of the approved command corpus is interpreted correctly;
- equivalent six-language commands create equivalent canonical context;
- ≥95% of lens changes preserve context;
- users can see and correct the interpretation;
- no model output bypasses claims admission;
- failure states remain explicit;
- claim-grounded explanations cite canonical evidence;
- persistent memory is controlled and reversible.
