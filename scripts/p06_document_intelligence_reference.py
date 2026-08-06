#!/usr/bin/env python3
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

_ALLOWED_LANGUAGES = {"en", "es", "fr", "de", "pt", "it"}
_AUTHORITY_RANK = {
    "REVOKED": 0,
    "SUPERSEDED": 1,
    "RAW_REFERENCE": 2,
    "EXTRACTED_CANDIDATE": 3,
    "TRANSLATION_CANDIDATE": 4,
    "SEMANTIC_CANDIDATE": 5,
    "HUMAN_REVIEWED": 6,
    "ADMITTED": 7,
}
_CRITICAL_DIMENSIONS = {
    "obligations",
    "eligibility",
    "amounts",
    "dates",
    "negation",
    "modality",
    "citation_anchors",
}


def validate_language_tag(language_tag: str) -> bool:
    return language_tag in _ALLOWED_LANGUAGES


def preserve_source_text(source_text: str, translated_text: str | None) -> dict[str, str | None]:
    if not source_text:
        raise ValueError("source text is required")
    return {"source_text": source_text, "translated_text": translated_text}


def ocr_confidence_decision(confidence: Decimal) -> str:
    if confidence < Decimal("0") or confidence > Decimal("1"):
        raise ValueError("confidence must be between zero and one")
    if confidence < Decimal("0.75"):
        return "QUARANTINE"
    if confidence < Decimal("0.90"):
        return "REVIEW_REQUIRED"
    return "CANDIDATE"


def validate_anchor(
    document_version: str,
    content_digest: str,
    anchor_document_version: str,
    anchor_content_digest: str,
    geometry_valid: bool,
    quote_digest_valid: bool,
) -> str:
    if document_version != anchor_document_version:
        return "INVALID"
    if content_digest != anchor_content_digest:
        return "INVALID"
    if not geometry_valid or not quote_digest_valid:
        return "INVALID"
    return "RESOLVED"


def semantic_parity_decision(dimension_results: dict[str, str]) -> str:
    if not _CRITICAL_DIMENSIONS.issubset(dimension_results):
        return "INDETERMINATE"
    for dimension in _CRITICAL_DIMENSIONS:
        result = dimension_results[dimension]
        if result == "MISMATCH":
            return "DENY"
        if result == "UNKNOWN":
            return "REVIEW_REQUIRED"
        if result not in {"MATCH", "NOT_APPLICABLE"}:
            return "INDETERMINATE"
    return "PASS"


def least_document_authority(states: list[str]) -> str:
    if not states:
        raise ValueError("at least one authority state is required")
    unknown = set(states) - set(_AUTHORITY_RANK)
    if unknown:
        raise ValueError(f"unknown authority states: {sorted(unknown)}")
    return min(states, key=_AUTHORITY_RANK.__getitem__)


def may_write_document_canonical(actor_type: str, human_approved: bool) -> bool:
    return human_approved and actor_type == "INDEPENDENT_ADMISSION_RUNTIME"


def parse_localized_decimal(value: str, language_tag: str) -> Decimal:
    if not validate_language_tag(language_tag):
        raise ValueError("unsupported language")
    normalized = value.strip().replace("\u00a0", "").replace(" ", "")
    if language_tag in {"es", "fr", "de", "pt", "it"}:
        normalized = normalized.replace(".", "").replace(",", ".")
    else:
        normalized = normalized.replace(",", "")
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError("invalid localized decimal") from exc


def preserve_unknown(value: Any, state: str) -> tuple[Any, str]:
    allowed = {"KNOWN", "UNKNOWN", "UNAVAILABLE", "NOT_APPLICABLE"}
    if state not in allowed:
        raise ValueError("unsupported state")
    if state != "KNOWN" and value is not None:
        raise ValueError("non-known states cannot carry a value")
    return value, state
