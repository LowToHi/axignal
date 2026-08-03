from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/programmes/e2e-2-happy-path-no-fixtures.v1.json"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, *tokens: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"Missing required tokens: {missing}")


def forbid(text: str, *tokens: str) -> None:
    present = [token for token in tokens if token in text]
    if present:
        raise AssertionError(f"Forbidden tokens present: {present}")


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True
    ).strip()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["phase_id"] == "E2E-2"
    assert manifest["closure_output"] == "AX_E2E_HAPPY_PATH_NO_FIXTURES_PASS"
    parent = manifest["parent_authority"]
    assert parent["sha"] == "9bbc60b9cfd46f52eef544eb8f91f4d5ddf21878"
    assert parent["tree"] == "db28fdea036c04980d0b33b77c756288bc9b4066"

    expected_head = os.environ.get("AXIGNAL_EXACT_SHA")
    actual_head = git("rev-parse", "HEAD")
    if expected_head:
        assert actual_head == expected_head, (actual_head, expected_head)
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", parent["sha"], actual_head],
        cwd=ROOT,
        check=False,
    ).returncode == 0

    entry = read("apps/web/components/subscriber/subscriber-entry.tsx")
    require(
        entry,
        "SubscriberLiveWorkspace",
        "BillingBridge",
        "SeatGovernanceBridge",
        "Authentication must be enabled for the main subscriber path.",
        "Fixture mode is forbidden on the main subscriber path.",
    )
    forbid(
        entry,
        "InvestigationShell",
        "SubscriberWorkspaceApp",
        "subscriber-workspace-server",
        "createSubscriberFixture",
    )

    live = read(
        "apps/web/components/subscriber/subscriber-live-workspace.tsx"
    )
    require(
        live,
        'data-e2e-no-fixtures="true"',
        'data-adapter="persistent-real"',
        "/api/subscriber-workspace/live/research-runs",
        "/api/subscriber-workspace/live/workspaces",
        "/api/subscriber-workspace/live/documents",
        "/api/subscriber-workspace/live/exports",
        "Synthetic ResearchRun data is forbidden",
        "Persistent dossier",
        "Append-only audit",
    )
    forbid(
        live,
        "axfx_",
        "fixture-opportunity",
        "fixture-claim",
        "fixture-document",
        "ENGINEERING FIXTURE",
    )

    routes = read(
        "apps/api/src/axignal_api/subscriber_workspace_routes.py"
    )
    require(
        routes,
        'router = APIRouter(prefix="/v1/subscriber-workspace"',
        '_require_capability(identity, "research:create")',
        '_require_capability(identity, "workspace:create")',
        '_require_capability(identity, "document:create")',
        '_require_capability(identity, "export:create")',
        '"ORG_OWNER"',
        '"RESEARCH_OPERATOR"',
        '"PERSISTENT_REAL_ADAPTER"',
        '"fallback_allowed": False',
        "create_ted_run",
        "OutboxPublisher",
    )

    repository = read(
        "apps/api/src/axignal_api/subscriber_workspace_repository.py"
    )
    require(
        repository,
        "research_run_not_completed",
        "persistent_dossier_required",
        "subscriber_workspace_documents",
        "subscriber_workspace_exports",
        "subscriber_workspace_audit_events",
        "sha256",
        "_render_markdown",
    )

    migration = read("infra/postgres/140-subscriber-workspace-live.sql")
    require(
        migration,
        "CREATE TABLE IF NOT EXISTS tenant_private.subscriber_workspaces",
        "CREATE TABLE IF NOT EXISTS tenant_private.subscriber_workspace_documents",
        "CREATE TABLE IF NOT EXISTS tenant_private.subscriber_workspace_exports",
        "CREATE TABLE IF NOT EXISTS tenant_private.subscriber_workspace_audit_events",
        "ENABLE ROW LEVEL SECURITY",
        "FORCE ROW LEVEL SECURITY",
        "tenant_private.current_tenant_id()",
        "subscriber_workspace_audit_immutable",
        "append-only",
        "REVOKE UPDATE, DELETE",
    )

    dockerfile = read("infra/postgres/Dockerfile")
    require(
        dockerfile,
        "140-subscriber-workspace-live.sql",
        "140-axignal-subscriber-workspace.sql",
    )

    compose = read("infra/pilot/compose.yaml")
    require(compose, 'AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED: "true"')
    overlay = read("infra/pilot/compose.billing-test.yaml")
    require(
        overlay,
        'AXIGNAL_SEAT_GOVERNANCE_ENABLED: "true"',
        "AXIGNAL_ORGANISATION_OWNER_SUBJECTS",
        'AXIGNAL_SEAT_GOVERNANCE_UI_ENABLED: "true"',
    )

    browser = read("tests/e2e/subscriber-live-happy-path.spec.ts")
    require(
        browser,
        "registerPasskey",
        "activateProfessional",
        "initialiseOwnerSeat",
        "Start ResearchRun",
        "src_ted_search_api_v3",
        "Persist document",
        "Create Markdown export",
        "EXPORT_CREATED",
        'locator(\'[data-e2e-no-fixtures="true"][data-adapter="persistent-real"]\')',
    )

    persistence = read("scripts/verify_e2e_2_persistence.py")
    require(
        persistence,
        "revoke_identity_session",
        "cross_tenant_visible_rows",
        "audit_append_only",
        "fixture_identifiers",
        "AX_E2E_HAPPY_PATH_NO_FIXTURES_PASS",
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "phase": "E2E-2",
                "exact_head": actual_head,
                "parent": parent["sha"],
                "main_path": "PERSISTENT_REAL_ADAPTER",
                "fixture_fallback": False,
                "closure_output_reserved": manifest["closure_output"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
