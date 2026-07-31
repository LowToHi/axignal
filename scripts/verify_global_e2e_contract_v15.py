from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def load_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def assert_contains(text: str, *needles: str) -> None:
    for needle in needles:
        assert needle in text, f"Missing required literal: {needle}"


def main() -> None:
    contract_path = "docs/contracts/31-global-e2e-development-contract-v1.5.md"
    adr_path = "docs/adr/ADR-016-v1-5-canonical-programme-and-final-launch-gate.md"
    programme_path = "docs/roadmap/15-global-e2e-development-program-v1.5.md"
    state_path = "data/programmes/global-e2e-canonical-state.v1.5.json"
    registry_path = "data/programmes/global-e2e-task-registry.v1.5.json"
    task_path = "data/programmes/global-e2e-tasks-p25-p27.v1.5.json"
    task_schema_path = "schemas/global-e2e-v1.5-task.schema.json"
    gsc_path = "data/growth/google-search-console-integration.v0.1.json"
    gsc_doc_path = "docs/growth/google-search-console-and-mcp-governance-v0.1.md"

    for relative_path in (
        contract_path,
        adr_path,
        programme_path,
        state_path,
        registry_path,
        task_path,
        task_schema_path,
        gsc_path,
        gsc_doc_path,
        "docs/contracts/30-global-e2e-development-contract-v1.4.md",
        "docs/adr/ADR-015-finished-global-product-before-public-launch.md",
    ):
        assert (ROOT / relative_path).is_file(), relative_path

    contract = load_text(contract_path)
    assert_contains(
        contract,
        "Contract `31`",
        "P00–P27",
        "P24 MUST NOT itself authorise public launch",
        "P27 is the only phase permitted to return",
        "PRIVATE_ACCEPTANCE",
        "BOUNDED_PUBLIC_LAUNCH",
        "Business-to-Government (B2G) Opportunity Intelligence",
        "149 EUR/month",
        "399 EUR/month",
        "1,000,000",
        "google-site-verification",
        "https://mcpservers.org/es/servers/ahonn/mcp-server-gsc",
    )

    adr = load_text(adr_path)
    assert_contains(
        adr,
        "ADR-016",
        "P27 the only final exact-head public-launch gate",
        "P26-T04",
        "NOT_PRODUCT_ADMITTED",
    )

    programme = load_text(programme_path)
    assert_contains(
        programme,
        "P00–P27",
        "P24 Acceptance framework",
        "P27 Final exact-head re-acceptance",
        "AX-GE2E-P26-T02",
        "AX-GE2E-P26-T03",
        "AX-GE2E-P26-T04",
    )

    state = load_json(state_path)
    assert state["version"] == "1.5.0"
    assert state["programme"] == "P00-P27"
    assert state["canonical_repository"]["head"] == (
        "b9a08a2a07d04d635164e161d1b27a7a53df8575"
    )
    assert state["engineering_stack"]["head"] == (
        "e1e4999ecd1a7140d9b18ea4b5ad6f0a20e32073"
    )
    launch = state["launch"]
    for key in (
        "public_launch_authorised",
        "partial_launch_allowed",
        "bounded_public_launch_allowed",
        "public_signup_authorised",
        "public_indexing_authorised",
        "public_tender_alerts_authorised",
        "live_self_service_billing_authorised",
        "global_coverage_claim_authorised",
        "production_mcp_authorised",
    ):
        assert launch[key] is False, key
    assert launch["decision"] == "NO_GO"
    assert launch["private_acceptance_allowed_under_contract"] is True

    phase_rows = state["phases"]
    p24 = next(row for row in phase_rows if row.get("phase") == "P24")
    p25 = next(row for row in phase_rows if row.get("phase") == "P25")
    p26 = next(row for row in phase_rows if row.get("phase") == "P26")
    p27 = next(row for row in phase_rows if row.get("phase") == "P27")
    assert p24["current_authority"] == (
        "ACCEPTANCE_FRAMEWORK_ONLY_NOT_FINAL_LAUNCH_GATE"
    )
    assert p25["canonical_state"] == "CANONICAL_ACCEPTANCE_BLOCKED"
    assert p26["current_authority"] == "T01_PASS_T02_T04_PENDING"
    assert p27["current_authority"] == (
        "ONLY_FUTURE_FINAL_PUBLIC_LAUNCH_GATE"
    )

    pricing = state["commercial"]["candidate_price_book"]
    assert pricing["CONTROLLED_TRIAL_7D"]["seat_capacity"] == 2
    assert pricing["CONTROLLED_TRIAL_7D"]["token_ceiling"] == 1_000_000
    assert pricing["PROFESSIONAL_MONTHLY"]["amount_minor"] == 14_900
    assert pricing["PROFESSIONAL_MONTHLY"]["seat_capacity"] == 3
    assert pricing["TEAM_MONTHLY"]["amount_minor"] == 39_900
    assert pricing["TEAM_MONTHLY"]["seat_capacity"] == 15
    assert state["commercial"]["pricing_validated"] is False

    registry = load_json(registry_path)
    assert registry["programme"] == "P00-P27"
    assert registry["total_phase_count"] == 28
    assert registry["total_task_count"] == 31
    assert registry["state_model"]["only_final_launch_task"] == (
        "AX-GE2E-P27-T01"
    )
    assert registry["supersession"]["p24"] == (
        "ACCEPTANCE_FRAMEWORK_NOT_FINAL_LAUNCH_AUTHORITY"
    )

    schema = load_json(task_schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    task_document = load_json(task_path)
    task_ids: list[str] = []
    for task in task_document["tasks"]:
        errors = sorted(
            validator.iter_errors(task),
            key=lambda error: list(error.path),
        )
        assert not errors, (
            f"{task['task_id']}: {[error.message for error in errors]}"
        )
        task_ids.append(task["task_id"])
    assert len(task_ids) == 6
    assert len(task_ids) == len(set(task_ids))
    assert task_ids == [
        "AX-GE2E-P25-T01",
        "AX-GE2E-P26-T01",
        "AX-GE2E-P26-T02",
        "AX-GE2E-P26-T03",
        "AX-GE2E-P26-T04",
        "AX-GE2E-P27-T01",
    ]
    final_task = task_document["tasks"][-1]
    assert final_task["engineering_state"] == "NOT_STARTED"
    assert final_task["canonical_state"] == "CANONICAL_NOT_STARTED"
    assert "No partial public launch" in final_task["prohibited_authority"]

    gsc = load_json(gsc_path)
    assert gsc["domain"] == "axignal.com"
    assert gsc["property_candidate"] == "sc-domain:axignal.com"
    assert gsc["state"] == "DNS_VERIFICATION_USER_ATTESTED_API_UNPROVEN"
    assert gsc["verification"]["record"] == (
        "google-site-verification="
        "MSME8b9va1BRkZOAtEXp_zw0v5c1noDOpf3BrVJkIhA"
    )
    assert gsc["official_api_admission"]["state"] == "NOT_YET_PROVEN"
    assert gsc["official_api_admission"]["default_access"] == "READ_ONLY"
    assert gsc["official_api_admission"]["write_operations_authorised"] is False
    mcp = gsc["mcp_candidate"]
    assert mcp["catalogue_url"] == (
        "https://mcpservers.org/es/servers/ahonn/mcp-server-gsc"
    )
    assert mcp["state"] == "DISCOVERED_NOT_PRODUCT_ADMITTED"
    assert mcp["security_reviewed"] is False
    assert mcp["connected_to_production"] is False
    assert mcp["default_permission"] == "DENY"
    assert "DELETE_SITE" in mcp["denied_tool_classes"]
    assert "DELETE_SITEMAP" in mcp["denied_tool_classes"]
    assert "EXPOSE_CREDENTIALS" in mcp["denied_tool_classes"]

    gsc_doc = load_text(gsc_doc_path)
    assert_contains(
        gsc_doc,
        "DNS token != API access",
        "MCP catalogue presence does not equal connector admission",
        "destructive tools        DISABLED",
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "contract": "31",
                "version": "1.5.0",
                "programme": "P00-P27",
                "new_tasks": len(task_ids),
                "launch": "NO_GO",
                "search_console_api": "NOT_YET_PROVEN",
                "mcp": "DISCOVERED_NOT_PRODUCT_ADMITTED",
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
