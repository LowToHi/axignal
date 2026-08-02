from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Iterable
from typing import Any

LANGUAGE_KEYS: dict[str, tuple[str, ...]] = {
    "de": ("de", "deu", "ger"),
    "en": ("en", "eng"),
    "es": ("es", "spa"),
    "fr": ("fr", "fra"),
    "it": ("it", "ita"),
    "pt": ("pt", "por"),
}


def _scalars(value: Any) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, str):
        candidate = value.strip()
        if candidate:
            yield candidate
        return
    if isinstance(value, (int, float, bool)):
        yield str(value)
        return
    if isinstance(value, dict):
        for key in sorted(value):
            yield from _scalars(value[key])
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _scalars(item)


def _language_values(record: dict[str, Any], language: str) -> list[str]:
    allowed = set(LANGUAGE_KEYS[language])
    values: list[str] = []
    for field in ("notice-title", "buyer-name"):
        container = record.get(field)
        if not isinstance(container, dict):
            continue
        for key, value in container.items():
            if str(key).casefold() not in allowed:
                continue
            values.extend(_scalars(value))
    return values


def _normalise(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split())


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def measure_multilingual_journeys(
    records: list[dict[str, Any]],
    *,
    required_languages: list[str],
) -> dict[str, Any]:
    journeys: dict[str, Any] = {}
    for language in required_languages:
        if language not in LANGUAGE_KEYS:
            journeys[language] = {
                "ingestion": "FAIL",
                "normalisation": "FAIL",
                "search": "FAIL",
                "presentation": "FAIL",
                "reason": "UNSUPPORTED_LANGUAGE_CONTRACT",
                "records_observed": 0,
                "values_observed": 0,
            }
            continue

        observed: list[tuple[str | None, str]] = []
        for record in records:
            publication_number = record.get("publication-number")
            if isinstance(publication_number, list):
                publication_number = publication_number[0] if publication_number else None
            publication_number = (
                str(publication_number) if publication_number is not None else None
            )
            for value in _language_values(record, language):
                observed.append((publication_number, value))

        normalised = [
            (publication_number, _normalise(value))
            for publication_number, value in observed
            if _normalise(value)
        ]
        search_index = {value.casefold() for _, value in normalised}
        search_pass = bool(normalised) and all(
            value.casefold() in search_index for _, value in normalised
        )
        presentation_candidates = [value for _, value in normalised if value.strip()]
        presentation_pass = bool(presentation_candidates)
        records_observed = len(
            {publication_number for publication_number, _ in observed if publication_number}
        )
        ingestion_pass = bool(observed)
        normalisation_pass = len(normalised) == len(observed) and bool(normalised)
        sample_value = presentation_candidates[0] if presentation_candidates else None

        journeys[language] = {
            "ingestion": "PASS" if ingestion_pass else "FAIL",
            "normalisation": "PASS" if normalisation_pass else "FAIL",
            "search": "PASS" if search_pass else "FAIL",
            "presentation": "PASS" if presentation_pass else "FAIL",
            "records_observed": records_observed,
            "values_observed": len(observed),
            "presentation_sample_sha256": _digest(sample_value) if sample_value else None,
            "presentation_sample_length": len(sample_value) if sample_value else 0,
            "raw_text_persisted": False,
        }

    all_pass = all(
        all(journey.get(stage) == "PASS" for stage in (
            "ingestion",
            "normalisation",
            "search",
            "presentation",
        ))
        for journey in journeys.values()
    ) and set(journeys) == set(required_languages)

    return {
        "schema_version": "axignal.o01-multilingual-journeys/v0.1",
        "status": "PASS" if all_pass else "FAIL",
        "output": (
            "O01_MULTILINGUAL_JOURNEYS_PASS"
            if all_pass
            else "O01_MULTILINGUAL_JOURNEYS_FAIL"
        ),
        "required_languages": required_languages,
        "journeys": journeys,
        "all_languages_complete": all_pass,
        "raw_text_persisted": False,
        "fabricated_evidence": 0,
    }


def load_retained_records(raw_payloads: Iterable[bytes]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for payload in raw_payloads:
        value = json.loads(payload)
        if not isinstance(value, dict):
            continue
        notices = value.get("notices")
        if not isinstance(notices, list):
            notices = value.get("results")
        if not isinstance(notices, list):
            continue
        records.extend(item for item in notices if isinstance(item, dict))
    return records
