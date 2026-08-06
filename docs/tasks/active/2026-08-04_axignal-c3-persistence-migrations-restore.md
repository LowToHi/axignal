# AXIGNAL C3 — Persistence, Migrations and Restore

```text
Contract                 AX-GE2E-CLOSURE-EXECUTION-002
Gate                     C3
Task authority           AX-GE2E-P03-T03
State                    EVIDENCE_READY
Candidate marker         AX_C3_PERSISTENCE_MIGRATIONS_RESTORE_PASS
Previous canonical gate  C2 CLOSED / PASS
Next gate                C4 BLOCKED_BY_C3
Merge                    NOT_AUTHORIZED
Public launch            NO_GO
```

## Material gap

The Subscriber Workspace shell currently proves UI and tenant-bound fixture behaviour, but its server module persists mutations to `.data/subscriber-workspace/*.json`. Its summary also derives `deadlines_next_30_days` from workspace count rather than persisted deadline timestamps. AXENT conversation history remains a browser `localStorage` envelope.

Those surfaces are not accepted as production authority.

## Bounded C3 implementation

C3 adds one ordered PostgreSQL migration:

```text
infra/postgres/140-subscriber-persistent-authority.sql
```

It defines the native authority consumed by the later C4 adapter:

```text
subscriber_workspaces
subscriber_requirements
subscriber_evidence
subscriber_amendments
subscriber_audit_events
axent_conversations
axent_messages
axent_legal_holds
axent_audit_events
c3_terminal_purge_receipts
```

The existing UI is not rewired in C3. C4 retains authority for the real Subscriber Workspace and AXENT product adapter, Navigator and worker journey.

## Workspace invariants

```text
blocking requirement unresolved
→ readiness false

blocking requirement MET without current VERIFIED evidence
→ preparation denied

unacknowledged amendment
→ preparation denied

same subject prepares and approves
→ approval denied

independent approval at current revision
→ submission_ready true

requirement/evidence/amendment mutation after preparation
→ package invalidated
→ revision advanced
→ typed append-only event emitted
```

`deadlines_next_30_days` uses the deterministic half-open interval:

```text
[as_of, as_of + 30 days)
```

Past deadlines and the exact upper boundary are excluded.

## AXENT authority

AXENT messages are persisted only as AES-256 `pgcrypto` ciphertext plus a SHA-256 content digest. Application roles have no direct table access. Export is an explicit tenant-scoped function that decrypts with the caller-provided server key and appends an audit event.

Retention classes:

```text
EPHEMERAL_30D
STANDARD_90D
```

Legal hold blocks both conversation purge and terminal tenant purge. Release permits the governed deletion path. Terminal tenant deletion cascades C3 objects through the existing workspace lifecycle and creates a separate append-only C3 object-count receipt in addition to the existing global deletion tombstone.

## Exact rehearsal

```text
fresh database
→ apply every ordered migration including 140
→ seed two tenant lifecycles
→ prove evidence insufficiency failure
→ prove amendment acknowledgement failure
→ prove separation-of-duties failure
→ approve at current revision
→ mutate and invalidate approval
→ verify typed append-only audit
→ verify deterministic deadline window
→ deny cross-tenant workspace access
→ encrypt AXENT messages
→ export only through tenant authority
→ deny cross-tenant AXENT export
→ place legal hold
→ deny conversation and tenant purge
→ dump database snapshot
→ restore into a second database
→ verify workspace, events, ciphertext, export and hold
→ release hold
→ purge conversation
→ execute terminal workspace deletion
→ verify C3 purge receipt and deletion tombstone
```

The rehearsal performs no external or model calls and publishes only a redacted structured marker.

## Current disposition

```text
Migration source                 PRESENT
Fresh migration registration    PRESENT
Workspace invariant rehearsal   PRESENT
AXENT retention rehearsal       PRESENT
Snapshot restore rehearsal      PRESENT
Full migration CI               PASS / run 30961773636
Exact-head root matrix           PASS / candidate 64c00df0ac2cb57448e54284b1bd0b333690b2ae
C3 marker                        ATTESTATION_PENDING / NOT_EFFECTIVE
C4                               BLOCKED_PENDING_ATTESTATION_HEAD
```

Candidate head `64c00df0ac2cb57448e54284b1bd0b333690b2ae` completed all five root authorities successfully. The marker remains ineffective until a later closure-attestation head also completes the full matrix.
