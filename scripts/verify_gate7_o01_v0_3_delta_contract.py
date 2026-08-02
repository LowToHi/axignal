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
    "AX-LIB-O01-quality-coverage-lag-execution-contract.v0.2.json"
)
DELTA = (
    ROOT
    / "data/acceptance/campaigns/"
    "AX-LIB-O01-quality-coverage-lag-execution-contract.v0.3.delta.json"
)
BASE_SHA = "sha256:f86672f2925343fccc61ebe0cb1085a470bbb54d062f1f936eed9347854ff3a3"
DELTA_SHA = "sha256:8ac8ab15dc8edcbbce584d8ccf4ecbd6785d30b7b364d07051b294e7c86372dc"
ALLOWED_POINTERS = {
    "/schema_version",
    "/campaign_id",
    "/fields/ephemeral_contact_projection/3",
}


class DeltaContractError(RuntimeError):
    """Raised when the v0.3 contract is not the exact admitted delta."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DeltaContractError(message)


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


def resolve_parent(document: Any, pointer: str) -> tuple[Any, str]:
    parts = pointer.removeprefix("/").split("/")
    require(parts and parts != [""], f"Invalid pointer: {pointer}")
    parent = document
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    return parent, parts[-1]


def apply_operation(document: dict[str, Any], operation: dict[str, Any]) -> None:
    require(operation.get("op") == "test_replace", "Only test_replace is admitted")
    pointer = str(operation["path"])
    parent, leaf = resolve_parent(document, pointer)
    current = parent[int(leaf)] if isinstance(parent, list) else parent[leaf]
    require(current == operation["from"], f"Precondition failed at {pointer}")
    if isinstance(parent, list):
        parent[int(leaf)] = operation["to"]
    else:
        parent[leaf] = operation["to"]


def changed_pointers(before: Any, after: Any, pointer: str = "") -> set[str]:
    if type(before) is not type(after):
        return {pointer or "/"}
    if isinstance(before, dict):
        pointers: set[str] = set()
        for key in sorted(set(before) | set(after)):
            child = f"{pointer}/{key}"
            if key not in before or key not in after:
                pointers.add(child)
            else:
                pointers.update(changed_pointers(before[key], after[key], child))
        return pointers
    if isinstance(before, list):
        pointers = set()
        if len(before) != len(after):
            pointers.add(pointer or "/")
        for index, (left, right) in enumerate(zip(before, after, strict=False)):
            pointers.update(changed_pointers(left, right, f"{pointer}/{index}"))
        return pointers
    return set() if before == after else {pointer or "/"}


def materialize() -> tuple[dict[str, Any], dict[str, Any]]:
    require(sha256_path(BASE) == BASE_SHA, "v0.2 base-contract digest drift")
    require(sha256_path(DELTA) == DELTA_SHA, "v0.3 delta-contract digest drift")
    base = load(BASE)
    delta = load(DELTA)
    require(
        delta["schema_version"] == "axignal.o01-execution-contract-delta/v0.1",
        "Unexpected delta schema",
    )
    require(
        delta["change_class"] == "VERSIONED_FIELD_IDENTIFIER_CORRECTION",
        "Unexpected remediation class",
    )
    require(delta["base_contract"]["sha256"] == BASE_SHA, "Base binding drift")

    operations = delta["metadata_operations"] + delta["experimental_operations"]
    require(
        {str(item["path"]) for item in operations} == ALLOWED_POINTERS,
        "Operation pointer set drift",
    )
    require(len(delta["experimental_operations"]) == 1, "Experimental delta expanded")
    experimental = delta["experimental_operations"][0]
    require(
        experimental
        == {
            "from": "buyer-tel",
            "op": "test_replace",
            "path": "/fields/ephemeral_contact_projection/3",
            "reason": (
                "TED Search API rejects buyer-tel and accepts "
                "organisation-tel-buyer, including in the full corrected "
                "contact projection."
            ),
            "to": "organisation-tel-buyer",
        },
        "Telephone-field remediation drift",
    )

    materialized = deepcopy(base)
    for operation in operations:
        apply_operation(materialized, operation)
    require(
        changed_pointers(base, materialized) == ALLOWED_POINTERS,
        "Materialized contract changed outside admitted pointers",
    )
    require(
        len(materialized["fields"]["ephemeral_contact_projection"])
        == len(base["fields"]["ephemeral_contact_projection"]),
        "Contact projection length changed",
    )

    evidence = delta["diagnostic_evidence"]
    require(evidence["artifact_id"] == 8835935926, "Diagnostic artifact drift")
    require(
        evidence["artifact_digest"]
        == "sha256:92cc4bd197b2ebbcaa6b6984efdf2e5ef392788c54c2615d48c876e8147dea3f",
        "Diagnostic artifact digest drift",
    )
    require(
        evidence["result_member_sha256"]
        == "sha256:36c1c054b5a8efd64f0ed93c667e6fd9f8acabcb35ab393a0ef6d1b7a4fdffdb",
        "Diagnostic result digest drift",
    )
    require(
        evidence["classification"]
        == "CANONICAL_TELEPHONE_REPLACEMENT_CONFIRMED",
        "Diagnostic classification drift",
    )
    require(evidence["controls_pass"] is True, "Diagnostic controls failed")
    require(
        evidence["canonical_replacement_accepted"] is True
        and evidence["corrected_full_projection_accepted"] is True,
        "Canonical replacement was not demonstrated",
    )
    require(
        evidence["raw_response_retained"] is False
        and evidence["contact_values_retained"] is False
        and evidence["fabricated_evidence"] == 0,
        "Diagnostic privacy boundary drift",
    )

    non_authorisations = delta["non_authorisations"]
    require(non_authorisations["public_launch"] == "NO_GO", "Launch advanced")
    require(
        all(
            value is False
            for key, value in non_authorisations.items()
            if key != "public_launch"
        ),
        "Authority boundary expanded",
    )
    return materialized, delta


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialized-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        materialized, delta = materialize()
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        DeltaContractError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    if args.materialized_output is not None:
        args.materialized_output.parent.mkdir(parents=True, exist_ok=True)
        args.materialized_output.write_text(
            json.dumps(materialized, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    result = {
        "status": "PASS",
        "output": "O01_V0_3_DELTA_CONTRACT_PASS",
        "base_contract_sha256": BASE_SHA,
        "delta_contract_sha256": DELTA_SHA,
        "materialized_contract_canonical_sha256": canonical_sha256(materialized),
        "campaign_id": materialized["campaign_id"],
        "change_class": delta["change_class"],
        "changed_json_pointers": sorted(ALLOWED_POINTERS),
        "sole_experimental_delta": {
            "from": "buyer-tel",
            "to": "organisation-tel-buyer",
        },
        "source_state": "CANDIDATE",
        "public_launch": "NO_GO",
        "automatic_human_approval": False,
        "automatic_human_signature": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
