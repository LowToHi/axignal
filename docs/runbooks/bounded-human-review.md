# Bounded Human Review v0.1

Status: `BOUNDED / TENANT-SCOPED / NON-CANONICAL / FAIL-CLOSED`

## Purpose

Resolve `HUMAN_REVIEW_REQUIRED` and `CONTESTED` decisions without allowing a reviewer to rewrite deterministic admission decisions, mutate Evidence Objects or insert into the Claim Ledger.

## Authority chain

```text
model → proposal only
deterministic runtime → admission decision
human reviewer → contextual resolution only
Claim Ledger → unchanged unless a later deterministic run admits a claim
```

## Runtime identity

The API uses only:

```dotenv
AXIGNAL_HUMAN_REVIEW_DATABASE_URL
AXIGNAL_HUMAN_REVIEWER_SUBJECTS
```

The reviewer login can execute three tenant-filtered PostgreSQL functions:

- `tenant_private.list_human_review_cases(uuid)`;
- `tenant_private.human_review_case_bundle(uuid)`;
- `tenant_private.resolve_human_review_case(...)`.

It has no direct DML privilege on review tables, canonical claims, claim-state events, admission decisions, sources, source objects, document fragments or Evidence Objects.

## Actions

- `ACCEPT_AS_CONTEXT` — add non-canonical context to the dossier.
- `REJECT_PROPOSAL` — record rejection without changing the deterministic decision.
- `CONFIRM_CONTESTED` — preserve the proposal as contested.
- `REQUEST_MORE_EVIDENCE` — keep the case open and append an evidence request.
- `RETURN_TO_DETERMINISTIC_REVIEW` — require a new evidence and handoff cycle.
- `MARK_OUT_OF_SCOPE` — close the proposal outside the governed profile.

No action creates a canonical claim.

## Non-bypassable gates

`ACCEPT_AS_CONTEXT` and `RETURN_TO_DETERMINISTIC_REVIEW` require the original source, package, rights, raw-object, producer-separation and policy-version gates to remain valid. The current source must remain admitted, reusable and have its kill switch disabled. Evidence-to-fragment bindings are rechecked from persisted records.

## Event history

Each case begins with `CASE_OPENED`. First action records `CASE_ASSIGNED` and `REVIEW_STARTED`. Terminal actions append `RESOLUTION_RECORDED` and `CASE_CLOSED`. Event updates and deletes are blocked by trigger.

## Rollback

Disable `AXIGNAL_HUMAN_REVIEW_UI_ENABLED` to remove the UI surface. Remove `AXIGNAL_HUMAN_REVIEW_DATABASE_URL` or the reviewer allowlist to fail the API closed. Preserve cases and events for audit. Database rollback is the tested pre-040 snapshot restore; no production down migration is authorised.
