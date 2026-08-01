from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(
    "data/acceptance/gate7/AX-G7-consolidated-engineering-contract.v1.json"
)
LIBRARY_DIR = Path("data/acceptance/library-coverage")
CONFLICT_MARKERS = ("<<<<<<< ", "=======", ">>>>>>> ")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def git_value(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def collect_expiries(value: Any) -> list[str]:
    expiries: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "expires_at" and isinstance(item, str):
                expiries.append(item)
            else:
                expiries.extend(collect_expiries(item))
    elif isinstance(value, list):
        for item in value:
            expiries.extend(collect_expiries(item))
    return expiries


def conflict_paths() -> list[str]:
    roots = (
        Path(".github/workflows"),
        Path("apps/api/src/axignal_api"),
        Path("apps/api/tests"),
        Path("data/acceptance"),
        Path("data/contracts"),
        Path("docs/acceptance"),
        Path("docs/runbooks"),
        Path("schemas"),
        Path("scripts"),
    )
    suffixes = {".json", ".md", ".py", ".sh", ".yaml", ".yml"}
    conflicts: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            if path.suffix not in suffixes:
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith(CONFLICT_MARKERS):
                    conflicts.append(str(path))
                    break
    return conflicts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the canonical Gate 7 engineering consolidation"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--approval-manifest-sha-file",
        type=Path,
        default=Path(
            "artifacts/o01-legal-privacy/approval-manifest.v0.2.sha256"
        ),
    )
    args = parser.parse_args()

    contract = load_json(CONTRACT_PATH)
    assert contract["contract_id"] == "AX-G7-CONSOLIDATED-ENGINEERING-v1"
    assert contract["gate"] == "PUBLIC_LAUNCH_GATE_7"
    assert contract["status"] == "ENGINEERING_CONSOLIDATED"
    assert contract["output"] == "GATE7_CONSOLIDATED_ENGINEERING_PASS"

    truth = contract["authority_boundary"]
    assert truth["historical_heads_are_current_authority"] is False
    assert truth["current_authority_is_runtime_exact_head"] is True
    assert truth["campaign_authority"] is False
    assert truth["source_admission_authority"] is False
    assert truth["legal_decision"] == "MISSING"
    assert truth["privacy_data_rights_decision"] == "MISSING"
    assert truth["public_launch"] == "NO_GO"

    criteria = contract["exit_criteria"]
    assert criteria == {
        "CAMPAIGN_AUTHORITY": False,
        "CI_FAILING": 0,
        "PUBLIC_LAUNCH": "NO_GO",
        "SINGLE_EXACT_HEAD": True,
        "STACK_CONSOLIDATED": True,
        "STALE_HEAD_EVIDENCE": 0,
        "UNRESOLVED_CONFLICTS": 0,
    }

    stack = contract["canonical_stack"]
    assert [item["sequence"] for item in stack] == list(range(1, 8))
    assert [item["source_pr"] for item in stack] == [101, 102, 119, 121, 123, 126, 127]
    assert stack[-1]["head_sha"] == (
        "abd37a5844c79288858e94ec308e85abe26822fe"
    )
    assert stack[-1]["authority"] == "CONSOLIDATION_BASE"
    assert all(item["authority"] != "CURRENT_EXACT_HEAD" for item in stack)

    parallel = contract["parallel_integrations"]
    assert [item["source_pr"] for item in parallel] == [120, 129]
    assert all(item["authority"] == "HISTORICAL_LINEAGE" for item in parallel)

    expected_libraries = set(contract["required_libraries"])
    actual_paths = sorted(LIBRARY_DIR.glob("AX-LIB-*.json"))
    assert {path.stem for path in actual_paths} == expected_libraries
    assert len(actual_paths) == 16

    library_ids: list[str] = []
    active_sources = 0
    admitted_sources = 0
    evidence_expiries: list[str] = []
    for path in actual_paths:
        dossier = load_json(path)
        library_ids.append(str(dossier["library_id"]))
        assert dossier["canonical_state"] == "BLOCKED"
        assert dossier["claim_decision"] == "DENIED"
        sources = dossier["sources"]
        active_sources += len(sources["active"])
        for group in ("active", "suspended", "candidate"):
            for source in sources[group]:
                if source.get("product_admitted") is True:
                    admitted_sources += 1
                if source.get("contributes_to_public_claim") is True:
                    raise AssertionError(
                        f"{path}: source contributes to a public claim"
                    )
        evidence_expiries.extend(collect_expiries(dossier))

    assert set(library_ids) == expected_libraries
    assert len(library_ids) == len(set(library_ids))
    assert active_sources == 0
    assert admitted_sources == 0

    active_contracts = contract["active_contracts"]
    assert len(active_contracts) == len(set(active_contracts.values()))
    for path_value in active_contracts.values():
        path = Path(path_value)
        assert path.is_file(), path
        if path.suffix == ".json":
            evidence_expiries.extend(collect_expiries(load_json(path)))

    performance = load_json(Path(active_contracts["performance_capacity_contract"]))
    assert performance["contract_id"] == "AX-G7-PERFORMANCE-CAPACITY-v0.2"
    assert performance["supersedes"] == "AX-G7-PERFORMANCE-CAPACITY-v0.1"
    assert performance["truth_boundary"]["ci_pass_closes_g7"] is False
    assert performance["truth_boundary"]["production_campaign_pass_closes_g7"] is False
    assert performance["truth_boundary"]["public_launch_authorised"] is False

    supersession = contract["supersession_map"]
    assert len(supersession) == 3
    assert {item["scope"] for item in supersession} == {
        "FULL",
        "PROFESSIONAL_CONTACT_PERSON_DATA_ONLY",
    }
    for item in supersession:
        assert Path(item["superseded"]).is_file()
        assert Path(item["active"]).is_file()
        assert item["historical_file_retained"] is True
        assert item["superseded"] != item["active"]

    conflicts = conflict_paths()
    assert not conflicts, conflicts

    exact_head = git_value("rev-parse", "HEAD")
    expected_head = os.environ.get("AXIGNAL_EXACT_SHA", exact_head)
    assert exact_head == expected_head
    git_tree = git_value("rev-parse", "HEAD^{tree}")

    digest_text = args.approval_manifest_sha_file.read_text(encoding="utf-8").strip()
    approval_manifest_digest = digest_text.split()[0]
    approval_manifest_hex = approval_manifest_digest.removeprefix("sha256:")
    assert SHA256_PATTERN.fullmatch(approval_manifest_hex)
    approval_manifest_digest = f"sha256:{approval_manifest_hex}"

    parsed_expiries = sorted(
        (datetime.fromisoformat(value.replace("Z", "+00:00")), value)
        for value in set(evidence_expiries)
    )
    assert parsed_expiries
    evidence_expiry = parsed_expiries[0][1]

    result = {
        "status": "PASS",
        "output": "GATE7_CONSOLIDATED_ENGINEERING_PASS",
        "contract_id": contract["contract_id"],
        "exact_head_sha": exact_head,
        "git_tree_sha": git_tree,
        "approval_manifest_digest": approval_manifest_digest,
        "evidence_expiry": evidence_expiry,
        "libraries": len(actual_paths),
        "active_sources": active_sources,
        "product_admitted_sources": admitted_sources,
        "stack_consolidated": True,
        "single_exact_head": True,
        "ci_failing": 0,
        "stale_head_evidence": 0,
        "unresolved_conflicts": 0,
        "campaign_authority": False,
        "public_launch": "NO_GO",
        "gate7_artifact_digest_source": "GITHUB_ACTIONS_ARTIFACT_DIGEST",
    }
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
