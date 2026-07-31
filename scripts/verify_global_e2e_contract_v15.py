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
    supersession_path = (
        "docs/contracts/31-v1.5-document-supersession-and-status-map.md"
    )

    required_files = (
        contract_path,
        adr_path,
        programme_path,
        state_path,
        registry_path,
        task_path,
        task_schema_path,
        gsc_path,
        gsc_doc_path,
        supersession_path,
        "docs/contracts/30-global-e2e-development-contract-v1.4.md",
        "docs/adr/ADR-015-finished-global-product-before-public-launch.md",
        "docs/roadmap/14-global-e2e-development-program-v1.4.md",
        "docs/contracts/00-product-constitution.md",
        "docs/contracts/01-business-model-and-pricing.md",
        "docs/contracts/21-marketing-site-and-conversion.md",
        "docs/contracts/22-packaging-pricing-and-entitlements.md",
        "docs/contracts/23-acquisition-analytics-and-experimentation.md",
        "docs/contracts/24-trust-center-and-public-methodology.md",
        "docs/contracts/28-b2g-procurement-commercial-and-global-source-program.md",
        "docs/contracts/29-bounded-ai-assistance-and-token-entitlements.md",
        "docs/roadmap/00-goal-lock.md",
        "docs/roadmap/01-phase-map.md",
        "docs/roadmap/02-task-catalogue.md",
        "docs/roadmap/03-contract-map.md",
        "docs/roadmap/04-dynamic-skill-map.md",
        "docs/roadmap/05-dependency-and-gates.md",
        "docs/roadmap/06-current-execution-state.md",
        "AGENTS.md",
        "README.md",
    )
    for relative_path in required_files:
        assert (ROOT / relative_path).is_file(), relative_path

    contract = load_text(contract_path)
    assert_contains(
        contract,
        "Contract 31",
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

    supersession = load_text(supersession_path)
    assert_contains(
        supersession,
        "PRESERVED_HISTORY",
        "ENGINEERING_EVIDENCE",
        "ACTIVE_WITH_SUPERSEDED_SECTIONS",
        "P24 launch modes ≠ Contract 31 launch authority",
        "P26-T01 pass ≠ P26 complete",
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

    subordinate_expectations = {
        "docs/contracts/00-product-constitution.md": (
            "Global Opportunity Intelligence & Operations",
            "Business-to-Government (B2G) Opportunity Intelligence",
            "P27",
        ),
        "docs/contracts/01-business-model-and-pricing.md": (
            "149 EUR/month",
            "399 EUR/month",
            "CANDIDATE_ONLY",
        ),
        "docs/contracts/21-marketing-site-and-conversion.md": (
            "IndexabilityGate",
            "Tender Alerts",
            "Search Console",
        ),
        "docs/contracts/22-packaging-pricing-and-entitlements.md": (
            "Flat-tier seat governance",
            "1,000,000-token ceiling",
            "P27",
        ),
        "docs/contracts/23-acquisition-analytics-and-experimentation.md": (
            "Search Console",
            "AI citation",
            "completed B2G value",
        ),
        "docs/contracts/24-trust-center-and-public-methodology.md": (
            "Google Search Console",
            "MCP",
            "Founder Operations",
        ),
        "docs/contracts/28-b2g-procurement-commercial-and-global-source-program.md": (
            "B2G Opportunity Intelligence",
            "0 / 149 / 399 / QUOTE",
            "P27",
        ),
        "docs/contracts/29-bounded-ai-assistance-and-token-entitlements.md": (
            "1,000,000",
            "Paid-package usage governance",
            "P27",
        ),
    }
    for path, literals in subordinate_expectations.items():
        assert_contains(load_text(path), *literals)

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
                "synchronised_contracts": len(subordinate_expectations),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
