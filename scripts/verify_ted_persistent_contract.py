from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/sources/ted-search-api-v3.v1.0.json"
POLICY = ROOT / "data/universes/eu-public-procurement/claim-policy.v1.0.json"
TASK = ROOT / "docs/roadmap/tasks/AX-F8-T14.json"
MIGRATION = ROOT / "infra/postgres/070-ted-persistent-source.sql"
RUNBOOK = ROOT / "docs/runbooks/ted-persistent-source.md"
SOURCE_DOC = ROOT / "docs/sources/ted-product-admission-v1.0.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    source = load(SOURCE)
    source_schema = load(ROOT / "schemas/source.schema.json")
    source_errors = list(
        Draft202012Validator(
            source_schema,
            format_checker=FormatChecker(),
        ).iter_errors(source)
    )
    require(not source_errors, f"source schema errors: {source_errors}")
    require(source["status"] == "PRODUCT_ADMITTED", "source is not product admitted")
    require(source["kill_switch_enabled"] is False, "source kill switch remains enabled")
    require(source["contains_personal_data"] is True, "source privacy risk was hidden")
    require(source["rights"]["model_training"] == "PROHIBITED", "model training allowed")
    require("non-personal" in source["rights"]["notes"].casefold(), "bounded rights missing")

    policy = load(POLICY)
    require(policy["policy_id"] == "ted-procurement-observed@1.0.0", "policy drift")
    require(
        policy["status"] == "ENABLED_FEATURE_FLAGGED_BOUNDED_PROFILE",
        "policy activation state drift",
    )
    require(policy["source_contract"]["raw_xml_persistence"] is False, "raw XML allowed")
    require(policy["personal_data_policy"]["persistent_values"] == "PROHIBITED", "PII allowed")
    automatic = set(policy["automatic_predicates"])
    excluded = set(policy["excluded_identity_predicates"])
    require(not automatic & excluded, "identity predicate entered automatic policy")
    require("procurement_awarded_value" in automatic, "award value missing")
    require("procurement_winner_official_name" in excluded, "winner identity exclusion missing")

    task = load(TASK)
    task_schema = load(ROOT / "schemas/task.schema.json")
    task_errors = list(
        Draft202012Validator(task_schema, format_checker=FormatChecker()).iter_errors(task)
    )
    require(not task_errors, f"task schema errors: {task_errors}")
    require(task["state"] in {"IN_PROGRESS", "EVIDENCE_READY"}, "task state overstated")

    migration = MIGRATION.read_text(encoding="utf-8")
    for token in (
        "axignal_ted_worker",
        "axignal_ted_admission_runtime",
        "PROCUREMENT_TED",
        "procurement_notice_versions",
        "raw_xml_persisted boolean NOT NULL DEFAULT false CHECK (raw_xml_persisted = false)",
        "ted-persistent-source@0.1.0",
        "REVOKE ALL PRIVILEGES ON",
    ):
        require(token in migration, f"migration contract missing: {token}")
    require(RUNBOOK.exists() and SOURCE_DOC.exists(), "operational documentation missing")

    print(
        json.dumps(
            {
                "status": "PASS",
                "source_status": source["status"],
                "policy_status": policy["status"],
                "automatic_predicate_count": len(automatic),
                "excluded_identity_predicate_count": len(excluded),
                "raw_xml_persistence": False,
                "personal_values_persistence": False,
                "feature_flag_required": True,
                "public_marketing_authorised": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
