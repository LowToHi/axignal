from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = (
    ROOT
    / "data/acceptance/campaigns/"
    "AX-LIB-O01-quality-coverage-lag-execution-contract.v0.3.json"
)
DELTA = (
    ROOT
    / "data/acceptance/campaigns/"
    "AX-LIB-O01-quality-coverage-lag-execution-contract.v0.4.delta.json"
)
BASE_SHA = "sha256:d7028945e0e82bae86da3a0a7ae0b6e03d421b820ce31f532aa28284cb4b8a49"
DELTA_SHA = "sha256:3b2f0613917492015866bf63fa30e723e992e827b7e0cfc6ae75df86764512d7"


class ScopeContractError(RuntimeError):
    """Raised when the v0.4 scope delta is not exact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScopeContractError(message)


def sha256_path(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected object: {path}")
    return value


def materialize() -> tuple[dict[str, Any], dict[str, Any]]:
    require(sha256_path(BASE) == BASE_SHA, "v0.3 base-contract digest drift")
    require(sha256_path(DELTA) == DELTA_SHA, "v0.4 delta-contract digest drift")
    base = load(BASE)
    delta = load(DELTA)
    expected_base = {
        "path": str(BASE.relative_to(ROOT)),
        "sha256": BASE_SHA,
    }
    require(delta["base_contract"] == expected_base, "Base binding drift")
    operations = delta["experimental_operations"]
    require(len(operations) == 1, "Exactly one experimental operation is required")
    operation = operations[0]
    require(operation["op"] == "test_replace", "Unsupported delta operation")
    require(operation["path"] == "/source/scope", "Only source.scope may change")
    require(
        operation["from"] == "ACTIVE" and operation["to"] == "ALL",
        "Scope delta drift",
    )

    result = deepcopy(base)
    require(result["source"]["scope"] == operation["from"], "Base scope mismatch")
    result["source"]["scope"] = operation["to"]
    for metadata in delta["metadata_operations"]:
        require(metadata["op"] == "test_replace", "Unsupported metadata operation")
        key = metadata["path"].removeprefix("/")
        require(
            key in {"schema_version", "campaign_id", "task_id"},
            "Unsupported metadata path",
        )
        require(
            result[key] == metadata["from"],
            f"Metadata precondition failed: {key}",
        )
        result[key] = metadata["to"]

    comparison = deepcopy(result)
    baseline = deepcopy(base)
    for key in ("schema_version", "campaign_id", "task_id"):
        comparison[key] = baseline[key]
    comparison["source"]["scope"] = baseline["source"]["scope"]
    require(comparison == baseline, "An undeclared contract value changed")
    require(result["source"]["scope"] == "ALL", "ALL scope not materialized")
    require(result["sampling"] == base["sampling"], "Sampling contract changed")
    require(result["fields"] == base["fields"], "Field contract changed")
    require(result["thresholds"] == base["thresholds"], "Thresholds changed")
    require(result["retention"] == base["retention"], "Retention changed")
    require(
        result["non_authorisations"] == base["non_authorisations"],
        "Authority boundary changed",
    )
    return result, delta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialized-output", type=Path)
    args = parser.parse_args()
    try:
        result, delta = materialize()
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        ScopeContractError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    if args.materialized_output:
        args.materialized_output.parent.mkdir(parents=True, exist_ok=True)
        args.materialized_output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    invariants = delta["invariants"]
    payload = {
        "status": "PASS",
        "output": "O01_CAMPAIGN_SCOPE_V0_4_CONTRACT_PASS",
        "campaign_id": result["campaign_id"],
        "source_scope": result["source"]["scope"],
        "only_permitted_delta": True,
        "query_unchanged": invariants["query_unchanged"],
        "fields_unchanged": (
            invariants["retained_projection_unchanged"]
            and invariants["ephemeral_contact_projection_unchanged"]
        ),
        "sample_thresholds_retention_unchanged": True,
        "authority_boundary_unchanged": True,
        "automatic_human_signature": False,
        "automatic_human_approval": False,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
