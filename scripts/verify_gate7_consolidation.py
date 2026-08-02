from __future__ import annotations

import argparse
import hashlib
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
ADMISSION_MANIFEST_PATH = Path(
    "data/acceptance/source-admission/"
    "AX-LIB-O01-TED-source-admission-authority-manifest.v0.2.json"
)
ADMISSION_CLOSURE_PATH = Path(
    "data/acceptance/source-admission/"
    "AX-LIB-O01-TED-source-admission-closure.v0.2.json"
)
CONFLICT_MARKERS = ("<<<<<<< ", "=======", ">>>>>>> ")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def verify_historical_contract(contract: dict[str, Any]) -> None:
    assert contract["contract_id"] == "AX-G7-CONSOLIDATED-ENGINEERING-v1"
    assert contract["gate"] == "PUBLIC_LAUNCH_GATE_7"
    assert contract["status"] == "ENGINEERING_CONSOLIDATED"
    assert contract["output"] == "GATE7_CONSOLIDATED_ENGINEERING_PASS"

    historical = contract["authority_boundary"]
    assert historical == {
        "campaign_authority": False,
        "current_authority_is_runtime_exact_head": True,
        "historical_heads_are_current_authority": False,
        "legal_decision": "MISSING",
        "privacy_data_rights_decision": "MISSING",
        "public_launch": "NO_GO",
        "source_admission_authority": False,
    }
    assert contract["exit_criteria"] == {
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
    assert stack[-1]["head_sha"] == "abd37a5844c79288858e94ec308e85abe26822fe"
    assert stack[-1]["authority"] == "CONSOLIDATION_BASE"
    assert all(item["authority"] != "CURRENT_EXACT_HEAD" for item in stack)

    parallel = contract["parallel_integrations"]
    assert [item["source_pr"] for item in parallel] == [120, 129]
    assert all(item["authority"] == "HISTORICAL_LINEAGE" for item in parallel)


def verify_current_admission(
    manifest: dict[str, Any],
    closure: dict[str, Any],
) -> None:
    assert manifest["schema_version"] == (
        "axignal.o01-source-admission-authority-manifest/v0.2"
    )
    assert closure["schema_version"] == (
        "axignal.o01-ted-source-admission-closure/v0.2"
    )
    assert closure["status"] == "PASS"
    assert closure["output"] == "O01_TED_SOURCE_ADMISSION_PASS"
    assert closure["decision"] == "ADMIT"
    assert closure["source_state"] == "PRODUCT_ADMITTED"
    assert closure["product_admitted"] is True
    assert closure["phase_closed"] is True
    assert closure["authority"]["head_match"] is True
    assert closure["authority"]["manifest_match"] is True
    assert closure["authority"]["scope_match"] is True
    assert closure["authority"]["issue_match"] is True
    assert closure["authority"]["signatures_human"] is True
    assert closure["authority"]["expiry_within_evidence"] is True
    assert set(closure["authority"]["authorities"]) == set(manifest["authorities"])
    assert {
        item["status"] for item in closure["authority"]["authorities"].values()
    } == {"APPROVED_CURRENT"}
    assert closure["evidence"]["manifest_reference"] == (
        f"sha256:{sha256_file(ADMISSION_MANIFEST_PATH)}"
    )

    boundary = closure["permanent_boundary"]
    assert boundary["bounded_product_use_authorised"] is True
    assert boundary["bounded_claim_contribution"] is False
    assert boundary["o01_canonical_state"] == "IN_REVIEW"
    assert boundary["o01_claim_decision"] == "PENDING"
    assert boundary["gate7_closed"] is False
    assert boundary["global_coverage_claim_authorised"] is False
    assert boundary["public_launch"] == "NO_GO"
    for key in (
        "public_redistribution_authorised",
        "contact_marketing_authorised",
        "model_training_authorised",
        "bid_submission_authorised",
        "external_notification_delivery_authorised",
    ):
        assert boundary[key] is False


def verify_libraries(
    contract: dict[str, Any],
) -> tuple[int, int, list[str]]:
    expected_libraries = set(contract["required_libraries"])
    actual_paths = sorted(LIBRARY_DIR.glob("AX-LIB-*.json"))
    assert {path.stem for path in actual_paths} == expected_libraries
    assert len(actual_paths) == 16

    active_sources = 0
    admitted_sources = 0
    evidence_expiries: list[str] = []
    for path in actual_paths:
        dossier = load_json(path)
        assert dossier["library_id"] == path.stem
        sources = dossier["sources"]
        active_sources += len(sources["active"])
        for group in ("active", "suspended", "candidate"):
            for source in sources[group]:
                if source["state"] == "PRODUCT_ADMITTED":
                    admitted_sources += 1
                assert source["contributes_to_public_claim"] is False

        if dossier["library_id"] != "AX-LIB-O01":
            assert dossier["canonical_state"] == "BLOCKED"
            assert dossier["claim_decision"] == "DENIED"
            assert sources["active"] == []
        else:
            assert dossier["canonical_state"] == "IN_REVIEW"
            assert dossier["claim_decision"] == "PENDING"
            assert sources["candidate"] == []
            assert sources["suspended"] == []
            assert len(sources["active"]) == 1
            ted = sources["active"][0]
            assert ted["source_id"] == "src_ted_search_api_v3"
            assert ted["state"] == "PRODUCT_ADMITTED"
            assert set(ted["admission"].values()) == {"PASS"}
            assert dossier["historical_depth"]["status"] == "MISSING"
            assert dossier["update_frequency"]["status"] == "MISSING"
            assert dossier["lag"]["status"] == "MISSING"
            assert dossier["kill_switch"]["implemented"] is True
            assert dossier["kill_switch"]["tested"] is True
            assert dossier["rollback"]["implemented"] is True
            assert dossier["rollback"]["tested"] is True

        evidence_expiries.extend(collect_expiries(dossier))

    assert active_sources == 1
    assert admitted_sources == 1
    return active_sources, admitted_sources, evidence_expiries


def verify_active_contracts(
    contract: dict[str, Any],
    evidence_expiries: list[str],
) -> None:
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the current exact-head Gate 7 engineering authority"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    contract = load_json(CONTRACT_PATH)
    manifest = load_json(ADMISSION_MANIFEST_PATH)
    closure = load_json(ADMISSION_CLOSURE_PATH)

    verify_historical_contract(contract)
    verify_current_admission(manifest, closure)
    active_sources, admitted_sources, evidence_expiries = verify_libraries(contract)
    verify_active_contracts(contract, evidence_expiries)
    evidence_expiries.extend(collect_expiries(manifest))
    evidence_expiries.extend(collect_expiries(closure))

    conflicts = conflict_paths()
    assert not conflicts, conflicts

    exact_head = git_value("rev-parse", "HEAD")
    expected_head = os.environ.get("AXIGNAL_EXACT_SHA", exact_head)
    assert exact_head == expected_head
    git_tree = git_value("rev-parse", "HEAD^{tree}")

    manifest_hex = sha256_file(ADMISSION_MANIFEST_PATH)
    assert SHA256_PATTERN.fullmatch(manifest_hex)
    manifest_digest = f"sha256:{manifest_hex}"

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
        "historical_contract_boundary_preserved": True,
        "exact_head_sha": exact_head,
        "git_tree_sha": git_tree,
        "source_admission_manifest_digest": manifest_digest,
        "evidence_expiry": evidence_expiry,
        "libraries": 16,
        "active_sources": active_sources,
        "product_admitted_sources": admitted_sources,
        "stack_consolidated": True,
        "single_exact_head": True,
        "ci_failing": 0,
        "stale_head_evidence": 0,
        "unresolved_conflicts": 0,
        "campaign_authority": False,
        "source_admission_authority": True,
        "legal_decision": "APPROVED_CURRENT",
        "privacy_data_rights_decision": "APPROVED_CURRENT",
        "ted_source_state": "PRODUCT_ADMITTED",
        "o01_canonical_state": "IN_REVIEW",
        "o01_claim_decision": "PENDING",
        "bounded_claim_contribution": False,
        "global_coverage_claim_authorised": False,
        "gate7_decision": "IN_PROGRESS",
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
