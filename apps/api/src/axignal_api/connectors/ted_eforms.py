from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from xml.etree.ElementTree import Element

from defusedxml import ElementTree as SafeElementTree
from defusedxml.common import DefusedXmlException

MAX_XML_BYTES = 2_097_152
SUPPORTED_CUSTOMIZATION_ID = "eforms-sdk-1.14"
SUPPORTED_UBL_VERSION = "2.3"
SUPPORTED_DOCUMENT_TYPE = "ContractNotice"
SUPPORTED_NOTICE_TYPE = "cn-standard"
SUPPORTED_NOTICE_SUBTYPE = "16"
NOTICE_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

NS = {
    "cn": "urn:oasis:names:specification:ubl:schema:xsd:ContractNotice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
    "efac": "http://data.europa.eu/p27/eforms-ubl-extension-aggregate-components/1",
    "efbc": "http://data.europa.eu/p27/eforms-ubl-extension-basic-components/1",
    "efext": "http://data.europa.eu/p27/eforms-ubl-extensions/1",
}

PERSONAL_LOCAL_NAMES = {
    "Contact",
    "ElectronicMail",
    "FamilyName",
    "FirstName",
    "Person",
    "Telefax",
    "Telephone",
}


class TEDEFormsParseError(RuntimeError):
    """Raised when an eForms notice violates the version-pinned parser contract."""


@dataclass(frozen=True)
class LocalisedText:
    value: str
    language: str | None


@dataclass(frozen=True)
class ProcurementOrganisation:
    organisation_id: str
    names: tuple[LocalisedText, ...]
    national_identifier: str | None
    nuts_codes: tuple[str, ...]
    country_codes: tuple[str, ...]


@dataclass(frozen=True)
class ProcurementProject:
    names: tuple[LocalisedText, ...]
    descriptions: tuple[LocalisedText, ...]
    contract_nature: str | None
    cpv_codes: tuple[str, ...]
    nuts_codes: tuple[str, ...]
    country_codes: tuple[str, ...]
    estimated_value: str | None
    estimated_value_currency: str | None


@dataclass(frozen=True)
class ProcurementLot:
    lot_id: str
    project: ProcurementProject | None
    submission_deadline_date: str | None
    submission_deadline_time: str | None
    eu_funding_indicator: str | None


@dataclass(frozen=True)
class ProcurementCandidateClaim:
    predicate: str
    subject_key: str
    value: Any
    source_path: str
    authority: str = "OBSERVED"

    @property
    def fingerprint(self) -> str:
        material = "\x1f".join(
            (
                self.authority,
                self.predicate,
                self.subject_key,
                repr(self.value),
                self.source_path,
            )
        )
        return f"sha256:{sha256(material.encode('utf-8')).hexdigest()}"


@dataclass(frozen=True)
class ParsedTEDEFormsNotice:
    document_type: str
    customization_id: str
    ubl_version: str
    notice_id: str
    version_id: str
    issue_date: str
    issue_time: str | None
    notice_type: str
    notice_subtype: str
    notice_languages: tuple[str, ...]
    procedure_identifier: str | None
    procedure_type: str | None
    buyer_organisation_refs: tuple[str, ...]
    organisations: tuple[ProcurementOrganisation, ...]
    procedure_project: ProcurementProject | None
    lots: tuple[ProcurementLot, ...]
    personal_field_element_count: int
    raw_content_hash: str

    def candidate_claims(self) -> tuple[ProcurementCandidateClaim, ...]:
        claims: list[ProcurementCandidateClaim] = [
            ProcurementCandidateClaim(
                predicate="procurement_notice_type",
                subject_key=self.notice_id,
                value=self.notice_type,
                source_path="/ContractNotice/cbc:NoticeTypeCode",
            ),
            ProcurementCandidateClaim(
                predicate="procurement_notice_subtype",
                subject_key=self.notice_id,
                value=self.notice_subtype,
                source_path=(
                    "/ContractNotice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/"
                    "efext:EformsExtension/efac:NoticeSubType/cbc:SubTypeCode"
                ),
            ),
            ProcurementCandidateClaim(
                predicate="procurement_notice_issue_date",
                subject_key=self.notice_id,
                value=self.issue_date,
                source_path="/ContractNotice/cbc:IssueDate",
            ),
        ]
        if self.procedure_identifier:
            claims.append(
                ProcurementCandidateClaim(
                    predicate="procurement_procedure_identifier",
                    subject_key=self.notice_id,
                    value=self.procedure_identifier,
                    source_path="/ContractNotice/cbc:ContractFolderID",
                )
            )
        if self.procedure_type:
            claims.append(
                ProcurementCandidateClaim(
                    predicate="procurement_procedure_type",
                    subject_key=self.notice_id,
                    value=self.procedure_type,
                    source_path="/ContractNotice/cac:TenderingProcess/cbc:ProcedureCode",
                )
            )
        organisation_map = {item.organisation_id: item for item in self.organisations}
        for buyer_ref in self.buyer_organisation_refs:
            buyer = organisation_map.get(buyer_ref)
            claims.append(
                ProcurementCandidateClaim(
                    predicate="procurement_buyer_organisation_ref",
                    subject_key=self.notice_id,
                    value=buyer_ref,
                    source_path=(
                        "/ContractNotice/cac:ContractingParty/cac:Party/"
                        "cac:PartyIdentification/cbc:ID"
                    ),
                )
            )
            if buyer:
                for name in buyer.names:
                    claims.append(
                        ProcurementCandidateClaim(
                            predicate="procurement_buyer_official_name",
                            subject_key=buyer_ref,
                            value={"text": name.value, "language": name.language},
                            source_path=(
                                "/ContractNotice/ext:UBLExtensions/.../efac:Organizations/"
                                "efac:Organization/efac:Company/cac:PartyName/cbc:Name"
                            ),
                        )
                    )
                if buyer.national_identifier:
                    claims.append(
                        ProcurementCandidateClaim(
                            predicate="procurement_buyer_identifier",
                            subject_key=buyer_ref,
                            value=buyer.national_identifier,
                            source_path=(
                                "/ContractNotice/ext:UBLExtensions/.../efac:Company/"
                                "cac:PartyLegalEntity/cbc:CompanyID"
                            ),
                        )
                    )
        self._append_project_claims(
            claims,
            subject_key=self.notice_id,
            project=self.procedure_project,
            path_prefix="/ContractNotice/cac:ProcurementProject",
        )
        for lot in self.lots:
            lot_subject = f"{self.notice_id}:{lot.lot_id}"
            claims.append(
                ProcurementCandidateClaim(
                    predicate="procurement_lot_identifier",
                    subject_key=lot_subject,
                    value=lot.lot_id,
                    source_path="/ContractNotice/cac:ProcurementProjectLot/cbc:ID",
                )
            )
            self._append_project_claims(
                claims,
                subject_key=lot_subject,
                project=lot.project,
                path_prefix="/ContractNotice/cac:ProcurementProjectLot/cac:ProcurementProject",
            )
            if lot.submission_deadline_date:
                claims.append(
                    ProcurementCandidateClaim(
                        predicate="procurement_submission_deadline",
                        subject_key=lot_subject,
                        value={
                            "date": lot.submission_deadline_date,
                            "time": lot.submission_deadline_time,
                        },
                        source_path=(
                            "/ContractNotice/cac:ProcurementProjectLot/cac:TenderingProcess/"
                            "cac:TenderSubmissionDeadlinePeriod"
                        ),
                    )
                )
            if lot.eu_funding_indicator:
                claims.append(
                    ProcurementCandidateClaim(
                        predicate="procurement_eu_funding_indicator",
                        subject_key=lot_subject,
                        value=lot.eu_funding_indicator,
                        source_path=(
                            "/ContractNotice/cac:ProcurementProjectLot/cac:TenderingTerms/"
                            "cbc:FundingProgramCode"
                        ),
                    )
                )
        return tuple(claims)

    @staticmethod
    def _append_project_claims(
        claims: list[ProcurementCandidateClaim],
        *,
        subject_key: str,
        project: ProcurementProject | None,
        path_prefix: str,
    ) -> None:
        if project is None:
            return
        for cpv_code in project.cpv_codes:
            claims.append(
                ProcurementCandidateClaim(
                    predicate="procurement_cpv_code",
                    subject_key=subject_key,
                    value=cpv_code,
                    source_path=f"{path_prefix}/cac:MainCommodityClassification/cbc:ItemClassificationCode",
                )
            )
        for nuts_code in project.nuts_codes:
            claims.append(
                ProcurementCandidateClaim(
                    predicate="procurement_place_of_performance_nuts",
                    subject_key=subject_key,
                    value=nuts_code,
                    source_path=(
                        f"{path_prefix}/cac:RealizedLocation/cac:Address/"
                        "cbc:CountrySubentityCode"
                    ),
                )
            )
        if project.contract_nature:
            claims.append(
                ProcurementCandidateClaim(
                    predicate="procurement_contract_nature",
                    subject_key=subject_key,
                    value=project.contract_nature,
                    source_path=f"{path_prefix}/cbc:ProcurementTypeCode",
                )
            )
        if project.estimated_value is not None:
            claims.append(
                ProcurementCandidateClaim(
                    predicate="procurement_estimated_value",
                    subject_key=subject_key,
                    value={
                        "amount": project.estimated_value,
                        "currency": project.estimated_value_currency,
                    },
                    source_path=f"{path_prefix}/cbc:EstimatedOverallContractAmount",
                )
            )


class TEDEFormsCN16Parser:
    """Fail-closed parser for ContractNotice subtype 16 under eForms SDK 1.14."""

    def parse(self, xml_bytes: bytes) -> ParsedTEDEFormsNotice:
        if not xml_bytes:
            raise TEDEFormsParseError("TED eForms XML is empty")
        if len(xml_bytes) > MAX_XML_BYTES:
            raise TEDEFormsParseError("TED eForms XML exceeded the parser size budget")
        lowered = xml_bytes.lower()
        if b"<!doctype" in lowered or b"<!entity" in lowered:
            raise TEDEFormsParseError("DTD and entity declarations are prohibited")
        try:
            root = SafeElementTree.fromstring(xml_bytes)
        except (DefusedXmlException, SafeElementTree.ParseError) as exc:
            raise TEDEFormsParseError("TED eForms XML is malformed or unsafe") from exc

        expected_root = f"{{{NS['cn']}}}{SUPPORTED_DOCUMENT_TYPE}"
        if root.tag != expected_root:
            raise TEDEFormsParseError("Unsupported TED eForms document type")

        customization_id = self._required_text(root, "cbc:CustomizationID")
        if customization_id != SUPPORTED_CUSTOMIZATION_ID:
            raise TEDEFormsParseError(
                f"Unsupported eForms customization {customization_id!r}; "
                f"expected {SUPPORTED_CUSTOMIZATION_ID!r}"
            )
        ubl_version = self._required_text(root, "cbc:UBLVersionID")
        if ubl_version != SUPPORTED_UBL_VERSION:
            raise TEDEFormsParseError("Unsupported UBL version")

        notice_id_element = root.find("cbc:ID[@schemeName='notice-id']", NS)
        notice_id = self._required_element_text(notice_id_element, "notice ID")
        if not NOTICE_UUID_PATTERN.fullmatch(notice_id):
            raise TEDEFormsParseError("Notice ID is not a version-4 UUID")
        version_id = self._required_text(root, "cbc:VersionID")
        if not re.fullmatch(r"[0-9]{2}", version_id) or version_id == "00":
            raise TEDEFormsParseError("Notice version ID is invalid")

        notice_type = self._required_text(root, "cbc:NoticeTypeCode")
        if notice_type != SUPPORTED_NOTICE_TYPE:
            raise TEDEFormsParseError("Unsupported TED notice type")
        notice_subtype = self._required_text(
            root,
            "ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/"
            "efext:EformsExtension/efac:NoticeSubType/cbc:SubTypeCode",
        )
        if notice_subtype != SUPPORTED_NOTICE_SUBTYPE:
            raise TEDEFormsParseError("Unsupported TED notice subtype")

        organisations = self._parse_organisations(root)
        buyer_refs = tuple(
            self._text(element)
            for element in root.findall(
                "cac:ContractingParty/cac:Party/cac:PartyIdentification/"
                "cbc:ID[@schemeName='organization']",
                NS,
            )
            if self._text(element)
        )
        if not buyer_refs:
            raise TEDEFormsParseError("Contract notice has no buyer organisation reference")
        known_ids = {item.organisation_id for item in organisations}
        if any(reference not in known_ids for reference in buyer_refs):
            raise TEDEFormsParseError("Buyer organisation reference is unresolved")

        return ParsedTEDEFormsNotice(
            document_type=SUPPORTED_DOCUMENT_TYPE,
            customization_id=customization_id,
            ubl_version=ubl_version,
            notice_id=notice_id,
            version_id=version_id,
            issue_date=self._required_text(root, "cbc:IssueDate"),
            issue_time=self._optional_text(root, "cbc:IssueTime"),
            notice_type=notice_type,
            notice_subtype=notice_subtype,
            notice_languages=tuple(self._texts(root, "cbc:NoticeLanguageCode")),
            procedure_identifier=self._optional_text(root, "cbc:ContractFolderID"),
            procedure_type=self._optional_text(
                root,
                "cac:TenderingProcess/cbc:ProcedureCode",
            ),
            buyer_organisation_refs=buyer_refs,
            organisations=organisations,
            procedure_project=self._parse_project(root.find("cac:ProcurementProject", NS)),
            lots=tuple(
                self._parse_lot(element)
                for element in root.findall("cac:ProcurementProjectLot", NS)
            ),
            personal_field_element_count=self._count_personal_elements(root),
            raw_content_hash=f"sha256:{sha256(xml_bytes).hexdigest()}",
        )

    def _parse_organisations(self, root: Element) -> tuple[ProcurementOrganisation, ...]:
        organisations: list[ProcurementOrganisation] = []
        seen: set[str] = set()
        for company in root.findall(
            "ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/"
            "efext:EformsExtension/efac:Organizations/efac:Organization/efac:Company",
            NS,
        ):
            identifier_element = company.find(
                "cac:PartyIdentification/cbc:ID[@schemeName='organization']",
                NS,
            )
            organisation_id = self._required_element_text(
                identifier_element,
                "organisation ID",
            )
            if organisation_id in seen:
                raise TEDEFormsParseError("Duplicate organisation ID")
            seen.add(organisation_id)
            names = tuple(
                LocalisedText(value=self._text(element), language=element.get("languageID"))
                for element in company.findall("cac:PartyName/cbc:Name", NS)
                if self._text(element)
            )
            if not names:
                raise TEDEFormsParseError("Organisation has no official name")
            organisations.append(
                ProcurementOrganisation(
                    organisation_id=organisation_id,
                    names=names,
                    national_identifier=self._optional_text(
                        company,
                        "cac:PartyLegalEntity/cbc:CompanyID",
                    ),
                    nuts_codes=tuple(
                        self._texts(
                            company,
                            "cac:PostalAddress/cbc:CountrySubentityCode[@listName='nuts']",
                        )
                    ),
                    country_codes=tuple(
                        self._texts(
                            company,
                            "cac:PostalAddress/cac:Country/"
                            "cbc:IdentificationCode[@listName='country']",
                        )
                    ),
                )
            )
        if not organisations:
            raise TEDEFormsParseError("Contract notice has no organisations")
        return tuple(organisations)

    def _parse_lot(self, element: Element) -> ProcurementLot:
        lot_id_element = element.find("cbc:ID[@schemeName='Lot']", NS)
        lot_id = self._required_element_text(lot_id_element, "lot ID")
        return ProcurementLot(
            lot_id=lot_id,
            project=self._parse_project(element.find("cac:ProcurementProject", NS)),
            submission_deadline_date=self._optional_text(
                element,
                "cac:TenderingProcess/cac:TenderSubmissionDeadlinePeriod/cbc:EndDate",
            ),
            submission_deadline_time=self._optional_text(
                element,
                "cac:TenderingProcess/cac:TenderSubmissionDeadlinePeriod/cbc:EndTime",
            ),
            eu_funding_indicator=self._optional_text(
                element,
                "cac:TenderingTerms/cbc:FundingProgramCode[@listName='eu-funded']",
            ),
        )

    def _parse_project(self, element: Element | None) -> ProcurementProject | None:
        if element is None:
            return None
        amount_element = element.find("cbc:EstimatedOverallContractAmount", NS)
        return ProcurementProject(
            names=tuple(
                LocalisedText(value=self._text(item), language=item.get("languageID"))
                for item in element.findall("cbc:Name", NS)
                if self._text(item)
            ),
            descriptions=tuple(
                LocalisedText(value=self._text(item), language=item.get("languageID"))
                for item in element.findall("cbc:Description", NS)
                if self._text(item)
            ),
            contract_nature=self._optional_text(element, "cbc:ProcurementTypeCode"),
            cpv_codes=tuple(
                self._texts(
                    element,
                    "cac:MainCommodityClassification/"
                    "cbc:ItemClassificationCode[@listName='cpv']",
                )
            ),
            nuts_codes=tuple(
                self._texts(
                    element,
                    "cac:RealizedLocation/cac:Address/"
                    "cbc:CountrySubentityCode[@listName='nuts']",
                )
            ),
            country_codes=tuple(
                self._texts(
                    element,
                    "cac:RealizedLocation/cac:Address/cac:Country/"
                    "cbc:IdentificationCode[@listName='country']",
                )
            ),
            estimated_value=self._text(amount_element) if amount_element is not None else None,
            estimated_value_currency=(
                amount_element.get("currencyID") if amount_element is not None else None
            ),
        )

    @staticmethod
    def _count_personal_elements(root: Element) -> int:
        return sum(
            1
            for element in root.iter()
            if element.tag.rsplit("}", 1)[-1] in PERSONAL_LOCAL_NAMES
        )

    @staticmethod
    def _text(element: Element | None) -> str:
        if element is None or element.text is None:
            return ""
        return " ".join(element.text.split())

    @classmethod
    def _required_element_text(cls, element: Element | None, label: str) -> str:
        value = cls._text(element)
        if not value:
            raise TEDEFormsParseError(f"Required {label} is missing")
        return value

    @classmethod
    def _required_text(cls, root: Element, path: str) -> str:
        return cls._required_element_text(root.find(path, NS), path)

    @classmethod
    def _optional_text(cls, root: Element, path: str) -> str | None:
        value = cls._text(root.find(path, NS))
        return value or None

    @classmethod
    def _texts(cls, root: Element, path: str) -> list[str]:
        values = [cls._text(element) for element in root.findall(path, NS)]
        return [value for value in values if value]
