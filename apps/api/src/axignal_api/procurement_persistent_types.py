from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from axignal_api.connectors.ted_xml import SOURCE_ID, TEDXMLNotice
from axignal_api.document_proposals import canonical_hash
from axignal_api.procurement_lifecycle_rehearsal import (
    LIFECYCLE_PROFILE,
    ProcurementLifecycleAssembler,
    ProcurementLifecycleError,
    TEDEFormsLifecycleParser,
)

PIPELINE_VERSION = "ted-persistent-source@0.1.0"
POLICY_VERSION = "ted-procurement-observed@1.0.0"
PRODUCT_PROFILE = "ted-eforms-non-personal@1.0.0"

PERSISTENT_AUTO_PREDICATES = frozenset(
    {
        "procurement_notice_type",
        "procurement_procedure_type",
        "procurement_contract_nature",
        "procurement_cpv_code",
        "procurement_place_of_performance_nuts",
        "procurement_estimated_value",
        "procurement_lot_identifier",
        "procurement_submission_deadline",
        "procurement_eu_funding_indicator",
        "procurement_notice_lifecycle_kind",
        "procurement_changed_notice_reference",
        "procurement_change_reason_code",
        "procurement_result_lot_identifier",
        "procurement_winner_selection_status",
        "procurement_tenders_received_count",
        "procurement_awarded_value",
        "procurement_award_date",
    }
)
EXCLUDED_IDENTITY_PREDICATES = frozenset(
    {
        "procurement_buyer_official_name",
        "procurement_buyer_identifier",
        "procurement_winner_official_name",
        "procurement_winner_organisation_ref",
        "procurement_contract_identifier",
    }
)
PERSONAL_TOKENS = frozenset(
    {"contact", "email", "phone", "telephone", "person", "firstname", "familyname"}
)
SAFE_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_.:/+\-]{1,200}$")
NOTICE_REFERENCE_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}-[0-9]{2}$",
    re.IGNORECASE,
)
XSD_DATE_PATTERN = re.compile(
    r"^(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
    r"(?P<timezone>Z|[+\-][0-9]{2}:[0-9]{2})?$"
)
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")


class ProcurementPersistencePolicyError(RuntimeError):
    """Raised when a parsed value cannot enter the non-personal profile."""


@dataclass(frozen=True)
class SanitisedNotice:
    publication_number: str
    notice_reference: str
    procedure_identifier: str
    lifecycle_kind: str
    previous_notice_reference: str | None
    issue_date: str
    raw_content_hash: str
    request_url: str
    retrieval_mode: str
    personal_field_element_count: int
    claim_fingerprints: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "publication_number": self.publication_number,
            "notice_reference": self.notice_reference,
            "procedure_identifier": self.procedure_identifier,
            "lifecycle_kind": self.lifecycle_kind,
            "previous_notice_reference": self.previous_notice_reference,
            "issue_date": self.issue_date,
            "raw_content_hash": self.raw_content_hash,
            "request_url": self.request_url,
            "retrieval_mode": self.retrieval_mode,
            "parser_profile": LIFECYCLE_PROFILE,
            "personal_field_element_count": self.personal_field_element_count,
            "claim_fingerprints": list(self.claim_fingerprints),
            "raw_xml_persisted": False,
        }


@dataclass(frozen=True)
class SanitisedClaim:
    publication_number: str
    notice_reference: str
    raw_content_hash: str
    issue_date: str
    fingerprint: str
    predicate: str
    subject_key: str
    value: Any
    source_path: str
    evidence_key: str
    evidence_content_hash: str
    value_hash: str

    def candidate_object_value(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "notice_reference": self.notice_reference,
            "publication_number": self.publication_number,
        }

    def deterministic_statement(self) -> str:
        encoded = json.dumps(
            self.value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return f"TED observed {self.predicate}={encoded}."

    def evidence_payload(self) -> dict[str, Any]:
        return {
            "publication_number": self.publication_number,
            "notice_reference": self.notice_reference,
            "raw_content_hash": self.raw_content_hash,
            "claim_fingerprint": self.fingerprint,
            "predicate": self.predicate,
            "subject_key": self.subject_key,
            "source_path": self.source_path,
            "value": self.value,
            "value_hash": self.value_hash,
            "parser_profile": LIFECYCLE_PROFILE,
            "rights_scope": "DERIVED_NON_PERSONAL_ONLY",
            "raw_xml_persisted": False,
        }


@dataclass(frozen=True)
class SanitisedProcurementLifecycle:
    source_id: str
    notices: tuple[SanitisedNotice, ...]
    claims: tuple[SanitisedClaim, ...]
    excluded_claim_count: int
    personal_field_element_count: int
    lineage_hash: str

    def package_projection(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "product_profile": PRODUCT_PROFILE,
            "parser_profile": LIFECYCLE_PROFILE,
            "notices": [item.payload() for item in self.notices],
            "claim_fingerprints": [item.fingerprint for item in self.claims],
            "excluded_claim_count": self.excluded_claim_count,
            "personal_field_element_count": self.personal_field_element_count,
            "lineage_hash": self.lineage_hash,
            "raw_xml_persisted": False,
            "personal_values_persisted": False,
        }


def sanitise_retrieved_lifecycle(
    retrieved: tuple[TEDXMLNotice, ...],
) -> SanitisedProcurementLifecycle:
    if not retrieved:
        raise ProcurementPersistencePolicyError("No TED notices were retrieved")
    if len(retrieved) > 4:
        raise ProcurementPersistencePolicyError("TED notice budget exceeded")
    if len({item.publication_number for item in retrieved}) != len(retrieved):
        raise ProcurementPersistencePolicyError("TED publication numbers are duplicated")

    parser = TEDEFormsLifecycleParser()
    first_pass = tuple(parser.parse(item.raw_xml) for item in retrieved)
    second_pass = tuple(parser.parse(item.raw_xml) for item in retrieved)
    if first_pass != second_pass:
        raise ProcurementPersistencePolicyError("Independent TED reparse diverged")
    assembler = ProcurementLifecycleAssembler(parser=parser)
    try:
        parsed = assembler._validate_lineage(first_pass)
    except ProcurementLifecycleError as exc:
        raise ProcurementPersistencePolicyError(str(exc)) from exc

    retrieval_by_hash = {item.content_hash: item for item in retrieved}
    if len(retrieval_by_hash) != len(retrieved):
        raise ProcurementPersistencePolicyError("TED XML content hashes are duplicated")
    evidence_by_fingerprint = {
        item.claim_fingerprint: item for item in assembler._build_evidence(parsed)
    }

    notices: list[SanitisedNotice] = []
    claims: list[SanitisedClaim] = []
    excluded = 0
    for notice in parsed:
        retrieval = retrieval_by_hash.get(notice.raw_content_hash)
        if retrieval is None:
            raise ProcurementPersistencePolicyError(
                "Parsed TED notice is not bound to a retrieved XML hash"
            )
        accepted_fingerprints: list[str] = []
        for claim in notice.claims:
            if _is_excluded_predicate(claim.predicate):
                excluded += 1
                continue
            if claim.predicate not in PERSISTENT_AUTO_PREDICATES:
                excluded += 1
                continue
            normalised_value = _validate_and_normalise_value(claim.predicate, claim.value)
            evidence = evidence_by_fingerprint.get(claim.fingerprint)
            if evidence is None:
                raise ProcurementPersistencePolicyError(
                    "TED claim lacks deterministic Evidence Object"
                )
            accepted_fingerprints.append(claim.fingerprint)
            claims.append(
                SanitisedClaim(
                    publication_number=retrieval.publication_number,
                    notice_reference=notice.identity.notice_reference,
                    raw_content_hash=notice.raw_content_hash,
                    issue_date=notice.identity.issue_date,
                    fingerprint=claim.fingerprint,
                    predicate=claim.predicate,
                    subject_key=claim.subject_key,
                    value=normalised_value,
                    source_path=claim.source_path,
                    evidence_key=evidence.evidence_key,
                    evidence_content_hash=evidence.content_hash,
                    value_hash=evidence.value_hash,
                )
            )
        notices.append(
            SanitisedNotice(
                publication_number=retrieval.publication_number,
                notice_reference=notice.identity.notice_reference,
                procedure_identifier=notice.identity.procedure_identifier,
                lifecycle_kind=notice.identity.lifecycle_kind,
                previous_notice_reference=notice.identity.changed_notice_reference,
                issue_date=notice.identity.issue_date,
                raw_content_hash=notice.raw_content_hash,
                request_url=retrieval.request_url,
                retrieval_mode=retrieval.retrieval_mode,
                personal_field_element_count=notice.personal_field_element_count,
                claim_fingerprints=tuple(accepted_fingerprints),
            )
        )
    if not claims:
        raise ProcurementPersistencePolicyError(
            "TED lifecycle contains no admissible non-personal claims"
        )
    lineage_material = {
        "profile": PRODUCT_PROFILE,
        "notices": [item.payload() for item in notices],
        "claim_fingerprints": [item.fingerprint for item in claims],
    }
    lifecycle = SanitisedProcurementLifecycle(
        source_id=SOURCE_ID,
        notices=tuple(notices),
        claims=tuple(claims),
        excluded_claim_count=excluded,
        personal_field_element_count=sum(
            item.personal_field_element_count for item in notices
        ),
        lineage_hash=canonical_hash(lineage_material),
    )
    _assert_no_personal_contract_keys(lifecycle.package_projection())
    return lifecycle


def _is_excluded_predicate(predicate: str) -> bool:
    lowered = predicate.casefold()
    return predicate in EXCLUDED_IDENTITY_PREDICATES or any(
        token in lowered for token in PERSONAL_TOKENS
    )


def _validate_and_normalise_value(predicate: str, value: Any) -> Any:
    if predicate in {"procurement_estimated_value", "procurement_awarded_value"}:
        if not isinstance(value, dict) or set(value) != {"amount", "currency"}:
            raise ProcurementPersistencePolicyError("TED monetary value is malformed")
        try:
            amount = Decimal(str(value["amount"]))
        except (InvalidOperation, ValueError) as exc:
            raise ProcurementPersistencePolicyError("TED amount is not decimal") from exc
        currency = str(value["currency"])
        if not CURRENCY_PATTERN.fullmatch(currency):
            raise ProcurementPersistencePolicyError("TED currency code is invalid")
        return {"amount": format(amount, "f"), "currency": currency}
    if predicate == "procurement_tenders_received_count":
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ProcurementPersistencePolicyError("TED tender count is invalid")
        return value
    if predicate == "procurement_submission_deadline":
        if not isinstance(value, dict) or set(value) != {"date", "time"}:
            raise ProcurementPersistencePolicyError("TED submission deadline is malformed")
        date_text = _normalise_xsd_date(
            value["date"],
            error_message="TED submission deadline date is invalid",
        )
        time_value = value["time"]
        time_text: str | None = None
        if time_value is not None:
            time_text = str(time_value)
            try:
                time.fromisoformat(time_text.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ProcurementPersistencePolicyError(
                    "TED submission deadline time is invalid"
                ) from exc
        return {"date": date_text, "time": time_text}
    if predicate == "procurement_award_date":
        return _normalise_xsd_date(value, error_message="TED award date is invalid")
    if predicate == "procurement_changed_notice_reference":
        text = str(value)
        if not NOTICE_REFERENCE_PATTERN.fullmatch(text):
            raise ProcurementPersistencePolicyError("TED previous notice reference is invalid")
        return text
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and SAFE_CODE_PATTERN.fullmatch(value):
        return value
    raise ProcurementPersistencePolicyError(
        f"TED value is outside the non-personal structural profile: {predicate}"
    )


def _normalise_xsd_date(value: Any, *, error_message: str) -> str:
    text = str(value)
    match = XSD_DATE_PATTERN.fullmatch(text)
    if match is None:
        raise ProcurementPersistencePolicyError(error_message)
    try:
        date.fromisoformat(match.group("date"))
    except ValueError as exc:
        raise ProcurementPersistencePolicyError(error_message) from exc
    timezone_text = match.group("timezone")
    if timezone_text not in {None, "Z"}:
        hours = int(timezone_text[1:3])
        minutes = int(timezone_text[4:6])
        if hours > 14 or minutes > 59 or (hours == 14 and minutes != 0):
            raise ProcurementPersistencePolicyError(error_message)
    return text


def observed_at(issue_date: str) -> datetime:
    text = _normalise_xsd_date(issue_date, error_message="TED issue date is invalid")
    match = XSD_DATE_PATTERN.fullmatch(text)
    if match is None:  # pragma: no cover - guaranteed by _normalise_xsd_date
        raise ProcurementPersistencePolicyError("TED issue date is invalid")
    timezone_text = match.group("timezone")
    zone = UTC
    if timezone_text not in {None, "Z"}:
        sign = 1 if timezone_text[0] == "+" else -1
        offset = timedelta(
            hours=int(timezone_text[1:3]),
            minutes=int(timezone_text[4:6]),
        )
        zone = timezone(sign * offset)
    return datetime.combine(
        date.fromisoformat(match.group("date")),
        time.min,
        tzinfo=zone,
    )


def numeric_projection(claim: SanitisedClaim) -> tuple[str | None, str | None]:
    if claim.predicate in {"procurement_estimated_value", "procurement_awarded_value"}:
        return str(claim.value["amount"]), str(claim.value["currency"])
    if claim.predicate == "procurement_tenders_received_count":
        return str(claim.value), "count"
    return None, None


def _assert_no_personal_contract_keys(payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).casefold()
    prohibited_keys = (
        '"email"',
        '"telephone"',
        '"phone"',
        '"firstname"',
        '"familyname"',
        '"contact"',
    )
    if any(token in encoded for token in prohibited_keys):
        raise ProcurementPersistencePolicyError(
            "Persistent TED projection contains a prohibited personal-data key"
        )
