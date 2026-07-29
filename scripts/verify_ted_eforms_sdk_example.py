from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse

import httpx

from axignal_api.connectors.ted_eforms import (
    MAX_XML_BYTES,
    SUPPORTED_CUSTOMIZATION_ID,
    SUPPORTED_NOTICE_SUBTYPE,
    SUPPORTED_NOTICE_TYPE,
    TEDEFormsCN16Parser,
)

SOURCE_URL = (
    "https://raw.githubusercontent.com/OP-TED/eForms-SDK/1.14.2/"
    "examples/notices/cn_24_minimal.xml"
)
EXPECTED_HOST = "raw.githubusercontent.com"
EXPECTED_PATH = "/OP-TED/eForms-SDK/1.14.2/examples/notices/cn_24_minimal.xml"
OUTPUT = Path("ted-eforms-sdk-example-evidence.json")


def validate_source_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise RuntimeError("Official SDK example requires HTTPS")
    if parsed.hostname != EXPECTED_HOST or parsed.path != EXPECTED_PATH:
        raise RuntimeError("Official SDK example URL is outside the pinned allowlist")
    if parsed.username or parsed.password or parsed.port not in {None, 443}:
        raise RuntimeError("Official SDK example URL contains forbidden authority data")
    if parsed.query or parsed.fragment:
        raise RuntimeError("Official SDK example URL must not contain query or fragment")


def main() -> int:
    validate_source_url(SOURCE_URL)
    with httpx.Client(
        timeout=20.0,
        follow_redirects=False,
        headers={"user-agent": "AXIGNAL/0.1 eForms-SDK-parser-verification"},
    ) as client:
        response = client.get(SOURCE_URL)
    if response.is_redirect:
        raise RuntimeError("Official SDK example request redirected")
    if response.status_code != 200:
        raise RuntimeError(f"Official SDK example returned status {response.status_code}")
    if len(response.content) > MAX_XML_BYTES:
        raise RuntimeError("Official SDK example exceeded the parser size budget")
    content_type = response.headers.get("content-type", "").casefold()
    if "xml" not in content_type and "text/plain" not in content_type:
        raise RuntimeError("Official SDK example returned an unexpected content type")

    parsed = TEDEFormsCN16Parser().parse(response.content)
    if parsed.customization_id != SUPPORTED_CUSTOMIZATION_ID:
        raise RuntimeError("Official SDK example customization drifted")
    if parsed.notice_type != SUPPORTED_NOTICE_TYPE:
        raise RuntimeError("Official SDK example notice type drifted")
    if parsed.notice_subtype != SUPPORTED_NOTICE_SUBTYPE:
        raise RuntimeError("Official SDK example notice subtype drifted")

    claims = parsed.candidate_claims()
    forbidden_tokens = ("contact", "email", "phone", "telephone", "person")
    if any(token in claim.predicate.casefold() for claim in claims for token in forbidden_tokens):
        raise RuntimeError("Parser emitted a personal-contact claim")

    evidence = {
        "goal_id": "AXIGNAL-GOAL-001",
        "task_id": "AX-F8-T11",
        "source": "OP-TED/eForms-SDK",
        "source_release": "1.14.2",
        "source_url": SOURCE_URL,
        "source_licence": "CC-BY-4.0",
        "raw_content_hash": parsed.raw_content_hash,
        "raw_content_persisted": False,
        "raw_values_persisted": False,
        "notice_identity_hash": (
            f"sha256:{sha256(parsed.notice_id.encode('utf-8')).hexdigest()}"
        ),
        "notice_identity_persisted": False,
        "document_type": parsed.document_type,
        "customization_id": parsed.customization_id,
        "ubl_version": parsed.ubl_version,
        "notice_type": parsed.notice_type,
        "notice_subtype": parsed.notice_subtype,
        "organisation_count": len(parsed.organisations),
        "buyer_reference_count": len(parsed.buyer_organisation_refs),
        "lot_count": len(parsed.lots),
        "candidate_claim_count": len(claims),
        "unique_candidate_fingerprint_count": len({claim.fingerprint for claim in claims}),
        "personal_field_elements_observed": parsed.personal_field_element_count,
        "personal_values_emitted": False,
        "model_calls": 0,
        "canonical_claim_writes": 0,
        "source_product_admitted": False,
        "universe_supported": False,
        "runtime_enabled": False,
        "verified_at": datetime.now(UTC).isoformat(),
    }
    if evidence["candidate_claim_count"] != evidence["unique_candidate_fingerprint_count"]:
        raise RuntimeError("Candidate claim fingerprints are not unique")
    if evidence["personal_field_elements_observed"] < 1:
        raise RuntimeError("Official example no longer exercises personal-field exclusion")

    OUTPUT.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "PASS official eForms SDK example",
        parsed.customization_id,
        parsed.notice_type,
        parsed.notice_subtype,
        len(claims),
        parsed.raw_content_hash,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
