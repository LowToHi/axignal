from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data/universes/eu-public-procurement/xml-parser-profile.v0.1.json"
POLICY_PATH = ROOT / "data/universes/eu-public-procurement/claim-policy.v0.1.json"
SOURCE_PATH = ROOT / "data/sources/ted-search-api-v3.v0.1.json"
TASK_PATH = ROOT / "docs/roadmap/tasks/AX-F8-T11.json"
TASK_SCHEMA_PATH = ROOT / "schemas/task.schema.json"
CATALOGUE_PATH = ROOT / "docs/roadmap/02-task-catalogue.md"
RUNBOOK_PATH = ROOT / "docs/sources/ted-eforms-xml-parser-v0.1.md"
PARSER_PATH = ROOT / "apps/api/src/axignal_api/connectors/ted_eforms.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    profile = load_json(PROFILE_PATH)
    require(profile["profile_id"] == "ted-eforms-cn16@0.1.0", "profile ID drifted")
    require(profile["status"] == "EVIDENCE_PROFILE_NOT_RUNTIME_ENABLED", "profile activated")
    require(profile["sdk"]["release"] == "1.14.2", "SDK release drifted")
    require(profile["sdk"]["customization_id"] == "eforms-sdk-1.14", "SDK ID drifted")
    require(profile["sdk"]["ubl_version"] == "2.3", "UBL version drifted")
    require(
        profile["notice_profile"]["document_type"] == "ContractNotice",
        "document drifted",
    )
    require(
        profile["notice_profile"]["notice_type"] == "cn-standard",
        "notice type drifted",
    )
    require(profile["notice_profile"]["notice_subtype"] == "16", "notice subtype drifted")
    require(profile["security"]["dtd_allowed"] is False, "DTD enabled")
    require(profile["security"]["entities_allowed"] is False, "entities enabled")
    require(profile["authority"]["model_calls"] == 0, "model authority introduced")
    require(profile["authority"]["canonical_writes"] == 0, "canonical writes introduced")
    require(
        profile["evidence_artifact"]["raw_xml_persisted"] is False,
        "raw XML persistence enabled",
    )
    require(
        profile["evidence_artifact"]["notice_values_persisted"] is False,
        "official notice values persistence enabled",
    )

    policy = load_json(POLICY_PATH)
    require(
        policy["status"] == "DISABLED_PENDING_PRODUCT_ADMISSION_AND_XML_PARSER",
        "claim policy activated",
    )

    # The shared TED Search source is now admitted only for the separately governed
    # fixed non-personal Search profile. That admission does not activate this XML
    # parser profile or the full procurement claim policy.
    source = load_json(SOURCE_PATH)
    require(source["status"] == "PRODUCT_ADMITTED", "bounded Search source admission missing")
    require(source["kill_switch_enabled"] is False, "bounded private-pilot Search source disabled")
    require(
        "fixed non-personal Search API projection" in source["rights"]["notes"],
        "bounded Search admission scope is not explicit",
    )
    require(source["rights"]["api_redistribution"] == "PROHIBITED", "API redistribution enabled")
    require(source["rights"]["model_training"] == "PROHIBITED", "model training enabled")

    task_schema = load_json(TASK_SCHEMA_PATH)
    task = load_json(TASK_PATH)
    errors = list(
        Draft202012Validator(
            task_schema,
            format_checker=FormatChecker(),
        ).iter_errors(task)
    )
    require(
        not errors,
        f"AX-F8-T11 task schema failure: {[item.message for item in errors]}",
    )
    require(task["state"] in {"IN_PROGRESS", "EVIDENCE_READY"}, "unexpected task state")
    require(
        all(item["answer"] == "YES" for item in task["goal_lock_checks"]),
        "Goal Lock blocker",
    )

    catalogue = CATALOGUE_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    parser_source = PARSER_PATH.read_text(encoding="utf-8")
    require("AX-GE2E-P08-T01" in catalogue, "active Procurement task not registered")
    require("defusedxml.ElementTree" in runbook, "safe-parser documentation missing")
    require(
        'SUPPORTED_CUSTOMIZATION_ID = "eforms-sdk-1.14"' in parser_source,
        "SDK code pin missing",
    )
    require("PERSONAL_LOCAL_NAMES" in parser_source, "personal-field exclusion missing")
    require("candidate_claims" in parser_source, "Candidate Claim derivation missing")
    require(
        "canonical" not in profile["status"].casefold(),
        "profile status implies canonical authority",
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "profile_id": profile["profile_id"],
                "sdk_release": profile["sdk"]["release"],
                "notice_type": profile["notice_profile"]["notice_type"],
                "notice_subtype": profile["notice_profile"]["notice_subtype"],
                "candidate_predicate_count": len(profile["candidate_claim_predicates"]),
                "shared_search_source_state": source["status"],
                "xml_runtime_enabled": False,
                "canonical_writes": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
