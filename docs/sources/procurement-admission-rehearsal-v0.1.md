# Procurement Admission Rehearsal v0.1

- Task: `AX-F8-T12`
- Profile: `ted-procurement-admission-rehearsal@0.1.0`
- Status: `SANDBOX REHEARSAL / NOT CANONICAL RUNTIME`
- Source: `src_ted_search_api_v3`
- Parser: `ted-eforms-cn16@0.1.0`
- Policy: `ted-procurement-observed@0.1.0`

## Purpose

Prove deterministic procurement policy behaviour over frozen official XML without bypassing the still-blocked source-admission gate.

```text
frozen version-pinned XML
→ parser produces Candidate Claims
→ independent parser invocation rederives claims
→ exact fingerprint comparison
→ sandbox policy decision
→ append-only transactional rehearsal history
→ replay and forced rollback
→ zero canonical writes
```

## Two contexts

### Actual TED context

```text
source_state = TECHNICAL_PROBE
policy_state = DISABLED_PENDING_PRODUCT_ADMISSION_AND_XML_PARSER
rights_valid_for_product = false
kill_switch_enabled = true
```

Every candidate must return:

```text
BLOCKED_SOURCE_NOT_PRODUCT_ADMITTED
```

No batch, decision or event is persisted even in the CI-only store.

### Explicit sandbox context

```text
source_state = SANDBOX
policy_state = SANDBOX_REHEARSAL
rights_valid_for_sandbox = true
kill_switch_enabled = false
sandbox_authorised = true
```

The strongest possible positive result is:

```text
SANDBOX_ADMISSIBLE_REDERIVED
```

The sandbox must never emit `ADMITTED_REDERIVED` or write the canonical Claim Ledger.

## Deterministic gates

A Candidate Claim can become sandbox-admissible only when:

1. its parser profile is exactly `ted-eforms-cn16@0.1.0`;
2. its producer is `DETERMINISTIC_XML_PARSER`;
3. its predicate is in the bounded auto-admission profile;
4. its predicate contains no personal-data token;
5. its predicate is not explicitly prohibited;
6. an independent reparse of the same XML produces the exact same fingerprint;
7. the sandbox context is explicitly authorised.

Claims outside the bounded predicate set require human review. Model-produced claims remain proposal-only. Tampered values are rejected by fingerprint mismatch. Personal or prohibited predicates are rejected. Parser-profile drift is quarantined.

## Transaction contract

The rehearsal store is intentionally in-memory and CI-only. It is not a second canonical ledger.

For an authorised sandbox batch it appends:

1. `PROCUREMENT_REHEARSAL_BATCH_STARTED`;
2. one `PROCUREMENT_REHEARSAL_DECISION_RECORDED` per candidate;
3. `PROCUREMENT_REHEARSAL_BATCH_COMMITTED`.

Event sequence numbers are contiguous and payloads are represented only by hashes. Replay uses an idempotency key over policy, parser, raw hash, sorted Candidate Claim fingerprints and context. A replay returns the existing batch without appending events.

A forced failpoint after the first decision must restore the exact prior state:

```text
batches = 0
decisions = 0
events = 0
canonical writes = 0
```

## Authority boundary

| Actor | Authority |
|---|---|
| XML parser | Candidate Claims only |
| Local or external model | Proposal only |
| Human reviewer | Context only; no canonical writes |
| CI rehearsal store | Sandbox decision evidence only |
| Existing production admission runtime | Not activated for procurement |
| Canonical Claim Ledger | Zero procurement writes |

## Privacy boundary

The rehearsal consumes Candidate Claims already stripped of personal contact values. It additionally rejects predicates containing contact, email, phone, telephone, person, first-name or family-name semantics. Evidence artifacts contain only raw hashes, aggregate outcome counts and state flags.

## Promotion gate

Production procurement admission remains blocked until:

- TED reaches `PRODUCT_ADMITTED` through `AX-F8-T04`;
- rights for persistence, customer display, attribution and derived claims are approved;
- the procurement policy is enabled independently;
- the PostgreSQL admission package and dedicated credential boundary are implemented;
- the existing admission runtime executes atomic canonical writes and rollback under that credential;
- correction, cancellation, expiry and retraction propagation pass;
- personal-data exclusion is proven in persistence and telemetry.

## Rollback

Remove the rehearsal module and workflow. No migration, source state, product runtime or canonical data changes are required. The system returns to the parser-only evidence state.
