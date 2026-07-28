# F2 Reproducible Runtime Spine

Status: `EVIDENCE CANDIDATE / NOT DEPLOYED`

## Scope

This unit closes the remaining F2 deliverable gaps without adding product scope:

- durable scheduler with PostgreSQL leases and transactional outbox;
- content-addressed object-store interface;
- OpenTelemetry trace-context and redaction baseline;
- explicit non-production process topology.

## Scheduler boundary

The scheduler uses `axignal_scheduler_login`. It has execute-only access to scheduler functions and no direct DML on canonical claims, Evidence Objects or admission decisions.

```text
schedule_maintenance_job
→ scheduled_jobs + scheduler_outbox_events in one transaction
→ Valkey queue
→ lease-bound worker
→ succeeded / retry / dead-letter
→ append-only scheduler_events
```

Repeated idempotency keys return the same job only when kind, tenant, payload and attempt policy match. A mismatch fails closed.

## Object storage

Objects are keyed as `{namespace}/sha256/{digest}`. Silent overwrite is prohibited and every read revalidates SHA-256. The local filesystem adapter is the executable baseline; memory and injected S3-compatible adapters preserve the same contract.

## Telemetry

Trace context can be injected into outbox payloads and reattached in workers. API keys, passwords, tokens, prompts, complete documents and raw email addresses are prohibited. The optional collector profile exports only debug traces in development.

## Topology

`infra/runtime/topology.yaml` is the machine-readable authority for process commands, credentials, feature flags, readiness, health and restart policies. `docker compose --profile runtime` starts the scheduler against PostgreSQL and Valkey.

## Rollback

No production data is migrated. Repository rollback is a revert of the F2 closure commit. Database rollback evidence is a snapshot taken before migration `050` and restored into a clean database.
