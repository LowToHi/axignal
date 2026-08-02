from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from verify_gate7_o01_v0_5_query_contract import materialize as materialize_v0_5

ROOT = Path(__file__).resolve().parents[1]
DELTA = (
    ROOT
    / "data/acceptance/campaigns/"
    "AX-LIB-O01-quality-coverage-lag-execution-contract.v0.6.delta.json"
)
DELTA_SHA = "sha256:31b808da4a95a6510882154addcb87d3ceb7af9fd79227b5cd77e26b1e5c4310"
BASE_CANONICAL_SHA = (
    "sha256:1be51417eeb95dbac8d68e39ed73cfe03202732688e3e5180a714ab2a2762387"
)


class ExecutionContractError(RuntimeError):
    """Raised when the v0.6 execution-mode delta is not exact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExecutionContractError(message)


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
    require(isinstance(value, dict), f"Expected object: {path}")
    return value


def materialize() -> tuple[dict[str, Any], dict[str, Any]]:
    require(sha256_path(DELTA) == DELTA_SHA, "v0.6 delta-contract digest drift")
    base, _query_delta = materialize_v0_5()
    require(
        canonical_sha256(base) == BASE_CANONICAL_SHA,
        "Materialized v0.5 base-contract digest drift",
    )
    delta = load(DELTA)
    require(
        delta["base_contract"]["materialized_canonical_sha256"]
        == BASE_CANONICAL_SHA,
        "v0.5 base binding drift",
    )
    operations = delta["experimental_operations"]
    require(len(operations) == 1, "Exactly one experimental operation is required")
    operation = operations[0]
    require(operation["op"] == "test_replace", "Unsupported delta operation")
    require(
        operation["path"] == "/sampling/check_query_syntax",
        "Only sampling.check_query_syntax may change",
    )
    require(
        operation["from"] is True and operation["to"] is False,
        "Execution-mode delta must be true to false",
    )

    result = deepcopy(base)
    require(
        result["sampling"]["check_query_syntax"] is True,
        "Base execution-mode precondition failed",
    )
    result["sampling"]["check_query_syntax"] = operation["to"]
    for metadata in delta["metadata_operations"]:
        require(metadata["op"] == "test_replace", "Unsupported metadata operation")
        key = metadata["path"].removeprefix("/")
        require(
            key in {"schema_version", "campaign_id", "task_id"},
            "Unsupported metadata path",
        )
        require(result[key] == metadata["from"], f"Metadata drift: {key}")
        result[key] = metadata["to"]

    comparison = deepcopy(result)
    baseline = deepcopy(base)
    for key in ("schema_version", "campaign_id", "task_id"):
        comparison[key] = baseline[key]
    comparison["sampling"]["check_query_syntax"] = baseline["sampling"][
        "check_query_syntax"
    ]
    require(comparison == baseline, "An undeclared contract value changed")
    require(
        result["sampling"]["check_query_syntax"] is False,
        "Query execution is not enabled",
    )
    require(result["source"]["scope"] == "ALL", "ALL scope regressed")
    require(
        result["sampling"]["query_contract"]
        == "buyer-country IN ({country}) AND publication-date = "
        "(20260701 <> 20260731) SORT BY publication-number",
        "Canonical query regressed",
    )
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
        ExecutionContractError,
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
        "output": "O01_QUERY_EXECUTION_V0_6_CONTRACT_PASS",
        "campaign_id": result["campaign_id"],
        "check_query_syntax": result["sampling"]["check_query_syntax"],
        "source_scope": result["source"]["scope"],
        "query_contract": result["sampling"]["query_contract"],
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
