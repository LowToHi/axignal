# TED Product Admission Record v0.1

Status: `PRODUCT_ADMITTED / BOUNDED NON-PERSONAL PROFILE / PRIVATE PILOT ENABLED / RUNTIME DEFAULT DISABLED`

Task: `AX-F8-T14`

Source: `src_ted_search_api_v3`

Profile: `ted-search-non-personal-projection@0.1.0`

## Decision

AXIGNAL admits one narrow TED Search API profile for product processing. This decision does not admit arbitrary TED queries, arbitrary fields, complete notice redistribution, national procurement portals or the worldwide procurement catalogue.

The admitted profile is limited to one fixed query, one page, at most three active notices and these fields:

- `publication-number`;
- `notice-title`;
- `buyer-name`;
- `notice-type`.

No contact, email, telephone or natural-person field may be requested, persisted, displayed, exported or used for a canonical Claim.

## Activation decision

The profile is enabled only in the authenticated private-pilot topology for verified organisations. It remains disabled by default in generic environments and is not public general availability.

The private pilot activates TED with three independent flags and controls:

```text
AXIGNAL_TED_PROCUREMENT_ENABLED=true
AXIGNAL_TED_LIVE_SOURCES_ENABLED=true
AXIGNAL_TED_PROCUREMENT_UI_ENABLED=true
```

The global `AXIGNAL_LIVE_SOURCES_ENABLED` flag remains `false`. Only the research worker joins the dedicated `ted-egress` network; API, web, PostgreSQL and Valkey remain without direct source egress.

## Official rights basis

The TED legal notice permits commercial and non-commercial reuse of procurement notices published in the Supplement to the Official Journal, subject to acknowledgement of the source, indication of changes, non-distortion, and any additional rights attached to identifiable persons or third-party material. Protected logos and emblems are excluded.

The official TED Search API documentation expressly supports reuse, analysis and integration into added-value services. Commission Decision 2011/833/EU supplies the general Commission-document reuse conditions, including attribution and indication of modifications.

This record deliberately adopts a narrower product boundary than the maximum theoretical reuse boundary.

## Permitted product operations

AXIGNAL may:

1. retrieve the fixed non-personal projection from the official HTTPS API;
2. persist that allowlisted projection and its hashes;
3. deterministically create Evidence Objects and Candidate Claims;
4. admit exact observed fields through the deterministic admission runtime;
5. show those fields inside the authenticated tenant's InvestigationContext;
6. assemble and export an evidence-linked dossier containing the bounded projection and required attribution.

## Prohibited operations

AXIGNAL must not:

- expose an arbitrary TED query interface;
- retain unrequested response fields;
- collect or use contact data;
- redistribute the TED API or bulk source dataset;
- use TED material for model training under this profile;
- display official EU or TED logos as reusable content;
- admit supplier suitability, win probability, profitability, legal conclusions or bid recommendations;
- submit a bid or represent the user;
- claim worldwide procurement coverage;
- treat private-pilot acceptance as proof of buyer demand, willingness to pay, billing readiness or public launch readiness.

## Attribution

Every customer-visible dossier produced by this profile must include:

> Source: TED (Tenders Electronic Daily), Supplement to the Official Journal of the European Union. AXIGNAL selected and normalised the allowlisted fields; changes are indicated in the dossier methodology.

## Technical enforcement

The source and workflow have independent controls:

```text
source registry admission and kill switch
→ AXIGNAL_TED_PROCUREMENT_ENABLED
→ AXIGNAL_TED_LIVE_SOURCES_ENABLED
→ worker-exclusive ted-egress network
→ authenticated identity
→ server-resolved tenant
→ fixed query and field allowlist
→ bounded retrieval
→ projection sanitisation
→ persistent ResearchRun
→ deterministic evidence and candidate construction
→ deterministic admission
→ attributed dossier
→ InvestigationContext polling
```

The runtime remains disabled unless `AXIGNAL_TED_PROCUREMENT_ENABLED=true` and `AXIGNAL_TED_LIVE_SOURCES_ENABLED=true`. Trial, billing, global-source expansion, public general availability and general-purpose AI remain disabled.

## Separation from commercial validation

Qualified B2G buyer comprehension, willingness to pay, paid Design Partner evidence, trial entitlements and billing are governed by `AX-F9-T15`. They are not claimed as evidence for the source/runtime admission completed by `AX-F8-T14`.

## Rollback

Rollback may disable the TED workflow flag, the dedicated live-source flag and/or the source registry kill switch. Each path blocks new runs fail-closed and preserves prior evidence, decisions and audit history. The tested source kill switch produces zero new Evidence Objects, Candidate Claims, canonical Claims or dossiers. Canonical history is not deleted or rewritten.
