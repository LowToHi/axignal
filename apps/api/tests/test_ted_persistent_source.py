from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from axignal_api.connectors.ted_xml import (
    TEDXMLConnector,
    TEDXMLRetrievalError,
    fixture_manifest_payload,
)
from axignal_api.persistent_procurement_research import ProcurementResearchRunCreate
from axignal_api.procurement_persistent_types import (
    EXCLUDED_IDENTITY_PREDICATES,
    PERSISTENT_AUTO_PREDICATES,
    PRODUCT_PROFILE,
    sanitise_retrieved_lifecycle,
)
from axignal_api.procurement_queue import (
    ProcurementAdmissionJob,
    ProcurementRetrievalJob,
)

FIXTURES = Path(__file__).parent / "fixtures"
MANIFEST = FIXTURES / "ted_persistent_fixture_manifest.json"
NUMBERS = ("10000001-2026", "10000002-2026", "10000003-2026", "10000004-2026")


def connector() -> TEDXMLConnector:
    return TEDXMLConnector(live_enabled=False, fixture_manifest_path=MANIFEST)


def test_direct_xml_url_is_pinned_to_official_host_and_exact_path() -> None:
    assert (
        TEDXMLConnector.direct_xml_url("10000001-2026")
        == "https://ted.europa.eu/en/notice/10000001-2026/xml"
    )
    with pytest.raises(TEDXMLRetrievalError):
        TEDXMLConnector.validate_publication_number("../secret")
    with pytest.raises(TEDXMLRetrievalError):
        TEDXMLConnector.validate_publication_number("https://example.com")


def test_fixture_manifest_is_relative_bounded_and_deterministic() -> None:
    payload = fixture_manifest_payload(
        {
            "10000002-2026": "b.xml",
            "10000001-2026": "a.xml",
        }
    )
    assert list(payload) == ["10000001-2026", "10000002-2026"]
    with pytest.raises(TEDXMLRetrievalError):
        fixture_manifest_payload({"10000001-2026": "/tmp/a.xml"})


def test_persistent_lifecycle_excludes_identity_and_personal_values() -> None:
    retrieved = tuple(connector().fetch(number) for number in NUMBERS)
    lifecycle = sanitise_retrieved_lifecycle(retrieved)

    assert lifecycle.source_id == "src_ted_search_api_v3"
    assert lifecycle.package_projection()["product_profile"] == PRODUCT_PROFILE
    assert len(lifecycle.notices) == 4
    assert lifecycle.claims
    assert lifecycle.personal_field_element_count > 0
    assert all(item.predicate in PERSISTENT_AUTO_PREDICATES for item in lifecycle.claims)
    assert not ({item.predicate for item in lifecycle.claims} & EXCLUDED_IDENTITY_PREDICATES)
    encoded = json.dumps(
        {
            "projection": lifecycle.package_projection(),
            "claims": [item.evidence_payload() for item in lifecycle.claims],
        },
        sort_keys=True,
    ).casefold()
    assert "excluded@example.invalid" not in encoded
    assert "winner@example.invalid" not in encoded
    assert '"email"' not in encoded
    assert '"telephone"' not in encoded
    assert '"contact"' not in encoded
    assert all(item.raw_content_hash.startswith("sha256:") for item in lifecycle.notices)
    assert all(item.evidence_content_hash.startswith("sha256:") for item in lifecycle.claims)


def test_retrieval_and_admission_jobs_roundtrip() -> None:
    tenant_id = UUID("11111111-1111-4111-8111-111111111111")
    run_id = UUID("22222222-2222-4222-8222-222222222222")
    handoff_id = UUID("33333333-3333-4333-8333-333333333333")
    retrieval = ProcurementRetrievalJob(
        tenant_id=tenant_id,
        research_run_id=run_id,
        publication_numbers=NUMBERS,
    )
    assert ProcurementRetrievalJob.from_payload(retrieval.as_payload()) == retrieval
    admission = ProcurementAdmissionJob(
        tenant_id=tenant_id,
        research_run_id=run_id,
        admission_handoff_id=handoff_id,
        expected_package_hash="sha256:" + "a" * 64,
        publication_numbers=NUMBERS,
    )
    assert ProcurementAdmissionJob.from_payload(admission.as_payload()) == admission
    tampered = admission.as_payload() | {"policy_version": "unknown@9.9.9"}
    with pytest.raises(ValueError):
        ProcurementAdmissionJob.from_payload(tampered)


def test_procurement_research_command_is_bounded() -> None:
    command = ProcurementResearchRunCreate(
        context_id="ctx_procurement_001",
        opportunity_id="opp_eu_ted_001",
        question="Reconstruct the official procurement lifecycle.",
        publication_numbers=list(NUMBERS),
    )
    assert len(command.publication_numbers) == 4
    with pytest.raises(ValidationError):
        ProcurementResearchRunCreate(
            context_id="ctx_procurement_001",
            opportunity_id="opp_eu_ted_001",
            question="Research",
            publication_numbers=["10000001-2026", "10000001-2026"],
        )


def test_connector_rejects_dtd_and_manifest_escape(tmp_path: Path) -> None:
    evil = tmp_path / "evil.xml"
    evil.write_text("<!DOCTYPE x [<!ENTITY y 'z'>]><x>&y;</x>", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"10000001-2026": "evil.xml"}), encoding="utf-8")
    with pytest.raises(TEDXMLRetrievalError, match="DTD"):
        TEDXMLConnector(live_enabled=False, fixture_manifest_path=manifest).fetch(
            "10000001-2026"
        )

    outside = tmp_path.parent / "outside.xml"
    outside.write_text("<x/>", encoding="utf-8")
    manifest.write_text(
        json.dumps({"10000001-2026": "../outside.xml"}), encoding="utf-8"
    )
    with pytest.raises(TEDXMLRetrievalError, match="escapes"):
        TEDXMLConnector(live_enabled=False, fixture_manifest_path=manifest).fetch(
            "10000001-2026"
        )
