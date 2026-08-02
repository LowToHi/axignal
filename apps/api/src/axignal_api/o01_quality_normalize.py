from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from .o01_quality_common import (
    PUBLICATION_NUMBER_RE,
    NormalizedNotice,
    O01QualityCampaignError,
    PageObservation,
    canonical_json_bytes,
    first_value,
    iso_z,
    normalized_code,
    parse_amount,
    parse_deadline,
    parse_source_date,
    publication_number,
    sha256_prefixed,
    values,
)


def _clean_publication_date(record: dict[str, Any]) -> str | None:
    parsed = parse_source_date(first_value(record, "publication-date"))
    return parsed.isoformat() if parsed else None


def _clean_deadlines(record: dict[str, Any]) -> tuple[str, ...]:
    cleaned: list[str] = []
    for item in values(record, "deadline"):
        parsed = parse_deadline(item)
        if isinstance(parsed, datetime):
            cleaned.append(
                parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
                if parsed.tzinfo
                else parsed.isoformat()
            )
        elif isinstance(parsed, date):
            cleaned.append(parsed.isoformat())
    return tuple(cleaned)


def _clean_amounts(record: dict[str, Any]) -> tuple[str, ...]:
    cleaned: list[str] = []
    for item in values(record, "estimated-value-proc"):
        parsed = parse_amount(item)
        if parsed is not None:
            cleaned.append(format(parsed.normalize(), "f"))
    return tuple(cleaned)


def normalize_notice(
    record: dict[str, Any],
    *,
    country: str,
    page_observation: PageObservation,
    normalised_at: datetime,
    indexed_at: datetime,
    notification_enqueued_at: datetime,
) -> NormalizedNotice:
    notice_id = publication_number(record)
    if not notice_id or not PUBLICATION_NUMBER_RE.fullmatch(notice_id):
        raise O01QualityCampaignError("Publication number is missing or malformed")
    source_record_sha = sha256_prefixed(canonical_json_bytes(record))
    payload: dict[str, Any] = {
        "publication_number": notice_id,
        "publication_date": _clean_publication_date(record),
        "notice_identifier": values(record, "notice-identifier"),
        "notice_version": values(record, "notice-version"),
        "notice_type": values(record, "notice-type"),
        "form_type": values(record, "form-type"),
        "titles": values(record, "notice-title"),
        "buyers": values(record, "buyer-name"),
        "buyer_countries": tuple(
            normalized_code(item) for item in values(record, "buyer-country")
        ),
        "procedure_types": values(record, "procedure-type"),
        "contract_natures": values(record, "contract-nature"),
        "cpv_codes": tuple(
            normalized_code(item) for item in values(record, "classification-cpv")
        ),
        "performance_countries": tuple(
            normalized_code(item)
            for item in values(record, "place-of-performance-country-proc")
        ),
        "nuts_codes": tuple(
            normalized_code(item)
            for item in values(record, "place-of-performance-subdiv-proc")
        ),
        "deadlines": _clean_deadlines(record),
        "estimated_amounts": _clean_amounts(record),
        "currencies": tuple(
            normalized_code(item)
            for item in values(record, "estimated-value-cur-proc")
        ),
        "lot_identifiers": values(record, "identifier-lot"),
        "source_url": f"https://ted.europa.eu/en/notice/-/detail/{notice_id}",
        "source_country_stratum": country,
        "retrieval_started_at": iso_z(page_observation.retrieval_started_at),
        "retrieval_completed_at": iso_z(page_observation.retrieval_completed_at),
        "normalised_at": iso_z(normalised_at),
        "indexed_at": iso_z(indexed_at),
        "notification_enqueued_at": iso_z(notification_enqueued_at),
        "source_record_sha256": source_record_sha,
    }
    normalized_sha = sha256_prefixed(canonical_json_bytes(payload))
    payload["normalized_record_sha256"] = normalized_sha
    return NormalizedNotice(**payload)
