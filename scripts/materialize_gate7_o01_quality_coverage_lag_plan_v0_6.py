from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from verify_gate7_o01_v0_6_execution_contract import materialize as materialize_contract

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "data/acceptance/approvals/"
    "AX-LIB-O01-campaign-authority-manifest.v0.6.json"
)
MANIFEST_SHA = "sha256:04356ad097ddb4efcc4622b4bd0224a96a9481f0efb28e237d04eca7be20ac8a"


class PlanMaterializationError(RuntimeError):
    """Raised when the v0.6 plan cannot be derived exactly."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PlanMaterializationError(message)


def sha256_path(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def materialize_plan() -> tuple[dict[str, Any], dict[str, Any]]:
    require(sha256_path(MANIFEST) == MANIFEST_SHA, "v0.6 authority-manifest digest drift")
    manifest = load(MANIFEST)
    materialized_contract, _delta = materialize_contract()

    plan = deepcopy(materialized_contract)
    plan["schema_version"] = "axignal.o01-quality-coverage-lag-plan/v0.6"
    target = manifest["target"]
    decision_contract = manifest["decision_contract"]
    plan["authority"] = {
        "evaluation_mode": "LIVE_GITHUB_ISSUE_COMMENT_RECONSTRUCTION",
        "target_head_sha": target["head_sha"],
        "manifest_reference": MANIFEST_SHA,
        "effective_expiry": decision_contract["decision_max_expires_at"],
        "required_output": "O01_CAMPAIGN_AUTHORISED",
        "required_authorities": decision_contract["required_authorities"],
    }

    comparable = deepcopy(plan)
    comparable.pop("authority")
    comparable["schema_version"] = materialized_contract["schema_version"]
    require(
        comparable == materialized_contract,
        "v0.6 plan differs from exact materialized contract",
    )
    require(
        plan["sampling"]["check_query_syntax"] is False,
        "TED query execution is not enabled",
    )
    require(plan["source"]["scope"] == "ALL", "Historical ALL scope regressed")
    require(
        plan["sampling"]["query_contract"]
        == "buyer-country IN ({country}) AND publication-date = "
        "(20260701 <> 20260731) SORT BY publication-number",
        "Canonical date interval regressed",
    )
    require(
        plan["fields"]["ephemeral_contact_projection"][3]
        == "organisation-tel-buyer",
        "Canonical telephone field regressed",
    )
    require(plan["source"]["source_state"] == "CANDIDATE", "TED admitted prematurely")
    boundary = plan["non_authorisations"]
    require(boundary["public_launch"] == "NO_GO", "Public launch advanced")
    require(
        all(value is False for key, value in boundary.items() if key != "public_launch"),
        "Authority boundary expanded",
    )
    return plan, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan, manifest = materialize_plan()
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        PlanMaterializationError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = {
        "status": "PASS",
        "output": "O01_V0_6_CAMPAIGN_PLAN_MATERIALIZED",
        "plan_sha256": sha256_path(args.output),
        "plan_canonical_sha256": canonical_sha256(plan),
        "campaign_id": plan["campaign_id"],
        "target_head_sha": plan["authority"]["target_head_sha"],
        "manifest_reference": plan["authority"]["manifest_reference"],
        "decision_max_expires_at": manifest["decision_contract"][
            "decision_max_expires_at"
        ],
        "check_query_syntax": False,
        "source_scope": "ALL",
        "query_contract": plan["sampling"]["query_contract"],
        "source_state": "CANDIDATE",
        "public_launch": "NO_GO",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
