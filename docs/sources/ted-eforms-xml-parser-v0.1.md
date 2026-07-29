# TED eForms XML Parser Profile v0.1

- Task: `AX-F8-T11`
- Goal ID: `AXIGNAL-GOAL-001`
- Profile: `ted-eforms-cn16@0.1.0`
- Status: `EVIDENCE PROFILE / NOT RUNTIME ENABLED`
- Source state: `TECHNICAL_PROBE / NOT_PRODUCT_ADMITTED`

## Purpose

Move the first lawful universe from a bounded TED Search API projection to one complete, version-pinned XML evidence profile without activating production ingestion or canonical claim authority.

```text
TED Search API discovery
→ official complete XML
→ hardened version gate
→ non-personal structured extraction
→ deterministic Candidate Claims
→ no database persistence
→ no canonical admission
```

## Exact supported profile

| Dimension | Supported value |
|---|---|
| SDK release used as evidence | `1.14.2` |
| `cbc:CustomizationID` | `eforms-sdk-1.14` |
| UBL | `2.3` |
| Document | `ContractNotice` |
| Notice type | `cn-standard` |
| Notice subtype | `16` |

Every other SDK version, document type, notice type or subtype is quarantined as unsupported. The parser must never attempt a best-effort fallback across profiles.

The official eForms SDK uses semantic versioning, UBL 2.3-based schemas and external Schematron validation rules. Its examples directory contains XML notices used by the Publications Office for testing and implementation support. AXIGNAL pins the exact `1.14.2` release and official `cn_24_minimal.xml` example rather than following a mutable branch.

Official references:

- `https://github.com/OP-TED/eForms-SDK/tree/1.14.2`
- `https://raw.githubusercontent.com/OP-TED/eForms-SDK/1.14.2/examples/notices/cn_24_minimal.xml`
- `https://docs.ted.europa.eu/eforms/1.14/schema/index.html`
- `https://docs.ted.europa.eu/eforms/latest/guide/understanding-the-sdk.html`

## Security boundary

The parser:

- uses `defusedxml.ElementTree`;
- caps XML input at `2 MiB`;
- rejects DTD and entity declarations before parsing;
- resolves no external resources;
- validates exact root namespace and document type;
- validates exact SDK customization and UBL versions;
- validates a version-4 UUID notice identifier and a non-zero two-digit notice version;
- validates exact notice type and subtype;
- requires at least one organisation and one contracting-party organisation reference;
- rejects duplicate organisation identifiers and unresolved buyer references.

No lxml recovery mode, browser parser or permissive local-name-only fallback is allowed.

## Extraction boundary

The parser extracts only the accepted ontology subset:

- notice ID, version, issue date/time, notice type/subtype and languages;
- procedure identifier and procedure type;
- organisation IDs, official names, national identifiers, NUTS and countries;
- buyer organisation references;
- project title/description as language-tagged source values;
- contract nature, CPV, NUTS and country;
- estimated value and currency when published;
- lot IDs;
- submission deadline when published;
- EU funding indicator when published.

Optional fields remain absent or `UNKNOWN`. They are never imputed to zero, false or low opportunity.

## Personal-data boundary

Official eForms notices and SDK examples can contain contact telephone numbers, email addresses and other personal or professional contact details.

The parser counts elements with local names such as:

- `Contact`;
- `Telephone`;
- `Telefax`;
- `ElectronicMail`;
- `Person`;
- `FirstName`;
- `FamilyName`.

It does not extract their values. Candidate Claims cannot contain contact predicates or contact values. The official-example evidence artifact records only the aggregate personal-element count to prove the exclusion path was exercised.

## Candidate Claim boundary

Parser output is non-authoritative. It may produce deterministic Candidate Claims for:

- notice type, subtype and issue date;
- procedure identifier and type;
- buyer organisation reference, official name and identifier;
- contract nature;
- CPV code;
- NUTS place of performance;
- stated estimated value and currency;
- lot identifier;
- stated submission deadline;
- stated EU funding indicator.

Every candidate has a deterministic fingerprint over authority class, predicate, subject key, value and source path.

The parser performs:

```text
model calls: 0
canonical writes: 0
human-review authority escalation: 0
```

The policy `ted-procurement-observed@0.1.0` remains disabled. A Candidate Claim produced by this parser is not an admitted procurement fact.

## Evidence handling

The CI workflow downloads the pinned official SDK example transiently. It does not commit or upload the XML.

The uploaded artifact may contain only:

- source release and pinned URL;
- raw XML SHA-256;
- hashed notice identity;
- SDK, UBL and notice profile;
- organisation, buyer, lot and candidate counts;
- personal-field element count;
- explicit zero model calls and canonical writes;
- disabled source, policy, runtime and public-support states.

It must not contain:

- raw XML;
- notice ID;
- organisation names or identifiers;
- titles, descriptions or values;
- telephone or email values;
- any Candidate Claim value.

## Validation layers

1. Synthetic schema-faithful fixture:
   - includes multilingual organisation and project names;
   - includes CPV, NUTS, estimated value, lot, deadline and EU funding;
   - includes synthetic telephone and email values solely to prove exclusion.

2. Negative tests:
   - wrong SDK, UBL, document, type or subtype;
   - DTD or entity declaration;
   - oversized XML;
   - unresolved buyer reference;
   - duplicate organisation ID;
   - optional values removed.

3. Pinned official example:
   - exact OP-TED release `1.14.2`;
   - exact file `examples/notices/cn_24_minimal.xml`;
   - transient parse;
   - deterministic unique candidate fingerprints;
   - personal fields observed but values excluded.

## Known limitations

- no XSD or Schematron validation is performed yet;
- no complete eForms field repository is vendored;
- only ContractNotice subtype 16 is supported;
- change notices, award notices and legacy TED XML are unsupported;
- notice-to-procedure lifecycle reconstruction is not implemented;
- organisation entity resolution is local to one notice;
- no live TED notice XML is persisted or parsed in product runtime;
- no source completeness or country/subtype coverage study has passed.

## Promotion gate

The profile may move from evidence-only toward a sandbox parser only after:

1. tests and pinned official example pass;
2. complete official XML hash and profile evidence are captured;
3. field-level personal-data exclusion is reviewed;
4. XSD and applicable Schematron validation strategy is defined;
5. one live TED notice retrieval path is validated without persisting raw or personal values in CI;
6. parser outputs are independently rederived by the deterministic admission runtime;
7. failure injection proves zero partial canonical state;
8. source remains separately admitted through `AX-F8-T04`.

## Rollback and kill switch

Rollback is immediate because no runtime wiring or database migration exists:

- remove or disable `ted-eforms-cn16@0.1.0`;
- quarantine outputs carrying its parser version;
- preserve raw hashes and audit artifacts;
- return to the Search API-only technical-probe state;
- supersede the parser profile rather than silently broadening it.
