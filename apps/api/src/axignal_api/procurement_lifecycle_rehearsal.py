from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from typing import Any

from defusedxml import ElementTree as SafeElementTree
from defusedxml.common import DefusedXmlException

from axignal_api.connectors.ted_eforms import (
    NS as BASE_NS,
    ProcurementCandidateClaim,
    TEDEFormsCN16Parser,
    TEDEFormsParseError,
)
from axignal_api.procurement_admission_rehearsal import (
    AUTO_ADMISSIBLE_PREDICATES,
    InMemoryProcurementAdmissionStore,
    ProcurementAdmissionContext,
    ProcurementAdmissionDecision,
    ProcurementAdmissionRehearsalResult,
)

LIFECYCLE_PROFILE = "ted-eforms-procurement-lifecycle@0.1.0"
SUPPORTED_CUSTOMIZATION_ID = "eforms-sdk-1.14"
SUPPORTED_UBL_VERSION = "2.3"
SUPPORTED_RESULT_NOTICE_TYPE = "can-standard"
SUPPORTED_RESULT_NOTICE_SUBTYPE = "29"
RESULT_DOCUMENT_TYPE = "ContractAwardNotice"
CHANGE_REASON_CODES = frozenset(
    {
        "cancel",
        "cancel-intent",
        "cor-buy",
        "cor-esen",
        "cor-pub",
        "info-release",
        "susp-review",
        "update-add",
    }
)
WINNER_SELECTION_CODES = frozenset({"clos-nw", "open-nw", "selec-w"})
LIFECYCLE_AUTO_ADMISSIBLE_PREDICATES = AUTO_ADMISSIBLE_PREDICATES | frozenset(
    {
        "procurement_notice_lifecycle_kind",
        "procurement_changed_notice_reference",
        "procurement_change_reason_code",
        "procurement_result_lot_identifier",
        "procurement_winner_selection_status",
        "procurement_tenders_received_count",
        "procurement_winner_organisation_ref",
        "procurement_winner_official_name",
        "procurement_awarded_value",
        "procurement_contract_identifier",
        "procurement_award_date",
    }
)
PERSONAL_PREDICATE_TOKENS = frozenset(
    {"contact", "email", "phone", "telephone", "person", "firstname", "familyname"}
)
NOTICE_REF_PATTERN = re.compile(
    r"^(?P<notice_id>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12})-(?P<version>[0-9]{2})$",
    re.IGNORECASE,
)
NS = dict(BASE_NS) | {
    "can": "urn:oasis:names:specification:ubl:schema:xsd:ContractAwardNotice-2",
    "efbc": "http://data.europa.eu/p27/eforms-ubl-extension-basic-components/1",
}


class ProcurementLifecycleError(RuntimeError):
    """Raised when procurement lifecycle evidence fails closed."""


@dataclass(frozen=True)
class ProcurementNoticeIdentity:
    notice_id: str
    version_id: str
    issue_date: str
    procedure_identifier: str
    document_type: str
    notice_type: str
    notice_subtype: str
    lifecycle_kind: str
    changed_notice_reference: str | None
    change_reason_code: str | None
    lot_ids: tuple[str, ...]
    raw_content_hash: str

    @property
    def notice_reference(self) -> str:
        return f"{self.notice_id}-{self.version_id}"


@dataclass(frozen=True)
class ParsedProcurementLifecycleNotice:
    identity: ProcurementNoticeIdentity
    claims: tuple[ProcurementCandidateClaim, ...]
    winner_selection_statuses: tuple[str, ...] = ()
    winner_organisation_refs: tuple[str, ...] = ()
    awarded_values: tuple[tuple[str, str], ...] = ()
    tenders_received_counts: tuple[int, ...] = ()
    contract_identifiers: tuple[str, ...] = ()
    award_dates: tuple[str, ...] = ()
    personal_field_element_count: int = 0

    @property
    def raw_content_hash(self) -> str:
        return self.identity.raw_content_hash

    def candidate_claims(self) -> tuple[ProcurementCandidateClaim, ...]:
        return self.claims


@dataclass(frozen=True)
class ProcurementEvidenceObject:
    evidence_key: str
    notice_reference: str
    claim_fingerprint: str
    predicate: str
    subject_key: str
    source_path: str
    value_hash: str
    content_hash: str
    parser_profile: str = LIFECYCLE_PROFILE
    authority: str = "OBSERVED"
    rights_state: str = "SANDBOX_ONLY"
    provisional: bool = True


@dataclass(frozen=True)
class ProcurementLifecycleEvent:
    sequence: int
    event_type: str
    notice_reference: str
    previous_notice_reference: str | None
    procedure_identifier: str
    lot_ids: tuple[str, ...]
    evidence_keys: tuple[str, ...]
    event_hash: str


@dataclass(frozen=True)
class ProcurementDossierSection:
    section_id: str
    title: str
    claim_fingerprints: tuple[str, ...]
    evidence_keys: tuple[str, ...]
    facts: tuple[dict[str, Any], ...]
    status: str


@dataclass(frozen=True)
class ProcurementDossier:
    dossier_id: str
    procedure_identifier: str
    status: str
    lifecycle_state: str
    notice_references: tuple[str, ...]
    sections: tuple[ProcurementDossierSection, ...]
    unknowns: tuple[str, ...]
    warnings: tuple[str, ...]
    content_hash: str

    def as_payload(self) -> dict[str, Any]:
        return {
            "dossier_id": self.dossier_id,
            "procedure_identifier": self.procedure_identifier,
            "status": self.status,
            "lifecycle_state": self.lifecycle_state,
            "notice_references": list(self.notice_references),
            "sections": [
                {
                    "section_id": section.section_id,
                    "title": section.title,
                    "claim_fingerprints": list(section.claim_fingerprints),
                    "evidence_keys": list(section.evidence_keys),
                    "facts": list(section.facts),
                    "status": section.status,
                }
                for section in self.sections
            ],
            "unknowns": list(self.unknowns),
            "warnings": list(self.warnings),
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True)
class ProcurementLifecycleRehearsalResult:
    notices: tuple[ParsedProcurementLifecycleNotice, ...]
    evidence_objects: tuple[ProcurementEvidenceObject, ...]
    lifecycle_events: tuple[ProcurementLifecycleEvent, ...]
    admission: ProcurementAdmissionRehearsalResult
    dossier: ProcurementDossier
    canonical_claim_writes: int = 0
    model_calls: int = 0
    reviewer_canonical_writes: int = 0


class TEDEFormsLifecycleParser:
    """Version-pinned parser for CN16 changes and CAN29 results."""

    def __init__(self) -> None:
        self._contract_notice_parser = TEDEFormsCN16Parser()

    def parse(self, xml_bytes: bytes) -> ParsedProcurementLifecycleNotice:
        if not xml_bytes:
            raise ProcurementLifecycleError("Procurement lifecycle XML is empty")
        if len(xml_bytes) > 2_097_152:
            raise ProcurementLifecycleError("Procurement lifecycle XML exceeded size budget")
        lowered = xml_bytes.lower()
        if b"<!doctype" in lowered or b"<!entity" in lowered:
            raise ProcurementLifecycleError("DTD and entity declarations are prohibited")
        try:
            root = SafeElementTree.fromstring(xml_bytes)
        except (DefusedXmlException, SafeElementTree.ParseError) as exc:
            raise ProcurementLifecycleError("Lifecycle XML is malformed or unsafe") from exc

        local_name = root.tag.rsplit("}", 1)[-1]
        if local_name == "ContractNotice":
            return self._parse_contract_notice(xml_bytes, root)
        if local_name == RESULT_DOCUMENT_TYPE:
            return self._parse_result_notice(xml_bytes, root)
        raise ProcurementLifecycleError("Unsupported procurement lifecycle document type")

    def _parse_contract_notice(
        self, xml_bytes: bytes, root: Any
    ) -> ParsedProcurementLifecycleNotice:
        try:
            parsed = self._contract_notice_parser.parse(xml_bytes)
        except TEDEFormsParseError as exc:
            raise ProcurementLifecycleError(str(exc)) from exc

        changes = root.find(
            "ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/"
            "efext:EformsExtension/efac:Changes",
            NS,
        )
        changed_reference: str | None = None
        change_reason: str | None = None
        lifecycle_kind = "COMPETITION_INITIAL"
        if changes is not None:
            changed_reference = self._required_text(
                changes, "efbc:ChangedNoticeIdentifier", "changed notice identifier"
            )
            self._validate_notice_reference(changed_reference)
            change_reason = self._required_text(
                changes,
                "efac:ChangeReason/cbc:ReasonCode",
                "change reason code",
            )
            if change_reason not in CHANGE_REASON_CODES:
                raise ProcurementLifecycleError("Unsupported change reason code")
            change_nodes = changes.findall("efac:Change", NS)
            if change_reason == "cancel":
                if change_nodes:
                    raise ProcurementLifecycleError(
                        "Notice cancellation must not carry efac:Change nodes"
                    )
                lifecycle_kind = "NOTICE_CANCELLATION"
            else:
                if not change_nodes:
                    raise ProcurementLifecycleError(
                        "Non-cancellation change notice requires at least one change"
                    )
                lifecycle_kind = "COMPETITION_CORRECTION"

        identity = ProcurementNoticeIdentity(
            notice_id=parsed.notice_id,
            version_id=parsed.version_id,
            issue_date=parsed.issue_date,
            procedure_identifier=parsed.procedure_identifier or "",
            document_type=parsed.document_type,
            notice_type=parsed.notice_type,
            notice_subtype=parsed.notice_subtype,
            lifecycle_kind=lifecycle_kind,
            changed_notice_reference=changed_reference,
            change_reason_code=change_reason,
            lot_ids=tuple(sorted(lot.lot_id for lot in parsed.lots)),
            raw_content_hash=parsed.raw_content_hash,
        )
        if not identity.procedure_identifier:
            raise ProcurementLifecycleError("Lifecycle notice has no procedure identifier")

        claims = list(parsed.candidate_claims())
        claims.append(
            self._claim(
                "procurement_notice_lifecycle_kind",
                identity.notice_reference,
                lifecycle_kind,
                "/ContractNotice/ext:UBLExtensions/.../efac:Changes",
            )
        )
        if changed_reference:
            claims.append(
                self._claim(
                    "procurement_changed_notice_reference",
                    identity.notice_reference,
                    changed_reference,
                    "/ContractNotice/ext:UBLExtensions/.../"
                    "efac:Changes/efbc:ChangedNoticeIdentifier",
                )
            )
        if change_reason:
            claims.append(
                self._claim(
                    "procurement_change_reason_code",
                    identity.notice_reference,
                    change_reason,
                    "/ContractNotice/ext:UBLExtensions/.../"
                    "efac:Changes/efac:ChangeReason/cbc:ReasonCode",
                )
            )
        return ParsedProcurementLifecycleNotice(
            identity=identity,
            claims=tuple(claims),
            personal_field_element_count=parsed.personal_field_element_count,
        )

    def _parse_result_notice(
        self, xml_bytes: bytes, root: Any
    ) -> ParsedProcurementLifecycleNotice:
        expected_root = f"{{{NS['can']}}}{RESULT_DOCUMENT_TYPE}"
        if root.tag != expected_root:
            raise ProcurementLifecycleError("Unsupported result notice namespace")
        customization_id = self._required_text(
            root, "cbc:CustomizationID", "customization ID"
        )
        if customization_id != SUPPORTED_CUSTOMIZATION_ID:
            raise ProcurementLifecycleError("Unsupported eForms customization")
        ubl_version = self._required_text(root, "cbc:UBLVersionID", "UBL version")
        if ubl_version != SUPPORTED_UBL_VERSION:
            raise ProcurementLifecycleError("Unsupported UBL version")
        notice_id = self._required_text(
            root, "cbc:ID[@schemeName='notice-id']", "notice ID"
        )
        version_id = self._required_text(root, "cbc:VersionID", "notice version")
        self._validate_notice_reference(f"{notice_id}-{version_id}")
        notice_type = self._required_text(root, "cbc:NoticeTypeCode", "notice type")
        notice_subtype = self._required_text(
            root,
            "ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/"
            "efext:EformsExtension/efac:NoticeSubType/cbc:SubTypeCode",
            "notice subtype",
        )
        if (
            notice_type != SUPPORTED_RESULT_NOTICE_TYPE
            or notice_subtype != SUPPORTED_RESULT_NOTICE_SUBTYPE
        ):
            raise ProcurementLifecycleError("Unsupported result notice profile")
        procedure_identifier = self._required_text(
            root, "cbc:ContractFolderID", "procedure identifier"
        )
        issue_date = self._required_text(root, "cbc:IssueDate", "issue date")
        notice_result = root.find(
            "ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/"
            "efext:EformsExtension/efac:NoticeResult",
            NS,
        )
        if notice_result is None:
            raise ProcurementLifecycleError("Result notice has no NoticeResult")

        organisation_names = self._organisation_names(root)
        tendering_parties: dict[str, tuple[str, ...]] = {}
        for party in notice_result.findall("efac:TenderingParty", NS):
            party_id = self._required_text(
                party, "cbc:ID[@schemeName='tendering-party']", "tendering party ID"
            )
            winner_refs = tuple(
                self._text(item)
                for item in party.findall(
                    "efac:Tenderer/cbc:ID[@schemeName='organization']", NS
                )
                if self._text(item)
            )
            tendering_parties[party_id] = winner_refs

        tenders: dict[str, dict[str, Any]] = {}
        for tender in notice_result.findall("efac:LotTender", NS):
            tender_id = self._required_text(
                tender, "cbc:ID[@schemeName='tender']", "tender ID"
            )
            party_id = self._optional_text(
                tender,
                "efac:TenderingParty/cbc:ID[@schemeName='tendering-party']",
            )
            lot_id = self._required_text(
                tender, "efac:TenderLot/cbc:ID[@schemeName='Lot']", "tender lot ID"
            )
            amount_element = tender.find(
                "cac:LegalMonetaryTotal/cbc:PayableAmount", NS
            )
            amount = self._text(amount_element) or None
            currency = (
                amount_element.get("currencyID") if amount_element is not None else None
            )
            tenders[tender_id] = {
                "party_id": party_id,
                "lot_id": lot_id,
                "amount": amount,
                "currency": currency,
            }

        claims: list[ProcurementCandidateClaim] = [
            self._claim(
                "procurement_notice_lifecycle_kind",
                f"{notice_id}-{version_id}",
                "PROCEDURE_RESULT",
                "/ContractAwardNotice/ext:UBLExtensions/.../efac:NoticeResult",
            )
        ]
        lot_ids: list[str] = []
        statuses: list[str] = []
        counts: list[int] = []
        winner_refs: list[str] = []
        awarded_values: list[tuple[str, str]] = []
        contracts: list[str] = []
        award_dates: list[str] = []

        for lot_result in notice_result.findall("efac:LotResult", NS):
            result_id = self._required_text(
                lot_result, "cbc:ID[@schemeName='result']", "lot result ID"
            )
            status = self._required_text(
                lot_result, "cbc:TenderResultCode", "winner selection status"
            )
            if status not in WINNER_SELECTION_CODES:
                raise ProcurementLifecycleError("Unsupported winner selection status")
            lot_id = self._required_text(
                lot_result,
                "efac:TenderLot/cbc:ID[@schemeName='Lot']",
                "result lot ID",
            )
            lot_ids.append(lot_id)
            statuses.append(status)
            claims.extend(
                [
                    self._claim(
                        "procurement_result_lot_identifier",
                        result_id,
                        lot_id,
                        "/ContractAwardNotice/.../efac:LotResult/"
                        "efac:TenderLot/cbc:ID",
                    ),
                    self._claim(
                        "procurement_winner_selection_status",
                        lot_id,
                        status,
                        "/ContractAwardNotice/.../efac:LotResult/"
                        "cbc:TenderResultCode",
                    ),
                ]
            )
            for statistic in lot_result.findall(
                "efac:ReceivedSubmissionsStatistics", NS
            ):
                statistic_code = self._optional_text(
                    statistic, "efbc:StatisticsCode"
                )
                statistic_value = self._optional_text(
                    statistic, "efbc:StatisticsNumeric"
                )
                if statistic_code == "tenders" and statistic_value is not None:
                    try:
                        count = int(statistic_value)
                    except ValueError as exc:
                        raise ProcurementLifecycleError(
                            "Tender count is not an integer"
                        ) from exc
                    if count < 0:
                        raise ProcurementLifecycleError("Tender count is negative")
                    counts.append(count)
                    claims.append(
                        self._claim(
                            "procurement_tenders_received_count",
                            lot_id,
                            count,
                            "/ContractAwardNotice/.../efac:LotResult/"
                            "efac:ReceivedSubmissionsStatistics",
                        )
                    )

            tender_refs = tuple(
                self._text(item)
                for item in lot_result.findall(
                    "efac:LotTender/cbc:ID[@schemeName='tender']", NS
                )
                if self._text(item)
            )
            if status == "selec-w" and not tender_refs:
                raise ProcurementLifecycleError(
                    "Winning lot result has no tender reference"
                )
            for tender_ref in tender_refs:
                tender = tenders.get(tender_ref)
                if tender is None or tender["lot_id"] != lot_id:
                    raise ProcurementLifecycleError(
                        "Lot result tender reference is unresolved or cross-lot"
                    )
                party_id = tender["party_id"]
                party_winners = tendering_parties.get(party_id or "", ())
                if status == "selec-w" and not party_winners:
                    raise ProcurementLifecycleError(
                        "Winning tender has no resolved tendering party"
                    )
                for winner_ref in party_winners:
                    if winner_ref not in organisation_names:
                        raise ProcurementLifecycleError(
                            "Winner organisation reference is unresolved"
                        )
                    winner_refs.append(winner_ref)
                    claims.append(
                        self._claim(
                            "procurement_winner_organisation_ref",
                            lot_id,
                            winner_ref,
                            "/ContractAwardNotice/.../efac:TenderingParty/"
                            "efac:Tenderer/cbc:ID",
                        )
                    )
                    for winner_name in organisation_names[winner_ref]:
                        claims.append(
                            self._claim(
                                "procurement_winner_official_name",
                                winner_ref,
                                winner_name,
                                "/ContractAwardNotice/.../efac:Organizations/"
                                "efac:Organization/efac:Company/cac:PartyName/cbc:Name",
                            )
                        )
                if tender["amount"] is not None:
                    if not tender["currency"]:
                        raise ProcurementLifecycleError(
                            "Awarded value has no currency"
                        )
                    awarded_values.append((tender["amount"], tender["currency"]))
                    claims.append(
                        self._claim(
                            "procurement_awarded_value",
                            lot_id,
                            {
                                "amount": tender["amount"],
                                "currency": tender["currency"],
                            },
                            "/ContractAwardNotice/.../efac:LotTender/"
                            "cac:LegalMonetaryTotal/cbc:PayableAmount",
                        )
                    )

        if not lot_ids:
            raise ProcurementLifecycleError("Result notice has no lot result")
        if len(lot_ids) != len(set(lot_ids)):
            raise ProcurementLifecycleError("Result notice repeats a lot result")

        for contract in notice_result.findall("efac:SettledContract", NS):
            contract_id = self._required_text(
                contract, "cbc:ID[@schemeName='contract']", "contract ID"
            )
            contracts.append(contract_id)
            claims.append(
                self._claim(
                    "procurement_contract_identifier",
                    procedure_identifier,
                    contract_id,
                    "/ContractAwardNotice/.../efac:SettledContract/cbc:ID",
                )
            )
            award_date = self._optional_text(contract, "cbc:AwardDate")
            if award_date:
                award_dates.append(award_date)
                claims.append(
                    self._claim(
                        "procurement_award_date",
                        contract_id,
                        award_date,
                        "/ContractAwardNotice/.../efac:SettledContract/cbc:AwardDate",
                    )
                )

        identity = ProcurementNoticeIdentity(
            notice_id=notice_id,
            version_id=version_id,
            issue_date=issue_date,
            procedure_identifier=procedure_identifier,
            document_type=RESULT_DOCUMENT_TYPE,
            notice_type=notice_type,
            notice_subtype=notice_subtype,
            lifecycle_kind="PROCEDURE_RESULT",
            changed_notice_reference=None,
            change_reason_code=None,
            lot_ids=tuple(sorted(lot_ids)),
            raw_content_hash=f"sha256:{sha256(xml_bytes).hexdigest()}",
        )
        return ParsedProcurementLifecycleNotice(
            identity=identity,
            claims=tuple(claims),
            winner_selection_statuses=tuple(statuses),
            winner_organisation_refs=tuple(dict.fromkeys(winner_refs)),
            awarded_values=tuple(awarded_values),
            tenders_received_counts=tuple(counts),
            contract_identifiers=tuple(contracts),
            award_dates=tuple(award_dates),
            personal_field_element_count=self._count_personal_elements(root),
        )

    @staticmethod
    def _organisation_names(root: Any) -> dict[str, tuple[str, ...]]:
        result: dict[str, tuple[str, ...]] = {}
        companies = root.findall(
            "ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/"
            "efext:EformsExtension/efac:Organizations/efac:Organization/"
            "efac:Company",
            NS,
        )
        for company in companies:
            identifier = TEDEFormsLifecycleParser._required_text(
                company,
                "cac:PartyIdentification/cbc:ID[@schemeName='organization']",
                "organisation ID",
            )
            if identifier in result:
                raise ProcurementLifecycleError("Duplicate organisation ID")
            names = tuple(
                TEDEFormsLifecycleParser._text(item)
                for item in company.findall("cac:PartyName/cbc:Name", NS)
                if TEDEFormsLifecycleParser._text(item)
            )
            if not names:
                raise ProcurementLifecycleError("Organisation has no official name")
            result[identifier] = names
        return result

    @staticmethod
    def _count_personal_elements(root: Any) -> int:
        personal_names = {
            "Contact",
            "ElectronicMail",
            "FamilyName",
            "FirstName",
            "Person",
            "Telefax",
            "Telephone",
        }
        return sum(
            element.tag.rsplit("}", 1)[-1] in personal_names
            for element in root.iter()
        )

    @staticmethod
    def _claim(
        predicate: str,
        subject_key: str,
        value: Any,
        source_path: str,
    ) -> ProcurementCandidateClaim:
        return ProcurementCandidateClaim(
            predicate=predicate,
            subject_key=subject_key,
            value=value,
            source_path=source_path,
        )

    @staticmethod
    def _validate_notice_reference(value: str) -> None:
        if not NOTICE_REF_PATTERN.fullmatch(value):
            raise ProcurementLifecycleError("Notice reference is not UUID-version")

    @staticmethod
    def _text(element: Any | None) -> str:
        if element is None or element.text is None:
            return ""
        return " ".join(element.text.split())

    @classmethod
    def _required_text(cls, root: Any, path: str, label: str) -> str:
        value = cls._text(root.find(path, NS))
        if not value:
            raise ProcurementLifecycleError(f"Required {label} is missing")
        return value

    @classmethod
    def _optional_text(cls, root: Any, path: str) -> str | None:
        value = cls._text(root.find(path, NS))
        return value or None


class ProcurementLifecycleAssembler:
    """Validate notice lineage and emit deterministic evidence and dossier state."""

    def __init__(
        self,
        *,
        parser: TEDEFormsLifecycleParser | None = None,
        store: InMemoryProcurementAdmissionStore | None = None,
    ) -> None:
        self.parser = parser or TEDEFormsLifecycleParser()
        self.store = store or InMemoryProcurementAdmissionStore()

    def run(
        self,
        *,
        raw_notices: tuple[bytes, ...],
        context: ProcurementAdmissionContext,
        fail_after_first_decision: bool = False,
    ) -> ProcurementLifecycleRehearsalResult:
        if not raw_notices:
            raise ProcurementLifecycleError("Lifecycle requires at least one notice")
        first_pass = tuple(self.parser.parse(raw) for raw in raw_notices)
        second_pass = tuple(self.parser.parse(raw) for raw in raw_notices)
        if first_pass != second_pass:
            raise ProcurementLifecycleError("Independent lifecycle reparse diverged")

        notices = self._validate_lineage(first_pass)
        evidence = self._build_evidence(notices)
        decisions = self._decide(notices, context)
        idempotency_key = self._idempotency_key(notices, context)
        if context.product_admission_ready:
            raise ProcurementLifecycleError(
                "Product admission is outside the lifecycle rehearsal authority"
            )
        if context.sandbox_ready:
            admission = self.store.commit(
                idempotency_key=idempotency_key,
                decisions=decisions,
                fail_after_first_decision=fail_after_first_decision,
            )
        else:
            admission = ProcurementAdmissionRehearsalResult(
                batch_id=None,
                decisions=decisions,
                idempotent_replay=False,
                sandbox_admissible_count=0,
            )
        events = self._build_events(notices, evidence)
        dossier = self._build_dossier(notices, evidence, admission)
        return ProcurementLifecycleRehearsalResult(
            notices=notices,
            evidence_objects=evidence,
            lifecycle_events=events,
            admission=admission,
            dossier=dossier,
        )

    def _validate_lineage(
        self, notices: tuple[ParsedProcurementLifecycleNotice, ...]
    ) -> tuple[ParsedProcurementLifecycleNotice, ...]:
        ordered = tuple(
            sorted(
                notices,
                key=lambda item: (
                    self._date_key(item.identity.issue_date),
                    item.identity.notice_reference,
                ),
            )
        )
        references: dict[str, ParsedProcurementLifecycleNotice] = {}
        procedure_identifier = ordered[0].identity.procedure_identifier
        latest_competition: ParsedProcurementLifecycleNotice | None = None
        initial_count = 0
        cancelled_references: set[str] = set()

        for notice in ordered:
            identity = notice.identity
            reference = identity.notice_reference
            if reference in references:
                raise ProcurementLifecycleError("Duplicate notice reference")
            if identity.procedure_identifier != procedure_identifier:
                raise ProcurementLifecycleError("Lifecycle crosses procedure identifiers")

            if identity.lifecycle_kind == "COMPETITION_INITIAL":
                initial_count += 1
                if latest_competition is not None:
                    raise ProcurementLifecycleError(
                        "Lifecycle contains more than one initial competition notice"
                    )
                latest_competition = notice
            elif identity.lifecycle_kind in {
                "COMPETITION_CORRECTION",
                "NOTICE_CANCELLATION",
            }:
                previous = identity.changed_notice_reference
                if previous is None or previous not in references:
                    raise ProcurementLifecycleError(
                        "Change notice has a dangling previous-notice reference"
                    )
                if (
                    latest_competition is None
                    or previous != latest_competition.identity.notice_reference
                ):
                    raise ProcurementLifecycleError(
                        "Change notice does not reference the latest competition notice"
                    )
                if previous in cancelled_references:
                    raise ProcurementLifecycleError(
                        "A cancelled notice cannot receive another change"
                    )
                if identity.lot_ids != latest_competition.identity.lot_ids:
                    raise ProcurementLifecycleError(
                        "Change notice altered the lot identity set"
                    )
                if identity.lifecycle_kind == "NOTICE_CANCELLATION":
                    cancelled_references.add(reference)
                latest_competition = notice
            elif identity.lifecycle_kind == "PROCEDURE_RESULT":
                if latest_competition is None:
                    raise ProcurementLifecycleError(
                        "Result notice has no competition lineage"
                    )
                competition_lots = set(latest_competition.identity.lot_ids)
                if not set(identity.lot_ids).issubset(competition_lots):
                    raise ProcurementLifecycleError(
                        "Result notice references an unknown lot"
                    )
            else:
                raise ProcurementLifecycleError("Unknown lifecycle kind")
            references[reference] = notice

        if initial_count != 1:
            raise ProcurementLifecycleError(
                "Lifecycle must contain exactly one initial competition notice"
            )
        return ordered

    @staticmethod
    def _build_evidence(
        notices: tuple[ParsedProcurementLifecycleNotice, ...]
    ) -> tuple[ProcurementEvidenceObject, ...]:
        evidence: list[ProcurementEvidenceObject] = []
        seen: set[str] = set()
        for notice in notices:
            for claim in notice.claims:
                value_hash = _canonical_hash(claim.value)
                evidence_material = {
                    "notice_reference": notice.identity.notice_reference,
                    "raw_content_hash": notice.raw_content_hash,
                    "claim_fingerprint": claim.fingerprint,
                    "predicate": claim.predicate,
                    "subject_key": claim.subject_key,
                    "source_path": claim.source_path,
                    "value_hash": value_hash,
                    "parser_profile": LIFECYCLE_PROFILE,
                }
                content_hash = _canonical_hash(evidence_material)
                evidence_key = f"ev_{content_hash.removeprefix('sha256:')[:24]}"
                if evidence_key in seen:
                    raise ProcurementLifecycleError("Duplicate Evidence Object key")
                seen.add(evidence_key)
                evidence.append(
                    ProcurementEvidenceObject(
                        evidence_key=evidence_key,
                        notice_reference=notice.identity.notice_reference,
                        claim_fingerprint=claim.fingerprint,
                        predicate=claim.predicate,
                        subject_key=claim.subject_key,
                        source_path=claim.source_path,
                        value_hash=value_hash,
                        content_hash=content_hash,
                    )
                )
        return tuple(evidence)

    @staticmethod
    def _decide(
        notices: tuple[ParsedProcurementLifecycleNotice, ...],
        context: ProcurementAdmissionContext,
    ) -> tuple[ProcurementAdmissionDecision, ...]:
        decisions: list[ProcurementAdmissionDecision] = []
        for notice in notices:
            for claim in notice.claims:
                personal = any(
                    token in claim.predicate.casefold()
                    for token in PERSONAL_PREDICATE_TOKENS
                )
                gates = {
                    "SOURCE_PRODUCT_ADMITTED": context.product_admission_ready,
                    "SANDBOX_REHEARSAL_AUTHORISED": context.sandbox_ready,
                    "PARSER_PROFILE_PINNED": True,
                    "PRODUCER_AUTHORITY_SEPARATED": True,
                    "PERSONAL_DATA_EXCLUDED": not personal,
                    "PREDICATE_AUTO_ADMISSIBLE": (
                        claim.predicate in LIFECYCLE_AUTO_ADMISSIBLE_PREDICATES
                    ),
                    "REEDERIVATION_EXACT_MATCH": True,
                    "LINEAGE_VALIDATED": True,
                    "EVIDENCE_OBJECT_BOUND": True,
                }
                if not context.product_admission_ready and not context.sandbox_ready:
                    outcome = "BLOCKED_SOURCE_NOT_PRODUCT_ADMITTED"
                    reasons = ("source_or_policy_gate_not_admitted",)
                    rederived = None
                elif personal:
                    outcome = "REJECTED_PROHIBITED"
                    reasons = ("personal_procurement_predicate",)
                    rederived = None
                elif claim.predicate not in LIFECYCLE_AUTO_ADMISSIBLE_PREDICATES:
                    outcome = "HUMAN_REVIEW_REQUIRED_OUTSIDE_PROFILE"
                    reasons = ("predicate_outside_lifecycle_admission_profile",)
                    rederived = None
                else:
                    outcome = "SANDBOX_ADMISSIBLE_REDERIVED"
                    reasons = ("all_lifecycle_sandbox_gates_passed",)
                    rederived = claim.fingerprint
                decisions.append(
                    ProcurementAdmissionDecision(
                        candidate_fingerprint=claim.fingerprint,
                        predicate=claim.predicate,
                        outcome=outcome,
                        reasons=reasons,
                        gate_results=gates,
                        rederived_fingerprint=rederived,
                    )
                )
        return tuple(decisions)

    @staticmethod
    def _build_events(
        notices: tuple[ParsedProcurementLifecycleNotice, ...],
        evidence: tuple[ProcurementEvidenceObject, ...],
    ) -> tuple[ProcurementLifecycleEvent, ...]:
        evidence_by_notice: dict[str, list[str]] = {}
        for item in evidence:
            evidence_by_notice.setdefault(item.notice_reference, []).append(
                item.evidence_key
            )
        events: list[ProcurementLifecycleEvent] = []
        for sequence, notice in enumerate(notices, start=1):
            identity = notice.identity
            material = {
                "sequence": sequence,
                "event_type": identity.lifecycle_kind,
                "notice_reference": identity.notice_reference,
                "previous_notice_reference": identity.changed_notice_reference,
                "procedure_identifier": identity.procedure_identifier,
                "lot_ids": list(identity.lot_ids),
                "evidence_keys": sorted(
                    evidence_by_notice.get(identity.notice_reference, ())
                ),
            }
            events.append(
                ProcurementLifecycleEvent(
                    sequence=sequence,
                    event_type=identity.lifecycle_kind,
                    notice_reference=identity.notice_reference,
                    previous_notice_reference=identity.changed_notice_reference,
                    procedure_identifier=identity.procedure_identifier,
                    lot_ids=identity.lot_ids,
                    evidence_keys=tuple(material["evidence_keys"]),
                    event_hash=_canonical_hash(material),
                )
            )
        return tuple(events)

    @staticmethod
    def _build_dossier(
        notices: tuple[ParsedProcurementLifecycleNotice, ...],
        evidence: tuple[ProcurementEvidenceObject, ...],
        admission: ProcurementAdmissionRehearsalResult,
    ) -> ProcurementDossier:
        procedure_identifier = notices[0].identity.procedure_identifier
        evidence_by_binding = {
            (item.notice_reference, item.claim_fingerprint): item.evidence_key
            for item in evidence
        }
        timeline_facts: list[dict[str, Any]] = []
        claim_fingerprints: list[str] = []
        evidence_keys: list[str] = []
        for notice in notices:
            for claim in notice.claims:
                claim_fingerprints.append(claim.fingerprint)
                evidence_keys.append(
                    evidence_by_binding[
                        (notice.identity.notice_reference, claim.fingerprint)
                    ]
                )
            timeline_facts.append(
                {
                    "notice_reference": notice.identity.notice_reference,
                    "issue_date": notice.identity.issue_date,
                    "event_type": notice.identity.lifecycle_kind,
                    "previous_notice_reference": (
                        notice.identity.changed_notice_reference
                    ),
                    "change_reason_code": notice.identity.change_reason_code,
                    "lot_ids": list(notice.identity.lot_ids),
                }
            )

        result_notices = [
            item
            for item in notices
            if item.identity.lifecycle_kind == "PROCEDURE_RESULT"
        ]
        lifecycle_state = "OPEN_OR_PENDING"
        if result_notices:
            statuses = {
                status
                for notice in result_notices
                for status in notice.winner_selection_statuses
            }
            if statuses == {"selec-w"}:
                lifecycle_state = "AWARDED"
            elif "selec-w" in statuses:
                lifecycle_state = "PARTIALLY_AWARDED"
            elif statuses == {"clos-nw"}:
                lifecycle_state = "NO_AWARD"
            else:
                lifecycle_state = "RESULT_PENDING_OR_MIXED"
        elif notices[-1].identity.lifecycle_kind == "NOTICE_CANCELLATION":
            lifecycle_state = "NOTICE_CANCELLED_PROCEDURE_UNRESOLVED"

        result_facts: list[dict[str, Any]] = []
        for notice in result_notices:
            result_facts.append(
                {
                    "notice_reference": notice.identity.notice_reference,
                    "winner_selection_statuses": list(
                        notice.winner_selection_statuses
                    ),
                    "winner_organisation_refs": list(
                        notice.winner_organisation_refs
                    ),
                    "awarded_values": [
                        {"amount": amount, "currency": currency}
                        for amount, currency in notice.awarded_values
                    ],
                    "tenders_received_counts": list(
                        notice.tenders_received_counts
                    ),
                    "contract_identifiers": list(
                        notice.contract_identifiers
                    ),
                    "award_dates": list(notice.award_dates),
                }
            )

        unknowns: list[str] = []
        if not result_notices:
            unknowns.append("No result notice is present for the procedure.")
        if result_notices and not any(
            item.tenders_received_counts for item in result_notices
        ):
            unknowns.append("Tender-count statistics are not published.")
        if result_notices and any(
            "selec-w" in item.winner_selection_statuses
            and not item.winner_organisation_refs
            for item in result_notices
        ):
            unknowns.append("A winning result lacks a resolved winner organisation.")
        if lifecycle_state == "NOTICE_CANCELLED_PROCEDURE_UNRESOLVED":
            unknowns.append(
                "The notice is cancelled, but procedure cancellation is not established "
                "without a no-award result notice."
            )

        sections = (
            ProcurementDossierSection(
                section_id="lifecycle",
                title="Notice lifecycle",
                claim_fingerprints=tuple(claim_fingerprints),
                evidence_keys=tuple(evidence_keys),
                facts=tuple(timeline_facts),
                status="TRACEABLE",
            ),
            ProcurementDossierSection(
                section_id="result",
                title="Award and competition result",
                claim_fingerprints=tuple(
                    claim.fingerprint
                    for notice in result_notices
                    for claim in notice.claims
                ),
                evidence_keys=tuple(
                    evidence_by_binding[
                        (notice.identity.notice_reference, claim.fingerprint)
                    ]
                    for notice in result_notices
                    for claim in notice.claims
                ),
                facts=tuple(result_facts),
                status="TRACEABLE" if result_notices else "UNKNOWN",
            ),
            ProcurementDossierSection(
                section_id="admission",
                title="Deterministic sandbox admission",
                claim_fingerprints=tuple(
                    item.candidate_fingerprint for item in admission.decisions
                ),
                evidence_keys=tuple(evidence_keys),
                facts=tuple(
                    {
                        "candidate_fingerprint": item.candidate_fingerprint,
                        "outcome": item.outcome,
                    }
                    for item in admission.decisions
                ),
                status="SANDBOX_ONLY",
            ),
        )
        payload_without_hash = {
            "procedure_identifier": procedure_identifier,
            "status": "TRACEABLE_SANDBOX_REHEARSAL",
            "lifecycle_state": lifecycle_state,
            "notice_references": [
                item.identity.notice_reference for item in notices
            ],
            "sections": [
                {
                    "section_id": item.section_id,
                    "claim_fingerprints": list(item.claim_fingerprints),
                    "evidence_keys": list(item.evidence_keys),
                    "facts": list(item.facts),
                    "status": item.status,
                }
                for item in sections
            ],
            "unknowns": unknowns,
            "warnings": [
                "TED remains TECHNICAL_PROBE and is not PRODUCT_ADMITTED.",
                "Sandbox decisions create zero canonical Claim Ledger writes.",
                "The dossier is not a bid, eligibility decision or personalised advice.",
            ],
        }
        content_hash = _canonical_hash(payload_without_hash)
        return ProcurementDossier(
            dossier_id=f"dos_{content_hash.removeprefix('sha256:')[:24]}",
            procedure_identifier=procedure_identifier,
            status="TRACEABLE_SANDBOX_REHEARSAL",
            lifecycle_state=lifecycle_state,
            notice_references=tuple(
                item.identity.notice_reference for item in notices
            ),
            sections=sections,
            unknowns=tuple(unknowns),
            warnings=tuple(payload_without_hash["warnings"]),
            content_hash=content_hash,
        )

    @staticmethod
    def _idempotency_key(
        notices: tuple[ParsedProcurementLifecycleNotice, ...],
        context: ProcurementAdmissionContext,
    ) -> str:
        return _canonical_hash(
            {
                "profile": LIFECYCLE_PROFILE,
                "notice_hashes": [item.raw_content_hash for item in notices],
                "candidate_fingerprints": sorted(
                    claim.fingerprint
                    for notice in notices
                    for claim in notice.claims
                ),
                "source_state": context.source_state,
                "policy_state": context.policy_state,
                "sandbox_authorised": context.sandbox_authorised,
            }
        )

    @staticmethod
    def _date_key(value: str) -> date:
        try:
            return date.fromisoformat(value[:10])
        except ValueError as exc:
            raise ProcurementLifecycleError("Notice issue date is invalid") from exc


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
    return f"sha256:{sha256(encoded.encode('utf-8')).hexdigest()}"
