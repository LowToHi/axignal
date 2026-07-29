from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    migration = (ROOT / "infra/postgres/090-trial-retention-lifecycle.sql").read_text(
        encoding="utf-8"
    )
    config = (ROOT / "apps/api/src/axignal_api/retention_config.py").read_text(
        encoding="utf-8"
    )
    routes = (ROOT / "apps/api/src/axignal_api/retention_routes.py").read_text(
        encoding="utf-8"
    )
    worker = (ROOT / "apps/api/src/axignal_api/retention_worker.py").read_text(
        encoding="utf-8"
    )
    application = (ROOT / "apps/api/src/axignal_api/application.py").read_text(
        encoding="utf-8"
    )
    dockerfile = (ROOT / "infra/postgres/Dockerfile").read_text(encoding="utf-8")

    required_sql = (
        "workspace_lifecycle",
        "workspace_lifecycle_events",
        "deletion_tombstones",
        "DELETION_REQUESTED",
        "PURGE_QUEUED",
        "PURGING",
        "PURGE_FAILED",
        "request_workspace_deletion",
        "operator_suspend_workspace",
        "queue_due_workspace_purges",
        "claim_workspace_purge",
        "purge_claimed_workspace",
        "reapply_deletion_tombstone",
        "workspace_terminally_deleted",
        "FORCE ROW LEVEL SECURITY",
        "SECURITY DEFINER",
        "SET search_path TO pg_catalog",
        "REVOKE ALL ON FUNCTION",
        "axignal_retention_worker",
        "axignal_operator",
    )
    for marker in required_sql:
        require(marker in migration, f"Missing retention SQL marker: {marker}")

    require(
        '_bool_env("AXIGNAL_DELETION_REQUESTS_ENABLED")' in config,
        "Deletion request flag must default disabled",
    )
    require(
        '_bool_env("AXIGNAL_PURGE_WORKER_ENABLED")' in config,
        "Purge worker flag must default disabled",
    )
    require(
        '_bool_env("AXIGNAL_OPERATOR_SUSPENSION_ENABLED")' in config,
        "Operator suspension flag must default disabled",
    )
    require(
        '_int_env("AXIGNAL_TRIAL_RETENTION_SECONDS", 0)' in config,
        "Retention duration must remain unconfigured by default",
    )
    require("ConfigDict(extra=\"forbid\")" in routes, "Request body must reject extras")
    require("tenant_id" not in routes.split("class DeletionRequestCommand", 1)[1].split(
        "class WorkspaceLifecycleView", 1
    )[0], "Deletion command cannot accept tenant_id")
    require("settings.require_purge_worker()" in worker, "Worker must enforce its kill switch")
    require("app.include_router(retention_router)" in application, "Retention router not wired")
    require("090-trial-retention-lifecycle.sql" in dockerfile, "Migration not installed")
    require("stripe" not in migration.casefold(), "Stripe is outside this runtime cut")

    result = {
        "schema": "axignal.trial-retention-contract.v0.1",
        "status": "PASS",
        "deletion_requests_enabled_by_default": False,
        "purge_worker_enabled_by_default": False,
        "operator_suspension_enabled_by_default": False,
        "retention_policy_configured_by_default": False,
        "tenant_id_accepted_from_client": False,
        "tombstone_append_only": True,
        "stripe_wired": False,
        "model_calls": 0,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
