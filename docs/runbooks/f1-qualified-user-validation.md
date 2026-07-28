# F1 Qualified-User Validation Runbook

## Enable locally

```dotenv
AXIGNAL_VALIDATION_ENABLED=true
AXIGNAL_VALIDATION_UI_ENABLED=true
AXIGNAL_VALIDATION_DATABASE_URL=postgresql://axignal_validation_runtime_login:axignal_validation_runtime@localhost:5432/axignal
AXIGNAL_VALIDATION_PARTICIPANT_SALT=<at-least-32-random-bytes>
AXIGNAL_AUTH_REQUIRED=true
```

Start PostgreSQL and the web/API processes, then open `/validation` with an authenticated test identity.

## Authority boundary

The validation runtime can execute only the `evaluation.*` functions granted to `axignal_validation_runtime`. It has no direct table access and no DML authority on canonical claims, Evidence Objects, admission decisions or ResearchRuns.

## Privacy boundary

The participant identifier is `HMAC-SHA256(tenant_id | subject)` using a validation-only salt. The evaluation schema contains no email, name or phone columns. Do not add recordings, free-form demographic data or exported identity assertions to validation events.

## Frozen tasks

Task answer keys remain inside `evaluation.validation_tasks.task_payload`. `validation_session_bundle` removes answer-key fields before returning participant content. Both conditions receive the same content hash and public payload.

## Campaign procedure

1. freeze task version and thresholds;
2. verify technical CI and snapshot restore;
3. recruit qualified users outside the application;
4. assign each participant only through `start_validation_session`;
5. do not reveal or alter condition assignment;
6. export aggregate metrics only;
7. inspect invalid or abandoned sessions separately;
8. declare F1 `PASSED`, `FAILED` or still `GATE_REVIEW` without rewriting raw events.

## Rollback

Disable `AXIGNAL_VALIDATION_ENABLED` and `AXIGNAL_VALIDATION_UI_ENABLED`. Preserve evaluation tables as append-only evidence. Restore the pre-060 snapshot only in a disposable or formally approved rollback environment.
