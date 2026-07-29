from __future__ import annotations

from pathlib import Path

import pytest

from axignal_api.connectors.ted_eforms import (
    SUPPORTED_CUSTOMIZATION_ID,
    TEDEFormsCN16Parser,
    TEDEFormsParseError,
)

FIXTURE = Path(__file__).parent / "fixtures" / "ted_eforms_cn16_synthetic.xml"
ESTIMATED_VALUE_XML = (
    b'<cbc:EstimatedOverallContractAmount currencyID="EUR">'
    b"750000.00</cbc:EstimatedOverallContractAmount>"
)


def fixture_bytes() -> bytes:
    return FIXTURE.read_bytes()


def test_parser_extracts_versioned_non_personal_procurement_structure() -> None:
    notice = TEDEFormsCN16Parser().parse(fixture_bytes())

    assert notice.document_type == "ContractNotice"
    assert notice.customization_id == SUPPORTED_CUSTOMIZATION_ID
    assert notice.ubl_version == "2.3"
    assert notice.notice_id == "123e4567-e89b-42d3-a456-426614174000"
    assert notice.version_id == "01"
    assert notice.notice_type == "cn-standard"
    assert notice.notice_subtype == "16"
    assert notice.notice_languages == ("ENG", "SPA")
    assert notice.procedure_identifier == "PROC-SYNTHETIC-001"
    assert notice.procedure_type == "open"
    assert notice.buyer_organisation_refs == ("ORG-0001",)
    assert len(notice.organisations) == 1
    assert notice.organisations[0].national_identifier == "SYNTHETIC-ORG-001"
    assert notice.organisations[0].nuts_codes == ("ES425",)
    assert notice.procedure_project is not None
    assert notice.procedure_project.cpv_codes == ("72212732",)
    assert notice.procedure_project.estimated_value == "750000.00"
    assert notice.procedure_project.estimated_value_currency == "EUR"
    assert len(notice.lots) == 1
    assert notice.lots[0].lot_id == "LOT-0001"
    assert notice.lots[0].submission_deadline_date == "2026-09-15+02:00"
    assert notice.lots[0].submission_deadline_time == "12:00:00+02:00"
    assert notice.lots[0].eu_funding_indicator == "eu-funds"
    assert notice.personal_field_element_count == 3
    assert notice.raw_content_hash.startswith("sha256:")


def test_candidate_claims_are_deterministic_and_exclude_contact_values() -> None:
    parser = TEDEFormsCN16Parser()
    first = parser.parse(fixture_bytes()).candidate_claims()
    second = parser.parse(fixture_bytes()).candidate_claims()

    assert first == second
    assert [claim.fingerprint for claim in first] == [claim.fingerprint for claim in second]
    assert len({claim.fingerprint for claim in first}) == len(first)
    predicates = {claim.predicate for claim in first}
    assert "procurement_notice_type" in predicates
    assert "procurement_buyer_official_name" in predicates
    assert "procurement_cpv_code" in predicates
    assert "procurement_place_of_performance_nuts" in predicates
    assert "procurement_submission_deadline" in predicates
    assert "procurement_estimated_value" in predicates
    assert "procurement_eu_funding_indicator" in predicates
    serialised = repr(first).casefold()
    assert "excluded@example.invalid" not in serialised
    assert "+34 000 000 000" not in serialised
    assert all(
        token not in claim.predicate.casefold()
        for claim in first
        for token in ("email", "phone", "telephone", "contact", "person")
    )


def test_missing_optional_fields_remain_absent_not_zero() -> None:
    xml = fixture_bytes().replace(ESTIMATED_VALUE_XML, b"").replace(
        b"<cbc:EndDate>2026-09-15+02:00</cbc:EndDate>",
        b"",
    )
    notice = TEDEFormsCN16Parser().parse(xml)

    assert notice.procedure_project is not None
    assert notice.procedure_project.estimated_value is None
    assert notice.procedure_project.estimated_value_currency is None
    assert notice.lots[0].submission_deadline_date is None
    values = [claim.value for claim in notice.candidate_claims()]
    assert 0 not in values
    assert "0" not in values


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            b"eforms-sdk-1.14",
            b"eforms-sdk-1.15",
            "Unsupported eForms customization",
        ),
        (
            b">16</cbc:SubTypeCode>",
            b">17</cbc:SubTypeCode>",
            "Unsupported TED notice subtype",
        ),
        (
            b">cn-standard</cbc:NoticeTypeCode>",
            b">can-standard</cbc:NoticeTypeCode>",
            "Unsupported TED notice type",
        ),
        (
            b">2.3</cbc:UBLVersionID>",
            b">2.2</cbc:UBLVersionID>",
            "Unsupported UBL version",
        ),
    ],
)
def test_parser_fails_closed_on_profile_drift(old: bytes, new: bytes, message: str) -> None:
    with pytest.raises(TEDEFormsParseError, match=message):
        TEDEFormsCN16Parser().parse(fixture_bytes().replace(old, new, 1))


def test_parser_rejects_unknown_document_type() -> None:
    xml = fixture_bytes().replace(
        b"urn:oasis:names:specification:ubl:schema:xsd:ContractNotice-2",
        b"urn:oasis:names:specification:ubl:schema:xsd:PriorInformationNotice-2",
        1,
    )
    with pytest.raises(TEDEFormsParseError, match="document type"):
        TEDEFormsCN16Parser().parse(xml)


def test_parser_rejects_dtd_and_entity_declarations() -> None:
    malicious = (
        b'<?xml version="1.0"?><!DOCTYPE x ['
        b'<!ENTITY y SYSTEM "file:///etc/passwd">]><x>&y;</x>'
    )
    with pytest.raises(TEDEFormsParseError, match="DTD and entity"):
        TEDEFormsCN16Parser().parse(malicious)


def test_parser_rejects_oversized_payload() -> None:
    with pytest.raises(TEDEFormsParseError, match="size budget"):
        TEDEFormsCN16Parser().parse(b" " * 2_097_153)


def test_parser_rejects_unresolved_buyer_reference() -> None:
    xml = fixture_bytes().replace(b">ORG-0001</cbc:ID>", b">ORG-9999</cbc:ID>", 1)
    with pytest.raises(TEDEFormsParseError, match="unresolved"):
        TEDEFormsCN16Parser().parse(xml)


def test_parser_rejects_duplicate_organisation_ids() -> None:
    company = b"""
            <efac:Organization>
              <efac:Company>
                <cac:PartyIdentification>
                  <cbc:ID schemeName="organization">ORG-0001</cbc:ID>
                </cac:PartyIdentification>
                <cac:PartyName>
                  <cbc:Name languageID="ENG">Duplicate</cbc:Name>
                </cac:PartyName>
              </efac:Company>
            </efac:Organization>
    """
    xml = fixture_bytes().replace(
        b"</efac:Organizations>",
        company + b"</efac:Organizations>",
    )
    with pytest.raises(TEDEFormsParseError, match="Duplicate organisation ID"):
        TEDEFormsCN16Parser().parse(xml)
