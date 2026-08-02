from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from verify_gate7_o01_v0_3_delta_contract import materialize as materialize_contract

ROOT = Path(__file__).resolve().parents[1]
BASE_PLAN = (
    ROOT
    / "data/acceptance/campaigns/"
    "AX-LIB-O01-real-quality-coverage-lag-plan.v0.2.json"
)
MANIFEST = (
    ROOT
    / "data/acceptance/approvals/"
    "AX-LIB-O01-campaign-authority-manifest.v0.3.json"
)
BASE_PLAN_SHA = "sha256:cae7894ca905ae7b0d0085699d6b9e75d08e684b70d58f6398594dad46fc5c97"
MANIFEST_SHA = "sha256:74ed362c8b856d586139062095c57a6d9a8944012bb9429dc4bb121ed6960d6d"
EVALUATOR_HEAD = "5a9b63056289b2b0851d9a88e712d4b8a24545dd"
EVALUATOR_TREE = "89fb112a7ec2ca12da626409a0bb5132c0ee7ee0"


class PlanMaterializationError(RuntimeError):
    """Raised when the v0.3 plan cannot be derived exactly."""


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
    require(sha256_path(BASE_PLAN) == BASE_PLAN_SHA, "v0.2 campaign-plan digest drift")
    require(sha256_path(MANIFEST) == MANIFEST_SHA, "v0.3 authority-manifest digest drift")

    base_plan = load(BASE_PLAN)
    manifest = load(MANIFEST)
    materialized_contract, _delta = materialize_contract()

    base_comparable = deepcopy(base_plan)
    base_comparable.pop("authority")
    base_comparable["schema_version"] = "axignal.o01-quality-coverage-lag-execution-contract/v0.2"
    base_contract = load(
        ROOT
        / "data/acceptance/campaigns/"
        "AX-LIB-O01-quality-coverage-lag-execution-contract.v0.2.json"
    )
    require(base_comparable == base_contract, "v0.2 plan no longer matches its contract")

    plan = deepcopy(materialized_contract)
    plan["schema_version"] = "axignal.o01-quality-coverage-lag-plan/v0.3"
    target = manifest["target"]
    decision_contract = manifest["decision_contract"]
    plan["authority"] = {
        "evaluation_mode": "LIVE_GITHUB_ISSUE_COMMENT_RECONSTRUCTION",
        "evaluator_head_sha": EVALUATOR_HEAD,
        "evaluator_tree_sha": EVALUATOR_TREE,
        "target_head_sha": target["head_sha"],
        "target_tree_sha": target["git_tree_sha"],
        "manifest_reference": MANIFEST_SHA,
        "effective_expiry": decision_contract["decision_max_expires_at"],
        "required_output": "O01_CAMPAIGN_AUTHORISED",
        "required_authorities": decision_contract["required_authorities"],
    }

    comparable = deepcopy(plan)
    comparable.pop("authority")
    comparable["schema_version"] = materialized_contract["schema_version"]
    require(comparable == materialized_contract, "v0.3 plan differs from exact materialized contract")
    require(
        plan["fields"]["ephemeral_contact_projection"][3]
        == "organisation-tel-buyer",
        "Canonical telephone field is not materialized",
    )
    require(
        "buyer-tel" not in plan["fields"]["ephemeral_contact_projection"],
        "Unsupported buyer-tel survived materialization",
    )
    require(plan["source"]["source_state"] == "CANDIDATE", "TED admitted prematurely")
    boundary = plan["non_authorisations"]
    require(boundary["public_launch"] == "NO_GO", "Public launch advanced")
    require(
        all(value is False for key, value in boundary.items() if key != "public_launch"),
        "Authority boundary expanded",
    )
    return plan, manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
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
        "output": "O01_V0_3_CAMPAIGN_PLAN_MATERIALIZED",
        "plan_sha256": sha256_path(args.output),
        "plan_canonical_sha256": canonical_sha256(plan),
        "campaign_id": plan["campaign_id"],
        "target_head_sha": plan["authority"]["target_head_sha"],
        "manifest_reference": plan["authority"]["manifest_reference"],
        "decision_max_expires_at": manifest["decision_contract"]["decision_max_expires_at"],
        "canonical_telephone_field": "organisation-tel-buyer",
        "source_state": "CANDIDATE",
        "public_launch": "NO_GO",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
