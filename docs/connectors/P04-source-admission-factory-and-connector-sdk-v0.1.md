# P04 — Source Admission Factory and Connector SDK v0.1

**Task:** `AX-GE2E-P04-T01`  
**Status:** `DRAFT_ENGINEERING_FOUNDATION`  
**Stacked baseline:** `AX-GE2E-P03-T01@3b950b1b111a0eb6e3b9b330cc15887db8699f3c`

## 1. Purpose

P04 freezes a repeatable, source-independent connector contract and a source-specific admission process. It separates four concerns that must never collapse into one another:

1. **Transport:** reach and retrieve data under declared network and authentication constraints.
2. **Interpretation:** parse and normalise source-native material without erasing provenance or ambiguity.
3. **Assessment:** evaluate legality, rights, privacy, quality, lifecycle and operational fitness.
4. **Admission:** a distinct human-governed decision that a connector, parser, worker or model cannot perform.

The factory produces candidate artifacts and evidence. It does not create canonical source admission, admitted evidence or canonical claims.

## 2. Dependency boundary

P04 is developed on the exact P03 engineering head. This is permitted as preparatory engineering because P03 has exact-head evidence. It does not imply canonical acceptance.

```text
P01 canonical state                  IN_PROGRESS
P02 canonical activation            false
P03 engineering evidence ready       true
P03 canonical activation            false
P04 engineering branch authorised    true
P04 canonical activation            false
merge to main                        false
```

## 3. Connector package

Every connector package has the same bounded layout:

```text
connector.yaml
source_profile.json
schemas/input.schema.json
schemas/normalized.schema.json
adapter.py
mappings/
fixtures/
tests/
README.md
```

The required adapter interface is:

```text
describe_source
preflight
authenticate
healthcheck
fetch_page
parse_payload
normalize_records
classify_records
emit_candidate_objects
checkpoint
reconcile
revoke
```

Interfaces are versioned. A package cannot silently add authority through a source-specific method.

## 4. Allowed and prohibited outputs

Allowed candidate outputs:

- `CandidateSourceObject`
- `CandidateEvidenceObject`
- `CandidateClaim`
- `ConnectorDiagnostic`
- `Checkpoint`
- `DeletionTombstone`

Prohibited outputs:

- `CanonicalSourceAdmission`
- `AdmittedEvidence`
- `CanonicalClaim`
- `RoleBinding`
- `RightsApproval`
- `ExportApproval`

A connector has zero authority to admit sources, approve rights, alter policy, select tenant scope or elevate a model output.

## 5. Source profile

A source profile is mandatory before any network request. It records:

- source and profile versions;
- owner and jurisdictions;
- exact endpoint origins;
- authentication mode and secret references;
- terms, licence and legal basis snapshots;
- all ten P02/P03 rights dimensions;
- personal-data and data-classification policy;
- allowed content mode;
- retention and attribution;
- rate, retry and cost budgets;
- parser, schema and mapping versions;
- quality and freshness thresholds;
- outage, revocation and deletion semantics;
- kill switch, observability and rollback.

Technical accessibility is never evidence of authority.

## 6. Admission pipeline

| Stage | Output | Required controls |
|---|---|---|
| S01 Profile | Source profile | Legal authority and rights matrix |
| S02 Preflight | Preflight record | Privacy, security, rate and cost |
| S03 Sandbox fetch | Transient payload | Outage and observability |
| S04 Parse and normalise | Candidate records | Provenance, schema, time and taxonomy |
| S05 Quality and reconcile | Quality report | Thresholds and idempotency |
| S06 Candidate handoff | Candidate objects | Revocation, deletion and rollback |
| S07 Human admission | Admission decision | Separate security, rights and product approval |

`INDETERMINATE` is `DENY`. A later stage cannot override an earlier denial or an active kill switch.

## 7. Sixteen gates

1. Legal authority
2. Per-dimension rights matrix
3. Privacy and classification
4. Security preflight
5. Provenance
6. Schema conformance
7. Quality thresholds
8. Temporal semantics
9. Taxonomy mapping
10. Idempotency
11. Rate and cost
12. Outage policy
13. Revocation and deletion
14. Observability
15. Rollback
16. Human admission

Each gate records immutable inputs, policy version, result and reason codes.

## 8. Lifecycle

```text
CANDIDATE
→ SANDBOX
→ VALIDATED
→ PRODUCT_ADMITTED
```

Exceptional transitions lead to `SUSPENDED`, `REVOKED` or `RETIRED`.

Rules:

- `PRODUCT_ADMITTED` is impossible while canonical activation is false.
- `SUSPENDED` and `REVOKED` contribute zero new material.
- `REVOKED` cannot return to an active state.
- Re-entry requires a new source version and source profile.
- Lifecycle changes invalidate caches, checkpoints and queued work.

## 9. Security controls

Network controls include:

- exact origin allowlists;
- redirect revalidation;
- DNS-rebinding defence;
- private-address denial;
- TLS validation;
- payload-size limits;
- archive-expansion limits.

Runtime controls include:

- isolated, non-root process;
- read-only root filesystem;
- minimal egress;
- secret references only;
- CPU, memory and time limits;
- no shell by default.

Source content cannot alter tools, policy, network destinations or admission decisions.

## 10. Rights and privacy

The source profile must specify all ten dimensions independently:

```text
collection
transient_processing
persistent_storage
model_input
derived_calculations
internal_display
customer_display
export
api_redistribution
model_training_or_evaluation
```

A general licence label cannot replace this matrix. Missing, ambiguous, expired, conflicting or revoked rights deny the affected operation.

Raw payload persistence is denied unless both rights and classification explicitly allow it.

## 11. Quality and temporal fidelity

Quality dimensions are completeness, validity, consistency, uniqueness, timeliness, provenance coverage and parse-error rate.

Unknown metrics do not pass. A regression suspends the source rather than silently lowering thresholds.

Source-native identifiers, taxonomies and timestamps remain immutable. Missing timezone, locale, currency or effective date stays unknown rather than being invented.

## 12. Outages and recovery

Outage states are `HEALTHY`, `DEGRADED`, `OUTAGE`, `RECOVERING` and `SUSPENDED`.

Retries are bounded by rate, time and cost. Circuit breakers prevent retry storms. Recovery requires observed health probes and reconciliation. A connector cannot self-declare recovery.

## 13. Revocation and deletion

Triggers include rights revocation, changed terms, licence expiry, security incident, privacy violation, source request, quality failure and operator kill switch.

Required actions:

```text
stop_fetch
stop_materialisation
invalidate_allow_cache
cancel_queued_work
emit_tombstones
propagate_deletion_or_restriction
preserve_audit
require_new_profile_for_reentry
```

Kill-switch evaluation precedes fetch, replay, materialisation and export.

## 14. Reference profiles

Four non-live profiles exercise distinct contract states:

- open metadata sandbox;
- restricted transient-document sandbox;
- suspended outage source;
- revoked source.

They use `example.invalid`, are reference-only and cannot be admitted.

## 15. Adversarial evidence

The conformance suite freezes 32 threats and 32 one-to-one cases covering:

- ambiguous legal authority and rights;
- changed terms and revocation;
- personal-data leakage;
- redirects, SSRF, DNS rebinding and secret exposure;
- archive expansion and payload bounds;
- missing provenance and unpinned parsers;
- schema drift and quality regression;
- temporal fabrication and taxonomy overwrite;
- duplicate replay and pagination loops;
- rate-limit bypass and retry storms;
- stale outage behavior and false recovery;
- kill-switch bypass and failed deletion propagation;
- missing observability and rollback residue;
- connector, model and worker authority escalation;
- cross-tenant credential reuse;
- prohibited export and invalid lifecycle recovery;
- source-key collision and hostile prompt/tool content.

Every case must result in `DENY`, `QUARANTINE` or `SUSPEND` with zero canonical-admission delta.

## 16. Rollback

P04 rollback:

1. starts from the complete P04 head;
2. removes only the eight P04 artifacts;
3. restores the P03 workflow;
4. confirms seven P03 authority artifacts are byte-identical;
5. compares the entire reconstructed tree with the frozen P03 head.

Any unexpected path, content drift or residual file fails the rehearsal.

## 17. Explicit exclusions

P04 does not:

- admit a real source;
- persist real source payloads;
- add credentials or outbound access;
- implement a production connector runtime;
- modify database or UI resources;
- enable public coverage;
- authorise commercial use;
- resolve P01, P02 or P03 canonical gates.

## 18. Canonical acceptance path

Canonical activation requires:

- P03 canonical acceptance or a normative superseding ADR;
- transitive P02 and P01 resolution;
- all schemas, gates and adversarial cases passing;
- network, sandbox, idempotency, outage and revocation evidence;
- byte-exact rollback;
- Human Security Authority approval;
- Human Rights Authority approval;
- Human Product Authority approval.
