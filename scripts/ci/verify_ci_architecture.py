#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github/workflows"
MANIFEST = ROOT / ".github/ci/workflow-scope.json"
ALLOWED_DIRECT = {
    "ci-pr-core.yml",
    "ci-pr-runtime.yml",
    "ci-pr-domain.yml",
    "rc5-security-inventory.yml",
    "procurement-admission-rehearsal.yml",
    "public-landing-resolver-contract.yml",
    "public-landing-ssh-channel-preflight.yml",
    "remote-pilot-operations.yml",
    "world-bank-live-source-smoke.yml",
}


def main() -> int:
    manifest: dict[str, Any] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    registered = {entry["file"] for entry in manifest["workflows"].values()}
    direct: set[str] = set()
    callable_workflows: set[str] = set()

    for path in sorted(WORKFLOWS.glob("*.yml")):
        payload = yaml.load(
            path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
        )
        triggers = payload.get("on", {})
        if isinstance(triggers, dict):
            if "pull_request" in triggers:
                direct.add(path.name)
            if "workflow_call" in triggers:
                callable_workflows.add(path.name)
            push = triggers.get("push")
            if isinstance(push, dict):
                branches = [str(item) for item in (push.get("branches") or [])]
                if "agent/**" in branches:
                    raise SystemExit(f"broad agent push remains in {path.name}")

    unexpected_direct = direct - ALLOWED_DIRECT
    if unexpected_direct:
        raise SystemExit(f"unexpected direct pull_request workflows: {sorted(unexpected_direct)}")
    missing_callable = registered - callable_workflows
    if missing_callable:
        raise SystemExit(f"registered workflows are not reusable: {sorted(missing_callable)}")

    grouped = [item for values in manifest["groups"].values() for item in values]
    if len(grouped) != len(set(grouped)):
        raise SystemExit("workflow appears in more than one gate group")
    if set(grouped) != set(manifest["workflows"]):
        raise SystemExit("group membership and workflow registry differ")
    for group, values in manifest["groups"].items():
        if len(values) > 20:
            raise SystemExit(f"group {group} exceeds the 20-suite design budget")

    print(json.dumps({
        "status": "PASS",
        "schema": manifest["schema"],
        "registered_workflows": len(registered),
        "direct_pull_request_workflows": sorted(direct),
        "group_sizes": {name: len(values) for name, values in manifest["groups"].items()},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
