from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = (
    ROOT
    / "data/acceptance/legal/AX-LIB-O01-TED-official-terms-snapshot.v0.1.json"
)
MATRIX_PATH = (
    ROOT / "data/acceptance/legal/AX-LIB-O01-TED-field-rights-matrix.v0.1.json"
)
APPROVAL_PATH = (
    ROOT
    / "data/acceptance/approvals/"
    "AX-LIB-O01-legal-privacy-approval-request.v0.1.json"
)
BUNDLE_PATH = (
    ROOT
    / "data/acceptance/source-rights/"
    "AX-LIB-O01-source-inventory-rights.v0.1.json"
)
DOSSIER_PATH = ROOT / "data/acceptance/library-coverage/AX-LIB-O01.json"

EXPECTED_SOURCE_ID = "src_ted_search_api_v3"
EXPECTED_LIBRARY_ID = "AX-LIB-O01"
EXPECTED_GATE_ID = "PUBLIC-LAUNCH-GATE-7"
OFFICIAL_HOSTS = {
    "https://ted.europa.eu/",
    "https://docs.ted.europa.eu/",
    "https://eur-lex.europa.eu/",
}
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
    """Raised when Gate 7 source-rights evidence violates the fail-closed contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RightsVerificationError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"Missing required evidence file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"Evidence must be an object: {path}")
    return payload


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_expiry(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def require_current_expiry(value: str, label: str) -> None:
    expiry = parse_expiry(value)
    require(expiry.tzinfo is not None, f"{label} expiry must be timezone-aware")
    require(expiry > datetime.now(timezone.utc), f"{label} evidence is expired")


def recursive_signatures(node: Any, location: str = "$") -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{location}.{key}"
            if key == "signature":
                found.append((child, value))
            found.extend(recursive_signatures(value, child))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(recursive_signatures(value, f"{location}[{index}]"))
    return found


def evidence_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["reference"]: item for item in items}


def verify() -> dict[str, Any]:
    snapshot = load_json(SNAPSHOT_PATH)
    matrix = load_json(MATRIX_PATH)
    approval = load_json(APPROVAL_PATH)
    bundle = load_json(BUNDLE_PATH)
    dossier = load_json(DOSSIER_PATH)

    require(
        snapshot["schema_version"] == "axignal.legal-source-snapshot/v0.1",
        "Unexpected legal source snapshot schema",
    )
    require(snapshot["gate_id"] == EXPECTED_GATE_ID, "Snapshot gate mismatch")
    require(snapshot["library_id"] == EXPECTED_LIBRARY_ID, "Snapshot library mismatch")
    require(snapshot["source_id"] == EXPECTED_SOURCE_ID, "Snapshot source mismatch")
    require(snapshot["legal_decision"] == "MISSING", "Machine snapshot cannot approve Legal")
    require(
        snapshot["privacy_data_rights_decision"] == "MISSING",
        "Machine snapshot cannot approve Privacy/Data Rights",
    )
    require(
        snapshot["machine_assessment"]["status"] == "PROVISIONAL_NON_AUTHORITATIVE",
        "Legal machine assessment must remain non-authoritative",
    )
    require_current_expiry(snapshot["expires_at"], "Legal source snapshot")
    source_documents = snapshot["source_documents"]
    require(len(source_documents) >= 4, "Official legal source set is incomplete")
    document_ids = {document["document_id"] for document in source_documents}
    require(len(document_ids) == len(source_documents), "Duplicate legal source document ID")
    for document in source_documents:
        url = document["url"]
        require(
            any(url.startswith(host) for host in OFFICIAL_HOSTS),
            f"Non-official legal source URL: {url}",
        )
        require(
            document["authority"] in {"PRIMARY", "PRIMARY_LEGAL_ACT"},
            f"Non-primary legal source: {document['document_id']}",
        )

    require(
        matrix["schema_version"] == "axignal.field-rights-matrix/v0.1",
        "Unexpected field-rights matrix schema",
    )
    require(matrix["gate_id"] == EXPECTED_GATE_ID, "Matrix gate mismatch")
    require(matrix["library_id"] == EXPECTED_LIBRARY_ID, "Matrix library mismatch")
    require(matrix["source_id"] == EXPECTED_SOURCE_ID, "Matrix source mismatch")
    require(
        matrix["overall_status"] == "PENDING_TYPED_HUMAN_APPROVAL",
        "Field-rights matrix must remain pending human approval",
    )
    require(matrix["default_policy"] == "DENY_UNLESS_EXPLICITLY_ALLOWED", "Unsafe default")
    require_current_expiry(matrix["expires_at"], "Field-rights matrix")
    claim_effect = matrix["claim_effect"]
    require(claim_effect["source_state"] == "CANDIDATE", "Matrix activated TED")
    require(claim_effect["legal_admission"] == "MISSING", "Matrix approved Legal")
    require(claim_effect["rights_admission"] == "MISSING", "Matrix approved rights")
    require(claim_effect["public_claim_contribution"] is False, "Matrix enabled claims")
    require(claim_effect["global_coverage_authorised"] is False, "Matrix enabled global claim")
    require(claim_effect["multilingual_authorised"] is False, "Matrix enabled language claim")

    fields = {item["field_class"]: item for item in matrix["fields"]}
    require(set(fields) == REQUIRED_FIELD_CLASSES, "Field-rights matrix class drift")
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
        "Public API redistribution is not fail-closed",
    )
    require(
        fields["MODEL_TRAINING_OR_FINE_TUNING"]["product_policy"] == "DENIED",
        "Model training is not denied",
    )
    require(
        matrix["human_approval_requirements"]["LEGAL"]["status"] == "MISSING",
        "Legal approval was fabricated",
    )
    require(
        matrix["human_approval_requirements"]["PRIVACY_DATA_RIGHTS"]["status"]
        == "MISSING",
        "Privacy/Data Rights approval was fabricated",
    )

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
    require(approval["approvals"] == [], "Approval request contains unsigned approvals")
    require(
        set(approval["requested_authorities"]) == {"LEGAL", "PRIVACY_DATA_RIGHTS"},
        "Approval authority set mismatch",
    )
    require(
        set(approval["approval_contract"]["required_fields"]) == REQUIRED_APPROVAL_FIELDS,
        "Typed approval contract is incomplete",
    )
    require(
        approval["approval_contract"]["approval_survives_head_change"] is False,
        "Approval incorrectly survives a head change",
    )

    require(
        bundle["schema_version"] == "axignal.source-inventory-rights-bundle/v0.2",
        "Unexpected source-rights bundle schema",
    )
    require(bundle["decision"] == "IN_PROGRESS", "Source-rights bundle is not in progress")
    require(bundle["claim_contribution"] is False, "Source-rights bundle enabled claims")
    require(bundle["inventory"]["active"] == [], "Source-rights bundle activated a source")
    require(bundle["inventory"]["exhaustive"] is False, "Inventory falsely marked exhaustive")
    require_current_expiry(bundle["expires_at"], "Source-rights bundle")
    require(len(bundle["sources"]) == 1, "Unexpected O01 source count")
    source = bundle["sources"][0]
    require(source["source_id"] == EXPECTED_SOURCE_ID, "Bundle source mismatch")
    require(source["state"] == "CANDIDATE", "Bundle activated TED")
    require(source["contributes_to_public_claim"] is False, "Bundle enabled claims")
    require(source["admission"]["technical"] == "PASS", "Technical evidence regressed")
    for dimension in ("legal", "quality", "rights", "human_authority"):
        require(source["admission"][dimension] == "MISSING", f"{dimension} was fabricated")
    require(source["field_policy"]["model_training"] == "DENIED", "Training enabled")
    require(source["field_policy"]["raw_payload_storage"] == "DENIED", "Raw storage enabled")
    require(
        source["field_policy"]["public_api_redistribution"].startswith("DENIED_PENDING_"),
        "Redistribution enabled",
    )
    terms_review = source["terms_review"]
    require(
        terms_review["status"] == "PENDING_TYPED_HUMAN_APPROVAL",
        "Terms review advanced without human approval",
    )
    require(terms_review["signature"] is None, "Machine terms review contains signature")

    expected_hashes = {
        str(SNAPSHOT_PATH.relative_to(ROOT)): sha256_file(SNAPSHOT_PATH),
        str(MATRIX_PATH.relative_to(ROOT)): sha256_file(MATRIX_PATH),
        str(APPROVAL_PATH.relative_to(ROOT)): sha256_file(APPROVAL_PATH),
        str(BUNDLE_PATH.relative_to(ROOT)): sha256_file(BUNDLE_PATH),
    }
    bundle_evidence = evidence_map(source["evidence"])
    for reference in (
        str(SNAPSHOT_PATH.relative_to(ROOT)),
        str(MATRIX_PATH.relative_to(ROOT)),
        str(APPROVAL_PATH.relative_to(ROOT)),
    ):
        require(reference in bundle_evidence, f"Bundle missing evidence: {reference}")
        require(
            bundle_evidence[reference]["sha256"] == expected_hashes[reference],
            f"Bundle digest mismatch: {reference}",
        )

    require(dossier["canonical_state"] == "BLOCKED", "O01 dossier advanced")
    require(dossier["claim_decision"] == "DENIED", "O01 claim was enabled")
    require(dossier["sources"]["active"] == [], "O01 activated a source")
    require(dossier["sources"]["suspended"] == [], "Unexpected suspended source")
    require(len(dossier["sources"]["candidate"]) == 1, "Unexpected O01 candidate count")
    dossier_source = dossier["sources"]["candidate"][0]
    require(dossier_source["source_id"] == EXPECTED_SOURCE_ID, "Dossier source mismatch")
    require(dossier_source["state"] == "CANDIDATE", "Dossier activated TED")
    require(dossier_source["contributes_to_public_claim"] is False, "Dossier enabled claims")
    for dimension in ("legal", "quality", "rights", "human_authority"):
        require(
            dossier_source["admission"][dimension] == "MISSING",
            f"Dossier {dimension} was fabricated",
        )
    require(dossier["rights"]["status"] == "MISSING", "Dossier rights were approved")
    require(dossier["reviews"] == [], "Dossier contains unverified human reviews")
    dossier_evidence = evidence_map(dossier_source["evidence"])
    for reference, digest in expected_hashes.items():
        require(reference in dossier_evidence, f"Dossier missing evidence: {reference}")
        require(
            dossier_evidence[reference]["sha256"] == digest,
            f"Dossier digest mismatch: {reference}",
        )

    for label, payload in (
        ("snapshot", snapshot),
        ("matrix", matrix),
        ("approval", approval),
        ("bundle", bundle),
        ("dossier", dossier),
    ):
        for location, value in recursive_signatures(payload):
            require(
                value in (None, ""),
                f"Unexpected signature in {label} at {location}",
            )

    return {
        "status": "PASS",
        "library_id": EXPECTED_LIBRARY_ID,
        "source_id": EXPECTED_SOURCE_ID,
        "source_state": "CANDIDATE",
        "legal_admission": "MISSING",
        "rights_admission": "MISSING",
        "privacy_data_rights_approval": "MISSING",
        "human_authority": "MISSING",
        "claim_contribution": False,
        "field_classes_checked": len(fields),
        "official_sources_checked": len(source_documents),
        "source_snapshots": expected_hashes,
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
