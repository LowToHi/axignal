# ADR-012 — European Public Procurement as the First Commercial Universe

- Status: `ACCEPTED / IMPLEMENTATION NOT ADMITTED`
- Date: `2026-07-29`
- Goal ID: `AXIGNAL-GOAL-001`
- Decision ID: `AX-F8-UNIVERSE-001`

## Context

AXIGNAL now has a governed executable vertical slice, a deployed public landing and a reusable epistemic runtime, but it does not yet have a commercially supported opportunity universe.

ADR-004 requires each universe to be selected and admitted independently. Contracts 00, 01, 03, 08 and 11 require the first wedge to combine buyer value, lawful data, machine access, deterministic claim potential, product fit, acceptable operating cost and a non-advisory regulatory boundary.

Seven candidate universes were evaluated through the versioned scorecard at:

`data/universes/first-lawful-universe-scorecard.v0.1.json`

## Decision

AXIGNAL selects **European Public Procurement Intelligence** as the sole first commercial implementation wedge.

The first source family to enter legal review and technical probing is **TED — Tenders Electronic Daily**.

The initial commercial workflow is:

```text
public-demand question
→ geography, CPV sector, buyer, value and deadline interpretation
→ governed ResearchRun
→ admitted notices and awards
→ observed and reproducibly calculated claims
→ deterministic admission or bounded escalation
→ Globe, Graph, Timeline and evidence-led dossier
→ saved and monitored investigation trail
```

The decision authorises only:

- `AX-F8-T03` — procurement ontology;
- `AX-F8-T04` — minimum lawful source admission, beginning with TED;
- `AX-F8-T05` — connector and quality monitoring after source admission;
- `AX-F8-T06` — procurement claim policies.

## Selection basis

European procurement ranked first at `96/100` and passed every knockout threshold.

The main advantages are:

- high-value recurring professional decisions;
- official machine-readable Search API and bulk-reuse path;
- official eProcurement Ontology;
- geographic, relational and temporal structure;
- observed facts suitable for deterministic admission;
- public-data-compatible initial cost structure;
- observation and research value without advice, execution or custody.

## Authority boundary

This ADR does **not**:

- set TED to `PRODUCT_ADMITTED`;
- market European procurement as supported;
- authorise live ingestion or national-portal scraping;
- infer supplier suitability, profitability or win probability;
- authorise bid submission or procurement representation;
- activate billing, entitlements or public API access;
- permit models or reviewers to write canonical procurement claims.

The runtime default remains `DISABLED` and the public-marketing state remains `PROHIBITED_UNTIL_UNIVERSE_GATE`.

## Rights and privacy boundary

Commission Decision 2011/833/EU provides a general reuse framework for Commission documents, including commercial reuse, subject to attribution, non-distortion, personal-data rules and third-party-rights exceptions.

That general framework is not a substitute for a source-specific TED admission record. Before any live ingestion, AXIGNAL must establish exact rights for:

- collection;
- transient processing;
- persistent storage;
- model input;
- derived claims;
- internal and customer display;
- export and API redistribution;
- attribution;
- retention;
- personal contact fields.

Natural-person contact fields must be excluded from canonical opportunity claims and minimised by default.

## Consequences

### Positive

- AXIGNAL receives a concrete first universe without abandoning its global architecture.
- Existing Navigator, ResearchRun, claim, evidence and admission infrastructure can be reused.
- Globe, Graph and Timeline gain a naturally aligned real-world domain.
- TED's structured notices and ontology reduce initial schema invention.
- Macro and trade data can later become context layers rather than competing wedges.

### Negative

- Procurement data quality and completeness vary by notice, form, jurisdiction and period.
- Product value may collapse into commodity alerts unless AXIGNAL proves evidence, history and relational differentiation.
- Some notices contain personal contact information requiring strict minimisation.
- National and below-threshold procurement coverage remains incomplete without separately admitted sources.
- Buyer willingness to pay is unvalidated.

## Deferred alternatives

- **European trade and supply-chain shifts** — runner-up and future context layer.
- **European grants and non-dilutive capital** — first adjacent universe after access fragmentation is resolved.
- **EU regulation-created demand** — deferred until inference and jurisdiction policies exist.
- **Public-company disclosures** — deferred due to investment-information sensitivity and weaker differentiation.
- **Macro and sovereign context** — mandatory context, not a standalone wedge.
- **European real assets and property** — rejected for the initial wedge due to rights and access fragmentation.

## Validation and falsification

The decision must be superseded or rejected if:

- source-specific rights fail;
- the bounded workflow cannot be supported from admitted official data;
- buyers value only generic alerts and reject evidence-led investigation;
- privacy minimisation removes essential functionality;
- operating cost is incompatible with target gross margin;
- product value requires unauthorised scraping;
- AXIGNAL cannot preserve observation-not-advice and bid-execution boundaries.

## Rollback

No runtime or data migration is introduced by this decision. Rollback consists of:

1. superseding ADR-012;
2. setting `AX-F8-UNIVERSE-001` to `REJECTED` or `SUPERSEDED`;
3. preserving the scorecard and evidence as audit history;
4. keeping all source, runtime and public-marketing switches disabled;
5. rerunning `AX-F8-T01` and `AX-F8-T02` with a new versioned scorecard.
