# AX-F9-T15 — Trial Retention, Suspension and Deletion Boundary

Status: `CANDIDATE / DISABLED BY DEFAULT / CUSTOMER RETENTION POLICY UNAPPROVED`

## Implemented transition

```text
trial workspace
→ expiry to READ_ONLY
→ explicit deletion request
→ versioned retention deadline
→ isolated purge queue and lease
→ terminal purge
→ pseudonymous append-only tombstone
→ restore-time tombstone reapplication
```

## Independent kill switches

- `AXIGNAL_DELETION_REQUESTS_ENABLED=false` blocks new deletion requests.
- `AXIGNAL_PURGE_WORKER_ENABLED=false` blocks queueing, claiming and purging.
- `AXIGNAL_OPERATOR_SUSPENSION_ENABLED=false` blocks administrative suspension.
- `AXIGNAL_TRIAL_RETENTION_SECONDS=0` means no customer-facing retention duration has been approved.
- Trial, end-user AI, TED, commercial and payment switches remain independent.

## Authority boundary

- Tenant identity for deletion requests comes only from the signed server assertion.
- Request bodies reject unknown fields and never accept `tenant_id`.
- `axignal_app` can request deletion and read its own lifecycle, but cannot mutate lifecycle tables or execute purge functions.
- `axignal_operator` can suspend a workspace but cannot purge it.
- `axignal_retention_worker` can queue, claim, purge and reapply tombstones but has no model, source-admission, canonical-claim, billing or pricing authority.
- Destructive functions are `SECURITY DEFINER`, have a fixed `search_path`, are revoked from `PUBLIC`, and are callable only by their declared roles.

## Lifecycle invariants

- Entitlement expiry persists `READ_ONLY` before authorization fails closed.
- Deletion requests are explicit and idempotent.
- A deletion request releases open token reservations and suspends the entitlement.
- New ResearchRuns and AI reservations are blocked outside `ACTIVE`.
- A purge requires a worker lease and cannot be invoked by the application role.
- Terminally deleted tenants cannot reactivate an entitlement or create a ResearchRun.
- Another tenant's workspace is not modified by request, purge or restore reapplication.

## Purge scope

The terminal purge removes tenant-private:

- ResearchRuns and dossiers;
- research/evidence links;
- knowledge items and intent events;
- human-review cases and events;
- tenant-scoped proposal/admission failures and handoffs;
- tenant-scoped outbox and scheduled jobs;
- entitlements, reservations and entitlement events;
- workspace lifecycle and lifecycle events.

Global admitted Sources, Evidence Objects, Candidate Claims and canonical Claims are not deleted merely because one tenant referenced them.

Evaluation-study records are governed by their separate consent and research-retention contract and are not silently collapsed into workspace deletion.

## Tombstone and restore barrier

The terminal record contains only:

- deletion identifier;
- SHA-256 tenant UUID hash;
- policy version;
- request and completion timestamps;
- aggregate purged-object counts;
- verification digest.

It contains no name, email, organisation label, prompt, document, dossier, evidence text or source payload.

A restored tenant-private row whose tenant hash matches a terminal tombstone is removed again before the workspace can become operational. The tombstone must therefore be exported to an operational deletion ledger that is not overwritten by an application-data restore before production acceptance.

## Explicit non-claims

This cut does not approve a legal retention duration, customer-facing terms, backup-destruction schedule, Stripe lifecycle, public trial, paid conversion, pricing, gross margin or commercial availability. Those remain gates for `AX-F9-T15`.
