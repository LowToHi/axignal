from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / (
    "data/acceptance/legal/AX-LIB-O01-TED-official-terms-snapshot.v0.1.json"
)
MATRIX_PATH = ROOT / (
    "data/acceptance/legal/AX-LIB-O01-TED-field-rights-matrix.v0.1.json"
)
APPROVAL_PATH = ROOT / (
    "data/acceptance/approvals/"
    "AX-LIB-O01-legal-privacy-approval-request.v0.1.json"
)
BUNDLE_PATH = ROOT / (
    "data/acceptance/source-rights/"
    "AX-LIB-O01-source-inventory-rights.v0.1.json"
)
DOSSIER_PATH = ROOT / "data/acceptance/library-coverage/AX-LIB-O01.json"

SOURCE_ID = "src_ted_search_api_v3"
LIBRARY_ID = "AX-LIB-O01"
GATE_ID = "PUBLIC-LAUNCH-GATE-7"
OFFICIAL_HOSTS = (
    "https://ted.europa.eu/",
    "https://docs.ted.europa.eu/",
    "https://eur-lex.europa.eu/",
)
REQUIRED_FIELD_CLASSES = {
    "SIMAP_SYSTEM_METADATA",
    "NOTICE_IDENTIFIERS_AND_PUBLICATION_METADATA",
    "NON_PERSONAL_PROCUREMENT_FACTS",
    "BUYER_AND_SUPPLIER_LEGAL_ENTITY_DATA",
    "PROFESSIONAL_CONTACT_PERSON_DATA",
    "NATURAL_PERSON_TENDERER_OR_CONTRACTOR",
    "SOURCE_NATIVE_NOTICE_TEXT",
    "ATTACHMENTS_AND_THIRD_PARTY_WORKS",
    "LOGOS_TRADEMARKS_NAMES_AND_INDUSTRIAL_PROPERTY",
    "SIMAP_EDITORIAL_DOCUMENTATION",
    "NORMALISED_DERIVED_FACTS_AND_TRANSLATIONS",
    "PUBLIC_API_REDISTRIBUTION",
    "MODEL_TRAINING_OR_FINE_TUNING",
}
REQUIRED_APPROVAL_FIELDS = {
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


class RightsVerificationError(RuntimeError):
    """Raised when source-rights evidence violates the fail-closed contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RightsVerificationError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"Missing evidence: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Evidence must be an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_current_expiry(value: str, label: str) -> None:
    expiry = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(expiry.tzinfo is not None, f"{label} expiry must include a timezone")
    require(expiry > datetime.now(UTC), f"{label} evidence is expired")


def evidence_by_reference(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["reference"]: item for item in items}


def iter_signatures(node: Any, location: str = "$") -> list[tuple[str, Any]]:
    signatures: list[tuple[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{location}.{key}"
            if key == "signature":
                signatures.append((child, value))
            signatures.extend(iter_signatures(value, child))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            signatures.extend(iter_signatures(value, f"{location}[{index}]"))
    return signatures


def verify_official_snapshot(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    require(
        snapshot["schema_version"] == "axignal.legal-source-snapshot/v0.1",
        "Unexpected legal snapshot schema",
    )
    require(snapshot["gate_id"] == GATE_ID, "Legal snapshot gate mismatch")
    require(snapshot["library_id"] == LIBRARY_ID, "Legal snapshot library mismatch")
    require(snapshot["source_id"] == SOURCE_ID, "Legal snapshot source mismatch")
    require(snapshot["legal_decision"] == "MISSING", "Machine approved Legal")
    require(
        snapshot["privacy_data_rights_decision"] == "MISSING",
        "Machine approved Privacy/Data Rights",
    )
    require(
        snapshot["machine_assessment"]["status"] == "PROVISIONAL_NON_AUTHORITATIVE",
        "Machine legal assessment became authoritative",
    )
    require_current_expiry(snapshot["expires_at"], "Legal snapshot")

    documents = snapshot["source_documents"]
    require(len(documents) >= 4, "Official legal source set is incomplete")
    require(
        len({item["document_id"] for item in documents}) == len(documents),
        "Duplicate legal source document ID",
    )
    for document in documents:
        require(
            document["authority"] in {"PRIMARY", "PRIMARY_LEGAL_ACT"},
            f"Non-primary source: {document['document_id']}",
        )
        require(
            document["url"].startswith(OFFICIAL_HOSTS),
            f"Non-official source URL: {document['url']}",
        )
    return documents


def verify_field_matrix(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    require(
        matrix["schema_version"] == "axignal.field-rights-matrix/v0.1",
        "Unexpected rights-matrix schema",
    )
    require(matrix["gate_id"] == GATE_ID, "Rights matrix gate mismatch")
    require(matrix["library_id"] == LIBRARY_ID, "Rights matrix library mismatch")
    require(matrix["source_id"] == SOURCE_ID, "Rights matrix source mismatch")
    require(
        matrix["overall_status"] == "PENDING_TYPED_HUMAN_APPROVAL",
        "Rights matrix advanced without human approval",
    )
    require(matrix["default_policy"] == "DENY_UNLESS_EXPLICITLY_ALLOWED", "Unsafe default")
    require_current_expiry(matrix["expires_at"], "Rights matrix")

    claim = matrix["claim_effect"]
    expected_claim = {
        "source_state": "CANDIDATE",
        "legal_admission": "MISSING",
        "rights_admission": "MISSING",
        "public_claim_contribution": False,
        "global_coverage_authorised": False,
        "multilingual_authorised": False,
    }
    for key, expected in expected_claim.items():
        require(claim[key] == expected, f"Unsafe claim transition: {key}")

    fields = {item["field_class"]: item for item in matrix["fields"]}
    require(set(fields) == REQUIRED_FIELD_CLASSES, "Rights-matrix field-class drift")
    require(
        all(item["human_decision_required"] is True for item in fields.values()),
        "Every field class must require a human decision",
    )
    require(
        fields["PROFESSIONAL_CONTACT_PERSON_DATA"]["product_policy"].startswith("BLOCK_"),
        "Professional contact data is not blocked",
    )
    require(
        fields["NATURAL_PERSON_TENDERER_OR_CONTRACTOR"]["product_policy"].startswith(
            "BLOCK_"
        ),
        "Natural-person tenderer data is not blocked",
    )
    require(
        fields["ATTACHMENTS_AND_THIRD_PARTY_WORKS"]["product_policy"].startswith("DENY_"),
        "Third-party attachments are not denied",
    )
    require(
        fields["LOGOS_TRADEMARKS_NAMES_AND_INDUSTRIAL_PROPERTY"]["product_policy"]
        == "DENIED",
        "Protected marks are not denied",
    )
    require(
        fields["PUBLIC_API_REDISTRIBUTION"]["product_policy"].startswith(
            "DENIED_PENDING_"
        ),
        "Public API redistribution is enabled",
    )
    require(
        fields["MODEL_TRAINING_OR_FINE_TUNING"]["product_policy"] == "DENIED",
        "Model training is enabled",
    )
    for authority in ("LEGAL", "PRIVACY_DATA_RIGHTS"):
        require(
            matrix["human_approval_requirements"][authority]["status"] == "MISSING",
            f"{authority} approval was fabricated",
        )
    return fields


def verify_approval_request(approval: dict[str, Any]) -> None:
    require(
        approval["schema_version"] == "axignal.typed-approval-request/v0.1",
        "Unexpected approval-request schema",
    )
    require(
        approval["status"] == "BLOCKED_UNTIL_EXACT_HEAD_IS_FROZEN",
        "Approval request advanced before exact-head freeze",
    )
    require(approval["target_head_sha"] is None, "Approval request has premature head")
    require(approval["manifest_digest"] is None, "Approval request has premature manifest")
    require(approval["approvals"] == [], "Approval request contains an unsigned decision")
    require(
        set(approval["requested_authorities"]) == {"LEGAL", "PRIVACY_DATA_RIGHTS"},
        "Approval authority set mismatch",
    )
    contract = approval["approval_contract"]
    require(
        set(contract["required_fields"]) == REQUIRED_APPROVAL_FIELDS,
        "Typed approval fields are incomplete",
    )
    require(
        contract["approval_survives_head_change"] is False,
        "Approval incorrectly survives a head change",
    )


def verify_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    require(
        bundle["schema_version"] == "axignal.source-inventory-rights-bundle/v0.2",
        "Unexpected source-rights bundle schema",
    )
    require(bundle["decision"] == "IN_PROGRESS", "Source-rights bundle advanced")
    require(bundle["claim_contribution"] is False, "Source-rights bundle enabled claims")
    require(bundle["inventory"]["active"] == [], "Source-rights bundle activated a source")
    require(bundle["inventory"]["exhaustive"] is False, "Inventory falsely exhaustive")
    require_current_expiry(bundle["expires_at"], "Source-rights bundle")
    require(len(bundle["sources"]) == 1, "Unexpected O01 source count")

    source = bundle["sources"][0]
    require(source["source_id"] == SOURCE_ID, "Bundle source mismatch")
    require(source["state"] == "CANDIDATE", "Bundle activated TED")
    require(source["contributes_to_public_claim"] is False, "Bundle enabled claims")
    require(source["admission"]["technical"] == "PASS", "Technical evidence regressed")
    for dimension in ("legal", "quality", "rights", "human_authority"):
        require(source["admission"][dimension] == "MISSING", f"Fabricated {dimension}")
    require(source["field_policy"]["model_training"] == "DENIED", "Training enabled")
    require(source["field_policy"]["raw_payload_storage"] == "DENIED", "Raw storage enabled")
    require(
        source["field_policy"]["public_api_redistribution"].startswith("DENIED_PENDING_"),
        "Redistribution enabled",
    )
    review = source["terms_review"]
    require(
        review["status"] == "PENDING_TYPED_HUMAN_APPROVAL",
        "Terms review advanced without a human decision",
    )
    require(review["signature"] is None, "Machine terms review contains a signature")
    return source


def verify_dossier(dossier: dict[str, Any]) -> dict[str, Any]:
    require(dossier["canonical_state"] == "BLOCKED", "O01 dossier advanced")
    require(dossier["claim_decision"] == "DENIED", "O01 claim was enabled")
    require(dossier["sources"]["active"] == [], "O01 activated a source")
    require(dossier["sources"]["suspended"] == [], "Unexpected suspended source")
    require(len(dossier["sources"]["candidate"]) == 1, "Unexpected candidate count")
    source = dossier["sources"]["candidate"][0]
    require(source["source_id"] == SOURCE_ID, "Dossier source mismatch")
    require(source["state"] == "CANDIDATE", "Dossier activated TED")
    require(source["contributes_to_public_claim"] is False, "Dossier enabled claims")
    for dimension in ("legal", "quality", "rights", "human_authority"):
        require(source["admission"][dimension] == "MISSING", f"Fabricated {dimension}")
    require(dossier["rights"]["status"] == "MISSING", "Dossier rights were approved")
    require(dossier["reviews"] == [], "Dossier contains unverified reviews")
    return source


def verify_cross_file_digests(
    bundle_source: dict[str, Any],
    dossier_source: dict[str, Any],
) -> dict[str, str]:
    paths = (SNAPSHOT_PATH, MATRIX_PATH, APPROVAL_PATH, BUNDLE_PATH)
    expected = {str(path.relative_to(ROOT)): sha256_file(path) for path in paths}
    bundle_refs = evidence_by_reference(bundle_source["evidence"])
    dossier_refs = evidence_by_reference(dossier_source["evidence"])

    for reference, digest in expected.items():
        if reference != str(BUNDLE_PATH.relative_to(ROOT)):
            require(reference in bundle_refs, f"Bundle missing evidence: {reference}")
            require(
                bundle_refs[reference]["sha256"] == digest,
                f"Bundle hash mismatch: {reference}",
            )
        require(reference in dossier_refs, f"Dossier missing evidence: {reference}")
        require(
            dossier_refs[reference]["sha256"] == digest,
            f"Dossier hash mismatch: {reference}",
        )
    return expected


def verify_no_machine_signatures(payloads: dict[str, dict[str, Any]]) -> None:
    for label, payload in payloads.items():
        for location, value in iter_signatures(payload):
            require(value in (None, ""), f"Unexpected signature in {label} at {location}")


def verify() -> dict[str, Any]:
    snapshot = load_json(SNAPSHOT_PATH)
    matrix = load_json(MATRIX_PATH)
    approval = load_json(APPROVAL_PATH)
    bundle = load_json(BUNDLE_PATH)
    dossier = load_json(DOSSIER_PATH)

    documents = verify_official_snapshot(snapshot)
    fields = verify_field_matrix(matrix)
    verify_approval_request(approval)
    bundle_source = verify_bundle(bundle)
    dossier_source = verify_dossier(dossier)
    hashes = verify_cross_file_digests(bundle_source, dossier_source)
    verify_no_machine_signatures(
        {
            "snapshot": snapshot,
            "matrix": matrix,
            "approval": approval,
            "bundle": bundle,
            "dossier": dossier,
        }
    )

    return {
        "status": "PASS",
        "library_id": LIBRARY_ID,
        "source_id": SOURCE_ID,
        "source_state": "CANDIDATE",
        "legal_admission": "MISSING",
        "rights_admission": "MISSING",
        "privacy_data_rights_approval": "MISSING",
        "human_authority": "MISSING",
        "claim_contribution": False,
        "field_classes_checked": len(fields),
        "official_sources_checked": len(documents),
        "source_snapshots": hashes,
        "controls": {
            "personal_data_blocked": True,
            "third_party_content_blocked": True,
            "protected_marks_blocked": True,
            "raw_payload_storage_denied": True,
            "public_api_redistribution_denied": True,
            "model_training_denied": True,
            "typed_human_approval_required": True,
        },
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
        RightsVerificationError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
