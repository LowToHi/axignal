from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from axignal_api.o01_contact_policy import (
    O01_CONTACT_POLICY_VERSION,
    evaluate_o01_contact_policy,
    policy_matrix,
)
from axignal_api.procurement_domain import (
    ContactChannelType,
    ContactDataClass,
    ContactPolicyDecision,
)

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_MATRIX_PATH = ROOT / (
    "data/acceptance/legal/AX-LIB-O01-TED-field-rights-matrix.v0.1.json"
)
RECONCILIATION_PATH = ROOT / (
    "data/acceptance/legal/"
    "AX-LIB-O01-TED-contact-policy-reconciliation.v0.2.json"
)
APPROVAL_REQUEST_PATH = ROOT / (
    "data/acceptance/approvals/"
    "AX-LIB-O01-legal-privacy-approval-request.v0.2.json"
)
DOMAIN_CONTRACT_PATH = ROOT / (
    "data/contracts/AX-GE2E-G7-O01-T02-domain-contracts.v0.1.json"
)
POLICY_SOURCE_PATH = ROOT / "apps/api/src/axignal_api/o01_contact_policy.py"
POLICY_TEST_PATH = ROOT / "apps/api/tests/test_o01_contact_policy.py"

EXPECTED_POLICY = {
    "INSTITUTIONAL": "ALLOW",
    "FUNCTIONAL_NON_PERSONAL": "ALLOW",
    "PROFESSIONAL_PERSONAL": "CONTEXTUAL",
    "AMBIGUOUS_PERSONAL": "LINK_ONLY",
    "BLOCKED": "BLOCK",
}
EXPECTED_REQUIRED_FIELDS = {
    "authority",
    "decision",
    "scope",
    "manifest_digest",
    "head_sha",
    "timestamp",
    "expiry",
    "conditions",
    "signature",
}
UNTOUCHED_PROHIBITIONS = {
    "NATURAL_PERSON_TENDERER_OR_CONTRACTOR",
    "ATTACHMENTS_AND_THIRD_PARTY_WORKS",
    "LOGOS_TRADEMARKS_NAMES_AND_INDUSTRIAL_PROPERTY",
    "PUBLIC_API_REDISTRIBUTION",
    "MODEL_TRAINING_OR_FINE_TUNING",
    "RAW_FULL_PAYLOAD",
    "FULL_SOURCE_NATIVE_TEXT",
}


class ReconciliationVerificationError(RuntimeError):
    """Raised when the O01 legal/privacy reconciliation is unsafe or incomplete."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReconciliationVerificationError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"Expected JSON object: {path}")
    return payload


def require_current_expiry(value: str, label: str) -> None:
    expiry = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(expiry.tzinfo is not None, f"{label} expiry lacks timezone")
    require(expiry > datetime.now(UTC), f"{label} is expired")


def iter_signatures(node: Any, location: str = "$") -> list[tuple[str, Any]]:
    result: list[tuple[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{location}.{key}"
            if key == "signature":
                result.append((child, value))
            if key == "signatures":
                result.append((child, value))
            result.extend(iter_signatures(value, child))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            result.extend(iter_signatures(value, f"{location}[{index}]"))
    return result


def verify_historical_baseline(matrix: dict[str, Any]) -> None:
    require(
        matrix["schema_version"] == "axignal.field-rights-matrix/v0.1",
        "Historical matrix schema drift",
    )
    fields = {item["field_class"]: item for item in matrix["fields"]}
    historical = fields["PROFESSIONAL_CONTACT_PERSON_DATA"]
    require(
        historical["product_policy"].startswith("BLOCK_"),
        "Historical blanket block was silently rewritten",
    )
    require(
        matrix["overall_status"] == "PENDING_TYPED_HUMAN_APPROVAL",
        "Historical matrix gained authority",
    )


def verify_domain_binding(
    reconciliation: dict[str, Any],
    domain_contract: dict[str, Any],
) -> None:
    binding = reconciliation["domain_contract_binding"]
    require(binding["task_id"] == "AX-GE2E-G7-O01-T02", "Wrong T02 binding")
    require(
        binding["path"] == str(DOMAIN_CONTRACT_PATH.relative_to(ROOT)),
        "Domain contract path drift",
    )
    require(
        domain_contract["output"] == binding["required_output"],
        "T02 output binding failed",
    )
    require(
        binding["required_entity"] in domain_contract["entities"],
        "ProcurementContactChannel is absent from T02",
    )
    contact = domain_contract["contact_channel_contract"]
    require(
        set(binding["required_policy_decisions"])
        == set(contact["policy_decisions"]),
        "Contact decision vocabulary drift",
    )
    require(
        set(binding["required_data_classes"]) == set(contact["data_classes"]),
        "Contact data-class vocabulary drift",
    )


def verify_reconciliation(reconciliation: dict[str, Any]) -> None:
    require(
        reconciliation["schema_version"]
        == "axignal.o01-contact-policy-reconciliation/v0.2",
        "Unexpected reconciliation schema",
    )
    require(
        reconciliation["task_id"] == "AX-GE2E-G7-O01-T03",
        "Task identity drift",
    )
    require(
        reconciliation["status"]
        == "IMPLEMENTED_CANDIDATE_PENDING_TYPED_APPROVAL",
        "Reconciliation advanced without typed approval",
    )
    require(
        reconciliation["policy_version"] == O01_CONTACT_POLICY_VERSION,
        "Policy version drift",
    )
    require_current_expiry(reconciliation["expires_at"], "Reconciliation")

    supersession = reconciliation["supersession"]
    require(
        supersession["historical_matrix"]
        == str(HISTORICAL_MATRIX_PATH.relative_to(ROOT)),
        "Historical matrix reference drift",
    )
    require(
        supersession["affected_field_class"] == "PROFESSIONAL_CONTACT_PERSON_DATA",
        "Supersession scope widened",
    )
    require(
        supersession["scope"] == "CONTACT_CHANNEL_CLASSIFICATION_AND_USE_ONLY",
        "Supersession is not narrowly scoped",
    )
    require(
        supersession["historical_evidence_remains_immutable"] is True,
        "Historical evidence was made mutable",
    )
    require(
        set(supersession["unaffected_prohibitions"]) == UNTOUCHED_PROHIBITIONS,
        "Unrelated prohibitions changed",
    )

    policy = {item["data_class"]: item for item in reconciliation["contact_policy"]}
    require(set(policy) == set(EXPECTED_POLICY), "Contact policy is not total")
    for data_class, decision in EXPECTED_POLICY.items():
        require(policy[data_class]["decision"] == decision, f"Policy drift: {data_class}")
        require(policy[data_class]["conditions"], f"Missing conditions: {data_class}")

    require(
        policy["PROFESSIONAL_PERSONAL"]["persistence"]
        == "OPPORTUNITY_SCOPED_REFERENCE_PENDING_TYPED_PRIVACY_DECISION",
        "Professional-personal retention was pre-approved",
    )
    require(
        policy["AMBIGUOUS_PERSONAL"]["persistence"]
        == "SOURCE_LINK_ONLY_NO_ENDPOINT_PERSISTENCE",
        "Ambiguous personal endpoint persistence enabled",
    )
    require(policy["BLOCKED"]["allowed_actions"] == [], "Blocked actions enabled")

    invariants = reconciliation["global_invariants"]
    for key in (
        "person_entity_created",
        "lead_or_prospect_entity_created",
        "crm_replication",
        "global_person_search",
        "bulk_contact_export",
        "marketing_use",
        "cross_opportunity_reuse",
        "autonomous_external_communication",
        "audit_endpoint_replication",
        "message_body_replication",
    ):
        require(invariants[key] is False, f"Unsafe invariant: {key}")
    for key in (
        "subscriber_approval_required_before_external_handoff",
        "subscriber_confirmation_required_for_sent_state",
        "source_provenance_required",
    ):
        require(invariants[key] is True, f"Missing invariant: {key}")

    for authority in ("LEGAL", "PRIVACY_DATA_RIGHTS"):
        decision = reconciliation["human_decisions_required"][authority]
        require(decision["status"] == "MISSING", f"{authority} was fabricated")
        require(decision["must_decide"], f"{authority} question set is empty")

    effect = reconciliation["campaign_effect"]
    require(effect["campaign_status"] == "BLOCKED", "Campaign unblocked")
    require(effect["execution_authorised"] is False, "Execution authorised")
    require(effect["external_request_budget"] == 0, "External budget enabled")
    require(effect["source_state"] == "CANDIDATE", "TED source activated")
    for key in (
        "product_admitted",
        "public_claim_contribution",
        "global_coverage_authorised",
        "multilingual_authorised",
        "public_launch_authorised",
    ):
        require(effect[key] is False, f"Unsafe claim transition: {key}")
    require(reconciliation["approvals"] == [], "Unsigned approval inserted")
    require(reconciliation["signatures"] == [], "Machine signature inserted")


def verify_executable_policy(reconciliation: dict[str, Any]) -> None:
    json_policy = {
        item["data_class"]: item["decision"]
        for item in reconciliation["contact_policy"]
    }
    code_policy = {
        item.data_class.value: item.decision.value for item in policy_matrix()
    }
    require(json_policy == code_policy, "Executable and legal policy matrices differ")

    examples = (
        (
            ContactDataClass.INSTITUTIONAL,
            ContactChannelType.PROCUREMENT_PLATFORM,
            ContactPolicyDecision.ALLOW,
        ),
        (
            ContactDataClass.FUNCTIONAL_NON_PERSONAL,
            ContactChannelType.FUNCTIONAL_EMAIL,
            ContactPolicyDecision.ALLOW,
        ),
        (
            ContactDataClass.PROFESSIONAL_PERSONAL,
            ContactChannelType.NAMED_PROFESSIONAL_EMAIL,
            ContactPolicyDecision.CONTEXTUAL,
        ),
        (
            ContactDataClass.AMBIGUOUS_PERSONAL,
            ContactChannelType.SOURCE_LINK_ONLY,
            ContactPolicyDecision.LINK_ONLY,
        ),
    )
    for data_class, channel_type, expected in examples:
        outcome = evaluate_o01_contact_policy(
            data_class=data_class,
            channel_type=channel_type,
        )
        require(outcome.decision is expected, f"Runtime policy drift: {data_class}")


def verify_approval_request(approval: dict[str, Any]) -> None:
    require(
        approval["schema_version"] == "axignal.typed-approval-request/v0.2",
        "Unexpected approval schema",
    )
    require(
        approval["task_id"] == "AX-GE2E-G7-O01-T03",
        "Approval task identity drift",
    )
    require(
        approval["status"]
        == "BLOCKED_PENDING_EXACT_HEAD_MANIFEST_AND_TYPED_DECISIONS",
        "Approval request advanced prematurely",
    )
    require(
        set(approval["requested_authorities"]) == {"LEGAL", "PRIVACY_DATA_RIGHTS"},
        "Approval authority set drift",
    )
    require(approval["target_head_sha"] is None, "Repository contains a stale head")
    require(approval["target_git_tree"] is None, "Repository contains a stale tree")
    require(approval["manifest_digest"] is None, "Repository contains a stale manifest")
    require(approval["manifest_artifact_id"] is None, "Repository contains stale artifact ID")
    require(approval["manifest_expiry"] is None, "Repository contains stale expiry")
    require(approval["approvals"] == [], "Approval request contains decisions")

    contract = approval["approval_contract"]
    require(
        set(contract["required_fields"]) == EXPECTED_REQUIRED_FIELDS,
        "Typed approval fields are incomplete",
    )
    require(contract["approval_survives_head_change"] is False, "Head drift accepted")
    require(
        contract["approval_survives_manifest_change"] is False,
        "Manifest drift accepted",
    )
    require(
        contract["partial_or_informal_approval_valid"] is False,
        "Informal approval accepted",
    )

    scope = approval["decision_scope"]
    require(scope["contact_policy"]["INSTITUTIONAL"] == "ALLOW", "Scope drift")
    require(
        scope["contact_policy"]["PROFESSIONAL_PERSONAL"] == "CONTEXTUAL",
        "Professional-personal scope drift",
    )
    require(
        scope["contact_policy"]["AMBIGUOUS_PERSONAL"] == "LINK_ONLY_OR_BLOCK",
        "Ambiguous-personal scope drift",
    )
    for key in (
        "public_product_admission",
        "public_claim_authority",
        "public_launch_authority",
        "autonomous_external_communication",
        "bid_submission_authority",
    ):
        require(scope[key] is False, f"Approval request overreaches: {key}")


def verify_source_contract() -> None:
    source = POLICY_SOURCE_PATH.read_text(encoding="utf-8")
    tests = POLICY_TEST_PATH.read_text(encoding="utf-8")
    required_source_literals = (
        "O01_CONTACT_POLICY_VERSION",
        "OPPORTUNITY_SCOPED_REFERENCE_PENDING_TYPED_PRIVACY_DECISION",
        "SOURCE_LINK_ONLY_NO_ENDPOINT_PERSISTENCE",
        "validate_o01_contact_channel",
    )
    for literal in required_source_literals:
        require(literal in source, f"Missing source literal: {literal}")
    required_test_literals = (
        "test_policy_matrix_is_total_and_versioned",
        "test_named_professional_contact_is_contextual_and_opportunity_scoped",
        "test_ambiguous_personal_data_degrades_to_source_link_only",
        "test_non_procurement_and_crm_use_remain_forbidden",
    )
    for literal in required_test_literals:
        require(literal in tests, f"Missing test: {literal}")


def verify_no_machine_signatures(payloads: dict[str, dict[str, Any]]) -> None:
    for label, payload in payloads.items():
        for location, value in iter_signatures(payload):
            require(value in (None, "", []), f"Unexpected signature in {label}: {location}")


def verify() -> dict[str, Any]:
    historical = load_json(HISTORICAL_MATRIX_PATH)
    reconciliation = load_json(RECONCILIATION_PATH)
    approval = load_json(APPROVAL_REQUEST_PATH)
    domain_contract = load_json(DOMAIN_CONTRACT_PATH)

    verify_historical_baseline(historical)
    verify_domain_binding(reconciliation, domain_contract)
    verify_reconciliation(reconciliation)
    verify_executable_policy(reconciliation)
    verify_approval_request(approval)
    verify_source_contract()
    verify_no_machine_signatures(
        {
            "historical": historical,
            "reconciliation": reconciliation,
            "approval": approval,
            "domain_contract": domain_contract,
        }
    )

    files = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            HISTORICAL_MATRIX_PATH,
            RECONCILIATION_PATH,
            APPROVAL_REQUEST_PATH,
            DOMAIN_CONTRACT_PATH,
            POLICY_SOURCE_PATH,
            POLICY_TEST_PATH,
        )
    }
    return {
        "status": "PASS",
        "task_id": "AX-GE2E-G7-O01-T03",
        "output": "O01_LEGAL_PRIVACY_RECONCILIATION_PASS",
        "policy_version": O01_CONTACT_POLICY_VERSION,
        "contact_policy": EXPECTED_POLICY,
        "legal_decision": "MISSING",
        "privacy_data_rights_decision": "MISSING",
        "campaign_status": "BLOCKED",
        "execution_authorised": False,
        "external_request_budget": 0,
        "source_state": "CANDIDATE",
        "product_admitted": False,
        "public_claim_contribution": False,
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
        ReconciliationVerificationError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
