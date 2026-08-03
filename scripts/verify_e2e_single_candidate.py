#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data/acceptance/e2e/AX-E2E-single-candidate.v1.json"


class VerificationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def is_ancestor(ancestor: str, descendant: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=ROOT,
            check=False,
        ).returncode
        == 0
    )


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def verify_blob(path_value: str, expected: str) -> None:
    path = ROOT / path_value
    require(path.is_file(), f"required file is missing: {path_value}")
    actual = git("hash-object", path_value)
    require(
        actual == expected,
        f"blob drift for {path_value}: {actual} != {expected}",
    )


def main() -> None:
    manifest = load_json(MANIFEST_PATH)
    require(
        manifest.get("schema_version") == "axignal.e2e-single-candidate/v1.0",
        "unexpected schema",
    )
    require(manifest.get("task_id") == "AX-E2E-1", "unexpected task")
    require(manifest.get("scope_frozen") is True, "scope must be frozen")
    require(
        manifest.get("state") == "CANDIDATE_PENDING_EXACT_HEAD_CI",
        "invalid candidate state",
    )
    require(
        manifest.get("required_output") == "AX_E2E_SINGLE_CANDIDATE_PASS",
        "invalid output",
    )

    head = git("rev-parse", "HEAD")
    tree = git("rev-parse", "HEAD^{tree}")
    parent = git("rev-parse", "HEAD^")
    expected_controller = str(manifest["controller_parent_sha"])
    require(
        is_ancestor(expected_controller, head),
        f"controller authority missing from lineage: {expected_controller}",
    )
    require(
        os.environ.get("AXIGNAL_EXACT_SHA", head) == head,
        "checked-out HEAD does not match exact-head authority",
    )

    lineage = manifest["lineage"]
    merge_commit = str(lineage["consolidation_merge_commit"])
    merge_tree = git("rev-parse", f"{merge_commit}^{{tree}}")
    require(
        merge_tree == lineage["consolidation_merge_tree"],
        "consolidation tree drift",
    )
    merge_parents = git("show", "-s", "--format=%P", merge_commit).split()
    require(
        merge_parents == lineage["merge_parents"],
        "consolidation parent order drift",
    )

    for ancestor_key in (
        "dominant_engineering_head",
        "subscriber_workspace_head",
    ):
        ancestor = str(lineage[ancestor_key])
        require(is_ancestor(ancestor, head), f"missing required ancestor: {ancestor}")

    for binding in manifest["required_capability_bindings"]:
        if binding["capability"] == "SUBSCRIBER_WORKSPACE_ENTRY":
            require(
                (ROOT / str(binding["path"])).is_file(),
                "Subscriber Workspace entry is missing",
            )
            continue
        verify_blob(str(binding["path"]), str(binding["blob"]))
    for binding in manifest["frozen_subscriber_bindings"]:
        verify_blob(str(binding["path"]), str(binding["blob"]))

    page_path = ROOT / "apps/web/app/page.tsx"
    entry_path = ROOT / "apps/web/components/subscriber/subscriber-entry.tsx"
    security_path = ROOT / "apps/web/lib/security-boundaries.ts"
    proxy_path = ROOT / "apps/web/proxy.ts"

    page = page_path.read_text(encoding="utf-8")
    entry = entry_path.read_text(encoding="utf-8")
    security = security_path.read_text(encoding="utf-8")
    proxy = proxy_path.read_text(encoding="utf-8")

    require(
        'import { SubscriberEntry }' in page,
        "SubscriberEntry is not the canonical page entry",
    )
    require(
        "return <SubscriberEntry />" in page,
        "canonical page does not render SubscriberEntry",
    )
    require(
        "if (!isAuthenticationRequired())" in entry,
        "main subscriber path does not require authentication",
    )
    require(
        'configurationError("Authentication must be enabled for the main subscriber path.")'
        in entry,
        "authentication failure is not fail-closed",
    )
    require(
        "AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED" in entry,
        "workspace feature flag missing",
    )
    require(
        'configurationError("AXIGNAL_SUBSCRIBER_WORKSPACE_ENABLED is required.")'
        in entry,
        "disabled workspace does not fail closed",
    )
    require(
        "AXIGNAL_SUBSCRIBER_WORKSPACE_FIXTURE_MODE" in entry,
        "fixture boundary missing",
    )
    require(
        'configurationError("Fixture mode is forbidden on the main subscriber path.")'
        in entry,
        "fixture mode is not rejected on the main subscriber path",
    )
    require(
        "<SubscriberLiveWorkspace" in entry,
        "persistent Subscriber Workspace is not rendered",
    )
    require(
        "resolveRequestAuthorityOrigin" in security,
        "proxy authority resolver missing",
    )
    require(
        "resolveRequestAuthorityOrigin" in proxy,
        "proxy does not use authority resolver",
    )

    pricing_path = (
        ROOT
        / "data/commercial/"
        "commercial-runtime-pricing-stripe-runtime.v0.1.json"
    )
    pricing = load_json(pricing_path)
    plans = {
        plan["plan_code"]: plan
        for plan in pricing["pricing_contract"]["plans"]
    }
    require(
        plans["PROFESSIONAL_MONTHLY"]["amount_minor"] == 14900,
        "Professional price drift",
    )
    require(
        plans["TEAM_MONTHLY"]["amount_minor"] == 39900,
        "Team price drift",
    )
    require(
        pricing["engineering_evidence_ready"] is True,
        "P21 engineering evidence missing",
    )

    source_path = (
        ROOT
        / "data/acceptance/source-admission/"
        "AX-LIB-O01-TED-source-admission-closure.v0.2.json"
    )
    source = load_json(source_path)
    require(
        source.get("output") == "O01_TED_SOURCE_ADMISSION_PASS",
        "TED admission output missing",
    )
    require(
        source.get("source_state") == "PRODUCT_ADMITTED",
        "TED is not product admitted",
    )
    require(
        source.get("product_admitted") is True,
        "TED product admission flag missing",
    )
    require(
        source["permanent_boundary"]["public_launch"] == "NO_GO",
        "launch boundary expanded",
    )

    authority = manifest["authority"]
    require(
        authority["superseded_refs_are_lineage_only"] is True,
        "superseded refs remain authoritative",
    )
    require(
        authority["main_activation_authorised"] is False,
        "main activation must remain false",
    )
    require(
        authority["production_activation_authorised"] is False,
        "production activation must remain false",
    )

    result = {
        "schema_version": "axignal.e2e-single-candidate-result/v1.0",
        "task_id": "AX-E2E-1",
        "output": "AX_E2E_SINGLE_CANDIDATE_PASS",
        "status": "PASS",
        "exact_head_sha": head,
        "git_tree_sha": tree,
        "immediate_parent_sha": parent,
        "controller_ancestor_sha": expected_controller,
        "controller_ancestor_present": True,
        "consolidation_merge_commit": merge_commit,
        "consolidation_merge_tree": merge_tree,
        "lineage_present": True,
        "required_capabilities_present": True,
        "subscriber_workspace_integrated": True,
        "main_workspace_fail_closed": True,
        "fixture_mode_forbidden_on_main": True,
        "real_source_present": True,
        "pricing": {
            "professional_monthly_eur": 149,
            "team_monthly_eur": 399,
        },
        "active_release_branch": manifest["active_release_branch"],
        "evaluated_ref": os.environ.get("GITHUB_REF_NAME"),
        "public_launch": "NO_GO",
        "next_transition": "E2E-2_HAPPY_PATH_NO_FIXTURES",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
