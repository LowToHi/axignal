from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

PUBLICATION_NUMBER_RE = re.compile(r"^[0-9]{1,8}-[0-9]{4}$")
CPV_RE = re.compile(r"^[0-9]{8}$")
NUTS_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{0,3}$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")

CORE_FIELDS = (
    "publication-number",
    "publication-date",
    "notice-title",
    "buyer-name",
    "buyer-country",
    "notice-type",
    "form-type",
    "procedure-type",
    "contract-nature",
    "classification-cpv",
    "deadline",
    "identifier-lot",
)


class O01QualityCampaignError(RuntimeError):
    """Raised when O01-C evidence cannot be measured without invention."""


@dataclass(frozen=True)
class PageObservation:
    country: str
    page: int
    query: str
    retrieval_started_at: datetime
    retrieval_completed_at: datetime
    response_date_header: str | None
    total_notice_count: int | None
    returned_count: int

    @property
    def acquisition_seconds(self) -> float:
        return max(
            0.0,
            (self.retrieval_completed_at - self.retrieval_started_at).total_seconds(),
        )


@dataclass(frozen=True)
class NormalizedNotice:
    publication_number: str
    publication_date: str | None
    notice_identifier: tuple[str, ...]
    notice_version: tuple[str, ...]
    notice_type: tuple[str, ...]
    form_type: tuple[str, ...]
    titles: tuple[str, ...]
    buyers: tuple[str, ...]
    buyer_countries: tuple[str, ...]
    procedure_types: tuple[str, ...]
    contract_natures: tuple[str, ...]
    cpv_codes: tuple[str, ...]
    performance_countries: tuple[str, ...]
    nuts_codes: tuple[str, ...]
    deadlines: tuple[str, ...]
    estimated_amounts: tuple[str, ...]
    currencies: tuple[str, ...]
    lot_identifiers: tuple[str, ...]
    source_url: str
    source_country_stratum: str
    retrieval_started_at: str
    retrieval_completed_at: str
    normalised_at: str
    indexed_at: str
    notification_enqueued_at: str
    source_record_sha256: str
    normalized_record_sha256: str


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def sha256_prefixed(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        raise O01QualityCampaignError("Timestamp requires timezone")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def flatten_scalars(value: Any) -> tuple[str, ...]:
    result: list[str] = []

    def visit(node: Any) -> None:
        if node is None:
            return
        if isinstance(node, bool):
            result.append("true" if node else "false")
            return
        if isinstance(node, (str, int, float, Decimal)):
            text = str(node).strip()
            if text:
                result.append(text)
            return
        if isinstance(node, dict):
            for key in sorted(node):
                visit(node[key])
            return
        if isinstance(node, (list, tuple, set)):
            for item in node:
                visit(item)
            return

    visit(value)
    seen: set[str] = set()
    ordered: list[str] = []
    for item in result:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return tuple(ordered)


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split())


def values(record: dict[str, Any], field: str) -> tuple[str, ...]:
    return tuple(normalize_text(item) for item in flatten_scalars(record.get(field)))


def first_value(record: dict[str, Any], field: str) -> str | None:
    items = values(record, field)
    return items[0] if items else None


def parse_source_date(value: str | None) -> date | None:
    if not value:
        return None
    candidate = value.strip()
    formats = ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y")
    for fmt in formats:
        try:
            return datetime.strptime(candidate[:10], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def parse_deadline(value: str) -> datetime | date | None:
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        return parsed
    except ValueError:
        pass
    return parse_source_date(candidate)


def parse_amount(value: str) -> Decimal | None:
    candidate = value.strip().replace(" ", "").replace(",", ".")
    try:
        parsed = Decimal(candidate)
    except InvalidOperation:
        return None
    if not parsed.is_finite():
        return None
    return parsed


def normalized_code(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value).upper()


def publication_number(record: dict[str, Any]) -> str | None:
    value = first_value(record, "publication-number")
    return value.strip() if value else None


def deterministic_rank(seed: str, country: str, notice_id: str) -> str:
    return hashlib.sha256(f"{seed}|{country}|{notice_id}".encode()).hexdigest()


def deterministic_sample(
    candidates_by_country: dict[str, list[dict[str, Any]]],
    *,
    seed: str,
    target_per_country: int,
) -> tuple[list[tuple[str, dict[str, Any]]], dict[str, int]]:
    selected: list[tuple[str, dict[str, Any]]] = []
    available: dict[str, int] = {}
    for country in sorted(candidates_by_country):
        unique: dict[str, dict[str, Any]] = {}
        for record in candidates_by_country[country]:
            if not isinstance(record, dict):
                continue
            notice_id = publication_number(record)
            if not notice_id or not PUBLICATION_NUMBER_RE.fullmatch(notice_id):
                continue
            unique.setdefault(notice_id, record)
        available[country] = len(unique)
        ranked = sorted(
            unique.items(),
            key=lambda item: deterministic_rank(seed, country, item[0]),
        )
        selected.extend((country, record) for _, record in ranked[:target_per_country])
    return selected, available
