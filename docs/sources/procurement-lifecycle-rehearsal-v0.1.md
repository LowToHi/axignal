# Procurement lifecycle, evidence and dossier rehearsal v0.1

Status: `SANDBOX ONLY / TED TECHNICAL_PROBE / ZERO CANONICAL WRITES`

## Scope

This rehearsal extends the version-pinned TED eForms parser with a bounded procurement lifecycle:

```text
ContractNotice CN16 initial
→ ContractNotice CN16 correction
→ ContractNotice CN16 notice cancellation
→ ContractAwardNotice CAN29 result
→ immutable provisional Evidence Objects
→ deterministic sandbox admission
→ traceable procurement dossier
```

The XML fixtures are synthetic but follow the OP-TED eForms SDK 1.14 structures for changes and competition results. The existing T12 verifier separately exercises a pinned official OP-TED XML notice.

## Critical semantic boundary

A Change notice with reason code `cancel` makes its parent notice null and void. It does **not** prove that the procurement procedure or lot was cancelled. Procedure or lot closure without a winner requires a Result notice with winner-selection status `clos-nw` and the corresponding non-award reason.

The dossier therefore uses `NOTICE_CANCELLED_PROCEDURE_UNRESOLVED` when no result notice exists. It never converts notice cancellation into a procedure-level claim.

## Lineage gates

- exactly one initial competition notice;
- every correction or notice cancellation references the latest notice using exact UUID-version BT-758;
- all notices share one procedure identifier;
- corrections preserve the lot identity set;
- no further Change notice may target a cancelled notice;
- result lots must exist in the competition lineage;
- duplicate notice references, dangling references, cross-procedure links and unknown lots fail closed;
- CN16 remains pinned to `eforms-sdk-1.14`, UBL `2.3`, subtype `16`;
- CAN29 remains pinned to `eforms-sdk-1.14`, UBL `2.3`, subtype `29`.

## Evidence Objects

Each observed Candidate Claim produces one provisional Evidence Object bound to:

- notice UUID-version;
- immutable XML SHA-256;
- Candidate Claim fingerprint;
- predicate, subject and XML source path;
- value hash;
- parser profile.

Evidence Object keys and content hashes are deterministic. Personal contact values are counted for privacy auditing but excluded from Candidate Claims, Evidence Objects, dossiers, logs and CI artifacts.

## Deterministic admission

The current TED context remains blocked:

```text
source_state = TECHNICAL_PROBE
policy_state = DISABLED
kill_switch = ON
outcome = BLOCKED_SOURCE_NOT_PRODUCT_ADMITTED
```

The CI-only sandbox may emit `SANDBOX_ADMISSIBLE_REDERIVED` after two identical parses, valid lineage and exact Evidence Object binding. It cannot emit production `ADMITTED_REDERIVED` and cannot write the Claim Ledger.

## Dossier contract

The dossier status is `TRACEABLE_SANDBOX_REHEARSAL`. It contains:

- notice lifecycle timeline;
- correction and cancellation references;
- result status by lot;
- winner organisation references and published names;
- awarded value and currency;
- tender count;
- contract identifier and award date;
- admission outcomes;
- explicit unknowns and authority warnings.

It is not a bid, eligibility decision, profitability estimate, win prediction, representation service or personalised recommendation.

## Replay and rollback

The lifecycle is reparsed independently. Identical inputs converge to the same Evidence Objects, event hashes and dossier hash. Duplicate execution reuses the existing sandbox batch without appending events. A forced failure after the first decision restores zero batches and zero events.

## Promotion blockers

Production wiring remains prohibited until:

1. TED source rights and field-level privacy review pass;
2. source state reaches `PRODUCT_ADMITTED` independently;
3. official correction, cancellation and result samples are frozen with licence snapshots;
4. country/subtype completeness is measured;
5. no-award and partial-award profiles are added;
6. a PostgreSQL migration and credential-isolated runtime are reviewed;
7. buyer workflow and willingness-to-pay evidence exist;
8. public limitations and outage/revocation behaviour are implemented.

## Rollback

Remove T13 lifecycle code, fixtures and workflow extensions. Keep TED at `TECHNICAL_PROBE`, leave the procurement policy disabled and preserve aggregate hashes and task history for audit.
