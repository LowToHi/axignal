from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data/experience/subscriber-workspace-ux-contract.v1.json"
REGISTRY_PATH = ROOT / "skills/subscriber-workspace-ux.registry.yaml"

ALLOWED_STATUS = {
    "OPERATIONAL_BOUNDED",
    "OPERATIONAL_CANDIDATE",
    "PARTIAL",
    "PARTIAL_SYNTHETIC_UI",
    "CONTRACT_IMPLEMENTED",
    "DOMAIN_CONTRACT_ONLY",
    "BACKEND_PARTIAL_UI_MISSING",
    "CONTRACT_ONLY",
    "MISSING",
}


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))

    assert contract["goal_id"] == "AXIGNAL-GOAL-001"
    assert contract["status"] == "NORMATIVE_CANDIDATE"
    assert contract["public_launch_authorised"] is False
    assert contract["perfect_ux_claim_authorised"] is False
    assert contract["design_target"] == "WCAG_2_2_AA"
    assert contract["architecture"]["sidebar_max_depth"] == 2

    global_destinations = contract["architecture"]["global_destinations"]
    workspace_destinations = contract["architecture"]["workspace_destinations"]
    assert len(global_destinations) == len(set(global_destinations)) >= 10
    assert len(workspace_destinations) == len(set(workspace_destinations)) >= 12

    inventory = contract["current_capability_inventory"]
    capabilities = [item["capability"] for item in inventory]
    assert len(capabilities) == len(set(capabilities))
    assert all(item["status"] in ALLOWED_STATUS for item in inventory)
    assert any(item["status"] == "MISSING" for item in inventory)
    assert next(
        item for item in inventory if item["capability"] == "TENDER_WORKSPACE_UI"
    )["status"] == "MISSING"

    integrity = contract["functional_integrity"]
    assert integrity["dead_controls_allowed"] == 0
    assert integrity["silent_fixture_fallback_allowed"] is False
    assert integrity["client_authority_allowed"] is False
    assert integrity["false_success_allowed"] is False
    assert len(integrity["required_states"]) >= 10

    acceptance = contract["acceptance"]
    assert acceptance["minimum_qualified_participants"] >= 8
    assert acceptance["external_authority_comprehension"] == 1.0
    assert acceptance["critical_accessibility_defects_max"] == 0
    assert acceptance["destructive_action_errors_max"] == 0
    assert acceptance["sus_median_min"] >= 85

    assert registry["goal_id"] == contract["goal_id"]
    assert registry["canonical_brand"] == "AXIGNAL"
    assert registry["canonical_domain"] == "axignal.com"
    skill_ids = [item["skill_id"] for item in registry["skills"]]
    assert len(skill_ids) == len(set(skill_ids)) >= 12
    assert set(registry["routing"]["mandatory_skill_ids"]) == set(skill_ids)

    for relative in contract["required_documents"]:
        assert (ROOT / relative).is_file(), relative

    print(
        json.dumps(
            {
                "status": "PASS",
                "contract": contract["schema_version"],
                "capabilities": len(inventory),
                "global_destinations": len(global_destinations),
                "workspace_destinations": len(workspace_destinations),
                "mandatory_skills": len(skill_ids),
                "public_launch_authorised": False,
                "perfect_ux_claim_authorised": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
