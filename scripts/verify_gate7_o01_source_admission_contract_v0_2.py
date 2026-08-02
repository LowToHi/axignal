#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_AUTHORITIES = {
    "PRODUCT",
    "SECURITY",
    "PRIVACY_DATA_RIGHTS",
    "LEGAL",
    "SOURCE_QUALITY",
    "UX_ACCESSIBILITY",
    "HUMAN_COVERAGE_AUTHORITY",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--closure", required=True, type=Path)
    parser.add_argument(
        "--schema",
        default=(
            ROOT
            / "schemas"
            / "o01-source-admission-authority-manifest.schema.json"
        ),
        type=Path,
    )
    return parser.parse_args()


def sha256_reference(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def validate_closure(closure: dict[str, Any], manifest: dict[str, Any]) -> None:
    expected = manifest["evidence"]
    evidence = closure["evidence"]
    execution = closure["execution"]
    thresholds = closure["thresholds"]
    controls = closure["controls"]
    boundary = closure["authority_boundary"]
    require(closure["status"] == "PASS", "Closure status must be PASS")
    require(
        closure["output"] == "O01_QUALITY_COVERAGE_LAG_PASS",
        "Closure output mismatch",
    )
    require(
        evidence["execution_commit_sha"] == expected["execution_commit_sha"],
        "Execution commit mismatch",
    )
    require(evidence["artifact_id"] == expected["artifact_id"], "Artifact ID mismatch")
    require(
        evidence["artifact_sha256"] == expected["artifact_sha256"],
        "Artifact digest mismatch",
    )
    require(
        execution["sample_count"] >= expected["minimum_sample_count"],
        "Representative sample below minimum",
    )
    require(
        execution["countries_observed"] >= expected["minimum_countries_observed"],
        "Observed countries below minimum",
    )
    require(
        sorted(execution["languages_verified"])
        == sorted(expected["required_languages"]),
        "Required multilingual journeys mismatch",
    )
    require(thresholds["all_pass"] is True, "One or more frozen thresholds failed")
    require(controls["human_authority_current"] is True, "Campaign authority not current")
    require(controls["kill_switch_tested"] is True, "Kill switch not tested")
    require(controls["rollback_tested"] is True, "Rollback not tested")
    require(
        controls["raw_responses_retained_securely"] is True,
        "Raw responses not securely retained",
    )
    require(controls["plaintext_removed"] is True, "Plaintext was not removed")
    require(controls["plaintext_uploaded"] is False, "Plaintext was uploaded")
    require(controls["contact_values_persisted"] is False, "Contact values persisted")
    require(boundary["source_state"] == "CANDIDATE", "Source was pre-admitted")
    require(boundary["product_admitted"] is False, "Product was pre-admitted")
    require(boundary["public_launch"] == "NO_GO", "Launch boundary changed")


def main() -> int:
    args = parse_args()
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    closure = json.loads(args.closure.read_text(encoding="utf-8"))

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(manifest), key=lambda item: list(item.path))
    if errors:
        raise SystemExit("\n".join(error.message for error in errors))

    require(
        sha256_reference(args.contract) == manifest["contract_sha256"],
        "Contract digest mismatch",
    )
    require(
        args.contract.as_posix().endswith(manifest["contract_path"]),
        "Contract path mismatch",
    )
    require(
        args.closure.as_posix().endswith(manifest["closure_path"]),
        "Closure path mismatch",
    )
    require(
        set(contract["authorities"]) == CANONICAL_AUTHORITIES,
        "Contract authority set mismatch",
    )
    require(
        contract["authorities"] == manifest["authorities"],
        "Manifest authority mapping drifted from contract",
    )
    require(
        contract["permanent_boundary"]["public_launch"] == "NO_GO",
        "Contract launch boundary changed",
    )
    require(
        contract["admitted_effect"]["global_coverage_claim_authorised"] is False,
        "Contract incorrectly authorises global coverage",
    )
    require(
        contract["admitted_effect"]["gate7_closed"] is False,
        "Contract incorrectly closes Gate 7",
    )
    require(
        contract["admitted_effect"]["bounded_claim_contribution"] is False,
        "Contract incorrectly enables claim contribution",
    )
    require(
        contract["admitted_effect"]["o01_canonical_state"] == "IN_REVIEW",
        "Contract incorrectly accepts O01 without history/frequency evidence",
    )
    require(
        contract["admitted_effect"]["o01_claim_decision"] == "PENDING",
        "Contract incorrectly approves the O01 public claim",
    )

    target = manifest["target_head_sha"]
    current = git("rev-parse", "HEAD").decode().strip()
    require(target != current, "Manifest must bind a frozen ancestor, not itself")
    subprocess.check_call(
        ["git", "merge-base", "--is-ancestor", target, current],
        cwd=ROOT,
    )
    target_contract = git("show", f"{target}:{manifest['contract_path']}")
    require(
        target_contract == args.contract.read_bytes(),
        "Frozen target does not contain the exact admission contract",
    )

    validate_closure(closure, manifest)
    print(
        json.dumps(
            {
                "status": "PASS",
                "output": "O01_TED_SOURCE_ADMISSION_CONTRACT_PASS",
                "target_head_sha": target,
                "current_head_sha": current,
                "contract_sha256": manifest["contract_sha256"],
                "authorities": sorted(CANONICAL_AUTHORITIES),
                "automatic_human_approval": False,
                "automatic_human_signature": False,
                "source_state_before_decision": "CANDIDATE",
                "bounded_claim_contribution": False,
                "o01_canonical_state_after_source_admission": "IN_REVIEW",
                "o01_claim_decision_after_source_admission": "PENDING",
                "global_coverage_claim_authorised": False,
                "gate7_closed": False,
                "public_launch": "NO_GO",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
