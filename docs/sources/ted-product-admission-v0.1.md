# TED Product Admission Record v0.1

Status: `PRODUCT_ADMITTED / BOUNDED NON-PERSONAL PROFILE / RUNTIME DEFAULT DISABLED`

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
- claim worldwide procurement coverage.

## Attribution

Every customer-visible dossier produced by this profile must include:

> Source: TED (Tenders Electronic Daily), Supplement to the Official Journal of the European Union. AXIGNAL selected and normalised the allowlisted fields; changes are indicated in the dossier methodology.

## Technical enforcement

The source and workflow have independent controls:

```text
source registry admission and kill switch
→ AXIGNAL_TED_PROCUREMENT_ENABLED
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

The runtime remains disabled unless `AXIGNAL_TED_PROCUREMENT_ENABLED=true`. Trial, billing, global-source expansion and general-purpose AI remain disabled.

## Rollback

Rollback disables the TED workflow flag and/or source kill switch, blocks new runs fail-closed and preserves prior evidence, decisions and audit history. Canonical history is not deleted or rewritten.
