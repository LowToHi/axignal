from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data/contracts/AX-GE2E-G7-O01-T02-domain-contracts.v0.1.json"
DOMAIN_PATH = ROOT / "apps/api/src/axignal_api/procurement_domain.py"
DOMAIN_TEST_PATH = ROOT / "apps/api/tests/test_procurement_domain_contracts.py"
DEEPSEEK_PATH = ROOT / "apps/api/src/axignal_api/deepseek_proposals.py"
SETTINGS_PATH = ROOT / "apps/api/src/axignal_api/settings.py"
DEEPSEEK_TEST_PATH = ROOT / "apps/api/tests/test_deepseek_v4_flash_proposals.py"

EXPECTED_ENTITIES = {
    "SourceProvenance",
    "ProcurementFact",
    "OpportunityVersion",
    "Opportunity",
    "ProcurementContactChannel",
    "TenderWorkspace",
    "Clarification",
    "PolicyDecisionRecord",
    "AuditEvent",
}
EXPECTED_CONTACT_POLICIES = {"ALLOW", "CONTEXTUAL", "LINK_ONLY", "BLOCK"}
EXPECTED_DATA_CLASSES = {
    "INSTITUTIONAL",
    "FUNCTIONAL_NON_PERSONAL",
    "PROFESSIONAL_PERSONAL",
    "AMBIGUOUS_PERSONAL",
    "BLOCKED",
}
MODEL = "deepseek-v4-flash-0731"
OLD_MODEL = "deepseek-v4-flash"


class ContractVerificationError(RuntimeError):
    """Raised when the O01 domain contract violates the product boundary."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractVerificationError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"Missing contract file: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "Domain contract must be a JSON object")
    return value


def require_source_literals(path: Path, literals: tuple[str, ...]) -> str:
    require(path.is_file(), f"Missing implementation file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for literal in literals:
        require(literal in text, f"Missing literal {literal!r} in {path.relative_to(ROOT)}")
    return text


def verify_contract(contract: dict[str, Any]) -> None:
    require(
        contract["schema_version"] == "axignal.o01-domain-contracts/v0.1",
        "Unexpected domain-contract schema",
    )
    require(contract["task_id"] == "AX-GE2E-G7-O01-T02", "Task identity drift")
    require(contract["status"] == "IMPLEMENTED_CANDIDATE", "Unsafe task status")
    require(contract["output"] == "O01_DOMAIN_CONTRACTS_PASS", "Output contract drift")
    require(set(contract["entities"]) == EXPECTED_ENTITIES, "Domain entity set drift")

    claims = contract["claim_effect"]
    require(claims["source_state"] == "CANDIDATE", "TED source was activated")
    for key in (
        "product_admitted",
        "public_claim_contribution",
        "global_coverage_authorised",
        "multilingual_authorised",
        "public_launch_authorised",
    ):
        require(claims[key] is False, f"Unsafe claim transition: {key}")

    execution = contract["execution_boundary"]
    require(execution["external_ted_request_budget"] == 0, "External TED requests enabled")
    require(execution["real_campaign_authorised"] is False, "Real campaign authorised")
    require(execution["approvals"] == [], "Human approval was fabricated")
    require(
        execution["approval_survives_head_change"] is False,
        "Approval incorrectly survives a head change",
    )

    contacts = contract["contact_channel_contract"]
    require(contacts["entity"] == "ProcurementContactChannel", "Wrong contact entity")
    require(
        {"Person", "Lead", "CRMContact", "Prospect"}.issubset(
            set(contacts["not_entities"])
        ),
        "CRM/person exclusions are incomplete",
    )
    require(
        set(contacts["policy_decisions"]) == EXPECTED_CONTACT_POLICIES,
        "Contact policy set drift",
    )
    require(set(contacts["data_classes"]) == EXPECTED_DATA_CLASSES, "Data-class drift")
    invariants = contacts["invariants"]
    for key in (
        "global_person_search",
        "bulk_contact_export",
        "marketing_use",
        "cross_opportunity_reuse",
        "blocked_data_exposes_endpoint",
    ):
        require(invariants[key] is False, f"Unsafe contact invariant: {key}")
    for key in (
        "named_professional_contact_requires_contextual_policy",
        "ambiguous_personal_requires_link_only_or_block",
        "workspace_uses_channel_reference",
    ):
        require(invariants[key] is True, f"Missing contact invariant: {key}")

    workspace = contract["workspace_contract"]
    require(workspace["explicit_creation_required"] is True, "Workspace auto-created")
    require(
        workspace["external_presentation_is_user_attested"] is True,
        "Presentation ungoverned",
    )
    require(workspace["axignal_signs_or_submits_bid"] is False, "AXIGNAL gained bid authority")

    clarification = contract["clarification_contract"]
    require(clarification["subscriber_approval_required"] is True, "Approval not required")
    require(clarification["autonomous_send"] is False, "Autonomous communication enabled")
    require(
        clarification["sent_state_is_subscriber_confirmed"] is True,
        "Send state ungoverned",
    )

    audit = contract["audit_contract"]
    require(audit["contact_endpoint_replication"] is False, "Audit replicates contacts")
    require(audit["message_body_replication"] is False, "Audit replicates message bodies")

    checkpoint = contract["ai_checkpoint"]
    require(checkpoint["provider"] == "deepseek", "Provider drift")
    require(checkpoint["base_url"] == "https://api.deepseek.com", "Base URL drift")
    require(checkpoint["model"] == MODEL, "Checkpoint drift")
    require(checkpoint["previous_model"] == OLD_MODEL, "Previous checkpoint trace missing")
    require(checkpoint["price_change_declared"] is False, "Unexpected price change")
    require(checkpoint["proposal_authority_only"] is True, "Model authority widened")
    require(checkpoint["canonical_claim_authority"] is False, "Model can write claims")
    require(checkpoint["external_action_authority"] is False, "Model can act externally")
    require(checkpoint["enabled_by_default"] is False, "Model enabled by default")

    prohibited = set(contract["prohibited_transitions"])
    require("AUTONOMOUS_BID_SUBMISSION" in prohibited, "Bid prohibition missing")
    require(
        "AUTONOMOUS_EXTERNAL_COMMUNICATION" in prohibited,
        "External communication prohibition missing",
    )


def verify_implementation() -> None:
    domain = require_source_literals(
        DOMAIN_PATH,
        (
            "class ProcurementContactChannel",
            "class TenderWorkspace",
            "class Clarification",
            "class PolicyDecisionRecord",
            "class AuditEvent",
            "Procurement contact channels cannot become CRM or marketing data",
            "External communication requires explicit subscriber approval",
        ),
    )
    for literal in EXPECTED_CONTACT_POLICIES | EXPECTED_DATA_CLASSES:
        require(literal in domain, f"Domain implementation is missing {literal}")

    tests = require_source_literals(
        DOMAIN_TEST_PATH,
        (
            "test_named_professional_channel_is_contextual_not_crm_data",
            "test_contact_channels_cannot_become_crm_or_marketing_data",
            "test_external_communication_requires_subscriber_approval_and_confirmation",
            "test_audit_event_does_not_replicate_contact_endpoint",
        ),
    )
    require("PRESENTED_EXTERNALLY" in tests, "Subscriber presentation test missing")

    deepseek = require_source_literals(
        DEEPSEEK_PATH,
        (
            f'DEEPSEEK_MODEL = "{MODEL}"',
            "proposal authority only",
            "canonical claims",
        ),
    )
    require(
        f'DEEPSEEK_MODEL = "{OLD_MODEL}"' not in deepseek,
        "Old checkpoint remains the admitted constant",
    )

    settings = require_source_literals(
        SETTINGS_PATH,
        (
            f'deepseek_model: str = "{MODEL}"',
            f'"{MODEL}"',
        ),
    )
    require(
        'deepseek_model: str = "deepseek-v4-flash"' not in settings,
        "Settings still default to the old checkpoint",
    )

    deepseek_tests = require_source_literals(
        DEEPSEEK_TEST_PATH,
        (
            MODEL,
            "test_deepseek_adapter_uses_direct_bounded_json_contract",
            "test_deepseek_adapter_rejects_non_official_host_and_wrong_model",
        ),
    )
    require(OLD_MODEL in deepseek_tests, "Old-model rejection is not tested")


def verify() -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH)
    verify_contract(contract)
    verify_implementation()
    files = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            CONTRACT_PATH,
            DOMAIN_PATH,
            DOMAIN_TEST_PATH,
            DEEPSEEK_PATH,
            SETTINGS_PATH,
            DEEPSEEK_TEST_PATH,
        )
    }
    return {
        "status": "PASS",
        "task_id": contract["task_id"],
        "output": contract["output"],
        "entities": len(EXPECTED_ENTITIES),
        "contact_policy_decisions": sorted(EXPECTED_CONTACT_POLICIES),
        "model": MODEL,
        "external_ted_request_budget": 0,
        "source_state": "CANDIDATE",
        "product_admitted": False,
        "public_launch_authorised": False,
        "files": files,
    }


def main() -> int:
    try:
        result = verify()
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        ContractVerificationError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
